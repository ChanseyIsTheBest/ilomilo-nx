#!/usr/bin/env python3
"""ilomilo-nx (2026-11-25): where the web installer finds ilomilo's shaders in the player's game files.

83 of the build's 218 shaders are containers in default.xex (with the title update applied: the installer applies it
in the page). The other 135 are in startup.par (a ZIP archive), in the compiled effects `shaders/xbox/*.fxo`, each
entry deflated (ZIP method 8: raw deflate) or stored (method 0). One record per entry that holds a wanted container:
the entry's data offset in the archive, its stored and decoded sizes, its coding (`deflate_raw` or `raw`; the
installer's lib/sources.js) and where each container lies in the decoded bytes. Numbers and hashes only, no game data:
it goes into the installer's release/manifest.json (tools/make_release.py --records).

  python tools/ilomilo_shader_records.py --game D:/ilomilo/game --wanted out/renut_shader_dump --image out/renut_image.bin \
      --out out/ilomilo_shader_records.json
"""
import argparse
import hashlib
import json
import os
import struct
import sys
import zipfile

import xxhash

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from renut_shader_dump import find_shader_headers  # noqa: E402


def containers(data):
    for h in find_shader_headers(data):
        virt, phys = struct.unpack_from('>II', data, h + 4)
        blob = data[h:h + virt + phys]
        if len(blob) == virt + phys:
            kind = 'vs' if struct.unpack_from('>I', data, h)[0] & 1 else 'ps'
            yield h, blob, f'{kind}_{xxhash.xxh3_64_hexdigest(blob)}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', required=True)
    ap.add_argument('--wanted', required=True)
    ap.add_argument('--image', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    wanted = {n[:-4].lower() for n in os.listdir(a.wanted) if n.endswith('.bin')}
    image = open(a.image, 'rb').read()
    in_image = {n: hashlib.sha256(b).hexdigest() for _, b, n in containers(image)}
    rest = wanted - set(in_image)
    print(f'{len(wanted)} shaders: {len(wanted & set(in_image))} in the image, {len(rest)} to find in the files')
    records = []
    missing = set(rest)
    for rel in ('Data/startup.par', 'Data/arch0.par', 'Data/arch1.par', 'Data/arch2.par', 'Data/arch3.par'):
        path = os.path.join(a.game, rel)
        if not os.path.exists(path) or not missing:
            continue
        raw = open(path, 'rb').read()
        with zipfile.ZipFile(path) as z:
            for info in z.infolist():
                if not info.file_size or not missing:
                    continue
                data = z.read(info)
                here = []
                for at, blob, n in containers(data):
                    if n in missing:
                        here.append({'at': at, 'length': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()})
                        missing.discard(n)
                if not here:
                    continue
                # The entry's data starts after its local header (30 bytes), its name and its extra field.
                lh = info.header_offset
                if raw[lh:lh + 4] != b'PK\x03\x04':
                    sys.exit(f'{rel}: no local header at {lh} for {info.filename}')
                name_len, extra_len = struct.unpack_from('<HH', raw, lh + 26)
                offset = lh + 30 + name_len + extra_len
                if info.compress_type not in (0, 8):
                    sys.exit(f'{rel}:{info.filename}: ZIP method {info.compress_type}')
                records.append({'file': rel, 'offset': offset, 'stored': info.compress_size, 'size': info.file_size,
                                'codec': 'deflate_raw' if info.compress_type == 8 else 'raw',
                                'entry': info.filename, 'containers': here})
    if missing:
        sys.exit(f'{len(missing)} shaders are in no record, e.g. {sorted(missing)[:3]}')
    out = {'image_sha256': sorted(v for k, v in in_image.items() if k in wanted), 'files': records}
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=1)
    print(f'{len(records)} records hold the {len(rest)}: {sum(r["stored"] for r in records) / 1e6:.2f} MB to read, '
          f'{sum(r["size"] for r in records) / 1e6:.2f} MB decoded -> {a.out}')


if __name__ == '__main__':
    main()
