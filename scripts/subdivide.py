#!/usr/bin/env python3
"""Midpoint (Loop-topology, linear) subdivision for the contest 'nv nf' OBJ-lite format.

Usage: python3 scripts/subdivide.py < in.obj > out.obj
Each edge gains a midpoint vertex; each face becomes 4. V' = V + E, F' = 4F.
Used to build big200k/big800k proxies from armadillo (case6/case7 scale tests).
"""
import sys


def main():
    data = sys.stdin.buffer.read().split()
    nv, nf = int(data[0]), int(data[1])
    idx = 2
    verts = []
    for _ in range(nv):
        assert data[idx] == b"v"
        verts.append((float(data[idx + 1]), float(data[idx + 2]), float(data[idx + 3])))
        idx += 4
    faces = []
    for _ in range(nf):
        assert data[idx] == b"f"
        faces.append((int(data[idx + 1]) - 1, int(data[idx + 2]) - 1, int(data[idx + 3]) - 1))
        idx += 4

    emap = {}

    def mid(a, b):
        key = (a, b) if a < b else (b, a)
        m = emap.get(key)
        if m is None:
            va, vb = verts[a], verts[b]
            verts.append(((va[0] + vb[0]) / 2, (va[1] + vb[1]) / 2, (va[2] + vb[2]) / 2))
            m = len(verts) - 1
            emap[key] = m
        return m

    out_faces = []
    for a, b, c in faces:
        ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
        out_faces += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]

    w = sys.stdout.write
    w(f"{len(verts)} {len(out_faces)}\n")
    for v in verts:
        w(f"v {v[0]:.10g} {v[1]:.10g} {v[2]:.10g}\n")
    for f in out_faces:
        w(f"f {f[0] + 1} {f[1] + 1} {f[2] + 1}\n")


if __name__ == "__main__":
    main()
