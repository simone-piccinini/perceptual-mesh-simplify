"""
Every constant here is dictated by the judge and must not be tuned:
the image is 1024x1024, focal length 800, principal point at the centre,
six cameras on the signed axes at distance D = 2.5 looking at the origin.
"""

import numpy as np

# --- evaluator constants (pinned by the statement) --------------------------
IMG_W = 1024
IMG_H = 1024
FOCAL = 800.0
CU = IMG_W / 2.0   # 512
CV = IMG_H / 2.0   # 512
OBS_DIST = 2.5


def face_normals(V, F):
    """World-space unit normal per face, from the face winding order.

    n = normalize( (p1 - p0) x (p2 - p0) ).  The sign therefore follows the
    triangle winding, so a simplifier must preserve winding to match the judge.
    """
    p0 = V[F[:, 0]]
    p1 = V[F[:, 1]]
    p2 = V[F[:, 2]]
    n = np.cross(p1 - p0, p2 - p0)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln == 0.0] = 1.0
    return n / ln


def face_areas(V, F):
    p0 = V[F[:, 0]]
    p1 = V[F[:, 1]]
    p2 = V[F[:, 2]]
    return 0.5 * np.linalg.norm(np.cross(p1 - p0, p2 - p0), axis=1)


def aabb_diagonal(V):
    """Spatial diagonal of the axis-aligned bounding box (the Hausdorff scale)."""
    mn = V.min(axis=0)
    mx = V.max(axis=0)
    return float(np.linalg.norm(mx - mn))


def build_views(dist=OBS_DIST):
    """The six axial cameras.

    Each entry is (eye, right, up, forward) where `forward` points from the
    camera toward the origin (the camera looks along its local -Z, OpenGL).
    Camera-space coords of a world point p are
        x' = (p-eye).right,  y' = (p-eye).up,  depth = (p-eye).forward
    with `depth` positive in front of the camera.

    NOTE on calibration: the six axial views and our choice of axis-aligned
    `up` vectors only ever flip / 90-rotate / permute the rendered images.
    Windowed-SSIM averaged over the six views is invariant to those, so the
    FinalSSIM number is unaffected by the exact handedness we pick here.
    """
    axes = [
        np.array([1.0, 0.0, 0.0]), np.array([-1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]), np.array([0.0, -1.0, 0.0]),
        np.array([0.0, 0.0, 1.0]), np.array([0.0, 0.0, -1.0]),
    ]
    # up vectors are axis-aligned and non-parallel to each forward direction
    ups = [
        np.array([0.0, 0.0, 1.0]), np.array([0.0, 0.0, 1.0]),
        np.array([0.0, 0.0, 1.0]), np.array([0.0, 0.0, 1.0]),
        np.array([0.0, 1.0, 0.0]), np.array([0.0, 1.0, 0.0]),
    ]
    views = []
    for a, up in zip(axes, ups):
        eye = dist * a
        forward = -a / np.linalg.norm(a)            # toward the origin
        right = np.cross(forward, up)
        right /= np.linalg.norm(right)
        true_up = np.cross(right, forward)
        true_up /= np.linalg.norm(true_up)
        views.append((eye, right, true_up, forward))
    return views
