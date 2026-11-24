#!/usr/bin/env python3
"""ilomilo-nx (2026-11-24): rewrites Renut's hard-coded Direct3D device offsets and guest data addresses from Beautiful
Katamari's (XDK 2.0.5632, the base's layout) to ilomilo's (XDK 2.0.20209). docs/ilomilo-notes.md, "The device
layout", has the evidence.

The zones come from tools/device_offset_votes.py (aligned D-form displacements of the 313 paired hooks: 0 below 10944,
then +12, the declaration +180, +184 to the clear colour, +192 to the ring words, then +216 / +220 / +224 / +232 word by
word, +236 from the command buffer, +240 after the gamma ramp, +244 / +248 at the display mode, +1928 / +1936 at the
end); every value they give for a named field equals bangaio-nx's (Bangai-O HD, the same XDK build, its own
measurement: tools/renut_device_offsets_bangaio.py) where both have it. Values that fall in no zone are reported, not
rewritten.

The sites are out/renut_map/offset_sites.txt (tools/renut_offset_sites.py: literals 10944..24191 / 0x2AC0..0x5E7F in
Renut's code). Data addresses are rewritten wherever they appear in code. Lines already rewritten carry `ilomilo-nx`
and are skipped.

  python tools/renut_device_offsets_ilomilo.py [--dry-run]
"""
import argparse
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPU = os.path.join(ROOT, 'app', 'src', 'renut_engine', 'gpu')
NUM = re.compile(r'(?<![0-9A-Za-z_.])(0x[0-9A-Fa-f]+|\d+)((?:u|U)?)(?![0-9A-Za-z_.])')

ZONES = [
    (0, 10943, 0),            # the public part, the fences and flags: the same (149 offsets voted, all 0)
    (10944, 11811, 12),       # 10996 -> 11008, 11000 -> 11012 (CBlocker_Check, BlockUntilIdle)
    (11812, 11812, 180),      # the vertex declaration 0x2E24 -> 0x2ED8 (SetVertexDeclaration; bangaio-nx 0x2ED8)
    (11813, 13183, 184),      # the private render state, the snapshot's tail, tiling: 11816 -> 12000 ... 13172 -> 13356
    (13184, 13351, 192),      # clear colour / Z / stencil (bangaio-nx 0x3440 / 0x3450 / 0x3454), InKickOff 13216 -> 13408
    (13352, 13352, 216),      # KickOff / KickOffSegment
    (13360, 13360, 220),      # KickOffSegment
    (13428, 13447, 224),      # VerticesRingEnd 0x3474 -> 0x3554 (EndIndexedVertices sub_82216AC0 reads 13652)
    (13480, 13491, 232),      # the export words 0x34A8-0x34B0 -> 0x3590-0x3598 (bangaio-nx; its BeginExport reads 13716)
    (13492, 16516, 236),      # the command buffer 13492 -> 13728 ... the gamma ramp 0x3A84 -> 0x3B70
    (16517, 21511, 240),      # SwapCount 16536 -> 16776, 16684 -> 16924, the side buffer 16704 -> 16944, 21508 -> 21748
    (21512, 21564, 244),      # display mode 21516-21528 -> 21760-21772, the -1 words 21532/6 -> 21776/80, perf 21560 -> 21804
    (21590, 21639, 248),      # 21592 -> 21840, 21596 -> 21844 (Swap)
    (21640, 22259, 1928),     # 21640 -> 23568, the title's -1 21672 -> 23600, 22244/8 -> 24172/6
    (22260, 22271, 1936),     # 22260 -> 24196, BehaviorFlags 22264 -> 24200
]
EXPLICIT = {
    0x5700: 0x5F00,  # kDeviceAllocSize: ilomilo's Direct3D_CreateDevice sub_8220E8A8 allocates 0x5F00 (as Bangai-O)
    0x2DF8: 0x2EAC,  # draw.h's end of the unread words: bangaio-nx's 0x2EAC (N&B 0x2E00 + 172), before the declaration
    11776: 11904,    # the delta chain's private unread end, a 64-byte chunk boundary (bangaio-nx 11904 at XDK 20209)
}
NOT_OFFSETS = {0x3FFF, 0x4000, 0x3C00, 0x2B00}  # masks, sizes, Renut's own struct split (d3d.h pad_2AA4)
SKIP_FILES = {'banjo_renut_tuning.cpp', 'banjo_renut_record.cpp', 'render/pipeline.cpp', 'render/surfaces.cpp',
              'render/textures.cpp'}
# kStateTagChunks' range (d3d_native.h:82) is rewritten by hand, its start and size together; queued.cpp:106 is text about
# N&B's and SA2's numbers.
SKIP_LINES = {('d3d/d3d_native.h', 82), ('backend/queued.cpp', 106)}

# Beautiful Katamari's guest data -> ilomilo's (tools/d3d_data_addrs_ilomilo.py: the address constants of paired
# functions, Bangai-O's as bangaio-nx found them; constants checked byte for byte).
DATA = {
    0x82AD93F8: 0x824B4A48,  # the XDK build qword (0x000200004EF1xxxx: 2.0.20209)
    0x82000750: 0x8200072C,  # VdGlobalDevice's import record (17 aligned uses)
    0x820FC1F8: 0x8201A930,  # D3DCAPS9, 304 bytes (GetDeviceCaps)
    0x820FAEB4: 0x8201A010,  # the full viewport constant, 24 bytes
    0x8315DFE0: 0x826C3500,  # XPhysicalAlloc's no-large-pages flag
    0x820FA9D0: 0x8201A0E0,  # the format table, 128 bytes (13 aligned uses)
    0x8315E830: 0x826C1860,  # the HiZ owner
    0x82AD8E48: 0x824B4440,  # the render state table
    0x82AD9308: 0x824B4900,  # the sampler state table
}


def ilo_offset(v):
    if v in EXPLICIT:
        return EXPLICIT[v]
    for lo, hi, d in ZONES:
        if lo <= v <= hi:
            return v + d
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    by_file = {}
    for line in open(os.path.join(ROOT, 'out', 'renut_map', 'offset_sites.txt'), encoding='utf-8'):
        rel, num = line.split(':', 2)[:2]
        if rel in SKIP_FILES or (rel, int(num)) in SKIP_LINES:
            continue
        by_file.setdefault(rel, set()).add(int(num))
    files = set(by_file)
    for dirpath, _, names in os.walk(GPU):
        for n in names:
            if n.endswith(('.cpp', '.h', '.inc')):
                files.add(os.path.relpath(os.path.join(dirpath, n), GPU).replace('\\', '/'))
    report, unknown = [], []
    for rel in sorted(files):
        path = os.path.join(GPU, rel)
        raw = open(path, encoding='utf-8', newline='').read()
        nl = '\r\n' if '\r\n' in raw else '\n'
        lines = raw.split(nl)
        changed = False
        for i, line in enumerate(lines):
            if 'ilomilo-nx' in line:
                continue
            cut = line.find('//')
            head, tail = (line, '') if cut < 0 else (line[:cut], line[cut:])
            new_head = head
            what = []
            for old, new in DATA.items():
                for s in ('0x%08X' % old, '0x%08x' % old):
                    if s in new_head:
                        new_head = new_head.replace(s, '0x%08X' % new)
                        what.append(f'{s}->0x{new:08X}')
            if (i + 1) in by_file.get(rel, ()):
                def sub(m):
                    s, suffix = m.group(1), m.group(2)
                    hexa = s.lower().startswith('0x')
                    v = int(s, 16) if hexa else int(s)
                    in_range = (0x2AC0 <= v < 0x5E80) if hexa else (10944 <= v < 24192)
                    if not in_range or v in NOT_OFFSETS:
                        return m.group(0)
                    k = ilo_offset(v)
                    if k is None:
                        unknown.append(f'{rel}:{i + 1}: {s} has no zone: {line.strip()[:120]}')
                        return m.group(0)
                    if k == v:
                        return m.group(0)
                    what.append(f'{s}->{("0x%X" % k) if hexa else k}')
                    return (('0x%X' % k) if hexa else str(k)) + suffix
                new_head = NUM.sub(sub, new_head)
            if new_head != head:
                if tail:
                    lines[i] = new_head + tail + ' (ilomilo-nx: ' + ', '.join(what) + ')'
                else:
                    lines[i] = new_head.rstrip() + '  // ilomilo-nx: ' + ', '.join(what)
                changed = True
                report.append(f'{rel}:{i + 1}: {", ".join(what)}')
        if changed and not a.dry_run:
            open(path, 'w', encoding='utf-8', newline='').write(nl.join(lines))
    out = os.path.join(ROOT, 'out', 'renut_map', 'offsets_report_ilomilo.txt')
    open(out, 'w', encoding='utf-8').write('\n'.join(report + ['', '# no zone:'] + unknown) + '\n')
    print(f'{len(report)} lines rewritten{" (dry run)" if a.dry_run else ""}, {len(unknown)} literals with no zone; {out}')
    for u in unknown:
        print('  ' + u)


if __name__ == '__main__':
    main()
