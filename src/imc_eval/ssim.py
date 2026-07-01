"""SSIM with an 11x11 window and foreground-only averaging.

Matches the statement: mean/variance over an 11x11 sliding window, constants
k1 = 0.01, k2 = 0.03, L = 255, and a window is averaged in only if its centre
pixel is non-background in the original OR the simplified render (coverage).

The statement says only "11x11"; it does NOT say whether the window is a uniform
(box) average or a Gaussian one (Wang 2004 uses Gaussian, sigma 1.5). That choice
is an oracle guess, so it is configurable via OracleConfig.ssim_window. The default
is "box" and is bit-for-bit identical to the original implementation.
"""

import numpy as np
from scipy.ndimage import uniform_filter, gaussian_filter

from .config import DEFAULT_CONFIG

WIN = 11
RAD = WIN // 2          # 5
C1 = (0.01 * 255.0) ** 2
C2 = (0.03 * 255.0) ** 2


def _make_filter(cfg):
    """Return the local-window operator a -> windowed-mean(a)."""
    if cfg.ssim_window == "box":
        # IDENTICAL to the original: uniform_filter over the 11x11 box.
        return lambda a: uniform_filter(a, WIN)
    # Gaussian window (Wang 2004): truncate so the kernel spans the 11-px window.
    sigma = cfg.gaussian_sigma
    truncate = RAD / sigma
    return lambda a: gaussian_filter(a, sigma, truncate=truncate)


def _ssim_map(X, Y, filt):
    """Per-pixel SSIM map using the given local-window operator `filt`."""
    mu_x = filt(X)
    mu_y = filt(Y)
    mu_x2 = mu_x * mu_x
    mu_y2 = mu_y * mu_y
    mu_xy = mu_x * mu_y

    sigma_x = filt(X * X) - mu_x2
    sigma_y = filt(Y * Y) - mu_y2
    sigma_xy = filt(X * Y) - mu_xy

    num = (2.0 * mu_xy + C1) * (2.0 * sigma_xy + C2)
    den = (mu_x2 + mu_y2 + C1) * (sigma_x + sigma_y + C2)
    return num / den


def _masked_mean(smap, mask):
    """Average the SSIM map over valid (fully in-image) foreground windows."""
    s = smap[RAD:-RAD, RAD:-RAD]
    m = mask[RAD:-RAD, RAD:-RAD]
    if m.sum() == 0:
        return 1.0
    return float(s[m].mean())


def ssim_normal(nX, nY, cov, cfg=DEFAULT_CONFIG):
    """SSIM of the RGB normal map: per channel, then averaged over channels."""
    filt = _make_filter(cfg)
    vals = []
    for c in range(3):
        vals.append(_masked_mean(_ssim_map(nX[:, :, c], nY[:, :, c], filt), cov))
    return float(np.mean(vals))


def ssim_depth(dX, dY, cov, cfg=DEFAULT_CONFIG):
    filt = _make_filter(cfg)
    return _masked_mean(_ssim_map(dX, dY, filt), cov)
