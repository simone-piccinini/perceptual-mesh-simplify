#!/usr/bin/env python3
"""check_constraints_and_fidelity — the output respects every HARD rule and the gate.

GUARANTEES: at the OPERATING POINT (max compression that stays above the perceptual
gate) the output satisfies every hard constraint of Problem B (manifold, positive
area, valid indices, Hausdorff <= 5% of the diagonal, output <= 100 MiB, orientation,
topology) AND clears FinalSSIM >= 0.90; it also checks robustness, scale (time/memory)
and stability, and proves the suite rejects a known garbage solver.
Does NOT GUARANTEE the secret judge's exact number — the perceptual part is the
oracle's ESTIMATE (with a documented uncertainty band near the gate).

Three independent test levels, kept strictly separate:

    scripts/validate_oracle.py                 level 1  "oracle reproduces known facts"
    tests/check_structural_validity.py         level 2  "output is a VALID mesh"
    tests/check_constraints_and_fidelity.py    level 3  "output respects every hard rule"

WHY A SEPARATE FILE (not an extension of the structural suite):
  - the structural suite must stay PURE: only absolute mathematics, importing nothing
    from the secret-judge-shaped oracle. Folding the oracle-dependent perceptual check
    into it would break that purity.
  - this file reuses the structural suite's generators + helpers via
    `import check_structural_validity as T`, a single source of truth, no duplication.

WHY structural validity is not enough (the motivating defect, reproduced in selftest):
  A "solver" that ignores its input and always returns a tetrahedron is manifold,
  has Euler 2, is deterministic and monotone -> it passes EVERY test2 invariant on
  any genus-0 input, yet FinalSSIM ~0.37 and Hausdorff ~5x over the limit. test3
  must REJECT it. `fake_solver_tetra` is the headline negative control.

[ABSOLUTE] vs [ORACLE] — the critical distinction, enforced everywhere:
  [ABSOLUTE] checks are pure mathematics, independent of the secret judge. A
             failure is a CERTAIN bug. They never import the oracle. Exit code is
             0 only if all [ABSOLUTE] checks pass.
  [ORACLE]   checks estimate the judge via src/imc_eval. They are calibrated
             estimates, not certainties, so they carry a documented safety margin
             and, when under margin, raise a highlighted WARNING rather than
             forcing a non-zero exit (policy below). Only C6 is [ORACLE].

POLICY for [ORACLE] (C6): a perceptual check below its margin prints a loud
  WARNING and is counted, but does NOT by itself set a non-zero exit code,
  because the oracle is an estimate of a secret judge. The garbage tetra is still
  hard-rejected — by the [ABSOLUTE] checks C1/C3/C4 — so a weak oracle can never
  let true garbage through. (Verified in the fake-solver demo at the end.)

Checks:
  C1 [ABSOLUTE] symmetric Hausdorff(input, output) <= 5% of input AABB diagonal.
  C2 [ABSOLUTE] consistent winding: every undirected edge traversed once each way.
  C3 [ABSOLUTE] output stays inside the unit sphere (max||v|| <= 1+eps).
  C4 [ABSOLUTE] connected-component count preserved (union-find).
  C5 [ABSOLUTE] genus preserved via Euler (test2 INV6) + components (C4): the pair
                (Euler, #components) pins the topology unambiguously.
  C6 [ORACLE]   perceptual fidelity with margin: if compression>0 then FinalSSIM
                >= margin (default 0.91).
  C7 [ABSOLUTE] robustness on extreme/malformed inputs (graceful, no crash).
  C8 [ABSOLUTE] scale & time: large meshes finish in budget; output passes C1-C5.
  C9 [ABSOLUTE] idempotence/stability: re-simplifying an output doesn't break it.

Dependencies: numpy required. scipy used ONLY to accelerate C1/C8 (cKDTree over a
  dense surface sampling); a pure-numpy exact point-triangle fallback is used if
  scipy is absent. No igl / numba.

Each checker carries a self-test with TEETH: a broken case it MUST reject and a
valid case it MUST accept, run at startup. If any checker fails to reject its
broken case, the whole suite aborts — a test without teeth is worse than none.

Run:  python tests/test3.py                 # full suite
      python tests/test3.py --selftest      # teeth only (fast, no large meshes)
      SOLVER=/path/to/bin python tests/test3.py
"""

import os
import sys
import time
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # for `import test2`
import check_structural_validity as T  # noqa: E402  (generators + structural helpers; single source)

EPS_SPHERE = 1e-6            # C3 tolerance on ||v|| <= 1
HAUS_FRACTION = 0.05        # C1 hard limit: 5% of input AABB diagonal

# --- C6 perceptual gate (FinalSSIM is the BINDING constraint: below the judge's
#     0.90 gate the test case scores ZERO, regardless of compression). The oracle
#     reproduces the judge but is not bit-identical to it, so we use a margin BAND
#     instead of a single threshold:
#       FinalSSIM <  SSIM_HARD_FLOOR        -> [ABSOLUTE] FAIL (certainly below gate;
#                                              no oracle<->judge drift explains a 5pt gap)
#       SSIM_HARD_FLOOR <= FinalSSIM < SSIM_SAFE -> WARNING (uncertainty band: absorbs
#                                              the ~0.002 box/gaussian SSIM divergence
#                                              and the margin above the 0.90 gate)
#       FinalSSIM >= SSIM_SAFE              -> OK (safe margin over the gate)
SSIM_GATE = 0.90            # the judge's hard validity gate (pinned by the problem)
SSIM_HARD_FLOOR = 0.85     # below this -> certain failure (absolute)
SSIM_SAFE = 0.91           # at/above this -> safely over the gate


# ============================================================================
# Self-test framework (teeth). Each checker registers a callable that builds a
# broken case (must be rejected) and a valid case (must be accepted).
# ============================================================================

_SELFTESTS = []


def teeth(name):
    def deco(fn):
        _SELFTESTS.append((name, fn))
        return fn
    return deco


def assert_rejects(checker, mesh_args, label):
    ok = checker(*mesh_args)[0]
    if ok:
        raise AssertionError(f"TEETH FAILURE: {label}: checker accepted a BROKEN case")


def assert_accepts(checker, mesh_args, label):
    ok, detail = checker(*mesh_args)
    if not ok:
        raise AssertionError(f"TEETH FAILURE: {label}: checker rejected a VALID case ({detail})")


def run_selftests(verbose=True):
    """Run every checker's teeth. Aborts the whole suite if any checker fails to
    reject its broken case (a toothless test is worse than none)."""
    if verbose:
        print("=" * 78)
        print("CHECKER SELF-TESTS (teeth) — every checker must reject its broken case")
        print("=" * 78)
    n = 0
    for name, fn in _SELFTESTS:
        try:
            fn()
        except AssertionError as e:
            print(f"  ❌  {lbl(name):24s} {e}")
            T.fail(f"checker '{lbl(name)}' has no teeth; aborting (a toothless test is worse than none)")
        n += 1
        if verbose:
            print(f"  ✅  {lbl(name):24s} rejects a broken mesh, accepts a valid one")
    if not verbose:
        print(f" auto-test dei checker (denti): {n}/{n} OK — ogni check boccia il suo "
              f"caso rotto e accetta uno valido")
    print()


# ============================================================================
# Shared geometry helpers (pure numpy; NO oracle import — these are [ABSOLUTE]).
# Meshes here are passed as (V (n,3) float, F (m,3) int, 1-BASED) to match test2.
# ============================================================================

def aabb_diag(V):
    return float(np.linalg.norm(V.max(axis=0) - V.min(axis=0)))


# Spatial-acceleration note: this is the contest's vertex-to-SURFACE Hausdorff,
# computed EXACTLY (closest point on each triangle, Ericson). Naive brute force is
# O(P*T), but the key structural fact makes it cheap here: in EACH direction one
# operand is the simplified OUTPUT, which is small. So we always loop over the
# SMALLER axis (few output faces, or few output vertices) and vectorise the larger
# over numpy — O(min(P,T) * max(P,T)) with the small factor bounded by the output
# size. This stays fast to ~1e6-vertex inputs without an external KD-tree, and is
# EXACT (a dense-sampling KD-tree, by contrast, badly over-estimates against the
# output's large facets — measured 103% vs the true 23% on a coarse sphere — which
# would false-alarm; so we do not sample). scipy is therefore not required for C1.


def _sqdist_points_to_tri(P, a, b, c):
    """Exact squared distance from MANY points P (N,3) to ONE triangle (a,b,c).
    Ericson closest-point, vectorised over the N points. Used when triangles are
    the small axis (loop triangles, vectorise points)."""
    ab = b - a; ac = c - a
    ap = P - a; d1 = ap @ ab; d2 = ap @ ac
    bp = P - b; d3 = bp @ ab; d4 = bp @ ac
    cp = P - c; d5 = cp @ ab; d6 = cp @ ac
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    denom = va + vb + vc
    ds = np.where(denom != 0.0, denom, 1.0)
    v = vb / ds; w = vc / ds
    closest = a + ab * v[:, None] + ac * w[:, None]
    dab = np.where((d1 - d3) != 0.0, d1 - d3, 1.0); c_ab = a + ab * (d1 / dab)[:, None]
    dac = np.where((d2 - d6) != 0.0, d2 - d6, 1.0); c_ac = a + ac * (d2 / dac)[:, None]
    dbc = np.where(((d4 - d3) + (d5 - d6)) != 0.0, (d4 - d3) + (d5 - d6), 1.0)
    c_bc = b + (c - b) * ((d4 - d3) / dbc)[:, None]
    m_a = (d1 <= 0) & (d2 <= 0); m_b = (d3 >= 0) & (d4 <= d3); m_c = (d6 >= 0) & (d5 <= d6)
    m_ab = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
    m_ac = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
    m_bc = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    closest[m_bc] = c_bc[m_bc]; closest[m_ac] = c_ac[m_ac]; closest[m_c] = c
    closest[m_ab] = c_ab[m_ab]; closest[m_b] = b; closest[m_a] = a
    diff = P - closest
    return np.einsum("ij,ij->i", diff, diff)


def _sqdist_point_to_tris(p, a, b, c):
    """Exact squared distance from ONE point p (3,) to MANY triangles (a,b,c each
    (T,3)). Vectorised over the T triangles. Used when points are the small axis."""
    ab = b - a; ac = c - a
    ap = p - a; d1 = np.einsum("ij,ij->i", ab, ap); d2 = np.einsum("ij,ij->i", ac, ap)
    bp = p - b; d3 = np.einsum("ij,ij->i", ab, bp); d4 = np.einsum("ij,ij->i", ac, bp)
    cp = p - c; d5 = np.einsum("ij,ij->i", ab, cp); d6 = np.einsum("ij,ij->i", ac, cp)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    denom = va + vb + vc
    ds = np.where(denom != 0.0, denom, 1.0)
    v = vb / ds; w = vc / ds
    closest = a + ab * v[:, None] + ac * w[:, None]
    dab = np.where((d1 - d3) != 0.0, d1 - d3, 1.0); c_ab = a + ab * (d1 / dab)[:, None]
    dac = np.where((d2 - d6) != 0.0, d2 - d6, 1.0); c_ac = a + ac * (d2 / dac)[:, None]
    dbc = np.where(((d4 - d3) + (d5 - d6)) != 0.0, (d4 - d3) + (d5 - d6), 1.0)
    c_bc = b + (c - b) * ((d4 - d3) / dbc)[:, None]
    m_a = (d1 <= 0) & (d2 <= 0); m_b = (d3 >= 0) & (d4 <= d3); m_c = (d6 >= 0) & (d5 <= d6)
    m_ab = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
    m_ac = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
    m_bc = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    closest[m_bc] = c_bc[m_bc]; closest[m_ac] = c_ac[m_ac]; closest[m_c] = c[m_c]
    closest[m_ab] = c_ab[m_ab]; closest[m_b] = b[m_b]; closest[m_a] = a[m_a]
    diff = p - closest
    return np.einsum("ij,ij->i", diff, diff)


def _directed_exact(P, Vt, Ft1):
    """Exact directed Hausdorff: max over points P of distance to surface(Vt,Ft1).
    Loops over whichever of {points, triangles} is smaller."""
    a = Vt[Ft1[:, 0] - 1]; b = Vt[Ft1[:, 1] - 1]; c = Vt[Ft1[:, 2] - 1]
    nP, nT = len(P), len(a)
    if nT <= nP:                                   # few triangles: loop triangles
        dmin = np.full(nP, np.inf)
        for t in range(nT):
            np.minimum(dmin, _sqdist_points_to_tri(P, a[t], b[t], c[t]), out=dmin)
        return float(np.sqrt(dmin.max()))
    worst = 0.0                                    # few points: loop points
    for p in P:
        dm = _sqdist_point_to_tris(p, a, b, c).min()
        if dm > worst:
            worst = dm
    return float(np.sqrt(worst))


def hausdorff_symmetric(Vin, Fin1, Vout, Fout1):
    """Exact symmetric vertex-to-surface Hausdorff between the two meshes."""
    d1 = _directed_exact(Vin, Vout, Fout1)         # original verts -> output surface
    d2 = _directed_exact(Vout, Vin, Fin1)          # output verts   -> original surface
    return max(d1, d2)


# ============================================================================
# C1 [ABSOLUTE] — Hausdorff constraint
# ============================================================================

def c1_hausdorff(Vin, Fin1, Vout, Fout1):
    """[ABSOLUTE] symmetric Hausdorff(input,output) <= 5% of input AABB diagonal."""
    diag = aabb_diag(Vin)
    limit = HAUS_FRACTION * diag
    haus = hausdorff_symmetric(Vin, Fin1, Vout, Fout1)
    ratio = haus / limit if limit > 0 else float("inf")
    return haus <= limit, f"haus={haus:.4f} limit={limit:.4f} ({ratio*100:.0f}% of budget)"


@teeth("C1")
def _selftest_c1():
    # valid: identity simplification -> Hausdorff 0
    V, F = T.gen_sphere(2)
    V = np.ascontiguousarray(V); F1 = np.ascontiguousarray(F) + 1
    assert_accepts(c1_hausdorff, (V, F1, V.copy(), F1.copy()), "C1 identity")
    # broken: tetra output vs sphere input -> Hausdorff ~ radius >> 5% diag
    Vt = np.array([[0.12, 0.12, 0.12], [-0.12, -0.12, 0.12],
                   [-0.12, 0.12, -0.12], [0.12, -0.12, -0.12]], np.float64)
    Ft = np.array([[1, 2, 3], [1, 4, 2], [1, 3, 4], [2, 4, 3]], np.int64)
    assert_rejects(c1_hausdorff, (V, F1, Vt, Ft), "C1 tetra-vs-sphere")


# ============================================================================
# C2 [ABSOLUTE] — consistent winding (orientability)
# ============================================================================

def c2_winding(Vin, Fin1, Vout, Fout1):
    """[ABSOLUTE] every undirected edge traversed exactly once in each direction.
    If a face's winding is flipped, the judge's flat-shaded normals are corrupted.
    For a consistently-oriented closed manifold each directed edge (a->b) occurs
    once and its reverse (b->a) once."""
    dc = Counter()
    for a, b, c in Fout1:
        a, b, c = int(a), int(b), int(c)
        dc[(a, b)] += 1; dc[(b, c)] += 1; dc[(c, a)] += 1
    bad = 0
    for (x, y), k in dc.items():
        if k != 1 or dc.get((y, x), 0) != 1:
            bad += 1
    return bad == 0, ("consistent winding" if bad == 0
                      else f"{bad} directed-edge orientation violation(s)")


@teeth("C2")
def _selftest_c2():
    Vt = np.array([[0.1, 0.1, 0.1], [-0.1, -0.1, 0.1],
                   [-0.1, 0.1, -0.1], [0.1, -0.1, -0.1]], np.float64)
    good = np.array([[1, 2, 3], [1, 4, 2], [1, 3, 4], [2, 4, 3]], np.int64)
    assert_accepts(c2_winding, (Vt, good, Vt, good), "C2 consistent tetra")
    bad = good.copy()
    bad[0] = [1, 3, 2]                 # flip one face's winding
    assert_rejects(c2_winding, (Vt, good, Vt, bad), "C2 flipped face")


# --- C2 reinforcement: orientation must match the INPUT (not just be internally
#     consistent). A GLOBAL winding flip keeps every edge consistent (passes
#     c2_winding) yet inverts every face normal -> the judge's normal map is the
#     photographic negative. The signed volume of a closed mesh
#     (sum dot(v0, cross(v1,v2))/6) is positive for outward-facing winding and
#     flips sign under a global inversion, so input and output signs must agree.

def signed_volume(V, F1):
    p0 = V[F1[:, 0] - 1]; p1 = V[F1[:, 1] - 1]; p2 = V[F1[:, 2] - 1]
    return float(np.einsum("ij,ij->i", p0, np.cross(p1, p2)).sum() / 6.0)


def c2b_orientation(Vin, Fin1, Vout, Fout1):
    """[ABSOLUTE] output winding orientation consistent with the input (same
    signed-volume sign; outward for both)."""
    si = signed_volume(Vin, Fin1)
    so = signed_volume(Vout, Fout1)
    ok = (si > 0) == (so > 0) and so != 0.0
    return ok, f"signed vol in={si:+.4f} out={so:+.4f}"


@teeth("C2b")
def _selftest_c2b():
    Vt = np.array([[0.1, 0.1, 0.1], [-0.1, -0.1, 0.1],
                   [-0.1, 0.1, -0.1], [0.1, -0.1, -0.1]], np.float64)
    good = np.array([[1, 2, 3], [1, 4, 2], [1, 3, 4], [2, 4, 3]], np.int64)
    assert_accepts(c2b_orientation, (Vt, good, Vt, good.copy()), "C2b same orientation")
    flipped = good[:, ::-1].copy()        # reverse every face -> global inversion
    assert_rejects(c2b_orientation, (Vt, good, Vt, flipped), "C2b global flip")


# ============================================================================
# C3 [ABSOLUTE] — output inside the unit sphere
# ============================================================================

def c3_unit_sphere(Vin, Fin1, Vout, Fout1):
    """[ABSOLUTE] the judge assumes the model lies in the unit sphere."""
    mx = float(np.linalg.norm(Vout, axis=1).max()) if len(Vout) else 0.0
    return mx <= 1.0 + EPS_SPHERE, f"max||v||={mx:.6f}"


@teeth("C3")
def _selftest_c3():
    V, F = T.gen_sphere(1)
    V = np.ascontiguousarray(V); F1 = np.ascontiguousarray(F) + 1
    assert_accepts(c3_unit_sphere, (V, F1, V.copy(), F1.copy()), "C3 in-sphere")
    Vb = V.copy()
    Vb[0] = Vb[0] / np.linalg.norm(Vb[0]) * 1.5     # push a vertex to ||v||=1.5
    assert_rejects(c3_unit_sphere, (V, F1, Vb, F1.copy()), "C3 vertex outside")


# ============================================================================
# C4 [ABSOLUTE] — connected-component count preserved
# ============================================================================

def _num_components(nv, F1):
    parent = list(range(nv))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for a, b, c in F1:
        a, b, c = int(a) - 1, int(b) - 1, int(c) - 1
        union(a, b); union(b, c)
    return len(set(find(i) for i in range(nv)))


def c4_components(Vin, Fin1, Vout, Fout1):
    """[ABSOLUTE] number of connected components must be preserved (union-find on
    edges). Euler alone cannot see a split/merge of components; this can."""
    ci = _num_components(len(Vin), Fin1)
    co = _num_components(len(Vout), Fout1)
    return co == ci, f"components in={ci} out={co}"


@teeth("C4")
def _selftest_c4():
    V, F = T.gen_sphere(1)                          # single-component input
    V = np.ascontiguousarray(V); F1 = np.ascontiguousarray(F) + 1
    Vt = np.array([[0.1, 0.1, 0.1], [-0.1, -0.1, 0.1],
                   [-0.1, 0.1, -0.1], [0.1, -0.1, -0.1]], np.float64)
    one = np.array([[1, 2, 3], [1, 4, 2], [1, 3, 4], [2, 4, 3]], np.int64)
    assert_accepts(c4_components, (V, F1, Vt, one), "C4 one component")
    # broken: two detached tetras -> 2 components
    Vtt = np.vstack([Vt, Vt + 5.0])
    two = np.vstack([one, one + 4])
    assert_rejects(c4_components, (V, F1, Vtt, two), "C4 two components")


# ============================================================================
# C5 [ABSOLUTE] — genus preserved via Euler (reinforced by C4 components)
# ============================================================================

def c5_genus(Vin, Fin1, Vout, Fout1):
    """[ABSOLUTE] Euler characteristic of the output must equal the input's.
    With C4 (component count), the pair (Euler, #components) pins the topology:
    Euler = 2C - 2g for C components of total genus g, so the two together pin
    (C, g) unambiguously. (test2 INV6 checks Euler against a known constant; here
    we compare output-vs-input directly so test3 needs no genus table.)"""
    ein = T.euler_characteristic(len(Vin), Fin1)
    eout = T.euler_characteristic(len(Vout), Fout1)
    return eout == ein, f"euler in={ein} out={eout}"


@teeth("C5")
def _selftest_c5():
    Vt = np.array([[0.1, 0.1, 0.1], [-0.1, -0.1, 0.1],
                   [-0.1, 0.1, -0.1], [0.1, -0.1, -0.1]], np.float64)
    full = np.array([[1, 2, 3], [1, 4, 2], [1, 3, 4], [2, 4, 3]], np.int64)
    assert_accepts(c5_genus, (Vt, full, Vt, full), "C5 euler preserved")
    holed = full[:3]                                  # drop a face -> open -> euler 1
    assert_rejects(c5_genus, (Vt, full, Vt, holed), "C5 euler changed")


# ============================================================================
# C6 [ORACLE] — perceptual fidelity: the BINDING constraint (margin band)
# ============================================================================
# FinalSSIM >= 0.90 is the judge's hard validity gate: below it the test case
# scores ZERO no matter how good the compression / Hausdorff / topology are. So
# C6 is NOT a soft warning — it is the constraint that decides whether we score.
#
# The oracle reproduces the judge but is not bit-identical to it, so a single
# threshold would be brittle near 0.90. Instead C6 returns a 3-state band:
#   "fail"  FinalSSIM < SSIM_HARD_FLOOR (0.85): certainly under the gate; no
#           oracle<->judge drift explains a 5-point gap -> [ABSOLUTE] failure.
#   "warn"  0.85 <= FinalSSIM < SSIM_SAFE (0.91): uncertainty band straddling the
#           0.90 gate; flagged loudly but does not force a non-zero exit, because
#           the true judge might read it just over or under.
#   "ok"    FinalSSIM >= SSIM_SAFE (0.91): safely over the gate.
# The band logic is split into a pure function so it can be teeth-tested cheaply
# without rendering; only the wrapper imports the oracle (locally, keeping the
# [ABSOLUTE] checks judge-free).

def c6_classify(final_ssim, compression):
    """[ORACLE] map (FinalSSIM, compression) -> ('ok'|'warn'|'fail', detail)."""
    if compression <= 1e-9:
        return "ok", f"comp={compression:.2f}% (no simplification) SSIM={final_ssim:.4f}"
    base = (f"comp={compression:.2f}% FinalSSIM={final_ssim:.4f} "
            f"(gate {SSIM_GATE}; floor {SSIM_HARD_FLOOR}/safe {SSIM_SAFE})")
    if final_ssim < SSIM_HARD_FLOOR:
        return "fail", base
    if final_ssim < SSIM_SAFE:
        return "warn", base
    return "ok", base


def c6_perceptual(Vin, Fin1, Vout, Fout1):
    """[ORACLE] run the oracle and classify FinalSSIM into the margin band.
    Returns ('ok'|'warn'|'fail', detail)."""
    src = os.path.join(T.REPO, "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from imc_eval import evaluate                       # local: keep absolutes pure
    rep = evaluate(Vin, (Fin1 - 1).astype(np.int64),
                   Vout, (Fout1 - 1).astype(np.int64))
    return c6_classify(rep.final_ssim, rep.compression)


_ORIG_RENDER_CACHE = {}


def oracle_score(Vin, Fin1, Vout, Fout1, key=None):
    """[ORACLE] (final_ssim, compression) for an output, caching the INPUT's six
    renders by `key` (the input is rendered once across a frac sweep)."""
    src = os.path.join(T.REPO, "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from imc_eval.geometry import build_views, face_normals
    from imc_eval.render import render_view
    from imc_eval.ssim import ssim_normal, ssim_depth
    views = build_views()
    Fi = (Fin1 - 1).astype(np.int64)
    Fo = (Fout1 - 1).astype(np.int64)
    if key is not None and key in _ORIG_RENDER_CACHE:
        orig = _ORIG_RENDER_CACHE[key]
    else:
        fno = face_normals(Vin, Fi)
        orig = [render_view(Vin, Fi, fno, vw) for vw in views]
        if key is not None:
            _ORIG_RENDER_CACHE[key] = orig
    fns = face_normals(Vout, Fo)
    blended = []
    for k, vw in enumerate(views):
        nO, dO, cO = orig[k]
        nS, dS, cS = render_view(Vout, Fo, fns, vw)
        cov = cO | cS
        blended.append(0.5 * ssim_normal(nO, nS, cov) + 0.5 * ssim_depth(dO, dS, cov))
    final = float(np.mean(blended))
    comp = 100.0 * (1.0 - len(Vout) / len(Vin))
    return final, comp


# Operating-point search: the largest frac whose FinalSSIM stays at/above the safe
# margin. This is the SUBMISSION regime (max safe compression) — the hard
# constraints must be re-validated here, not only in the easy low-frac regime.
OP_FRAC_MAX = 3.0


def op_bisect(ssim_of, safe=SSIM_SAFE, frac_max=OP_FRAC_MAX, iters=8):
    """Bisection for the operating point. `ssim_of(frac) -> FinalSSIM`, assumed
    roughly monotone non-increasing in frac. Returns (status, frac):
      'fail_gate' (frac 0)      even no simplification is below the safe gate
                                -> the solver is broken at identity.
      'beyond'    (frac_max)    still above the gate at the largest tested frac
                                -> the true operating point is beyond the range.
      'ok'        (boundary)    largest frac with FinalSSIM >= safe.
    Robust to the edge cases above; never raises on a monotone input."""
    if ssim_of(0.0) < safe:
        return ("fail_gate", 0.0)
    if ssim_of(frac_max) >= safe:
        return ("beyond", frac_max)
    lo, hi, best = 0.0, frac_max, 0.0
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if ssim_of(mid) >= safe:
            lo, best = mid, mid
        else:
            hi = mid
    return ("ok", best)


@teeth("operating-point search")
def _selftest_op_bisect():
    # monotone SSIM = 1 - 0.1*frac crosses the 0.91 safe line at frac=0.9
    st, fr = op_bisect(lambda f: 1.0 - 0.1 * f, safe=0.91, frac_max=3.0)
    assert st == "ok" and abs(fr - 0.9) < 0.05, f"bad boundary: {st} {fr}"
    # broken solver: even identity (frac 0) is below the gate
    st, _ = op_bisect(lambda f: 0.50, safe=0.91)
    assert st == "fail_gate", "must flag a solver that fails the gate at frac 0"
    # never drops below: operating point is beyond the tested range
    st, fr = op_bisect(lambda f: 0.99, safe=0.91, frac_max=3.0)
    assert st == "beyond" and fr == 3.0, "must flag 'beyond range'"


@teeth("C6")
def _selftest_c6():
    # band logic (pure, no render): the three states must be distinguished.
    assert c6_classify(0.40, 50.0)[0] == "fail", "C6 band: 0.40 must FAIL"
    assert c6_classify(0.88, 50.0)[0] == "warn", "C6 band: 0.88 must WARN"
    assert c6_classify(0.95, 50.0)[0] == "ok", "C6 band: 0.95 must be OK"
    assert c6_classify(0.84, 50.0)[0] == "fail", "C6 band: just under floor -> FAIL"
    assert c6_classify(0.40, 0.0)[0] == "ok", "C6 band: no compression -> OK"
    # integration (oracle): a real garbage tetra must land in the FAIL band.
    V, F = T.gen_sphere(1)                              # small -> fast oracle render
    V = np.ascontiguousarray(V); F1 = np.ascontiguousarray(F) + 1
    Vt = np.array([[0.12, 0.12, 0.12], [-0.12, -0.12, 0.12],
                   [-0.12, 0.12, -0.12], [0.12, -0.12, -0.12]], np.float64)
    Ft = np.array([[1, 2, 3], [1, 4, 2], [1, 3, 4], [2, 4, 3]], np.int64)
    assert c6_perceptual(V, F1, Vt, Ft)[0] == "fail", "C6 tetra must FAIL the gate"
    assert c6_perceptual(V, F1, V.copy(), F1.copy())[0] == "ok", "C6 identity must be OK"


# ============================================================================
# Solver invocation (raw, non-raising) for C7/C8/C9
# ============================================================================
import subprocess  # noqa: E402


def run_raw(solver, obj_text, *args, timeout=120):
    """Run the solver without raising. Returns (rc, stdout, stderr). A process
    killed by a signal yields rc < 0 (subprocess convention) -> treated as a crash."""
    try:
        r = subprocess.run([solver, *map(str, args)], input=obj_text,
                           capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


import os  # noqa: E402  (os.wait4 for child rusage)
import tempfile  # noqa: E402


def run_raw_mem(solver, obj_text, *args):
    """Run the solver and capture peak RSS via os.wait4 child rusage.
    Returns (rc, stdout, elapsed_s, peak_rss_bytes). ru_maxrss is bytes on macOS
    and kilobytes on Linux; normalised to bytes here."""
    with tempfile.TemporaryFile() as fin, tempfile.TemporaryFile() as fout, \
            tempfile.TemporaryFile() as ferr:
        fin.write(obj_text.encode()); fin.seek(0)
        t0 = time.time()
        p = subprocess.Popen([solver, *map(str, args)], stdin=fin, stdout=fout, stderr=ferr)
        _, status, ru = os.wait4(p.pid, 0)
        elapsed = time.time() - t0
        p.returncode = os.waitstatus_to_exitcode(status)   # keep Popen consistent
        fout.seek(0); out = fout.read().decode()
    rss = ru.ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    return p.returncode, out, elapsed, rss


# ============================================================================
# C7 [ABSOLUTE] — robustness on extreme / malformed inputs
# ============================================================================

STRUCTURAL_CHECKS = [("C2", c2_winding), ("C2b", c2b_orientation),
                     ("C3", c3_unit_sphere), ("C4", c4_components), ("C5", c5_genus)]


def c7_classify(rc, stdout, category, Vin=None, Fin1=None):
    """[ABSOLUTE] classify one solver run.

      'valid_extreme' — a VALID input at a SANE/boundary frac (0, a small frac, or
        the minimal tetra which cannot be reduced). The solver MUST succeed and the
        output MUST pass C1-C5 (including the Hausdorff budget).

      'overdrive' — a VALID input at a deliberately ABUSIVE frac (e.g. 100, which
        instructs the solver to spend ~100x the Hausdorff budget; or a negative
        frac, which squares to a large budget). Keeping Hausdorff <= 5% while being
        told to exceed it is contradictory, so C1 is INFORMATIONAL here. The hard
        requirement is graceful behaviour: rc==0, no crash, and the output is still
        a STRUCTURALLY valid manifold (C2-C5). (Hausdorff at sane fracs is enforced
        in Sections A/C/D.)

      'malformed' — a structurally broken input. Must degrade gracefully: a clean
        non-zero exit (1..123), OR rc==0 with a structurally valid mesh. A crash
        (rc<0 or rc>=128 signal, or timeout) is a FAILURE.

    The toothy distinction throughout: 'graceful/valid' != 'crash/corrupt'."""
    crashed = rc < 0 or rc >= 128
    if category in ("valid_extreme", "overdrive"):
        if rc != 0:
            return False, f"rc={rc} (a valid input must succeed)"
        try:
            nv, nf, V, F1 = T.parse_obj(stdout)
        except Exception as e:
            return False, f"unparseable output: {e!r}"
        man_ok, man_d = T.inv1_manifold(nv, nf, V, F1)
        if not man_ok:
            return False, f"output not manifold: {man_d}"
        for cname, cfn in STRUCTURAL_CHECKS:
            ok, d = cfn(Vin, Fin1, V, F1)
            if not ok:
                return False, f"output fails {cname}: {d}"
        c1_ok, c1_d = c1_hausdorff(Vin, Fin1, V, F1)
        if category == "valid_extreme":
            if not c1_ok:
                return False, f"output fails C1: {c1_d}"
            return True, f"rc=0, valid output (V'={nv}), passes C1-C5"
        note = "within budget" if c1_ok else "OVER budget — expected for frac>>1"
        return True, f"rc=0, structurally valid (V'={nv}); C1 {c1_d} [{note}]"
    # malformed
    if crashed:
        return False, f"CRASH rc={rc} (not graceful)"
    if rc != 0:
        return True, f"graceful non-zero exit rc={rc}"
    try:
        nv, nf, V, F1 = T.parse_obj(stdout)
    except Exception as e:
        return False, f"rc=0 but corrupt output: {e!r}"
    man_ok, _ = T.inv1_manifold(nv, nf, V, F1)
    return man_ok, (f"rc=0 produced a valid mesh (V'={nv})" if man_ok
                    else "rc=0 but output is not a manifold")


@teeth("C7")
def _selftest_c7():
    V, F = T.gen_sphere(1)
    V = np.ascontiguousarray(V); F1 = np.ascontiguousarray(F) + 1
    good_out = T.mesh_to_obj(V, F1)
    # valid_extreme accept: rc=0 with a faithful (identity) output
    assert_accepts(lambda *a: c7_classify(0, good_out, "valid_extreme", V, F1),
                   (None,), "C7 valid-extreme ok")
    # valid_extreme reject: nonzero rc on a valid input is a failure
    assert_rejects(lambda *a: c7_classify(1, "", "valid_extreme", V, F1),
                   (None,), "C7 valid-extreme errored")
    # valid_extreme reject: rc=0 but the output is a non-manifold mesh
    open_out = T.mesh_to_obj(V, F1[:-2])      # drop faces -> open boundary
    assert_rejects(lambda *a: c7_classify(0, open_out, "valid_extreme", V, F1),
                   (None,), "C7 valid-extreme non-manifold output")
    # overdrive accept: a structurally valid output (here the tetra as its own
    # input, so orientation/topology agree; C1 is informational for overdrive).
    Vt = np.array([[0.1, 0.1, 0.1], [-0.1, -0.1, 0.1],
                   [-0.1, 0.1, -0.1], [0.1, -0.1, -0.1]], np.float64)
    Ft = np.array([[1, 2, 3], [1, 4, 2], [1, 3, 4], [2, 4, 3]], np.int64)
    tetra_out = T.mesh_to_obj(Vt, Ft)
    assert_accepts(lambda *a: c7_classify(0, tetra_out, "overdrive", Vt, Ft),
                   (None,), "C7 overdrive structurally valid")
    # overdrive reject: a crash is never acceptable
    assert_rejects(lambda *a: c7_classify(-11, "", "overdrive", Vt, Ft),
                   (None,), "C7 overdrive crash")
    # malformed accept: graceful non-zero exit
    assert_accepts(lambda *a: c7_classify(1, "", "malformed"), (None,),
                   "C7 malformed graceful")
    # malformed reject: a crash (SIGSEGV => rc -11)
    assert_rejects(lambda *a: c7_classify(-11, "", "malformed"), (None,),
                   "C7 malformed crash")


# ============================================================================
# C8 [ABSOLUTE] — scale & time (catch O(n^2) before the 21s judge timeout)
# ============================================================================

TIME_BUDGET_S = 60.0        # local time is only a relative proxy for the judge's
                            # 21s; this loose cap exists to catch O(n^2) blow-ups.
MEM_BUDGET_MB = 1800.0      # under the judge's 2048 MB with margin (C11)


def c8_time_ok(elapsed, budget=TIME_BUDGET_S):
    """[ABSOLUTE] the solver must finish within the configured wall-clock budget."""
    return elapsed <= budget, f"{elapsed:.2f}s (budget {budget:.0f}s)"


def c11_mem_ok(rss_bytes, budget_mb=MEM_BUDGET_MB):
    """[ABSOLUTE] peak resident memory must stay under the budget (C11)."""
    mb = rss_bytes / (1024 * 1024)
    return mb <= budget_mb, f"{mb:.0f}MB (budget {budget_mb:.0f}MB)"


@teeth("C8")
def _selftest_c8():
    assert_accepts(lambda *a: c8_time_ok(1.0, 10.0), (None,), "C8 within budget")
    assert_rejects(lambda *a: c8_time_ok(99.0, 10.0), (None,), "C8 over budget")


@teeth("C11")
def _selftest_c11():
    assert_accepts(lambda *a: c11_mem_ok(500 * 1024 * 1024, 1800), (None,), "C11 within mem")
    assert_rejects(lambda *a: c11_mem_ok(3000 * 1024 * 1024, 1800), (None,), "C11 over mem")


# ============================================================================
# C9 [ABSOLUTE] — idempotence / fixed-point stability
# ============================================================================

def c9_idempotent(V1, F1a, V2, F2a):
    """[ABSOLUTE] re-simplifying an already-simplified output (same frac) must not
    break it: O2 stays a valid manifold, keeps O1's Euler and component count,
    never GROWS, and stays within the Hausdorff budget of O1 (no drift)."""
    man_ok, man_d = T.inv1_manifold(len(V2), len(F2a), V2, F2a)
    if not man_ok:
        return False, f"O2 not manifold: {man_d}"
    if len(V2) > len(V1):
        return False, f"O2 grew: V {len(V1)}->{len(V2)}"
    e_ok, e_d = c5_genus(V1, F1a, V2, F2a)
    if not e_ok:
        return False, f"topology changed: {e_d}"
    comp_ok, comp_d = c4_components(V1, F1a, V2, F2a)
    if not comp_ok:
        return False, comp_d
    h_ok, h_d = c1_hausdorff(V1, F1a, V2, F2a)
    if not h_ok:
        return False, f"drifted from O1: {h_d}"
    return True, f"stable: V {len(V1)}->{len(V2)}, {h_d}"


@teeth("C9")
def _selftest_c9():
    V, F = T.gen_sphere(2)
    V = np.ascontiguousarray(V); F1 = np.ascontiguousarray(F) + 1
    assert_accepts(c9_idempotent, (V, F1, V.copy(), F1.copy()), "C9 fixed point")
    # broken: second pass returns a tetra -> drifts far from O1 + grows? (shrinks)
    Vt = np.array([[0.12, 0.12, 0.12], [-0.12, -0.12, 0.12],
                   [-0.12, 0.12, -0.12], [0.12, -0.12, -0.12]], np.float64)
    Ft = np.array([[1, 2, 3], [1, 4, 2], [1, 3, 4], [2, 4, 3]], np.int64)
    assert_rejects(c9_idempotent, (V, F1, Vt, Ft), "C9 unstable->tetra")


# ============================================================================
# C10 [ABSOLUTE] — output size <= 100 MiB, with projection to the largest case
# ============================================================================
MIB = 1024 * 1024
OUTPUT_LIMIT_BYTES = 100 * MIB
CASE7_V = 1_100_000          # largest test case (problem statement)
CASE7_F = 2_100_000


def c10_size(out_text, nv, nf, case_v=CASE7_V, case_f=CASE7_F):
    """[ABSOLUTE] the actual output must be <= 100 MiB. In addition, project this
    proxy's vertex-line cost (coordinate precision) onto case 7. Face lines are
    modelled at case-7 INDEX width (up to 7 digits), which a small proxy with
    1-3 digit indices would otherwise badly underestimate. If the projection
    exceeds 100 MiB the decimal precision is too high for the big case -> WARNING.
    Returns ('ok'|'warn'|'fail', detail)."""
    nbytes = len(out_text.encode("utf-8"))
    vb = 0
    for line in out_text.splitlines():
        if line.startswith("v "):
            vb += len(line) + 1
    bpv = vb / nv if nv else 0.0
    bpf_case = len(f"f {case_v} {case_v} {case_v}\n")    # case-7 worst-case index width
    proj = bpv * case_v + bpf_case * case_f
    detail = (f"out={nbytes/MIB:.4f}MiB ({bpv:.1f} B/vtx; faces@{bpf_case}B) "
              f"-> case7 proj={proj/MIB:.1f}/100 MiB")
    if nbytes > OUTPUT_LIMIT_BYTES:
        return "fail", detail
    if proj > OUTPUT_LIMIT_BYTES:
        return "warn", detail
    return "ok", detail


@teeth("C10")
def _selftest_c10():
    good = "4 4\n" + "v 0.1 0.2 0.3\n" * 4 + "f 1 2 3\n" * 4
    assert c10_size(good, 4, 4)[0] == "ok", "C10 short coords must be OK"
    # excessive decimals -> vertex term alone pushes the projection over 100 MiB
    bad = ("4 4\n" + "v -0.123456789012345 -0.123456789012345 -0.123456789012345\n" * 4
           + "f 1 2 3\n" * 4)
    assert c10_size(bad, 4, 4)[0] in ("warn", "fail"), "C10 long decimals must WARN"
    # actual output already over the hard cap -> fail
    huge = "1 1\n" + "v " + "0" * (101 * MIB) + " 0 0\nf 1 1 1\n"
    assert c10_size(huge, 1, 1)[0] == "fail", "C10 over 100 MiB must FAIL"


# ============================================================================
# Sample-case check [ABSOLUTE] — the one known-correct answer in the statement
# ============================================================================
# The problem ships a single case with a known optimum: a 9-vertex cube with a
# redundant coplanar vertex collapses to 8 vertices / 12 faces with FinalSSIM = 1.0
# (the removed vertex changes neither normals nor depth). A correct solver must
# reproduce this exactly: FinalSSIM ~ 1.0 AND V' <= 8.

SAMPLE_SSIM_MIN = 0.999
SAMPLE_V_MAX = 8


def sample_classify(final_ssim, nv):
    """[ABSOLUTE] ('ok'|'fail', detail) for the sample-case output."""
    ok = final_ssim >= SAMPLE_SSIM_MIN and nv <= SAMPLE_V_MAX
    return ("ok" if ok else "fail",
            f"V'={nv} (need <= {SAMPLE_V_MAX}), FinalSSIM={final_ssim:.4f} "
            f"(need >= {SAMPLE_SSIM_MIN})")


@teeth("sample")
def _selftest_sample():
    assert sample_classify(1.0, 8)[0] == "ok", "sample 1.0/8 must pass"
    assert sample_classify(0.5, 8)[0] == "fail", "sample low-SSIM must fail"
    assert sample_classify(1.0, 9)[0] == "fail", "sample V'>8 must fail"


# ============================================================================
# Irregular realistic proxy [FIX 7] — analytic proxies have uniform connectivity;
# connectivity bugs hide in irregular meshes. We build a bumpy sphere with
# spatially varying displacement (sharp features + uneven geometric density),
# self-validated as a closed 2-manifold before use.
# ============================================================================

def gen_irregular(subdiv=3, seed=20260626):
    V0, F0 = T.gen_sphere(subdiv)
    V = np.ascontiguousarray(V0, np.float64)
    rng = np.random.default_rng(seed)
    r = np.linalg.norm(V, axis=1, keepdims=True)
    dirs = V / np.maximum(r, 1e-12)
    # amplitude varies over the surface -> some regions bumpy/dense in feature,
    # others smooth; plus per-vertex jitter for an irregular look.
    field = 0.06 + 0.05 * np.sin(3.0 * V[:, 0]) * np.cos(3.0 * V[:, 1]) * np.sin(3.0 * V[:, 2] + 1.0)
    jitter = rng.uniform(-0.025, 0.025, size=len(V))
    disp = field + jitter
    V = V + dirs * disp[:, None]
    V = T._center_unit(V, radius=0.97)
    F1 = np.ascontiguousarray(F0, np.int64) + 1
    # self-validate: closed 2-manifold, non-degenerate, in-sphere, consistent winding
    assert T.inv1_manifold(len(V), len(F1), V, F1)[0], "irregular proxy not 2-manifold"
    assert T.inv2_area(len(V), len(F1), V, F1)[0], "irregular proxy has degenerate face"
    assert c3_unit_sphere(V, F1, V, F1)[0], "irregular proxy left unit sphere"
    assert c2_winding(V, F1, V, F1)[0], "irregular proxy winding inconsistent"
    return V, F1


def gen_irregular0():
    """gen_irregular returning 0-based faces, to match the T.PROXIES convention."""
    V, F1 = gen_irregular(3)
    return V, F1 - 1


# A REAL, ADVERSARIAL mesh (the missing piece of test coverage). The analytic
# proxies (spheres/tori/cubes) are smoothly approximable: QEM keeps them within ~40%
# of the Hausdorff budget at ANY compression, so they could NEVER reproduce the
# judge's "too much geometric deviation" failures. The libigl Stanford bunny is a
# real watertight 2-manifold whose thin ears + fine concave detail make the QEM-cost
# budget UNDER-estimate the true point-to-surface Hausdorff: pushed to high
# compression it genuinely blows past 5% of the diagonal (measured 102-716% of the
# budget), and the oracle correctly rejects it. (See scripts that produced it /
# docs/theory/qem-cost-is-not-hausdorff.md "Why the cube hid this".)
def _load_real(stem):
    """Load + self-validate a bundled real watertight mesh (AABB-centered, in the
    unit sphere); returns (V, F0). These real models are the only proxies that can
    reproduce the judge's geometric-deviation failures (smooth analytic blobs can't)."""
    path = os.path.join(T.REPO, "tests", "data", stem + "_watertight.obj")
    _, _, V, F1 = T.parse_obj(open(path).read())
    assert T.inv1_manifold(len(V), len(F1), V, F1)[0], f"{stem} not 2-manifold"
    assert T.inv2_area(len(V), len(F1), V, F1)[0], f"{stem} has degenerate face"
    assert float(np.linalg.norm(V, axis=1).max()) <= 1.0 + 1e-6, f"{stem} outside unit sphere"
    return V, F1 - 1


def gen_bunny():     return _load_real("bunny")
def gen_armadillo(): return _load_real("armadillo")
def gen_fandisk():   return _load_real("fandisk")
def gen_cow():       return _load_real("cow")


# Real watertight models, varied failure modes: detailed-organic (bunny, cow),
# large-detailed (armadillo), and CAD with large flat regions + sharp creases
# (fandisk). (name, gen, vertex-count) — armadillo is heavy, used where time allows.
REAL_MESHES = [
    ("bunny 3485v", gen_bunny, 3485),
    ("cow 2903v", gen_cow, 2903),
    ("fandisk 6475v", gen_fandisk, 6475),
    ("armadillo 49990v", gen_armadillo, 49990),
]


# The analytic proxies (from test2) plus the realistic irregular one (FIX 7) and the
# real adversarial bunny.
ALL_PROXIES = list(T.PROXIES) + [("irregular", gen_irregular0, 2), ("bunny", gen_bunny, 2)]

# Proxies used to find + gate the OPERATING POINT. Curated to be diverse and at or
# above contest-relevant scale (the tiny 42-/162-vertex spheres can't compress and
# only add noise to the headline). Includes two contest-scale spheres (2.5k, 10k)
# so the reported safe compression reflects real submission sizes. Names carry the
# vertex count so the table is self-explanatory.
OP_PROXIES = [
    ("sfera 10242v", lambda: T.gen_sphere(5), 2),
    ("toro 392v",    lambda: T.gen_torus(), 0),
    ("bunny reale 3485v", gen_bunny, 2),   # real: detailed organic
    ("cow reale 2903v",   gen_cow, 2),     # real: organic, different topology
    ("fandisk reale 6475v", gen_fandisk, 2),  # real: CAD, large flats + sharp creases
    ("cubo 218v",    lambda: T.gen_cube(6), 2),
    ("lastra sottile", lambda: T.gen_thin_slab(6), 2),
]
# Curved, contest-relevant meshes whose compression defines the headline (flat
# cube/slab trivially hit ~96% and would flatter the number). The real bunny is
# included: it is the most honest data point for achievable safe compression.
REPRESENTATIVE = {"sfera 10242v", "toro 392v", "bunny reale 3485v",
                  "cow reale 2903v", "fandisk reale 6475v"}


# ============================================================================
# Full suite driver
# ============================================================================

MARK = {True: "✅", False: "❌"}
WARN = "⚠️ "
STATUS_MARK = {"ok": "✅", "warn": "⚠️ ", "fail": "❌"}

# Human-readable name for every check code, so the report never makes you consult
# a legend: failures/warnings are printed by name (e.g. "Hausdorff", "perceptual
# SSIM") with the offending number, not as "C1"/"C6".
LABEL = {
    "C1":  "Hausdorff <= 5%",
    "C2":  "winding consistency",
    "C2b": "orientation vs input",
    "C3":  "inside unit sphere",
    "C4":  "connected components",
    "C5":  "genus / Euler",
    "C6":  "perceptual SSIM >= 0.9",
    "C7":  "robustness",
    "C8":  "time budget",
    "C9":  "idempotence",
    "C10": "output size <= 100MiB",
    "C11": "memory budget",
    "C8-time": "time budget",
    "C11-mem": "memory budget",
    "sample": "sample-case answer",
    "run": "solver run",
    "gate-teeth": "SSIM-gate teeth",
}


def lbl(code):
    return LABEL.get(code, code)


def describe_results(results):
    """Turn a list of (code, tag, status, detail) into a one-line, legend-free
    verdict: all-green -> a short OK; otherwise the non-OK checks spelled out by
    name with their detail."""
    bad = [(c, st, d) for c, _t, st, d in results if st != "ok"]
    if not bad:
        n = len(results)
        return f"✅ all {n} checks pass"
    return "   ".join(f"{STATUS_MARK[st]} {lbl(c)} — {d}" for c, st, d in bad)

# Per-(mesh,frac) checks. C1-C5 return a bool (ABSOLUTE). C6 returns a 3-state
# margin band ('ok'/'warn'/'fail'); a 'fail' (FinalSSIM < 0.85) is ABSOLUTE — the
# perceptual gate is the binding constraint — while 'warn' is the uncertainty band.
CORRECTNESS = [("C1", "ABS", c1_hausdorff), ("C2", "ABS", c2_winding),
               ("C2b", "ABS", c2b_orientation),
               ("C3", "ABS", c3_unit_sphere), ("C4", "ABS", c4_components),
               ("C5", "ABS", c5_genus), ("C6", "ORC", c6_perceptual)]
ABS_CORRECTNESS = [c for c in CORRECTNESS if c[1] == "ABS"]   # C1..C5 + C2b (no C6)

TETRA_V = np.array([[0.12, 0.12, 0.12], [-0.12, -0.12, 0.12],
                    [-0.12, 0.12, -0.12], [0.12, -0.12, -0.12]], np.float64)
TETRA_F1 = np.array([[1, 2, 3], [1, 4, 2], [1, 3, 4], [2, 4, 3]], np.int64)


class Tally:
    def __init__(self):
        self.abs_fail = []      # (where, check, detail) — a real solver bug
        self.orc_warn = []      # (where, detail) — oracle uncertainty band, not fatal
        self.test_error = []    # (where, detail) — an error INSIDE the test itself

    def record(self, where, name, status, detail):
        """status in {'ok','warn','fail'}; 'fail' is an absolute failure."""
        if status == "fail":
            self.abs_fail.append((where, name, detail))
        elif status == "warn":
            self.orc_warn.append((where, f"{name}: {detail}"))


def _to_status(res):
    """Normalise a checker result to a status: bool -> ok/fail; str passes through."""
    if isinstance(res, bool):
        return "ok" if res else "fail"
    return res


def _run_checks(Vin, Fin1, Vout, Fout1, checks):
    """Return ordered [(name, tag, status, detail)] for the requested checks."""
    out = []
    for name, tag, fn in checks:
        try:
            res, detail = fn(Vin, Fin1, Vout, Fout1)
            status = _to_status(res)
        except Exception as e:
            status, detail = "fail", f"checker raised {e!r}"
        out.append((name, tag, status, detail))
    return out


# fracs spanning gentle -> abusive so the table shows the full ok -> warn -> fail
# cliff. The user-suggested set is augmented with one gentle point (0.02) at the
# low end so the operating point (highest frac still scoring) is visible.
CLIFF_FRACS = [0.02, 0.1, 0.3, 0.5, 0.8, 1.2, 2.0, 3.0]
CLIFF_PROXIES = ["sphere_s3", "spiky_s2", "torus"]   # curved: a real SSIM cliff


def compute_cliff(solver):
    """DIAGNOSTIC only (does not gate): the SSIM-vs-frac curve per curved proxy,
    so a reader sees the ok->warn->fail cliff. Returns [(name, V, rows)]."""
    proxy_gen = dict((n, g) for n, g, _ in T.PROXIES)
    out = []
    for name in CLIFF_PROXIES:
        V0, F0 = proxy_gen[name]()
        V = np.ascontiguousarray(V0); F1 = np.ascontiguousarray(F0) + 1
        obj = T.mesh_to_obj(V, F1)
        diag = aabb_diag(V); limit = HAUS_FRACTION * diag
        rows = []
        for fr in CLIFF_FRACS:
            try:
                _, _, Vo, Fo = T.parse_obj(T.run_solver(solver, obj, fr))
            except Exception:
                continue
            ssim, comp = oracle_score(V, F1, Vo, Fo, key=name)   # reuse cached input render
            haus = hausdorff_symmetric(V, F1, Vo, Fo)
            status, _ = c6_classify(ssim, comp)
            rows.append((fr, len(Vo), comp, haus / limit * 100, ssim, status, ssim >= SSIM_GATE))
        out.append((name, len(V), rows))
    return out


# The FULL hard-constraint set, re-checked at the operating point, with labels
# phrased in the words of the problem statement. Judge constraints first, then the
# extra structural guards we add. Returns [(label, 'ok'|'fail', detail)].
def hard_checks_at(Vin, Fin1, Vout, Fout1, out_text):
    nv, nf = len(Vout), len(Fout1)

    def st(b):
        return "ok" if b else "fail"

    mok, md = T.inv1_manifold(nv, nf, Vout, Fout1)
    aok, ad = T.inv2_area(nv, nf, Vout, Fout1)
    iok, idd = T.inv3_indices(nv, nf, Vout, Fout1)
    vrange = 1 <= nv <= len(Vin)
    hok, hd = c1_hausdorff(Vin, Fin1, Vout, Fout1)
    nbytes = len(out_text.encode("utf-8"))
    ook, od = c2b_orientation(Vin, Fin1, Vout, Fout1)
    wok, wd = c2_winding(Vin, Fin1, Vout, Fout1)
    sok, sd = c3_unit_sphere(Vin, Fin1, Vout, Fout1)
    cok, cd = c4_components(Vin, Fin1, Vout, Fout1)
    gok, gd = c5_genus(Vin, Fin1, Vout, Fout1)
    return [
        ("Manifold: ogni edge condiviso da esattamente 2 facce", st(mok), md),
        ("Facce non degeneri: area positiva", st(aok), ad),
        ("Indici validi e numero vertici 1 <= V' <= V", st(iok and vrange),
         f"{idd}; V'={nv} <= V={len(Vin)}"),
        ("Hausdorff <= 5% della diagonale del bounding box", st(hok), hd),
        ("Output <= 100 MiB", st(nbytes <= OUTPUT_LIMIT_BYTES), f"{nbytes/MIB:.4f} MiB"),
        ("Orientazione coerente con l'input (normali verso l'esterno)", st(ook), od),
        ("Winding coerente (ogni edge una volta per verso)", st(wok), wd),
        ("Vertici dentro la sfera unitaria", st(sok), sd),
        ("Stesso numero di componenti connesse", st(cok), cd),
        ("Stesso genere topologico (V-E+F invariato)", st(gok), gd),
    ]


def compute_robustness(solver, tally):
    """Extreme & malformed inputs must degrade gracefully (never crash). Returns
    dict(ok, n, fails)."""
    tetra_obj = T.mesh_to_obj(TETRA_V, TETRA_F1)
    Vs, Fs = T.gen_sphere(2)
    Vs = np.ascontiguousarray(Vs); Fs1 = np.ascontiguousarray(Fs) + 1
    sphere_obj = T.mesh_to_obj(Vs, Fs1)
    cases = []   # (label, category, obj, args, Vin, Fin1)
    for lab, args in [("tetra frac=0", ["0"]), ("tetra frac=-1", ["-1"])]:
        cases.append((lab, "valid_extreme", tetra_obj, args, TETRA_V, TETRA_F1))
    for lab, args in [("sphere frac=0", ["0"]), ("sphere frac=0.05", ["0.05"])]:
        cases.append((lab, "valid_extreme", sphere_obj, args, Vs, Fs1))
    for lab, args in [("tetra frac=100", ["100"]), ("sphere frac=100", ["100"]),
                      ("sphere frac=-1", ["-1"])]:
        Vin, Fin1 = (TETRA_V, TETRA_F1) if lab.startswith("tetra") else (Vs, Fs1)
        obj = tetra_obj if lab.startswith("tetra") else sphere_obj
        cases.append((lab, "overdrive", obj, args, Vin, Fin1))
    v = "v 0.1 0.1 0.1\nv -0.1 -0.1 0.1\nv -0.1 0.1 -0.1\nv 0.1 -0.1 -0.1\n"
    for lab, obj in [("header conteggi errati", "10 4\n" + v + "f 1 2 3\nf 1 4 2\nf 1 3 4\nf 2 4 3\n"),
                     ("indice di faccia 0", "4 4\n" + v + "f 0 2 3\nf 1 4 2\nf 1 3 4\nf 2 4 3\n"),
                     ("indice fuori range", "4 4\n" + v + "f 1 2 99\nf 1 4 2\nf 1 3 4\nf 2 4 3\n"),
                     ("input vuoto", "")]:
        cases.append((lab, "malformed", obj, ["0.5"], None, None))
    fails = []
    for lab, cat, obj, args, Vin, Fin1 in cases:
        rc, out, err = run_raw(solver, obj, *args)
        ok, detail = c7_classify(rc, out, cat, Vin, Fin1)
        if not ok:
            fails.append((lab, detail))
            tally.abs_fail.append(("Robustezza", f"input '{lab}'", detail))
    return dict(ok=not fails, n=len(cases), fails=fails)


def compute_scale(solver, tally, max_subdiv):
    """Time & memory as the mesh grows; output must still pass C1-C5. Returns
    dict(ok, rows, proj_time, proj_mem, proj_ok)."""
    rows = []   # (V, F, Vp, time, usv, rss_mb, valid_ok, fail_reason)
    pts = []
    ok_all = True
    for s in range(4, max_subdiv + 1):
        V0, F0 = T.gen_sphere(s)
        V = np.ascontiguousarray(V0); F1 = np.ascontiguousarray(F0) + 1
        rc, out, elapsed, rss = run_raw_mem(solver, T.mesh_to_obj(V, F1), "0.05")
        if rc != 0:
            ok_all = False
            tally.abs_fail.append(("Scala", f"subdiv{s} ({len(V)} vertici)", f"solver rc={rc}"))
            rows.append((len(V), len(F0), None, elapsed, 0, rss / MIB, False, f"rc={rc}"))
            continue
        _, _, Vo, Fo = T.parse_obj(out)
        tok, td = c8_time_ok(elapsed)
        mok, md = c11_mem_ok(rss)
        abs_results = _run_checks(V, F1, Vo, Fo, ABS_CORRECTNESS)
        c15 = all(st == "ok" for _, _, st, _ in abs_results)
        reason = ""
        if not (tok and mok and c15):
            ok_all = False
            if not tok:
                tally.abs_fail.append(("Scala", f"subdiv{s} ({len(V)} vertici)", f"oltre il tempo: {td}"))
                reason = f"tempo {td}"
            if not mok:
                tally.abs_fail.append(("Scala", f"subdiv{s} ({len(V)} vertici)", f"oltre la memoria: {md}"))
                reason = (reason + "; " if reason else "") + f"memoria {md}"
            if not c15:
                tally.abs_fail.append(("Scala", f"subdiv{s} ({len(V)} vertici)", describe_results(abs_results)))
                reason = (reason + "; " if reason else "") + describe_results(abs_results)
        rows.append((len(V), len(F0), len(Vo), elapsed, elapsed / len(V) * 1e6,
                     rss / MIB, tok and mok and c15, reason))
        pts.append((len(V), elapsed, rss))
    proj_time = proj_mem = None
    if len(pts) >= 2:
        (v1, t1, _), (v2, t2, m2) = pts[-2], pts[-1]
        proj_time = t2 + (t2 - t1) / (v2 - v1) * (CASE7_V - v2)
        proj_mem = m2 / v2 * CASE7_V / MIB
    proj_ok = (proj_time is None) or (proj_time <= 21.0 and proj_mem <= 2048.0)
    return dict(ok=ok_all, rows=rows, proj_time=proj_time, proj_mem=proj_mem, proj_ok=proj_ok)


def compute_idempotence(solver, tally):
    """Re-simplify an output at the same frac: must stay valid and not drift.
    Returns dict(ok, lines)."""
    gens = dict((n, g) for n, g, _ in ALL_PROXIES)
    lines = []
    ok_all = True
    for name in ("sphere_s3", "torus", "cube_n6", "thin_slab", "irregular"):
        V0, F0 = gens[name]()
        V = np.ascontiguousarray(V0); F1 = np.ascontiguousarray(F0) + 1
        _, _, V1, F1a = T.parse_obj(T.run_solver(solver, T.mesh_to_obj(V, F1), 0.05))
        _, _, V2, F2a = T.parse_obj(T.run_solver(solver, T.mesh_to_obj(V1, F1a), 0.05))
        ok, detail = c9_idempotent(V1, F1a, V2, F2a)
        lines.append((name, len(V1), len(V2), ok, detail))
        if not ok:
            ok_all = False
            tally.abs_fail.append(("Stabilita/idempotenza", name, detail))
    return dict(ok=ok_all, lines=lines)


def compute_determinism(solver, tally):
    """The solver must be deterministic: same input + args -> byte-identical output.
    Returns dict(ok, detail)."""
    V0, F0 = T.gen_sphere(3)
    V = np.ascontiguousarray(V0); F1 = np.ascontiguousarray(F0) + 1
    obj = T.mesh_to_obj(V, F1)
    a = T.run_solver(solver, obj, 0.05)
    b = T.run_solver(solver, obj, 0.05)
    ok = (a == b)
    if not ok:
        tally.abs_fail.append(("Determinismo", "due run dello stesso input",
                               "output non byte-identico"))
    return dict(ok=ok, detail="due run identici byte-per-byte" if ok else "output divergente")


def compute_sample(solver, tally):
    """The one published example must come out exactly right. Returns dict(ok, vin, vout, ssim)."""
    path = os.path.join(T.REPO, "tests", "data", "sample.in")
    text = open(path).read()
    nvi, nfi, Vin, Fin1 = T.parse_obj(text)
    out = T.run_solver(solver, text, 0.5)
    nvo, nfo, Vout, Fout1 = T.parse_obj(out)
    ssim, comp = oracle_score(Vin, Fin1, Vout, Fout1)
    status, detail = sample_classify(ssim, nvo)
    if status != "ok":
        tally.abs_fail.append(("Caso di esempio", "sample.in", detail))
    return dict(ok=status == "ok", vin=nvi, vout=nvo, ssim=ssim)


def compute_fake(solver):
    """Proof the suite has teeth: a garbage 'always tetra' solver (which test2
    accepts) must be rejected. Returns dict(ok, rejected_by, real_ok)."""
    V0, F0 = T.gen_sphere(3)
    V = np.ascontiguousarray(V0); F1 = np.ascontiguousarray(F0) + 1
    fake_obj = ("4 4\nv 0.12 0.12 0.12\nv -0.12 -0.12 0.12\nv -0.12 0.12 -0.12\n"
                "v 0.12 -0.12 -0.12\nf 1 2 3\nf 1 4 2\nf 1 3 4\nf 2 4 3\n")
    _, _, Vfake, Ffake = T.parse_obj(fake_obj)
    _, _, Vreal, Freal = T.parse_obj(T.run_solver(solver, T.mesh_to_obj(V, F1), 0.02))
    real_fail = [lbl(n) for n, _t, stt, _ in _run_checks(V, F1, Vreal, Freal, CORRECTNESS) if stt == "fail"]
    fake_fail = [lbl(n) for n, _t, stt, _ in _run_checks(V, F1, Vfake, Ffake, CORRECTNESS) if stt == "fail"]
    return dict(ok=(not real_fail) and bool(fake_fail), rejected_by=fake_fail, real_ok=not real_fail)


def compute_operating_points(solver, tally):
    """For each proxy: find the operating point (max frac with FinalSSIM >= safe),
    re-assert every HARD constraint there, and return per-proxy result rows. Any
    hard failure here is [ABSOLUTE] — it is exactly the regime we submit in.
    Reuses oracle_score's cached input renders and the exact Hausdorff primitive."""
    rows = []
    for name, gen, _euler in OP_PROXIES:
        try:
            V0, F0 = gen()
            V = np.ascontiguousarray(V0, np.float64); F1 = np.ascontiguousarray(F0, np.int64) + 1
            diag = aabb_diag(V); limit = HAUS_FRACTION * diag
            cache = {}

            def ssim_of(fr, V=V, F1=F1, name=name, cache=cache):
                if fr not in cache:
                    out = T.run_solver(solver, T.mesh_to_obj(V, F1), fr)
                    nv, nf, Vo, Fo = T.parse_obj(out)
                    s, c = oracle_score(V, F1, Vo, Fo, key=name)
                    cache[fr] = (out, nv, nf, Vo, Fo, s, c)
                return cache[fr][5]

            status, frac = op_bisect(ssim_of)
            out, nv, nf, Vo, Fo, ssim, comp = cache[frac]
            hard = hard_checks_at(V, F1, Vo, Fo, out)   # full judge+extra hard set
            haus = hausdorff_symmetric(V, F1, Vo, Fo)
            haus_pct = haus / limit * 100.0
        except RuntimeError as e:                       # the solver itself crashed
            if "solver exit" in str(e):
                tally.abs_fail.append((f"{name} @ punto operativo", "Esecuzione del solver",
                                       f"il solver e' terminato con errore: {e}"))
            else:
                tally.test_error.append((f"{name} (punto operativo)", repr(e)))
            continue
        except Exception as e:                          # internal test error, NOT a solver fail
            tally.test_error.append((f"{name} (punto operativo)", repr(e)))
            continue

        hard_ok = (status != "fail_gate") and all(st == "ok" for _, st, _ in hard)
        where = f"{name} @ punto operativo (frac={frac:.3f}, compr {comp:.1f}%)"
        if status == "fail_gate":
            # root cause is the perceptual gate; don't pile on hard fails on garbage
            tally.abs_fail.append((where, "Punteggio percettivo FinalSSIM >= 0.90",
                                   f"FinalSSIM={ssim:.4f} < {SSIM_SAFE} anche senza "
                                   f"semplificare (frac=0)"))
        else:
            for clabel, st, d in hard:
                if st == "fail":
                    tally.abs_fail.append((where, clabel, d))

        rows.append(dict(name=name, status=status, frac=frac, comp=comp, ssim=ssim,
                         haus_pct=haus_pct, hard=hard, hard_ok=hard_ok))
    return rows


def compute_size_projection(solver):
    """Worst case-7 output-size projection (MiB) across a few proxies."""
    gens = dict((n, g) for n, g, _ in ALL_PROXIES)
    worst = 0.0
    for name in ("sphere_s3", "torus", "irregular"):
        V0, F0 = gens[name]()
        V = np.ascontiguousarray(V0); F1 = np.ascontiguousarray(F0) + 1
        out = T.run_solver(solver, T.mesh_to_obj(V, F1), 0.02)
        nv, nf, _, _ = T.parse_obj(out)
        _, detail = c10_size(out, nv, nf)
        proj = float(detail.split("proj=")[1].split("/")[0])
        worst = max(worst, proj)
    return worst


GUARD_MESHES = ["bunny", "cow", "fandisk"]   # real meshes (armadillo is slow; tested ad hoc)
GUARD_PUSH_FRACS = ["2", "8", "32"]          # push compression hard


def compute_deviation_guard(solver, tally):
    """FASE 1 verification (the safety floor), on REAL meshes. Two assertions:
      (1) GUARD ON (default devfrac): pushed to high compression, the symmetric
          Hausdorff MUST stay <= 5% of the diagonal. Before the guard the bunny blew
          to 532% of the budget; now it must never exceed 100%.
      (2) GUARD OFF (devfrac huge, argv[4]): the same solver over-compresses and the
          oracle MUST flag the > 5% violation — proving the ruler still has teeth and
          that the guard, not a blind oracle, is what keeps us valid.
    A guard breach (1) or a blind ruler (2) is an ABSOLUTE failure."""
    gens = dict((n, g) for n, g, _ in REAL_MESHES)
    rows = []
    guard_ok = teeth_ok = True
    for name in GUARD_MESHES:
        gen = next(g for k, g in gens.items() if k.startswith(name))
        V0, F0 = gen()
        V = np.ascontiguousarray(V0); F1 = np.ascontiguousarray(F0) + 1
        obj = T.mesh_to_obj(V, F1)
        lim = HAUS_FRACTION * aabb_diag(V)
        # (1) guard ON, pushed hard -> worst Hausdorff across fracs
        worst_pct = 0.0; worst_comp = 0.0
        for fr in GUARD_PUSH_FRACS:
            _, _, Vo, Fo = T.parse_obj(T.run_solver(solver, obj, fr))
            h = hausdorff_symmetric(V, F1, Vo, Fo)
            pct = h / lim * 100.0
            if pct > worst_pct:
                worst_pct = pct; worst_comp = 100.0 * (1.0 - len(Vo) / len(V))
        on_ok = worst_pct <= 100.0
        guard_ok = guard_ok and on_ok
        # (2) guard OFF (frac mode, devfrac huge) -> must over-compress AND be flagged
        _, _, Vo2, Fo2 = T.parse_obj(T.run_solver(solver, obj, "32", "0", "0", "1e9"))
        h2 = hausdorff_symmetric(V, F1, Vo2, Fo2)
        off_pct = h2 / lim * 100.0
        off_comp = 100.0 * (1.0 - len(Vo2) / len(V))
        off_violates = h2 > lim
        off_flagged = not c1_hausdorff(V, F1, Vo2, Fo2)[0]
        if off_violates and not off_flagged:
            teeth_ok = False
        rows.append((name, worst_comp, worst_pct, on_ok, off_comp, off_pct,
                     off_violates, off_flagged))
    if not guard_ok:
        tally.abs_fail.append(("Guardia di deviazione (Fase 1)", "mesh reale",
                               "la guardia NON tiene: l'Hausdorff sfora il 5% a "
                               "compressione spinta"))
    if not teeth_ok:
        tally.abs_fail.append(("Oracolo Hausdorff", "righello cieco",
                               "con la guardia DISATTIVATA il solver sfora ma l'oracolo "
                               "non lo rileva"))
    return dict(rows=rows, guard_ok=guard_ok, teeth_ok=teeth_ok)


def _agg_hard(op_rows):
    """Aggregate the per-proxy hard checks: a constraint is OK only if every
    operating point passes it; otherwise report the first offender."""
    if not op_rows:
        return []
    labels = [l for l, _, _ in op_rows[0]["hard"]]
    out = []
    for lab in labels:
        status, note = "ok", ""
        for r in op_rows:
            d = dict((l, (s, dd)) for l, s, dd in r["hard"])
            s, dd = d.get(lab, ("ok", ""))
            if s == "fail":
                status, note = "fail", f"{r['name']}: {dd}"
                break
        out.append((lab, status, note))
    return out


MARK_OK, MARK_BAD = "OK", "❌"


def print_verdict_block(op_rows, rob, scale, idem, det, samp, fake, size_proj, tally):
    fail_hard = len(tally.abs_fail)
    valido = fail_hard == 0
    ok_rows = [r for r in op_rows if r["status"] != "fail_gate"]
    # headline compression: the worst case among the representative curved meshes
    # (tiny/flat proxies are excluded so the number is honest and contest-relevant)
    rep_rows = [r for r in ok_rows if r["name"] in REPRESENTATIVE]
    comp_min = min((r["comp"] for r in rep_rows), default=0.0)
    comp_min_mesh = min(rep_rows, key=lambda r: r["comp"])["name"] if rep_rows else "-"
    comp_max = max((r["comp"] for r in rep_rows), default=0.0)
    haus_worst = max((r["haus_pct"] for r in op_rows), default=0.0)
    # "beyond range" operating points are the only oracle-uncertain gated results
    warning = sum(1 for r in op_rows if r["status"] == "beyond")

    line = "=" * 80
    print(line)
    verdict = "PASS" if valido else "FAIL"
    head = " TEST3  ·  la mesh semplificata rispetta Problem B?"
    print(head + " " * max(1, 80 - len(head) - len(f"VERDETTO: {verdict}")) + f"VERDETTO: {verdict}")
    print(line)
    print(" Ogni riga corrisponde a una regola del testo di Problem B.")
    print(" Legenda:  OK = rispettato    ❌ = violato (bug certo)    "
          "⚠️ = incertezza oracolo (non fatale)")
    print()

    # --- OPERATING POINT (the submission result) ---
    print(" PUNTO OPERATIVO  (massima compressione che resta sopra il gate: il tuo")
    print("                   risultato di gara — i vincoli hard sono verificati QUI)")
    print("   {:14s} {:>9s} {:>11s} {:>13s}   {}".format(
        "mesh", "compr max", "FinalSSIM", "Hausdorff", "vincoli hard"))
    for r in op_rows:
        hard_bad = [l for l, s, _ in r["hard"] if s == "fail"]
        if r["status"] == "fail_gate":
            vc = "❌ SSIM sotto soglia anche senza semplificare"
        elif hard_bad:
            vc = "❌ " + "; ".join(hard_bad)
        else:
            vc = "OK, tutti" + ("  (oltre il range testato)" if r["status"] == "beyond" else "")
        print("   {:14s} {:>8.1f}% {:>11.4f} {:>10.0f}% bud   {}".format(
            r["name"], r["comp"], r["ssim"], r["haus_pct"], vc))
    if rep_rows:
        print(f"   => compressione sicura: dal {comp_min:.0f}% (caso piu' difficile: "
              f"'{comp_min_mesh}') fino al {comp_max:.0f}% (mesh grandi);")
        print(f"      vincoli hard a TUTTI i punti operativi: "
              f"{'tutti rispettati' if valido else 'VIOLATI (vedi COSA SISTEMARE)'}")
    print()

    # --- HARD CONSTRAINTS (aggregated, in the words of the statement) ---
    print(' VINCOLI HARD  (sezione "Constraints" del testo: devono valere TUTTI)')
    for lab, status, note in _agg_hard(op_rows):
        extra = ""
        if lab.startswith("Hausdorff"):
            extra = f"   (peggiore: {haus_worst:.0f}% del budget)"
        elif lab.startswith("Output"):
            extra = f"   (proiezione caso 7: {size_proj:.0f} MiB)"
        mark = MARK_OK if status == "ok" else MARK_BAD
        body = f"   {mark}  {lab}{extra}"
        print(body)
        if status == "fail":
            print(f"        -> {note}")
    print()

    # --- PERCEPTUAL GATE ---
    print(' GATE PERCETTIVO  ("Optimization Objective": FinalSSIM >= 0.90)')
    gate_bad = [r for r in op_rows if r["status"] == "fail_gate"]
    if gate_bad:
        for r in gate_bad:
            print(f"   {MARK_BAD}  {r['name']}: FinalSSIM={r['ssim']:.4f} < 0.90 "
                  f"anche senza semplificare")
    else:
        print(f"   {MARK_OK}  Tutti i punti operativi superano il gate con margine "
              f"(>= {SSIM_SAFE}).")
    print(f"   nota: e' una stima dell'oracolo locale, ~0.002 di incertezza vs il "
          f"giudice reale (non fatale).")
    print()

    # --- ROBUSTNESS / SCALE / STABILITY ---
    print(" ROBUSTEZZA / SCALA / STABILITA'  (sicurezza ingegneristica, non nel testo)")
    rm = MARK_OK if rob["ok"] else MARK_BAD
    print(f"   {rm}  Input estremi e malformati gestiti senza crash ({rob['n']} casi)")
    if scale["rows"]:
        big = scale["rows"][-1]
        sm = MARK_OK if scale["ok"] and scale["proj_ok"] else MARK_BAD
        proj = ""
        if scale["proj_time"] is not None:
            warn = "" if scale["proj_ok"] else "  ⚠️ vicino ai limiti"
            proj = (f"; proiezione caso 7 (1.1M v): ~{scale['proj_time']:.0f}s, "
                    f"~{scale['proj_mem']:.0f}MB{warn}")
        print(f"   {sm}  Scala a {big[0]} vertici in {big[3]:.1f}s, {big[5]:.0f}MB{proj}")
    dm = MARK_OK if (det["ok"] and idem["ok"]) else MARK_BAD
    print(f"   {dm}  Deterministico (output byte-identico) e idempotente "
          f"(ri-semplificare non rompe)")
    print()

    # --- SAMPLE CASE ---
    print(" CASO DI ESEMPIO  (l'esempio risolto nel testo: da 9 a 8 vertici)")
    sm = MARK_OK if samp["ok"] else MARK_BAD
    print(f"   {sm}  Il solver lo riproduce: V'={samp['vout']} (atteso <= 8), "
          f"FinalSSIM={samp['ssim']:.3f}")
    print()

    # --- SELF-VERIFICATION ---
    print(" AUTO-VERIFICA  (prova che il test stesso ha i denti)")
    fm = MARK_OK if fake["ok"] else MARK_BAD
    print(f"   {fm}  Rifiuta un solver-spazzatura noto (ritorna sempre un tetraedro): "
          f"bocciato da [{', '.join(fake['rejected_by'])}]")
    print()

    # --- COSA SISTEMARE (only on failure): grouped by constraint, worst first ---
    if not valido:
        print(" COSA SISTEMARE  (fallimenti hard, dal piu' grave; raggruppati per vincolo)")
        groups = {}   # constraint label -> list of (where, detail)
        for where, lab, detail in _sort_failures(tally.abs_fail):
            groups.setdefault(lab, []).append((where, detail))
        for lab in groups:   # _sort_failures already ordered; dict keeps insertion order
            items = groups[lab]
            print(f"   ❌ {lab}  ({len(items)} mesh)")
            w, d = items[0]
            print(f"        es.: {d}")
            print(f"        su: {', '.join(sorted({w.split(' @ ')[0] for w, _ in items}))}")
        print()

    # --- machine-readable status line (last) ---
    print("-" * 80)
    print(f" STATO: valido={'SI' if valido else 'NO'}  "
          f"compressione_sicura_min={comp_min:.1f}%  "
          f"hausdorff_peggiore={haus_worst:.0f}%budget  "
          f"fail_hard={fail_hard}  warning={warning}")
    print(line)


_SEVERITY = ["SSIM", "Hausdorff", "Manifold", "degeneri", "Indici", "Orientazione",
             "Winding", "componenti", "genere", "sfera", "Output", "Scala", "memoria",
             "tempo", "Determinismo", "idempot", "Robustezza", "Caso", "Auto"]


def _sort_failures(abs_fail):
    def rank(item):
        text = (item[1] + " " + item[2]).lower()
        for i, kw in enumerate(_SEVERITY):
            if kw.lower() in text:
                return i
        return len(_SEVERITY)
    return sorted(abs_fail, key=rank)


def print_diagnostics(cliff, scale):
    print()
    print("-" * 80)
    print(" DIAGNOSTICA  (informativa, NON incide sul verdetto)")
    print("-" * 80)
    print(" Curva SSIM vs compressione (mostra dove si supera il gate 0.90):")
    for name, nv, rows in cliff:
        print(f"   [{name}]  V={nv}")
        print("     {:>5s} {:>5s} {:>7s} {:>11s} {:>9s}  {:9s}".format(
            "frac", "V'", "compr%", "Haus(%bud)", "FinalSSIM", "sopra 0.90?"))
        for fr, vp, comp, hpct, ssim, status, scores in rows:
            print("     {:>5} {:>5d} {:>6.1f}% {:>10.0f}% {:>9.4f}  {:9s}".format(
                fr, vp, comp, hpct, ssim, "SI" if scores else "no (0 pti)"))
    print()
    print(" Scala (tempo e memoria per dimensione):")
    print("   {:>9s} {:>9s} {:>6s} {:>8s} {:>8s}  valido?".format(
        "V", "F", "V'", "tempo", "RAM"))
    for v, f, vp, t, usv, rss, ok, reason in scale["rows"]:
        flag = "OK" if ok else f"❌ {reason}"
        vps = f"{vp}" if vp is not None else "-"
        print(f"   {v:>9d} {f:>9d} {vps:>6s} {t:>7.2f}s {rss:>6.0f}MB  {flag}")
    print()


def print_deviation_guard(g):
    print()
    print("=" * 80)
    print(" GUARDIA DI DEVIAZIONE (Fase 1) — Hausdorff sempre <= 5%, anche spinto, su REALI")
    print("  (il vincolo che bocciava le submission storiche: 'too much geometric")
    print("   deviation'. Le mesh lisce non lo riproducono mai; le reali si.)")
    print("=" * 80)
    print("   {:14s} | GUARDIA ON (spinta) | GUARDIA OFF (prova: oracolo coi denti)".format("mesh reale"))
    print("   {:14s}   {:>7s} {:>10s}   {:>7s} {:>10s}  {}".format(
        "", "compr", "Haus%bud", "compr", "Haus%bud", "oracolo?"))
    for name, oncomp, onpct, on_ok, offcomp, offpct, offv, offf in g["rows"]:
        on = f"{onpct:.0f}% {'OK' if on_ok else 'SFORA!'}"
        orc = ("BOCCIA" if offf else "CIECO!") if offv else "n/a"
        print("   {:14s}   {:>6.1f}% {:>9s}   {:>6.1f}% {:>9.0f}%  {}".format(
            name, oncomp, on, offcomp, offpct, orc))
    if g["guard_ok"] and g["teeth_ok"]:
        print("\n   ✅ Guardia ON: l'Hausdorff resta SEMPRE sotto il 5% (prima il bunny "
              "arrivava al 532%).")
        print("      Guardia OFF: il solver sfora e l'oracolo lo BOCCIA -> e' la guardia, "
              "non un oracolo cieco, a tenerci validi.")
    else:
        if not g["guard_ok"]:
            print("\n   ❌ La guardia NON tiene: Hausdorff oltre il 5% a compressione spinta.")
        if not g["teeth_ok"]:
            print("\n   ❌ Con guardia OFF l'oracolo non rileva lo sforamento (righello cieco).")
    print()


def main():
    selftest_only = "--selftest" in sys.argv
    run_selftests(verbose=selftest_only)
    if selftest_only:
        print("auto-test dei checker completato.")
        return 0

    if "--explain" in sys.argv:
        print_legend()
    solver = T.build_solver()
    max_subdiv = 8 if "--huge" in sys.argv else 7
    tally = Tally()

    # compute everything (no printing); the verdict block renders the result.
    # A guarded helper so an internal test error in one section is reported as
    # such (exit 2) and never as a silent crash or a fake solver failure.
    def guarded(fn, default):
        try:
            return fn()
        except Exception as e:
            import traceback
            tally.test_error.append((fn.__name__ if hasattr(fn, "__name__") else "sezione",
                                     f"{e!r}\n{traceback.format_exc()}"))
            return default

    op_rows = guarded(lambda: compute_operating_points(solver, tally), [])
    rob = guarded(lambda: compute_robustness(solver, tally), dict(ok=False, n=0, fails=[]))
    scale = guarded(lambda: compute_scale(solver, tally, max_subdiv),
                    dict(ok=False, rows=[], proj_time=None, proj_mem=None, proj_ok=False))
    idem = guarded(lambda: compute_idempotence(solver, tally), dict(ok=False, lines=[]))
    det = guarded(lambda: compute_determinism(solver, tally), dict(ok=False, detail="errore interno"))
    samp = guarded(lambda: compute_sample(solver, tally), dict(ok=False, vin=0, vout=0, ssim=0.0))
    fake = guarded(lambda: compute_fake(solver), dict(ok=False, rejected_by=[], real_ok=False))
    if not fake["ok"]:
        tally.abs_fail.append(("Auto-verifica", "denti del test",
                               "la suite non ha respinto il solver-spazzatura"))
    size_proj = guarded(lambda: compute_size_projection(solver), 0.0)
    haus_cov = guarded(lambda: compute_deviation_guard(solver, tally),
                       dict(rows=[], guard_ok=False, teeth_ok=False))

    if tally.test_error:
        print(" ATTENZIONE: errori INTERNI al test (non sono fallimenti del solver):")
        for where, d in tally.test_error:
            print(f"   - {where}: {d}")
        print()

    print_verdict_block(op_rows, rob, scale, idem, det, samp, fake, size_proj, tally)
    print_deviation_guard(haus_cov)
    if "--diag" in sys.argv or "--verbose" in sys.argv:
        print_diagnostics(guarded(lambda: compute_cliff(solver), []), scale)
    else:
        print(" (dettagli diagnostici, curva SSIM e tabella scala: rilancia con --diag)")

    # exit codes: 0 = pass, 1 = solver hard failure, 2 = internal test error
    if tally.test_error:
        return 2
    return 0 if not tally.abs_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
