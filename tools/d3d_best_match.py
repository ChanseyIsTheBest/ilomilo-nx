#!/usr/bin/env python3
"""ilomilo-nx (2026-11-24): the ilomilo functions most like a reference (Bangai-O) function, by the token alignment
of tools/d3d_propagate_ilomilo.py (difflib ratio over opcode / register tokens), for the hooks the propagation left
unpaired. Prints the best few with their ratio and length.

  python -I tools/d3d_best_match.py BANGAIO_ADDR [ADDR ...] [--lo 0x82200000 --hi 0x82240000] [--top 4]
"""
import argparse
import difflib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from d3d_propagate_ilomilo import Img, starts_of, REF_CODE, TGT_CODE, ROOT  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('addrs', nargs='+')
    ap.add_argument('--ref', default='D:/bango/bangaio-nx')
    ap.add_argument('--ref-image', default='')  # another reference (the base's Katamari: out/renut_image.bin)
    ap.add_argument('--ref-gen', default='')
    ap.add_argument('--lo', default=hex(TGT_CODE[0]))
    ap.add_argument('--hi', default=hex(TGT_CODE[1]))
    ap.add_argument('--top', type=int, default=4)
    a = ap.parse_args()
    R = Img(a.ref_image or os.path.join(a.ref, 'out', 'renut_image.bin'),
            starts_of(a.ref_gen or os.path.join(a.ref, 'app', 'generated')),
            0x82000000 if a.ref_image else REF_CODE[0], 0x83000000 if a.ref_image else REF_CODE[1])
    T = Img(os.path.join(ROOT, 'out', 'renut_image.bin'), starts_of(os.path.join(ROOT, 'app', 'generated')),
            int(a.lo, 16), int(a.hi, 16))
    for s in a.addrs:
        r = int(s, 16)
        if r not in R.f:
            print(f'{r:08X}: not a Bangai-O function start')
            continue
        rt = R.f[r][1]
        best = []
        for t, (w, tt) in T.f.items():
            if not 0.5 * len(rt) <= len(tt) <= 2.0 * len(rt) + 4:
                continue
            sm = difflib.SequenceMatcher(None, rt, tt, autojunk=False)
            if sm.real_quick_ratio() < 0.5 or sm.quick_ratio() < 0.5:
                continue
            best.append((sm.ratio(), t, len(tt)))
        best.sort(reverse=True)
        print(f'{r:08X} ({len(rt)} insns): ' + ', '.join(f'{t:08X} {q:.3f} ({n})' for q, t, n in best[:a.top]))


if __name__ == '__main__':
    main()

