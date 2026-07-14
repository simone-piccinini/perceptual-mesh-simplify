#!/usr/bin/env python3
"""noisegen — add CORRELATED (band-limited) normal-displacement noise to a solver-format mesh.

The 3.C.1 de-bias recipe, done at the frequency that matters: iid per-vertex noise vanishes after
decimation+refine (above the rung's Nyquist); ring-SMOOTHED noise survives in the rendered normal
field at the c3 rung. Amplitude is set AFTER smoothing (rescaled to a fraction of bbox diag).

usage: py -3 noisegen.py in.obj out.obj --amp 0.002 --rings 2 [--seed 7]
"""
import argparse
import numpy as np

def read_solver(p):
    with open(p) as f:
        nv, nf = map(int, f.readline().split())
        V = np.empty((nv, 3)); F = np.empty((nf, 3), dtype=np.int64)
        for i in range(nv): V[i] = f.readline().split()[1:4]
        for i in range(nf): F[i] = f.readline().split()[1:4]
    return V, F - 1

def write_solver(V, F, p):
    with open(p, "w", newline="\n") as f:
        f.write(f"{len(V)} {len(F)}\n")
        for x, y, z in V: f.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
        for t in F + 1: f.write(f"f {t[0]} {t[1]} {t[2]}\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--amp", type=float, required=True, help="post-smoothing RMS, fraction of bbox diag")
    ap.add_argument("--rings", type=int, default=2, help="smoothing iterations (correlation radius)")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    V, F = read_solver(a.inp)
    n = len(V)
    # vertex normals (area-weighted)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    N = np.zeros_like(V)
    for k in range(3): np.add.at(N, F[:, k], fn)
    L = np.linalg.norm(N, axis=1); L[L == 0] = 1; N /= L[:, None]
    # adjacency (uniform) for ring smoothing
    src = np.concatenate([F[:, 0], F[:, 1], F[:, 2], F[:, 1], F[:, 2], F[:, 0]])
    dst = np.concatenate([F[:, 1], F[:, 2], F[:, 0], F[:, 0], F[:, 1], F[:, 2]])
    deg = np.zeros(n); np.add.at(deg, src, 1.0); deg[deg == 0] = 1
    rng = np.random.default_rng(a.seed)
    s = rng.standard_normal(n)
    for _ in range(a.rings):
        acc = np.zeros(n); np.add.at(acc, src, s[dst])
        s = 0.5 * s + 0.5 * (acc / deg)          # half-lazy smoothing keeps some mid-frequency
    diag = float(np.linalg.norm(V.max(0) - V.min(0)))
    s *= (a.amp * diag) / max(1e-30, float(np.sqrt((s ** 2).mean())))   # rescale AFTER smoothing
    write_solver(V + N * s[:, None], F, a.out)
    print(f"wrote {a.out}  (amp={a.amp} diag, rings={a.rings}, rms={a.amp*diag:.5g})")

if __name__ == "__main__":
    main()
