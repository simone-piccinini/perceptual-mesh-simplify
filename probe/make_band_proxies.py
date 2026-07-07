#!/usr/bin/env python3
"""Regenerate the band proxy meshes + the Eigen copy the harness preflight needs.

- probe/cache/c3band.obj : fandisk midpoint-subdivided once  (25,894 v -> case-3 band)
- probe/cache/c4band.obj : c3band + a second fandisk offset in x (32,369 v -> case-4 band)
- probe/cache/eigeninc/  : resolved copy of solver/Eigen for the docker gcc:14 check
  (solver/Eigen is a symlink into homebrew, which Docker cannot mount)
"""
import os, shutil

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "probe", "cache")
os.makedirs(CACHE, exist_ok=True)

def load(path):
    V, F = [], []
    for ln in open(path):
        p = ln.split()
        if not p: continue
        if p[0] == "v": V.append(tuple(map(float, p[1:4])))
        elif p[0] == "f": F.append(tuple(int(x.split("/")[0]) - 1 for x in p[1:4]))
    return V, F

def subdivide(V, F):
    """One round of midpoint subdivision: V+E vertices, 4F faces (manifold-preserving)."""
    V = list(V); em = {}
    def mid(a, b):
        k = (a, b) if a < b else (b, a)
        if k not in em:
            em[k] = len(V)
            V.append(tuple((V[a][i] + V[b][i]) / 2 for i in range(3)))
        return em[k]
    F2 = []
    for a, b, c in F:
        ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
        F2 += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
    return V, F2

def write(path, V, F):
    with open(path, "w") as f:
        f.write(f"{len(V)} {len(F)}\n")
        for x, y, z in V: f.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
        for a, b, c in F: f.write(f"f {a+1} {b+1} {c+1}\n")
    print(f"wrote {os.path.relpath(path, ROOT)}: V={len(V)} F={len(F)}")

fan = os.path.join(ROOT, "tests", "data", "fandisk_watertight.obj")
V, F = subdivide(*load(fan))
write(os.path.join(CACHE, "c3band.obj"), V, F)              # 25,894 -> (7000, 30000]

V2, F2 = load(fan)                                          # union: shift 2nd component in x
xmax = max(v[0] for v in V); n0 = len(V)
Vu = V + [(x + (xmax + 1.0), y, z) for x, y, z in V2]
Fu = F + [(a + n0, b + n0, c + n0) for a, b, c in F2]
write(os.path.join(CACHE, "c4band.obj"), Vu, Fu)            # 32,369 -> (30000, 40000]

eig_src = os.path.realpath(os.path.join(ROOT, "solver", "Eigen"))
eig_dst = os.path.join(CACHE, "eigeninc", "Eigen")
if not os.path.isdir(eig_dst):
    shutil.copytree(eig_src, eig_dst)
    print(f"copied Eigen -> {os.path.relpath(eig_dst, ROOT)} (for docker gcc:14 preflight)")
else:
    print("Eigen copy already present")
