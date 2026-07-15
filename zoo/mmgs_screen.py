#!/usr/bin/env python3
"""mmgs_screen — run MMGS anisotropic remesh on a judge-format proxy at a target vertex count.

Converts judge-format OBJ -> Medit .mesh, bisects -hausd to hit the vertex target,
converts the result back to judge format for the oracle.
"""
import argparse, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MMGS = os.path.join(HERE, "mmg", "bin", "mmgs.exe")


def read_judge(path):
    tok = open(path).read().split()
    nv, nf = int(tok[0]), int(tok[1]); i = 2
    V, F = [], []
    for _ in range(nv):
        V.append((float(tok[i + 1]), float(tok[i + 2]), float(tok[i + 3]))); i += 4
    for _ in range(nf):
        F.append((int(tok[i + 1]), int(tok[i + 2]), int(tok[i + 3]))); i += 4
    return V, F


def write_judge(V, F, path):
    with open(path, "w", newline="\n") as f:
        f.write(f"{len(V)} {len(F)}\n")
        for x, y, z in V:
            f.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
        for a, b, c in F:
            f.write(f"f {a} {b} {c}\n")


def write_medit(V, F, path):
    with open(path, "w", newline="\n") as f:
        f.write("MeshVersionFormatted 2\nDimension 3\n")
        f.write(f"Vertices\n{len(V)}\n")
        for x, y, z in V:
            f.write(f"{x:.9g} {y:.9g} {z:.9g} 0\n")
        f.write(f"Triangles\n{len(F)}\n")
        for a, b, c in F:
            f.write(f"{a} {b} {c} 0\n")
        f.write("End\n")


def read_medit(path):
    lines = open(path).read().split("\n")
    V, F = [], []
    i = 0
    while i < len(lines):
        w = lines[i].strip()
        if w == "Vertices":
            n = int(lines[i + 1]); i += 2
            for k in range(n):
                p = lines[i + k].split()
                V.append((float(p[0]), float(p[1]), float(p[2])))
            i += n
        elif w == "Triangles":
            n = int(lines[i + 1]); i += 2
            for k in range(n):
                p = lines[i + k].split()
                F.append((int(p[0]), int(p[1]), int(p[2])))
            i += n
        else:
            i += 1
    return V, F


def run_mmgs(mesh_in, mesh_out, hausd, extra):
    cmd = [MMGS, "-in", mesh_in, "-out", mesh_out, "-hausd", f"{hausd:.6g}", "-v", "1"] + extra
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    m = re.search(r"NUMBER OF VERTICES\s+(\d+)", r.stdout)
    nv = int(m.group(1)) if m else None
    return nv, r.stdout, r.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mesh", required=True, help="judge-format input proxy")
    ap.add_argument("--target", type=int, default=6610)
    ap.add_argument("--tol", type=int, default=60)
    ap.add_argument("--hausd0", type=float, default=2e-4, help="initial hausd guess")
    ap.add_argument("--tag", default="mmgs")
    ap.add_argument("--extra", default="-A -nr", help="extra mmgs flags (space-separated)")
    a = ap.parse_args()

    V, F = read_judge(a.mesh)
    src = os.path.join(HERE, f"{a.tag}_in.mesh")
    dst = os.path.join(HERE, f"{a.tag}_out.mesh")
    write_medit(V, F, src)
    extra = a.extra.split()

    # bisect hausd: larger hausd -> fewer vertices
    lo, hi = a.hausd0 / 64, a.hausd0 * 64  # lo = many verts, hi = few verts
    h = a.hausd0
    best = None
    for it in range(14):
        nv, out, err = run_mmgs(src, dst, h, extra)
        if nv is None:
            print(f"[{it}] hausd={h:.3g} FAILED\n{out[-800:]}\n{err[-400:]}")
            sys.exit(1)
        print(f"[{it}] hausd={h:.6g}  ->  V={nv}")
        if best is None or abs(nv - a.target) < abs(best[0] - a.target):
            Vo, Fo = read_medit(dst)
            best = (nv, h, Vo, Fo)
        if abs(nv - a.target) <= a.tol:
            break
        if nv > a.target:
            lo = h          # too many verts -> raise hausd
        else:
            hi = h
        h = (lo * hi) ** 0.5  # geometric bisection

    nv, h, Vo, Fo = best
    outp = os.path.join(HERE, f"{a.tag}_{nv}_judge.obj")
    write_judge(Vo, Fo, outp)
    print(f"\nBEST: V={nv} (hausd={h:.6g})  ->  {outp}")


if __name__ == "__main__":
    main()
