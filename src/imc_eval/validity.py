"""Structural validity checks — the cheap pass/fail gate run on every candidate.

Mirrors the judge's "Mesh Validity Constraint": vertex-count bound, valid
indices, non-degenerate faces, and a closed 2-manifold (every edge shared by
exactly two faces).
"""

from collections import defaultdict

import numpy as np

from .geometry import face_areas

DEGENERATE_AREA_EPS = 1e-15


def check_manifold(F):
    """Closed 2-manifold check: every undirected edge in exactly two faces."""
    edge_count = defaultdict(int)
    for tri in F:
        a, b, c = int(tri[0]), int(tri[1]), int(tri[2])
        for x, y in ((a, b), (b, c), (c, a)):
            key = (x, y) if x < y else (y, x)
            edge_count[key] += 1
    bad = sum(1 for n in edge_count.values() if n != 2)
    if bad == 0:
        return True, "every edge shared by exactly 2 faces"
    return False, f"{bad} edge(s) not shared by exactly 2 faces"


def check_validity(V, F, v_orig):
    """Return a dict of per-rule booleans plus an aggregate `all_ok`."""
    nv = len(V)
    nf = len(F)
    res = {"nv": nv, "nf": nf, "v_orig": v_orig}

    res["vertex_count_ok"] = bool(1 <= nv <= v_orig)
    res["indices_ok"] = bool(((F >= 0) & (F < nv)).all()) if nf > 0 else False

    if res["indices_ok"]:
        areas = face_areas(V, F)
        res["min_area"] = float(areas.min())
        res["nondegenerate_ok"] = bool((areas > DEGENERATE_AREA_EPS).all())
        man_ok, man_detail = check_manifold(F)
        res["manifold_ok"] = man_ok
        res["manifold_detail"] = man_detail
    else:
        res["min_area"] = 0.0
        res["nondegenerate_ok"] = False
        res["manifold_ok"] = False
        res["manifold_detail"] = "skipped (invalid indices)"

    res["all_ok"] = bool(
        res["vertex_count_ok"]
        and res["indices_ok"]
        and res["nondegenerate_ok"]
        and res["manifold_ok"]
    )
    return res
