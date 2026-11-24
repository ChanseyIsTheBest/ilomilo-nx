#!/usr/bin/env python3
"""ilomilo-nx (2026-11-24, from bangaio-nx's tools/d3d_propagate.py, itself nights-nx's): pairs Bangai-O HD's functions
(XDK 2.0.20209, the same XDK build as ilomilo) with ilomilo's by shape and call sites, to move Renut's Direct3D hooks
from Beautiful Katamari's addresses (the base) to ilomilo's by the route

    the base's hook line `// katamari-nx: N&B sub_X`  ->  bangaio-nx's out/renut_map/nb_to_bangaio_final.json (N&B ->
    Bangai-O, three reference ports agreeing)  ->  this tool's pairs (Bangai-O -> ilomilo)

  tables  the render / sampler state tables ({getter, setter, default} rows): Bangai-O's at 0x824A3460 / 0x824A3920;
          ilomilo's found here by Bangai-O's default column word for word (101 and 20 rows);
  seeds   functions whose shape (opcode and register fields, no immediates or displacements) is unique in both images
          and equal (6 instructions or more);
  calls   for a paired function whose token sequences align (difflib over the tokens), each aligned `bl` pairs its
          two targets; repeated to a fixpoint. A target paired two different ways is a conflict and dropped.

  python -I tools/d3d_propagate_ilomilo.py [--ref D:/bango/bangaio-nx]
Writes out/renut_map/bangaio_to_ilomilo.json ({bangaio: {ilomilo, how}}) and out/renut_map/state_tables.txt.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import struct
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 0x82000000
MAX_INSNS = 3000
REF_TABLES = ((0x824A3460, 101), (0x824A3920, 20))
REF_CODE = (0x820C0000, 0x82491544)
TGT_CODE = (0x820B0000, 0x824A6B44)


def starts_of(gen):
    s = set()
    for name in os.listdir(gen):
        if name.endswith('_init.cpp'):
            for m in re.finditer(r'\{\s*0x([0-9A-Fa-f]{8}),\s*\w+\s*\}', open(os.path.join(gen, name), errors='replace').read()):
                s.add(int(m.group(1), 16))
    return sorted(s)


def token(x):
    op = x >> 26
    rd, ra, rb = (x >> 21) & 31, (x >> 16) & 31, (x >> 11) & 31
    if op in (16, 18):
        return (op, x & 1, rd if op == 16 else 0, ra if op == 16 else 0)
    if op in (19, 31, 63):
        return (op, (x >> 1) & 0x3FF, rd, ra, rb)
    if op == 59:
        return (op, (x >> 1) & 0x1F, rd, ra, rb)
    if op == 30:
        return (op, (x >> 2) & 7, rd, ra)
    if op == 4:
        return (op, x & 0x7FF, rd)
    return (op, rd, ra)


class Img:
    def __init__(self, path, starts, lo, hi):
        self.b = open(path, 'rb').read()
        self.starts = [s for s in starts if lo <= s < hi]
        self.f = {}
        for i, s in enumerate(self.starts):
            e = self.starts[i + 1] if i + 1 < len(self.starts) else s + 256
            n = min((e - s) // 4, MAX_INSNS)
            words = [struct.unpack_from('>I', self.b, s - BASE + 4 * k)[0] for k in range(n)]
            self.f[s] = (words, [token(w) for w in words])
        self.hash = {s: hashlib.sha1(repr(t).encode()).hexdigest() for s, (w, t) in self.f.items()}

    def calls(self, s):
        out = []
        for k, w in enumerate(self.f[s][0]):
            if w >> 26 == 18 and w & 1:
                d = w & 0x03FFFFFC
                if d & 0x02000000:
                    d -= 0x04000000
                out.append((k, (s + 4 * k + d) & 0xFFFFFFFF))
        return out

    def words(self, addr, n):
        return struct.unpack_from('>%dI' % n, self.b, addr - BASE)


def find_table(R, T, ref_addr, rows):
    """Where T holds a table whose default column (every third word from +8) equals R's at ref_addr."""
    ref = R.words(ref_addr, 3 * rows)
    defaults = [ref[3 * i + 2] for i in range(rows)]
    first = struct.pack('>I', defaults[0])
    hits = []
    pos = T.b.find(first)
    while pos != -1:
        a = BASE + pos - 8
        if pos % 4 == 0 and pos >= 8 and pos + 12 * rows <= len(T.b):
            w = T.words(a, 3 * rows)
            if [w[3 * i + 2] for i in range(rows)] == defaults:
                hits.append(a)
        pos = T.b.find(first, pos + 4)
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', default='D:/bango/bangaio-nx')
    a = ap.parse_args()
    R = Img(os.path.join(a.ref, 'out', 'renut_image.bin'), starts_of(os.path.join(a.ref, 'app', 'generated')),
            REF_CODE[0], REF_CODE[1])
    T = Img(os.path.join(ROOT, 'out', 'renut_image.bin'), starts_of(os.path.join(ROOT, 'app', 'generated')),
            TGT_CODE[0], TGT_CODE[1])
    out = os.path.join(ROOT, 'out', 'renut_map')
    os.makedirs(out, exist_ok=True)
    pairs, how = {}, {}
    tlog = []
    for ref_addr, rows in REF_TABLES:
        hits = find_table(R, T, ref_addr, rows)
        tlog.append(f'Bangai-O {ref_addr:08X} ({rows} rows) -> ilomilo {", ".join(f"{h:08X}" for h in hits) or "none"}')
        if len(hits) != 1:
            continue
        rw, tw = R.words(ref_addr, 3 * rows), T.words(hits[0], 3 * rows)
        for i in range(rows):
            for c in range(2):
                pr, tr = rw[3 * i + c], tw[3 * i + c]
                if pr and tr:
                    pairs[pr] = tr
                    how[pr] = f'state table {ref_addr:08X} row {i} col {c}'
    open(os.path.join(out, 'state_tables.txt'), 'w').write('\n'.join(tlog) + '\n')
    print('\n'.join(tlog))
    rh, th = Counter(R.hash.values()), Counter(T.hash.values())
    tby = {h: s for s, h in T.hash.items()}
    for s, h in R.hash.items():
        if s not in pairs and rh[h] == 1 and th.get(h) == 1 and len(R.f[s][0]) >= 6:
            pairs[s] = tby[h]
            how[s] = 'unique shape'
    conflicts = set()
    done = set()
    changed = True
    while changed:
        changed = False
        for p in list(pairs):
            n = pairs[p]
            if p in done or p not in R.f or n not in T.f:
                continue
            done.add(p)
            pt, nt = R.f[p][1], T.f[n][1]
            pc, nc = dict(R.calls(p)), dict(T.calls(n))
            if pt == nt:
                idx = [(k, k) for k in pc]
            else:
                sm = difflib.SequenceMatcher(None, pt, nt, autojunk=False)
                if sm.ratio() < 0.6:
                    continue
                idx = []
                for tag, i1, i2, j1, j2 in sm.get_opcodes():
                    if tag == 'equal' or (tag == 'replace' and i2 - i1 == j2 - j1):
                        idx += [(i1 + k, j1 + k) for k in range(i2 - i1) if i1 + k in pc]
            for i, j in idx:
                if j not in nc:
                    continue
                tp, tn = pc[i], nc[j]
                if tp in conflicts:
                    continue
                if tp in pairs:
                    if pairs[tp] != tn:
                        conflicts.add(tp)
                    continue
                pairs[tp] = tn
                how[tp] = f'call at +{4 * i:#x} of {p:08X}'
                changed = True
    for c in conflicts:
        if how.get(c, '').startswith('call'):
            pairs.pop(c, None)
    # Same shape check for every pair: equal tokens (exact), or the alignment ratio.
    res = {}
    for k, v in sorted(pairs.items()):
        if k in R.f and v in T.f:
            eq = R.f[k][1] == T.f[v][1]
            ratio = 1.0 if eq else round(difflib.SequenceMatcher(None, R.f[k][1], T.f[v][1], autojunk=False).ratio(), 3)
        else:
            eq, ratio = False, None
        res[f'{k:08X}'] = {'ilomilo': f'{v:08X}', 'how': how[k], 'same_shape': eq, 'ratio': ratio}
    json.dump(res, open(os.path.join(out, 'bangaio_to_ilomilo.json'), 'w'), indent=1)
    print('pairs', len(pairs), 'conflicts', len(conflicts), Counter(h.split(' ')[0] for h in how.values() if True))


if __name__ == '__main__':
    main()
