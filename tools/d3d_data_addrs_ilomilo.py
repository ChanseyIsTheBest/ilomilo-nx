#!/usr/bin/env python3
"""ilomilo-nx (2026-11-24): guest data addresses, Bangai-O HD -> ilomilo, by the address constants of paired functions.

For each pair of out/renut_map/bangaio_to_ilomilo.json (tools/d3d_propagate_ilomilo.py) the two instruction lists are
aligned on their tokens; every aligned `lis rX,HI` followed (within 8 instructions, same base register) by a D-form
`addi / lwz / stw / lbz / ... rY,LO(rX)` gives the address HI + LO on each side: a vote Bangai-O address -> ilomilo
address. Then the addresses Renut names (bangaio-nx's docs/bangaio-notes.md, "Guest data") are looked up, and each
.rdata constant is checked by content (the same bytes at both addresses).

  python -I tools/d3d_data_addrs_ilomilo.py [--ref D:/bango/bangaio-nx]
"""
import argparse
import collections
import difflib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from d3d_propagate_ilomilo import Img, starts_of, REF_CODE, TGT_CODE, ROOT, BASE  # noqa: E402

DFORM = {14, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 48, 49, 50, 51, 52, 53, 54, 55, 58, 62}
# (what, Bangai-O address, bytes to compare by content or 0 for a variable)
WANTED = [
    ('build qword (device +10880)', 0x824A3A68, 8),
    ('VdGlobalDevice import slot', 0x82000618, 0),
    ('D3DCAPS9', 0x8203AC28, 304),
    ('full viewport', 0x82039140, 24),
    ('XPhysicalAlloc no-large-pages flag', 0x8250C18C, 0),
    ('format table', 0x82038F90, 128),
    ('HiZ owner', 0x8250C1A4, 0),
    ('render state table', 0x824A3460, 12 * 101),
    ('sampler state table', 0x824A3920, 12 * 20),
    ('export switch NaN vertex', 0x8250C1B4, 0),
    ('export switch 512 pixels', 0x8250C1B8, 0),
]


def consts(words):
    """[(index of the lis, address)] for lis + D-form pairs."""
    out = []
    for i, w in enumerate(words):
        if w >> 26 != 15 or (w >> 16) & 31 != 0:  # lis = addis rD,0,imm
            continue
        rd = (w >> 21) & 31
        hi = (w & 0xFFFF) << 16
        for j in range(i + 1, min(i + 9, len(words))):
            x = words[j]
            op = x >> 26
            if op in DFORM and (x >> 16) & 31 == rd:
                lo = x & (0xFFFC if op in (58, 62) else 0xFFFF)
                if lo & 0x8000:
                    lo -= 0x10000
                out.append((i, (hi + lo) & 0xFFFFFFFF))
                break
            if (x >> 21) & 31 == rd and op not in (36, 37, 38, 39, 44, 45, 52, 53, 54, 55, 62):
                break  # rd rewritten
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', default='D:/bango/bangaio-nx')
    a = ap.parse_args()
    R = Img(os.path.join(a.ref, 'out', 'renut_image.bin'), starts_of(os.path.join(a.ref, 'app', 'generated')),
            REF_CODE[0], REF_CODE[1])
    T = Img(os.path.join(ROOT, 'out', 'renut_image.bin'), starts_of(os.path.join(ROOT, 'app', 'generated')),
            TGT_CODE[0], TGT_CODE[1])
    pairs = json.load(open(os.path.join(ROOT, 'out', 'renut_map', 'bangaio_to_ilomilo.json')))
    votes = collections.defaultdict(collections.Counter)
    for k, v in pairs.items():
        r, t = int(k, 16), int(v['ilomilo'], 16)
        if r not in R.f or t not in T.f:
            continue
        rw, rt = R.f[r]
        tw, tt = T.f[t]
        rc, tc = dict(consts(rw)), dict(consts(tw))
        if not rc or not tc:
            continue
        if rt == tt:
            idx = [(i, i) for i in rc]
        else:
            sm = difflib.SequenceMatcher(None, rt, tt, autojunk=False)
            idx = []
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == 'equal':
                    idx += [(i1 + o, j1 + o) for o in range(i2 - i1) if i1 + o in rc]
        for i, j in idx:
            if j in tc:
                votes[rc[i]][tc[j]] += 1
    json.dump({f'{k:08X}': {f'{x:08X}': n for x, n in c.most_common()} for k, c in sorted(votes.items())},
              open(os.path.join(ROOT, 'out', 'renut_map', 'data_votes.json'), 'w'), indent=0)
    for what, b, size in WANTED:
        c = votes.get(b)
        best = c.most_common(1)[0] if c else None
        line = f'{what:38} Bangai-O {b:08X} -> '
        if best:
            t = best[0]
            line += f'{t:08X} ({best[1]}/{sum(c.values())} votes)'
            if size:
                same = R.b[b - BASE:b - BASE + size] == T.b[t - BASE:t - BASE + size]
                line += ' same bytes' if same else ' BYTES DIFFER'
        else:
            line += 'no vote'
            if size:
                blob = R.b[b - BASE:b - BASE + size]
                hits = []
                pos = T.b.find(blob)
                while pos != -1 and len(hits) < 4:
                    hits.append(BASE + pos)
                    pos = T.b.find(blob, pos + 1)
                line += '; by content: ' + (', '.join(f'{h:08X}' for h in hits) or 'none')
        print(line)


if __name__ == '__main__':
    main()
