#!/usr/bin/env python3
"""relief_vs_closed — completion of the view-decoupling screen: honest closed-mesh
Sn(+Z) at the SAME budgets as the heightfield reliefs. If closed >= relief at every
equal N, per-view shells are dominated at all budgets and the hypothesis is airtight-dead
(the uniform-grid handicap can no longer be the excuse: adaptivity is bounded by this curve).
"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MESH = os.path.join(ROOT, "zoo", "build", "happy_unit.obj")
OUT = os.path.join(ROOT, "zoo", "build")


def read_judge(path):
    tok = open(path).read().split()
    nv, nf = int(tok[0]), int(tok[1]); i = 2
    V, F = [], []
    for _ in range(nv):
        V.append((float(tok[i+1]), float(tok[i+2]), float(tok[i+3]))); i += 4
    for _ in range(nf):
        F.append((int(tok[i+1]), int(tok[i+2]), int(tok[i+3]))); i += 4
    return V, F


def main():
    import pymeshlab
    V, F = read_judge(MESH)
    std = os.path.join(OUT, "happy_unit_std.obj")
    with open(std, "w", newline="\n") as f:
        for v in V: f.write("v %.9g %.9g %.9g\n" % v)
        for t in F: f.write("f %d %d %d\n" % t)

    for B in [464, 1273, 2626, 5972]:
        lo, hi = B, 4 * B
        best = None
        for _ in range(12):
            mid = (lo + hi) // 2
            ms = pymeshlab.MeshSet(); ms.load_new_mesh(std)
            ms.meshing_decimation_quadric_edge_collapse(targetfacenum=mid, preservetopology=True,
                                                        preservenormal=True, planarquadric=True)
            nv = ms.current_mesh().vertex_number()
            if best is None or abs(nv - B) < abs(best[0] - B):
                best = (nv, ms)
            if abs(nv - B) <= max(6, B // 60): break
            if nv > B: hi = mid
            else: lo = mid
        nv, ms = best
        mm = ms.current_mesh()
        out = os.path.join(OUT, f"closed_{nv}.obj")
        with open(out, "w", newline="\n") as f:
            f.write(f"{mm.vertex_number()} {mm.face_number()}\n")
            for p in mm.vertex_matrix(): f.write(f"v {p[0]:.9g} {p[1]:.9g} {p[2]:.9g}\n")
            for t in mm.face_matrix(): f.write(f"f {t[0]+1} {t[1]+1} {t[2]+1}\n")
        r = subprocess.run([sys.executable, "-m", "src.imc_eval.cli", "--input", MESH, "--output", out],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           cwd=ROOT, timeout=1800)
        m = re.search(r"\+Z:\s+(-?[\d.]+)\s+(-?[\d.]+)\s+->\s+(-?[\d.]+)", r.stdout + r.stderr)
        fin = re.search(r"FinalSSIM\s*:\s*([\d.]+)", r.stdout + r.stderr)
        print(f"CLOSED N={nv:5d}  +Z: {m.groups() if m else 'PARSE FAIL'}   Final6={fin.group(1) if fin else '?'}")


if __name__ == "__main__":
    main()
