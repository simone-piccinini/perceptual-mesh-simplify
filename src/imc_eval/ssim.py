"""SSIM with an 11x11 box window and foreground-only averaging.

Matches the statement: mean/variance over an 11x11 sliding window, constants
k1 = 0.01, k2 = 0.03, L = 255, and a window is averaged in only if its centre
pixel is non-background in the original OR the simplified render (coverage).
"""

import numpy as np
from scipy.ndimage import uniform_filter

WIN = 11
RAD = WIN // 2          # 5
C1 = (0.01 * 255.0) ** 2
C2 = (0.03 * 255.0) ** 2


def _ssim_map(X, Y):
    """Per-pixel SSIM map using uniform (box) 11x11 local statistics."""

    """ compute the mean """
    mu_x = uniform_filter(X, WIN)
    mu_y = uniform_filter(Y, WIN)
    mu_x2 = mu_x * mu_x
    mu_y2 = mu_y * mu_y
    mu_xy = mu_x * mu_y

    """ compute the variance """
    sigma_x = uniform_filter(X * X, WIN) - mu_x2
    sigma_y = uniform_filter(Y * Y, WIN) - mu_y2

    sigma_xy = uniform_filter(X * Y, WIN) - mu_xy

    num = (2.0 * mu_xy + C1) * (2.0 * sigma_xy + C2)
    den = (mu_x2 + mu_y2 + C1) * (sigma_x + sigma_y + C2)
    return num / den


""" this is to put away the useless background pixels, which would otherwise mess up the SSIM stats."""
def _masked_mean(smap, mask):
    """Average the SSIM map over valid (fully in-image) foreground windows."""
    s = smap[RAD:-RAD, RAD:-RAD]
    m = mask[RAD:-RAD, RAD:-RAD]
    if m.sum() == 0:
        return 1.0
    return float(s[m].mean())


def ssim_normal(nX, nY, cov):
    """SSIM of the RGB normal map: per channel, then averaged over channels."""
    vals = []
    for c in range(3):
        vals.append(_masked_mean(_ssim_map(nX[:, :, c], nY[:, :, c]), cov))
    return float(np.mean(vals))


def ssim_depth(dX, dY, cov):
    return _masked_mean(_ssim_map(dX, dY), cov)
