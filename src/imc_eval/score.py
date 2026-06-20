"""Top-level scoring oracle: combine renderer + SSIM + Hausdorff + validity.

`evaluate(Vo, Fo, Vs, Fs)` returns a Report with the exact things the judge
reports: per-view normal/depth SSIM, FinalSSIM, the compression rate, the
Hausdorff check, structural validity, and whether the case would score.
"""

from dataclasses import dataclass

import numpy as np

from .geometry import aabb_diagonal, build_views, face_normals
from .hausdorff import symmetric_hausdorff
from .render import render_view
from .ssim import ssim_depth, ssim_normal
from .validity import check_validity

SSIM_THRESHOLD = 0.9
HAUSDORFF_FRACTION = 0.05


@dataclass
class Report:
    v_orig: int
    v_simp: int
    compression: float
    validity: dict
    per_view: list
    final_ssim: float
    ssim_ok: bool
    hausdorff: float
    hausdorff_limit: float
    hausdorff_ok: bool
    passed: bool          # would this case score > 0 on the judge?

    @property
    def score(self):
        return self.compression if self.passed else 0.0


def evaluate(Vo, Fo, Vs, Fs):
    validity = check_validity(Vs, Fs, len(Vo))

    diag = aabb_diagonal(Vo)
    haus = symmetric_hausdorff(Vo, Vs)
    haus_limit = HAUSDORFF_FRACTION * diag
    haus_ok = haus <= haus_limit

    views = build_views()
    fno = face_normals(Vo, Fo)
    fns = face_normals(Vs, Fs)

    per_view = []
    finals = []
    for view in views:
        nO, dO, cO = render_view(Vo, Fo, fno, view)
        nS, dS, cS = render_view(Vs, Fs, fns, view)
        cov = cO | cS
        s_normal = ssim_normal(nO, nS, cov)
        s_depth = ssim_depth(dO, dS, cov)
        blended = 0.5 * s_normal + 0.5 * s_depth
        per_view.append({"normal": s_normal, "depth": s_depth, "blended": blended})
        finals.append(blended)

    final_ssim = float(np.mean(finals))
    ssim_ok = final_ssim >= SSIM_THRESHOLD
    compression = 100.0 - 100.0 * len(Vs) / len(Vo)
    passed = validity["all_ok"] and ssim_ok and haus_ok

    return Report(
        v_orig=len(Vo), v_simp=len(Vs), compression=compression,
        validity=validity, per_view=per_view,
        final_ssim=final_ssim, ssim_ok=ssim_ok,
        hausdorff=haus, hausdorff_limit=haus_limit, hausdorff_ok=haus_ok,
        passed=passed,
    )
