"""Top-level scoring oracle: combine renderer + SSIM + Hausdorff + validity.

`evaluate(Vo, Fo, Vs, Fs)` returns a Report with the exact things the judge
reports: per-view normal/depth SSIM, FinalSSIM, the compression rate, the
Hausdorff check, structural validity, and whether the case would score.
"""

from dataclasses import dataclass

import numpy as np

from .config import DEFAULT_CONFIG
from .geometry import aabb_diagonal, build_views, face_normals
from .hausdorff import symmetric_hausdorff, symmetric_hausdorff_v2v
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
    hausdorff: float          # vertex-to-surface reading (loose)
    hausdorff_limit: float
    hausdorff_ok: bool
    hausdorff_v2v: float      # vertex-to-vertex reading (strict; CLAUDE.md says judge)
    hausdorff_v2v_ok: bool
    passed: bool          # would this case score > 0 on the judge?

    @property
    def score(self):
        return self.compression if self.passed else 0.0


def evaluate(Vo, Fo, Vs, Fs, config=DEFAULT_CONFIG):
    """Score a simplification against the original. `config` (OracleConfig) tunes the
    parameters the statement leaves ambiguous; the default reproduces the original
    behaviour bit-for-bit."""
    cfg = config
    validity = check_validity(Vs, Fs, len(Vo))

    diag = aabb_diagonal(Vo)
    haus = symmetric_hausdorff(Vo, Fo, Vs, Fs)
    haus_limit = HAUSDORFF_FRACTION * diag
    haus_ok = haus <= haus_limit
    haus_v2v = symmetric_hausdorff_v2v(Vo, Vs)
    haus_v2v_ok = haus_v2v <= haus_limit

    views = build_views()
    fno = face_normals(Vo, Fo)
    fns = face_normals(Vs, Fs)
    ztie_le = (cfg.ztie == "le")

    per_view = []
    finals = []
    for view in views:
        nO, dO, cO = render_view(Vo, Fo, fno, view, edge_eps=cfg.edge_eps, ztie_le=ztie_le)
        nS, dS, cS = render_view(Vs, Fs, fns, view, edge_eps=cfg.edge_eps, ztie_le=ztie_le)
        cov = cO | cS
        s_normal = ssim_normal(nO, nS, cov, cfg)
        s_depth = ssim_depth(dO, dS, cov, cfg)
        blended = cfg.lambda_normal * s_normal + cfg.lambda_depth * s_depth
        per_view.append({"normal": s_normal, "depth": s_depth, "blended": blended})
        finals.append(blended)

    final_ssim = float(np.mean(finals))
    ssim_ok = final_ssim >= SSIM_THRESHOLD
    compression = 100.0 - 100.0 * len(Vs) / len(Vo)
    passed = validity["all_ok"] and ssim_ok and haus_ok and haus_v2v_ok

    return Report(
        v_orig=len(Vo), v_simp=len(Vs), compression=compression,
        validity=validity, per_view=per_view,
        final_ssim=final_ssim, ssim_ok=ssim_ok,
        hausdorff=haus, hausdorff_limit=haus_limit, hausdorff_ok=haus_ok,
        hausdorff_v2v=haus_v2v, hausdorff_v2v_ok=haus_v2v_ok,
        passed=passed,
    )
