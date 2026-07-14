#!/usr/bin/env python3
"""external_check — verify the zoo's instrument with tools OUTSIDE the solver family.

Two independent checks, zero submissions:
  1. RULER CROSS-CHECK: score OUR 6610 output with src/imc_eval (the oracle = metric-truth
     Python implementation) and compare to the solver's in-process self-score S2. Documented
     self-score bias is ~+0.010 optimistic; the oracle number is the anchor.
  2. INDEPENDENT-SIMPLIFIER BOUND: MeshLab's Garland-Heckbert QEM (a genuinely different
     implementation, no SSIM refine) at the same vertex count, scored by the same oracle.
     If it comes CLOSE to our full pipeline -> our family is not at the implementation
     frontier (big signal). If it clearly loses -> confirms our edge on an independent ruler
     and bounds the upside of 'try a different kernel' from outside.

usage: py -3 zoo/external_check.py [--rung 6610]
"""
import argparse, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MESH = os.path.join(ROOT, "probe", "cache", "c3cand", "dragon_n10.obj")
BASE = os.path.join(ROOT, "zoo", "build", "base.exe")
OUT  = os.path.join(ROOT, "zoo", "build")

def read_judge(path):
    tok = open(path).read().split()
    nv, nf = int(tok[0]), int(tok[1]); i = 2
    V = []; F = []
    for _ in range(nv): V.append((float(tok[i+1]), float(tok[i+2]), float(tok[i+3]))); i += 4
    for _ in range(nf): F.append((int(tok[i+1]), int(tok[i+2]), int(tok[i+3]))); i += 4
    return V, F

def write_judge(V, F, path):
    with open(path, "w", newline="\n") as f:
        f.write(f"{len(V)} {len(F)}\n")
        for x, y, z in V: f.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
        for a, b, c in F: f.write(f"f {a} {b} {c}\n")

def oracle(inp, out):
    r = subprocess.run([sys.executable, "-m", "src.imc_eval.cli",
                        "--input", inp, "--output", out],
                       capture_output=True, text=True, cwd=ROOT, timeout=1800)
    txt = r.stdout + r.stderr
    m = re.search(r"FinalSSIM[^0-9]*([\d.]+)", txt)
    return (float(m.group(1)) if m else None), txt[-500:]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--rung", type=int, default=6610)
    a = ap.parse_args()

    # --- ours: full pipeline at the rung ---
    ours = os.path.join(OUT, f"ours_{a.rung}.obj")
    env = dict(os.environ); env["G_C3T"] = str(a.rung); env["G_S2"] = "1"
    with open(MESH, "rb") as fin:
        r = subprocess.run([BASE], stdin=fin, capture_output=True, text=True, env=env, timeout=600)
    open(ours, "w", newline="\n").write(r.stdout)
    self_s2 = re.search(r"S2=([\d.]+)", r.stderr)
    self_s2 = float(self_s2.group(1)) if self_s2 else None

    # --- independent simplifier: MeshLab QEM at the same vertex count ---
    import pymeshlab
    V, F = read_judge(MESH)
    tmp_obj = os.path.join(OUT, "dragon_std.obj")
    with open(tmp_obj, "w", newline="\n") as f:
        for v in V: f.write("v %.9g %.9g %.9g\n" % v)
        for t in F: f.write("f %d %d %d\n" % t)
    ms = pymeshlab.MeshSet(); ms.load_new_mesh(tmp_obj)
    lo, hi = 2 * a.rung - 3000, 2 * a.rung + 100   # bisect facenum to hit the vertex target
    for _ in range(12):
        mid = (lo + hi) // 2
        ms2 = pymeshlab.MeshSet(); ms2.load_new_mesh(tmp_obj)
        ms2.meshing_decimation_quadric_edge_collapse(targetfacenum=mid, preservetopology=True,
                                                     preservenormal=True, planarquadric=True)
        nv = ms2.current_mesh().vertex_number()
        if nv > a.rung: hi = mid
        else: lo = mid
        if abs(nv - a.rung) <= 3: break
    mm = ms2.current_mesh()
    ml = os.path.join(OUT, f"meshlab_{a.rung}.obj")
    write_judge([tuple(p) for p in mm.vertex_matrix()],
                [tuple(int(x) + 1 for x in t) for t in mm.face_matrix()], ml)
    print(f"meshlab QEM: {mm.vertex_number()} verts (target {a.rung})")

    # --- oracle-score both ---
    s_ours, _ = oracle(MESH, ours)
    s_ml, tail = oracle(MESH, ml)
    print("\n=== EXTERNAL VERIFICATION (oracle = metric-truth, independent of the solver) ===")
    print(f"ours   @ {a.rung}: oracle FinalSSIM = {s_ours}   (self-score S2 = {self_s2}, "
          f"bias = {None if None in (s_ours, self_s2) else '%+.4f' % (self_s2 - s_ours)})")
    print(f"meshlab@ {a.rung}: oracle FinalSSIM = {s_ml}")
    if None not in (s_ours, s_ml):
        print(f"OUR EDGE over independent QEM (same N, same oracle): {s_ours - s_ml:+.4f}")
    if s_ml is None: print("meshlab scoring failed:", tail)

if __name__ == "__main__":
    main()
