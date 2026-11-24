#!/usr/bin/env python3
"""ilomilo-nx (2026-11-24): Renut's Direct3D hooks (the base's: Beautiful Katamari's addresses, XDK 2.0.5632) moved to
ilomilo's (XDK 2.0.20209).

Each of the base's hook lines carries katamari-nx's note `N&B sub_X` (the function in banjo-nx's N&B title update 3
that the hook was written for). The route to ilomilo:
  N&B sub_X -> Bangai-O (bangaio-nx's out/renut_map/nb_to_bangaio_final.json: three reference ports that agree)
            -> ilomilo (out/renut_map/bangaio_to_ilomilo.json, tools/d3d_propagate_ilomilo.py: same XDK build)
and MANUAL below (each with its evidence) wins over both.

For every BANJO_RENUT_HOOK* / BANJO_RENUT_UNHOOKED_* line in app/src/renut_engine/gpu:
  - placed (ilomilo links the function): the macro's sub_<Katamari> becomes sub_<ilomilo>, an UNHOOKED_ form becomes
    the hooked one only with --rehook (its body was never run at Katamari's XDK: each needs a check first), and the
    note gains `ilomilo-nx: Bangai-O sub_B (how)`;
  - not placed: a HOOKED line becomes the UNHOOKED_ form (compiled, registered nowhere) at its old address, noted.
Every other `sub_<Katamari address>` (REX_EXTERN, __imp__ calls in bodies) of a moved hook is rewritten too when it is
the hook's own address. Run once on the base's tree (idempotent: a line with an `ilomilo-nx:` note is skipped).

  python -I tools/renut_hook_remap_ilomilo.py [--apply] [--rehook NAME,...] [--ref D:/bango/bangaio-nx]
Writes out/renut_map/hook_remap_report.txt.
"""
import argparse
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPU = os.path.join(ROOT, 'app', 'src', 'renut_engine', 'gpu')
HOOK = re.compile(r'\b(BANJO_RENUT_(?:UNHOOKED_)?HOOK(?:_RAW)?(?:_SHARED)?)\(\s*sub_([0-9A-Fa-f]{8})\s*(?:,\s*([A-Za-z0-9_<>:, ]+?))?\)')
NOTE = re.compile(r'N&B sub_([0-9A-Fa-f]{8})')

# Placed by hand (ilomilo address, evidence). Filled as the checks find them.
MANUAL = {
    # Keyed by the base's (Katamari's) address. tools/d3d_best_match.py against Bangai-O or the base's Katamari image,
    # then read by hand (tools/ppc_dis.py), 2026-11-24:
    '824DB7B0': ('82211068', 'D3DVertexBuffer_Unlock: Bangai-O sub_82168898 instruction for instruction (lwz r11,24(r3);'
                             ' li r5,0; rlwinm r4,r11,0,0,29; b <resource unlock 82210C58>)'),
    '824DB7C0': ('82211078', 'D3DDevice_CreateIndexBuffer: Katamari sub_824DB7C0 at 0.977 (44 instructions), next after'
                             ' VertexBuffer_Unlock as in Katamari (+0x10)'),
    '824DB8B8': ('82211128', 'the unlock after CreateIndexBuffer: Katamari sub_824DB8B8 instruction for instruction'
                             ' (lwz r4,24(r3); li r5,0; b <the same resource unlock as VertexBuffer_Unlock>)'),
    '824E0590': ('8221DFE8', 'D3DDevice_InsertCallback: Katamari sub_824E0590 at 0.864 (22 instructions, the same'
                             ' loads of +56 / +48 and the same call pattern, reordered)'),
    '824D0430': ('8220E408', 'D3DDevice_AcquireThreadOwnership: Katamari sub_824D0430 at 0.938 (+10888 read, the'
                             ' current-thread call twice, +10888 written)'),
    '824D0470': ('8220E448', 'D3DDevice_ReleaseThreadOwnership: Katamari sub_824D0470 at 1.000, right after'
                             ' AcquireThreadOwnership as in Katamari'),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', default='D:/bango/bangaio-nx')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--rehook', default='')
    ap.add_argument('--tu-map', default='D:/Banjo kazooie port/tu_v3/map/func_map.json')
    a = ap.parse_args()
    nb2b = json.load(open(os.path.join(a.ref, 'out', 'renut_map', 'nb_to_bangaio_final.json')))
    # katamari-nx's notes name N&B's title update 3 (banjo-nx since 2026-10-29); bangaio-nx's map (made from banjo-nx's
    # tree of 2026-10-28) names N&B's base game. banjo-nx's base -> update function map (its docs/title-update-3.md,
    # tools/map_functions.py), inverted: update -> base.
    fm = json.load(open(a.tu_map))
    tu2base = {}
    for b, v in fm.items():
        tu2base.setdefault(v[0].upper(), b.upper())
    b2i = json.load(open(os.path.join(ROOT, 'out', 'renut_map', 'bangaio_to_ilomilo.json')))
    rehook = set(x for x in a.rehook.split(',') if x)
    # A second route by name: bangaio-nx's own hook lines (its gpu tree), each `BANJO_RENUT_HOOK*(sub_<Bangai-O>, ...);
    # // <D3D function name>`, outside `#if 0` blocks and inside Bangai-O's code range. Used when the N&B route finds
    # nothing (bangaio-nx placed some hooks by hand: CreateDevice, Present, Release, the tiling functions ...).
    by_name = {}
    dup = set()
    bgpu = os.path.join(a.ref, 'app', 'src', 'renut_engine', 'gpu')
    for dirpath, _, files in os.walk(bgpu):
        for fn in files:
            if not fn.endswith(('.cpp', '.h', '.inc')):
                continue
            depth = 0
            for line in open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace'):
                s = line.strip()
                if s.startswith('#if'):
                    depth = depth + 1 if (depth or s.startswith('#if 0')) else 0
                    continue
                if s.startswith('#endif') and depth:
                    depth -= 1
                    continue
                if depth or s.startswith('//') or s.startswith('#define'):
                    continue
                m = HOOK.search(line)
                c = re.search(r';\s*//\s*([A-Za-z_][A-Za-z0-9_]*)', line)
                if not m or not c or 'UNHOOKED' in m.group(1):
                    continue
                addr = int(m.group(2), 16)
                if not 0x820C0000 <= addr < 0x82491544:
                    continue
                nm = c.group(1)
                if nm in by_name and by_name[nm] != m.group(2).upper():
                    dup.add(nm)
                by_name[nm] = m.group(2).upper()
    for nm in dup:
        by_name.pop(nm, None)
    report = []
    counts = {}
    for dirpath, _, files in os.walk(GPU):
        for fn in sorted(files):
            if not fn.endswith(('.cpp', '.h', '.inc')):
                continue
            path = os.path.join(dirpath, fn)
            text = open(path, encoding='utf-8', errors='replace', newline='').read()
            nl = '\r\n' if '\r\n' in text else '\n'  # keep the file's line endings
            lines = text.split(nl)
            changed = False
            for i, line in enumerate(lines):
                m = HOOK.search(line)
                if not m or line.lstrip().startswith('#define') or line.lstrip().startswith('//'):
                    continue
                macro, kat, fnname = m.group(1), m.group(2).upper(), (m.group(3) or '').strip()
                rel = os.path.relpath(path, ROOT)
                if 'ilomilo-nx:' in line:
                    counts['already'] = counts.get('already', 0) + 1
                    continue
                n = NOTE.search(line)
                nb = n.group(1).upper() if n else None
                target, why = None, ''
                if nb and nb in MANUAL:
                    target, why = MANUAL[nb]
                elif kat in MANUAL:
                    target, why = MANUAL[kat]
                elif nb:
                    nbb = tu2base.get(nb)
                    e = nb2b.get(nbb) if nbb else None
                    if e is None and nb in nb2b:  # a base-game address already
                        e = nb2b.get(nb)
                    if e and e.get('target'):
                        b = e['target'].upper()
                        p = b2i.get(b)
                        if p:
                            target = p['ilomilo']
                            why = f"Bangai-O sub_{b} ({p['how']}{'' if p['same_shape'] else ', ratio %s' % p['ratio']})"
                        else:
                            why = f'Bangai-O sub_{b} has no ilomilo pair'
                    elif e:
                        why = 'not in Bangai-O (' + e.get('why', '')[:80] + ')'
                    else:
                        why = 'N&B address not in bangaio-nx\'s map'
                else:
                    why = 'no N&B note'
                if not target:
                    c = re.search(r';\s*//\s*([A-Za-z_][A-Za-z0-9_]*)', line)
                    d3dname = c.group(1) if c else ''
                    b = by_name.get(d3dname)
                    if b:
                        p = b2i.get(b)
                        if p:
                            target = p['ilomilo']
                            why = (f"by name: bangaio-nx hooks {d3dname} at sub_{b}; Bangai-O sub_{b} ({p['how']}"
                                   f"{'' if p['same_shape'] else ', ratio %s' % p['ratio']})")
                        else:
                            why += f'; by name: Bangai-O sub_{b} has no ilomilo pair'
                unhooked = 'UNHOOKED' in macro
                name = fnname.split(',')[0].strip() if fnname else ''
                if target:
                    kind = 'placed-unhooked' if unhooked else 'placed'
                    new_macro = macro
                    if unhooked and (name in rehook or kat in rehook):
                        new_macro = macro.replace('UNHOOKED_', '')
                        kind = 'rehooked'
                    new = line[:m.start()] + new_macro + '(sub_' + target + line[m.start(2) + 8:m.end()] + line[m.end():]
                    new = new.rstrip() + f'  // ilomilo-nx: was sub_{kat}; {why}'
                else:
                    kind = 'absent-unhooked' if unhooked else 'unplaced'
                    new = line
                    if not unhooked:
                        new_macro = macro.replace('BANJO_RENUT_', 'BANJO_RENUT_UNHOOKED_')
                        new = line[:m.start()] + new_macro + line[m.start() + len(macro):]
                    new = new.rstrip() + f'  // ilomilo-nx: not placed ({why})'
                counts[kind] = counts.get(kind, 0) + 1
                report.append(f'{kind:16} {rel}:{i + 1} {name or "?"} kat={kat} nb={nb} -> {target or "-"}  {why}')
                if a.apply and new != line:
                    lines[i] = new
                    changed = True
            if a.apply and changed:
                open(path, 'w', encoding='utf-8', newline='').write(nl.join(lines))
    out = os.path.join(ROOT, 'out', 'renut_map')
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, 'hook_remap_report.txt'), 'w').write('\n'.join(report) + '\n')
    print(counts)


if __name__ == '__main__':
    main()
