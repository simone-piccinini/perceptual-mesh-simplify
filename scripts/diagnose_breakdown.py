"""D0 — per-view, per-channel SSIM breakdown (the 'diagnose first' lever).

Un-aggregates FinalSSIM into its leaves so we can read WHERE the score is lost:
  FinalSSIM = mean_v [ 0.5*N_v + 0.5*D_v ],  N_v = mean(S_nx, S_ny, S_nz)
For each (mesh, compression) it prints the 6 views x {nx, ny, nz | N_v, D_v, B_v}
plus foreground coverage, and the aggregates.

IMPORTANT — what this can and cannot tell you:
  * The six JUDGE cases are hidden meshes we never receive, and the judge returns
    only PASS/FAIL (no per-view numbers). So this runs on LOCAL PROXY meshes,
    matched by character (organic bunny/cow ~ cases 3,5; mechanical fandisk ~ case 4).
    It is a HYPOTHESIS ENGINE about the shape of the loss, not a measurement of a
    real case. Confirm every resulting idea on the judge.
  * ABSOLUTE SSIM is NOT trustworthy (oracle depth-scale / window uncalibrated, and
    we render below 1024 for speed). RELATIVE structure within a run IS trustworthy
    (both meshes go through the identical pipeline): which views/channels are weak,
    and depth-vs-normal, are faithful.
  * No C++ toolchain is present here, so the simplified mesh is produced by a QEM
    decimator (fast_simplification) as a stand-in for solver/main.cpp. Same algorithm
    CLASS (quadric edge-collapse); the loss shape is mesh+compression driven, not
    sensitive to the exact QEM implementation.

Usage:
    py scripts/diagnose_breakdown.py [--res 384] [--cases fandisk:0.83,bunny:0.67,...]
"""

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import fast_simplification as fs

from imc_eval.obj_io import load_mesh
from imc_eval.geometry import build_views, face_normals
import imc_eval.render as render
from imc_eval.render import render_view
from imc_eval.ssim import ssim_normal_channels, ssim_depth
from imc_eval.config import DEFAULT_CONFIG


def set_resolution(res):
    """Scale focal + principal point with resolution so the fixed camera frames the
    unit-sphere model identically at any render size (F = 800*res/1024, C = res/2) —
    the same rescaling the solver uses for its own sub-1024 renders. At res=1024 this
    is bit-identical to the oracle default."""
    render.FOCAL = 800.0 * res / 1024.0
    render.CU = res / 2.0
    render.CV = res / 2.0

DATA = ROOT / "tests" / "data"
VIEW_NAMES = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]


def normalize(V):
    """Center on the AABB midpoint and scale into the unit sphere, as the judge's
    input is pre-normalized. Both meshes then sit in the fixed camera frame."""
    mn, mx = V.min(0), V.max(0)
    V = V - 0.5 * (mn + mx)
    r = np.linalg.norm(V, axis=1).max()
    return V / r if r > 0 else V


def decimate(V, F, target_reduction):
    """QEM decimation stand-in (fast_simplification). target_reduction = fraction of
    faces to remove. Returns float64 verts / int64 faces."""
    Vo, Fo = fs.simplify(V.astype(np.float32), F.astype(np.int32), float(target_reduction))
    return np.asarray(Vo, np.float64), np.asarray(Fo, np.int64)


def breakdown(Vo, Fo, Vs, Fs, res, cfg=DEFAULT_CONFIG):
    """Per-view rows of per-channel normal SSIM, normal mean, depth, blend, coverage."""
    views = build_views()
    fno, fns = face_normals(Vo, Fo), face_normals(Vs, Fs)
    rows = []
    for name, view in zip(VIEW_NAMES, views):
        nO, dO, cO = render_view(Vo, Fo, fno, view, W=res, H=res)
        nS, dS, cS = render_view(Vs, Fs, fns, view, W=res, H=res)
        cov = cO | cS
        ch = ssim_normal_channels(nO, nS, cov, cfg)     # [nx, ny, nz]
        Nv = float(np.mean(ch))
        Dv = ssim_depth(dO, dS, cov, cfg)
        Bv = cfg.lambda_normal * Nv + cfg.lambda_depth * Dv
        fg = 100.0 * cov.mean()
        rows.append((name, ch[0], ch[1], ch[2], Nv, Dv, Bv, fg))
    return rows


def print_table(title, rows):
    print("\n" + "=" * len(title))
    print(title)
    print("=" * len(title))
    print(f"{'view':>5} | {'nx':>6} {'ny':>6} {'nz':>6} | {'N_v':>6} {'D_v':>6} | {'B_v':>6} | {'fg%':>5}")
    print("-" * 62)
    arr = np.array([r[1:] for r in rows])
    for r in rows:
        print(f"{r[0]:>5} | {r[1]:6.3f} {r[2]:6.3f} {r[3]:6.3f} | {r[4]:6.3f} {r[5]:6.3f} | {r[6]:6.3f} | {r[7]:5.1f}")
    m = arr.mean(0)
    print("-" * 62)
    print(f"{'mean':>5} | {m[0]:6.3f} {m[1]:6.3f} {m[2]:6.3f} | {m[3]:6.3f} {m[4]:6.3f} | {m[5]:6.3f} | {m[6]:5.1f}")
    final = float(np.mean([r[6] for r in rows]))
    print(f"\nFinalSSIM = {final:.4f}   (normal {m[3]:.4f}, depth {m[4]:.4f})")
    # quick read-off flags
    weakest = min(rows, key=lambda r: r[4]); strongest = max(rows, key=lambda r: r[4])
    spread = strongest[4] - weakest[4]
    ch_lbl = ["nx", "ny", "nz"][int(np.argmin(m[:3]))]
    print(f"read-off: depth {'SATURATED' if m[4] > 0.99 else 'has slack (%.3f)' % m[4]}"
          f" | view spread(N) {spread:.3f} ({'anisotropic->' + weakest[0] if spread > 0.03 else 'isotropic'})"
          f" | weakest channel {ch_lbl} ({m[int(np.argmin(m[:3]))]:.3f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", type=int, default=384, help="render resolution (below judge 1024 for speed)")
    ap.add_argument("--cases", type=str,
                    default="fandisk:0.83,bunny:0.67,cow:0.67,bunny:0.90,cow:0.90",
                    help="comma list of stem:compression")
    args = ap.parse_args()

    set_resolution(args.res)
    print(f"D0 breakdown | render {args.res}px | QEM stand-in = fast_simplification | box window")
    for spec in args.cases.split(","):
        stem, comp = spec.split(":")
        comp = float(comp)
        V, F = load_mesh(str(DATA / f"{stem}_watertight.obj"))
        V = normalize(V)
        Vs, Fs = decimate(V, F, comp)
        actual = 100.0 * (1 - len(Vs) / len(V))
        title = f"{stem} @ target {comp*100:.0f}%  (V {len(V)}->{len(Vs)}, {actual:.1f}%)"
        rows = breakdown(V, F, Vs, Fs, args.res)
        print_table(title, rows)


if __name__ == "__main__":
    main()
