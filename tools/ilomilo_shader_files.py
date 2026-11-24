#!/usr/bin/env python3
"""ilomilo-nx (2026-11-24): every Xenos shader container in ilomilo's data files, for Renut's shader cache.

ilomilo's `.par` archives (Data/startup.par, arch0-3.par; the DLC's dlc1.par) are ZIP files (deflate): the compiled
effects are `shaders/xbox/*.fxo` in startup.par, and arch3.par carries `cache/*.XSCH` entries. Each entry is
decompressed and scanned for containers (the flags word 0x102A11xx, tools/renut_shader_dump.py's checks, at any
4-aligned offset and, with --unaligned, any byte); loose files are scanned as they are. Each container is written as
<kind>_<xxh3>.bin into --out, and the ones --known does not have are listed (copy them into out/renut_shader_dump:
Renut skips a draw whose shader the build lacks).

  python tools/ilomilo_shader_files.py --game D:/ilomilo/game --dlc D:/ilomilo/dlc --out out/ilomilo_file_shaders
         [--known out/renut_shader_dump] [--copy] [--unaligned]
"""
import argparse
import collections
import os
import struct
import sys
import zipfile

import xxhash

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from renut_shader_dump import find_shader_headers  # noqa: E402


def containers(data, aligned):
    for h in find_shader_headers(data, aligned=aligned):
        virt, phys = struct.unpack_from('>II', data, h + 4)
        blob = data[h:h + virt + phys]
        if len(blob) == virt + phys:
            kind = 'vs' if struct.unpack_from('>I', data, h)[0] & 1 else 'ps'
            yield kind, blob


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', required=True)
    ap.add_argument('--dlc', default='')
    ap.add_argument('--out', required=True)
    ap.add_argument('--known', default='')
    ap.add_argument('--copy', action='store_true')
    ap.add_argument('--unaligned', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    known = set(os.listdir(a.known)) if a.known and os.path.isdir(a.known) else set()
    per_source = collections.Counter()
    names = {}
    for root in [r for r in (a.game, a.dlc) if r]:
        for dp, _, files in os.walk(root):
            for fn in sorted(files):
                path = os.path.join(dp, fn)
                items = []
                if fn.lower().endswith('.par'):
                    with zipfile.ZipFile(path) as z:
                        for info in z.infolist():
                            if info.file_size:
                                items.append((f'{fn}:{info.filename}', z.read(info)))
                elif fn.lower().endswith(('.xex', '.xexp', '.wmv', '.xwb', '.ttf', '.dds', '.png')):
                    continue  # the image is tools/renut_shader_dump.py's; media and textures hold none
                else:
                    items.append((os.path.relpath(path, root), open(path, 'rb').read()))
                for src, data in items:
                    for kind, blob in containers(data, not a.unaligned):
                        name = '%s_%s.bin' % (kind, xxhash.xxh3_64_hexdigest(blob))
                        names.setdefault(name, src)
                        per_source[src.split(':')[0] + (':' + src.split(':')[1].split('/')[0] if ':' in src else '')] += 1
                        p = os.path.join(a.out, name)
                        if not os.path.exists(p):
                            open(p, 'wb').write(blob)
    new = sorted(n for n in names if n not in known)
    if a.copy and a.known:
        for n in new:
            open(os.path.join(a.known, n), 'wb').write(open(os.path.join(a.out, n), 'rb').read())
    kinds = collections.Counter(n[:2] for n in names)
    print(f'{len(names)} unique containers ({kinds["vs"]} vertex, {kinds["ps"]} pixel); {len(new)} not in '
          f'{a.known or "--known"}{" (copied)" if a.copy else ""}')
    for s, n in per_source.most_common():
        print(f'  {n:5} in {s}')


if __name__ == '__main__':
    main()
