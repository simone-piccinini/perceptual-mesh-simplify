"""Symmetric vertex-to-vertex Hausdorff distance (matches the judge).

Judge clarification (2026-06-18): in
    d_dir(A, B) = max_{a in A} min_{b in B} ||a - b||
both a and b range over the **vertices** of their meshes only -- the judge does
NOT iterate over interior or surface points. So this is exact vertex-to-vertex,
not an approximation:

    d_dir(A, B) = max over vertices a of A  of  distance to the nearest vertex of B
    d_H         = max( d_dir(A, B), d_dir(B, A) )

With A = original, B = simplified, the first direction is a *coverage*
constraint: every original vertex must stay within tolerance of some surviving
vertex. The reverse forbids a moved/new vertex from sitting far from every
original vertex.

DO NOT change this to point-to-surface -- that disagrees with the judge (it would
pass simplifications the judge rejects). cKDTree keeps it fast: O((V+V') log V').
"""

from scipy.spatial import cKDTree


def directed_hausdorff(Va, Vb):
    """max over vertices in Va of the distance to the nearest vertex in Vb."""
    d, _ = cKDTree(Vb).query(Va, k=1)
    return float(d.max())


def symmetric_hausdorff(Va, Vb):
    return max(directed_hausdorff(Va, Vb), directed_hausdorff(Vb, Va))
