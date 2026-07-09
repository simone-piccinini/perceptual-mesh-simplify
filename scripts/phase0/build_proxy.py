"""Build a faithful ORGANIC case-3 proxy: armadillo (49,990 v) decimated to ~V verts
with a QEM library (fast_simplification), matching case 3's real V=23,201.

Why not the harness's c3band.obj? That is subdivided *fandisk* — mechanical and
artificially smooth, wrong for diagnosing an organic registration deficit.

Run:  py scripts/phase0/build_proxy.py            # default 23201 verts
      py scripts/phase0/build_proxy.py 23201
Out:  .phase0/proxy_c3_orig.obj   (+ a validity report)
"""
import sys
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[2]
WORK = REPO / ".phase0"; WORK.mkdir(exist_ok=True)
sys.path[:0] = [str(REPO), str(REPO / "src")]

import fast_simplification as fs
from imc_eval.obj_io import load_mesh, save_mesh
from imc_eval.validity import check_validity

TARGET_V = int(sys.argv[1]) if len(sys.argv) > 1 else 23201
V, F = load_mesh(str(REPO / "tests/data/armadillo_watertight.obj"))
print(f"armadillo: V={len(V)} F={len(F)}  max|v|={np.linalg.norm(V,axis=1).max():.4f} "
      f"(must be <=1: judge input is unit-sphere-normalized)")

tr = 1 - 2 * TARGET_V / len(F)                       # F ~ 2V for a closed mesh
Vo, Fo = fs.simplify(V.astype(np.float32), F.astype(np.int32), float(tr))
Vo = np.asarray(Vo, np.float64); Fo = np.asarray(Fo, np.int64)
save_mesh(str(WORK / "proxy_c3_orig.obj"), Vo, Fo)

val = check_validity(Vo, Fo, len(Vo))
print(f"proxy_c3_orig.obj: V={len(Vo)} F={len(Fo)}  manifold_ok={val['manifold_ok']} "
      f"nondegenerate_ok={val['nondegenerate_ok']}")
print(f"  (a few non-manifold edges are fine here -- the diagnostic only renders it; "
      f"detail: {val.get('manifold_detail')})")
