"""Symmetric Hausdorff distance between two meshes.

v1 APPROXIMATION: this compares vertex sets via a KD-tree, i.e. it computes a
*vertex-to-vertex* Hausdorff distance, not the exact point-to-surface distance
the judge uses. It is fast and a reasonable early proxy because the 5%-of-
diagonal tolerance is loose and rarely the binding constraint. Upgrade path:
sample points across faces (or use point-to-triangle queries) for the directed
distances. See README "Known calibration gaps".
"""

from scipy.spatial import cKDTree


def directed_hausdorff(Va, Vb):
    """max over a in Va of distance to nearest vertex in Vb."""
    tree_b = cKDTree(Vb)
    d, _ = tree_b.query(Va, k=1)
    return float(d.max())


def symmetric_hausdorff(Va, Vb):
    return max(directed_hausdorff(Va, Vb), directed_hausdorff(Vb, Va))
