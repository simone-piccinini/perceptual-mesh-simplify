#!/usr/bin/env python3
"""relief_test — single-view relief screen (the view-decoupling hypothesis, 2026-07-15).

Question: can a 2.5D relief serving ONE view (+Z) reach Sn(+Z) ~ 0.81+ at ~400-600 verts?
That is the per-view budget implied by leader-tier (93.77) scores under the 6-shell
construction (total N ~ 2500-3500 on c3-class). Compare against the honest closed mesh's
per-view cost (ours_6610: all 6 views from 6610v).

Crude v1 construction (conservative): faces with normal nz > eps (front-facing; includes
occluded-but-frontfacing waste -> biases AGAINST the hypothesis), open submesh, pymeshlab
QEM to budget. Score via src.imc_eval CLI (validity FAIL expected/ignored; the +Z SSIM row
is the read).

usage: py -3 zoo/relief_test.py [--mesh probe/cache/c3cand/happy_qem.obj] [--budgets 400 800 1500 3000]
"""
import argparse, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "zoo", "build")


def read_judge(path):
    tok = open(path).read().split()
    nv, nf = int(tok[0]), int(tok[1]); i = 2
    V, F = [], []
    for _ in range(nv):
        V.append((float(tok[i + 1]), float(tok[i + 2]), float(tok[i + 3]))); i += 4
    for _ in range(nf):
        F.append((int(tok[i + 1]) - 1, int(tok[i + 2]) - 1, int(tok[i + 3]) - 1)); i += 4
    return V, F


def write_judge(V, F, path):
    with open(path, "w", newline="\n") as f:
        f.write(f"{len(V)} {len(F)}\n")
        for x, y, z in V:
            f.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
        for a, b, c in F:
            f.write(f"f {a + 1} {b + 1} {c + 1}\n")


def oracle_views(inp, outp):
    r = subprocess.run([sys.executable, "-m", "src.imc_eval.cli", "--input", inp, "--output", outp],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=ROOT, timeout=1800)
    txt = r.stdout + r.stderr
    views = {}
    for m in re.finditer(r"([+-][XYZ]):\s+([\d.]+)\s+([\d.]+)\s+->\s+([\d.]+)", txt):
        views[m.group(1)] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
    fin = re.search(r"FinalSSIM\s*:\s*([\d.]+)", txt)
    return views, (float(fin.group(1)) if fin else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mesh", default=os.path.join("probe", "cache", "c3cand", "happy_qem.obj"))
    ap.add_argument("--budgets", type=int, nargs="+", default=[400, 800, 1500, 3000])
    ap.add_argument("--eps", type=float, default=0.05, help="front-facing threshold on nz")
    a = ap.parse_args()

    import numpy as np
    V, F = read_judge(os.path.join(ROOT, a.mesh))
    V = np.array(V); F = np.array(F, dtype=int)

    # front-facing (+Z) faces
    e1 = V[F[:, 1]] - V[F[:, 0]]; e2 = V[F[:, 2]] - V[F[:, 0]]
    n = np.cross(e1, e2)
    nz = n[:, 2] / (np.linalg.norm(n, axis=1) + 1e-30)
    keep = nz > a.eps
    Fk = F[keep]
    used = np.unique(Fk)
    remap = -np.ones(len(V), dtype=int); remap[used] = np.arange(len(used))
    Vr = V[used]; Fr = remap[Fk]
    print(f"relief base: {len(Vr)} verts, {len(Fr)} faces (of {len(V)}/{len(F)}; nz>{a.eps})")

    base_obj = os.path.join(OUT, "relief_base.obj")
    with open(base_obj, "w", newline="\n") as f:
        for x, y, z in Vr: f.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
        for t in Fr: f.write(f"f {t[0]+1} {t[1]+1} {t[2]+1}\n")

    import pymeshlab
    # v2 CLEAN: the raw front-facing submesh is Swiss cheese (7,441 boundary edges measured);
    # QEM on it produced garbage (Sd 0.40) while the UNDECIMATED base scores +Z 0.9945.
    # Drop micro-islands, close small holes, then decimate the clean relief.
    msc = pymeshlab.MeshSet(); msc.load_new_mesh(base_obj)
    try:
        msc.meshing_remove_connected_component_by_face_number(mincomponentsize=100)
    except Exception as e:
        print("component filter:", e)
    try:
        msc.meshing_close_holes(maxholesize=40)
    except Exception as e:
        print("close holes:", e)
    clean_obj = os.path.join(OUT, "relief_clean.obj")
    msc.save_current_mesh(clean_obj)
    print(f"cleaned relief: {msc.current_mesh().vertex_number()} verts, {msc.current_mesh().face_number()} faces")
    base_obj = clean_obj

    results = []
    for B in a.budgets:
        ms = pymeshlab.MeshSet(); ms.load_new_mesh(base_obj)
        # bisect facenum to hit the vertex budget (open mesh: V ~ F/2 + boundary/2)
        lo, hi = max(4, 2 * B - 3 * B), 4 * B
        best = None
        for _ in range(12):
            mid = (lo + hi) // 2
            ms2 = pymeshlab.MeshSet(); ms2.load_new_mesh(base_obj)
            ms2.meshing_decimation_quadric_edge_collapse(
                targetfacenum=mid, preservetopology=False, preservenormal=True,
                planarquadric=True, boundaryweight=1.0)
            nv = ms2.current_mesh().vertex_number()
            if best is None or abs(nv - B) < abs(best[0] - B):
                best = (nv, ms2)
            if abs(nv - B) <= max(10, B // 50):
                break
            if nv > B: hi = mid
            else: lo = mid
        nv, ms2 = best
        mm = ms2.current_mesh()
        relief = os.path.join(OUT, f"relief_{nv}.obj")
        write_judge([tuple(p) for p in mm.vertex_matrix()],
                    [tuple(int(x) for x in t) for t in mm.face_matrix()], relief)
        views, fin = oracle_views(os.path.join(ROOT, a.mesh), relief)
        zn, zd, zb = views.get("+Z", (None, None, None))
        print(f"RELIEF N={nv:5d}  +Z: Sn={zn} Sd={zd} blend={zb}   (FinalSSIM-6view={fin})")
        results.append((nv, zn, zd, zb))

    print("\n=== SUMMARY (+Z single view) ===")
    print("bar for 6-shell/93.77 arithmetic: Sn(+Z) >= ~0.81 at N <= ~600")
    for nv, zn, zd, zb in results:
        verdict = "PASS-BAR" if (zn is not None and zn >= 0.81 and nv <= 700) else ""
        print(f"N={nv:5d}  Sn={zn}  Sd={zd}  blend={zb}  {verdict}")


if __name__ == "__main__":
    main()
