"""D3 diagnostic: split the normal-SSIM deficit into silhouette vs interior windows.

A window is "silhouette" if its 11x11 footprint touches a background pixel of the
union coverage (orig | simp); otherwise "interior". Reports each group's share of
the total normal-SSIM deficit (sum of 1 - SSIM over counted windows), per view and
overall. Decides whether silhouette-protection machinery is worth building (Tier 2
M3) for a given case.

Usage: python scripts/deficit_split.py <original.obj> <simplified.obj>
"""

import sys

import numpy as np
from scipy.ndimage import minimum_filter

sys.path.insert(0, "src")

from imc_eval.geometry import build_views, face_normals
from imc_eval.obj_io import load_mesh
from imc_eval.render import render_view
from imc_eval.ssim import _ssim_map, _make_filter, RAD, WIN
from imc_eval.config import DEFAULT_CONFIG


def main(orig_path, simp_path):
    Vo, Fo = load_mesh(orig_path)
    Vs, Fs = load_mesh(simp_path)
    fno = face_normals(Vo, Fo)
    fns = face_normals(Vs, Fs)
    filt = _make_filter(DEFAULT_CONFIG)

    tot = {"sil": 0.0, "int": 0.0}
    cnt = {"sil": 0, "int": 0}
    names = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]
    for vi, view in enumerate(build_views()):
        nO, dO, cO = render_view(Vo, Fo, fno, view)
        nS, dS, cS = render_view(Vs, Fs, fns, view)
        cov = cO | cS
        # interior = every pixel in the 11x11 footprint is foreground
        interior = minimum_filter(cov.astype(np.uint8), WIN).astype(bool)

        smap = np.zeros(cov.shape)
        for c in range(3):
            smap += _ssim_map(nO[:, :, c], nS[:, :, c], filt) / 3.0

        s = smap[RAD:-RAD, RAD:-RAD]
        m = cov[RAD:-RAD, RAD:-RAD]
        it = interior[RAD:-RAD, RAD:-RAD]
        sil_m = m & ~it
        int_m = m & it
        d_sil = float((1.0 - s[sil_m]).sum())
        d_int = float((1.0 - s[int_m]).sum())
        tot["sil"] += d_sil
        tot["int"] += d_int
        cnt["sil"] += int(sil_m.sum())
        cnt["int"] += int(int_m.sum())
        n = max(1, int(m.sum()))
        print(f"{names[vi]}: normalSSIM={float(s[m].mean()):.4f}  "
              f"deficit sil={d_sil:9.1f} ({100*d_sil/max(1e-12,d_sil+d_int):5.1f}%)  "
              f"int={d_int:9.1f}   windows sil={int(sil_m.sum())} int={int(int_m.sum())}")

    T = tot["sil"] + tot["int"]
    print(f"\nTOTAL deficit: silhouette {tot['sil']:.1f} ({100*tot['sil']/T:.1f}%)  "
          f"interior {tot['int']:.1f} ({100*tot['int']/T:.1f}%)")
    print(f"window counts: sil {cnt['sil']} ({100*cnt['sil']/(cnt['sil']+cnt['int']):.1f}%)  "
          f"int {cnt['int']}")
    print(f"mean deficit per window: sil {tot['sil']/max(1,cnt['sil']):.4f}  "
          f"int {tot['int']/max(1,cnt['int']):.4f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
