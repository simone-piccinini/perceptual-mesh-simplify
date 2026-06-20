"""Command-line entry point: score one simplified mesh against the original.

    imc-score --input mesh.in --output mesh.out
"""

import argparse

from .obj_io import load_mesh
from .score import evaluate


def _flag(ok):
    return "OK  " if ok else "FAIL"


def print_report(r):
    line = "=" * 60
    print(line)
    print("IMC Problem B — local evaluation")
    print(line)
    print(f"vertices : {r.v_orig}  ->  {r.v_simp}")
    print(f"compression : {r.compression:.2f}%")
    print("-" * 60)
    v = r.validity
    print("Validity (Wrong Answer if any FAIL):")
    print(f"  [{_flag(v['vertex_count_ok'])}] vertex count (1 <= V' <= V)")
    print(f"  [{_flag(v['indices_ok'])}] valid face indices")
    print(f"  [{_flag(v['nondegenerate_ok'])}] non-degenerate faces (min area {v['min_area']:.2e})")
    print(f"  [{_flag(v['manifold_ok'])}] closed 2-manifold ({v['manifold_detail']})")
    print("-" * 60)
    print("Per-view SSIM   normal / depth / blended:")
    names = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]
    for name, p in zip(names, r.per_view):
        print(f"  {name}:  {p['normal']:.4f}  {p['depth']:.4f}  ->  {p['blended']:.4f}")
    print("-" * 60)
    print(f"FinalSSIM : {r.final_ssim:.4f}   [{_flag(r.ssim_ok)}] (>= 0.90)")
    print(f"Hausdorff : {r.hausdorff:.4e} / limit {r.hausdorff_limit:.4e}   [{_flag(r.hausdorff_ok)}]")
    print(line)
    if r.passed:
        print(f"RESULT: PASS  ->  scores {r.compression:.2f}%")
    else:
        print("RESULT: FAIL  ->  scores 0")
    print(line)


def main(argv=None):
    ap = argparse.ArgumentParser(description="IMC Problem B local evaluator")
    ap.add_argument("--input", required=True, help="original mesh (judge input)")
    ap.add_argument("--output", required=True, help="simplified mesh (your output)")
    args = ap.parse_args(argv)

    Vo, Fo = load_mesh(args.input)
    Vs, Fs = load_mesh(args.output)
    print_report(evaluate(Vo, Fo, Vs, Fs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
