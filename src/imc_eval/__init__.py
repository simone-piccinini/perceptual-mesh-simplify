"""Local offline evaluator for IMC 2026 Problem B (mesh simplification).

The package reimplements the judge so we can score candidate simplifications
locally instead of spending submissions:

    from imc_eval import load_mesh, evaluate
    Vo, Fo = load_mesh("mesh.in")
    Vs, Fs = load_mesh("mesh.out")
    report = evaluate(Vo, Fo, Vs, Fs)
    print(report.final_ssim, report.compression, report.passed)
"""

from .obj_io import load_mesh, save_mesh, parse_mesh
from .score import evaluate, Report
from .validity import check_validity

__all__ = [
    "load_mesh", "save_mesh", "parse_mesh",
    "evaluate", "Report", "check_validity",
]
