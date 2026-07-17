#!/usr/bin/env python3
"""alpha_grid — map the Z-saliency mechanism's HELPFUL vs HARMFUL regime across meshes.

Runs the full (proxy x alpha) grid in PARALLEL (the box is not thermal-throttled; ~1 slow-run of
wall time per wave), parses RC4 self-scores, and prints:
  * a mesh x alpha table of S2d (and dS2d vs alpha=0),
  * per-mesh best alpha + whether allocation ever helps,
  * a regime summary (does 'helps' correlate with baseline S2d / mesh difficulty?).
This is a LOCAL characterisation (proxy oracle) -- it explains WHEN the mechanism helps, not whether
a given alpha transfers to the judge (that stays a judge question, per §2.1).

  usage: py -3 scripts/alpha_grid.py [--alphas 0 0.25 0.5 ...] [--workers 5] [--metric S2d|S2]
"""
import argparse, concurrent.futures as cf, glob, json, os, re, subprocess, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN  = os.environ.get("BIN", "/tmp/mein.exe")
OUT  = os.path.join(ROOT, "handoff/alpha_grid.jsonl")

PDIR = "probe/cache/c4"

def run(mesh, alpha):
    e = dict(os.environ); e["G_ALLOC_WEIGHT"] = str(alpha)
    r = subprocess.run(f'"{BIN}" < {PDIR}/{mesh}.obj', shell=True, capture_output=True,
                       text=True, cwd=ROOT, env=e, timeout=3000)
    m = re.search(r"S2n=([\d.]+) S2d=([\d.]+) S2=([\d.]+)", r.stderr)
    return (mesh, alpha, (float(m.group(1)), float(m.group(2)), float(m.group(3))) if m else None)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alphas", nargs="+", type=float,
                    default=[0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0])
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--metric", choices=["S2d", "S2"], default="S2d")
    ap.add_argument("--dir", default="probe/cache/c4", help="proxy dir (solver-format .obj)")
    args = ap.parse_args()
    mi = {"S2n": 0, "S2d": 1, "S2": 2}[args.metric]

    global PDIR; PDIR = args.dir
    meshes = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(ROOT, PDIR, "*.obj")))
    if not os.path.exists(BIN): sys.exit(f"binary {BIN} missing -> bash scripts/winbuild.sh {BIN}")
    grid = [(m, a) for m in meshes for a in args.alphas]
    print(f"grid: {len(meshes)} meshes x {len(args.alphas)} alphas = {len(grid)} runs, {args.workers} parallel\n", flush=True)

    res = {}
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for fut in cf.as_completed([ex.submit(run, m, a) for (m, a) in grid]):
            m, a, sc = fut.result(); res[(m, a)] = sc
            print(f"  done {m} a={a} {'S2d=%.3f'%sc[mi] if sc else 'FAIL'}", flush=True)

    with open(OUT, "w") as f:
        for (m, a), sc in sorted(res.items()):
            f.write(json.dumps({"mesh": m, "alpha": a, "S2n": sc[0] if sc else None,
                                "S2d": sc[1] if sc else None, "S2": sc[2] if sc else None}) + "\n")

    # ---- table ----
    A = args.alphas
    print(f"\n=== {args.metric} : mesh x alpha  (base = alpha 0) ===")
    hdr = "mesh".ljust(11) + "base ".rjust(7) + "".join(f"a{a}".rjust(9) for a in A if a != 0)
    print(hdr); print("-" * len(hdr))
    regime = []
    for m in meshes:
        base = res.get((m, 0.0)); b = base[mi] if base else None
        row = m.ljust(11) + (f"{b:.3f}".rjust(7) if b is not None else "  FAIL ")
        best_a, best_d = 0.0, 0.0
        for a in A:
            if a == 0: continue
            sc = res.get((m, a))
            if sc and b is not None:
                d = sc[mi] - b
                row += (f"{d:+.3f}".rjust(9))
                if d > best_d: best_a, best_d = a, d
            else:
                row += "    -   ".rjust(9)
        print(row + f"   -> best a={best_a} ({best_d:+.3f})")
        regime.append((m, b, best_a, best_d))

    # ---- regime summary: does 'helps' track baseline difficulty? ----
    print("\n=== REGIME MAP (sorted by baseline; does allocation help harder meshes?) ===")
    for m, b, best_a, best_d in sorted(regime, key=lambda x: (x[1] if x[1] is not None else 9)):
        verdict = f"HELPS (peak a={best_a}, +{best_d:.3f})" if best_d > 0.005 else "no-help / harmful (best <= +0.005)"
        print(f"  {m}  base {args.metric}={b:.3f}  ->  {verdict}")
    print(f"\nraw -> {OUT}")

if __name__ == "__main__":
    main()
