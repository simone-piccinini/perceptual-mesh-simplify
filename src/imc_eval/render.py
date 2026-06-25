"""Software rasteriser reproducing the evaluator's normal and depth maps.

For each view it produces:
  - normal map  (H, W, 3) float in [0, 255], flat per-face normal encoded
                as (n + 1) * 127.5; background = 127.5 neutral gray.
  - depth map   (H, W)    float, perspective-correct camera-space depth;
                background = 255 (far plane).
  - coverage    (H, W)    bool, True where a triangle covers the pixel.

The inner rasteriser is numba-jitted when numba is available, and falls back
to pure Python otherwise (correct, just slower — fine for the small cases).
"""

""" turns a 3D shape (vertices and triangles) into a flat, 2D image made of pixels, exactly like taking a photograph. """

import numpy as np

from .geometry import IMG_W, IMG_H, FOCAL, CU, CV

try:
    from numba import njit
    HAVE_NUMBA = True
except Exception:  # numba missing or unsupported on this Python — run as plain Python
    HAVE_NUMBA = False

    def njit(*args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            return args[0]

        def deco(fn):
            return fn
        return deco


@njit(cache=True)
def _rasterize(u, v, depth, faces, H, W):
    """Z-buffered rasteriser. Returns (faceid HxW int64, zbuf HxW float64)."""
    faceid = np.full((H, W), -1, np.int64)
    zbuf = np.full((H, W), 1e30)
    M = faces.shape[0]
    for f in range(M):
        i0 = faces[f, 0]
        i1 = faces[f, 1]
        i2 = faces[f, 2]
        d0 = depth[i0]
        d1 = depth[i1]
        d2 = depth[i2]
        if d0 <= 0.0 or d1 <= 0.0 or d2 <= 0.0:
            continue  # behind the camera (does not happen for the unit-sphere meshes)
        u0 = u[i0]; v0 = v[i0]
        u1 = u[i1]; v1 = v[i1]
        u2 = u[i2]; v2 = v[i2]
        det = (v1 - v2) * (u0 - u2) + (u2 - u1) * (v0 - v2)
        if det > -1e-12 and det < 1e-12:
            continue  # zero screen area
        inv = 1.0 / det

        fminx = u0
        if u1 < fminx: fminx = u1
        if u2 < fminx: fminx = u2
        fmaxx = u0
        if u1 > fmaxx: fmaxx = u1
        if u2 > fmaxx: fmaxx = u2
        fminy = v0
        if v1 < fminy: fminy = v1
        if v2 < fminy: fminy = v2
        fmaxy = v0
        if v1 > fmaxy: fmaxy = v1
        if v2 > fmaxy: fmaxy = v2

        minx = int(np.floor(fminx)); maxx = int(np.ceil(fmaxx))
        miny = int(np.floor(fminy)); maxy = int(np.ceil(fmaxy))
        if minx < 0: minx = 0
        if miny < 0: miny = 0
        if maxx > W - 1: maxx = W - 1
        if maxy > H - 1: maxy = H - 1

        for py in range(miny, maxy + 1):
            cy = py + 0.5
            for px in range(minx, maxx + 1):
                cx = px + 0.5
                w0 = ((v1 - v2) * (cx - u2) + (u2 - u1) * (cy - v2)) * inv
                w1 = ((v2 - v0) * (cx - u2) + (u0 - u2) * (cy - v2)) * inv
                w2 = 1.0 - w0 - w1
                if w0 < -1e-9 or w1 < -1e-9 or w2 < -1e-9:
                    continue
                denom = w0 / d0 + w1 / d1 + w2 / d2
                if denom <= 0.0:
                    continue
                zP = 1.0 / denom  # perspective-correct depth
                if zP < zbuf[py, px]:
                    zbuf[py, px] = zP
                    faceid[py, px] = f
    return faceid, zbuf


def render_view(V, F, fnormals, view, W=IMG_W, H=IMG_H):
    eye, right, up, forward = view
    rel = V - eye
    xp = rel @ right
    yp = rel @ up
    dp = rel @ forward                # camera-space depth, positive in front
    safe = dp.copy()
    safe[safe == 0.0] = 1e-9
    u = FOCAL * xp / safe + CU
    v = FOCAL * yp / safe + CV

    faces = np.ascontiguousarray(F.astype(np.int64))
    faceid, zbuf = _rasterize(
        np.ascontiguousarray(u),
        np.ascontiguousarray(v),
        np.ascontiguousarray(dp),
        faces, H, W,
    )

    cov = faceid >= 0
    nimg = np.full((H, W, 3), 127.5)
    dimg = np.full((H, W), 255.0)
    if cov.any():
        ids = faceid[cov]
        nimg[cov] = (fnormals[ids] + 1.0) * 127.5
        dimg[cov] = zbuf[cov]
    return nimg, dimg, cov
