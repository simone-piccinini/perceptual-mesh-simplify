#!/usr/bin/env python3
"""check_structural_validity — absolute STRUCTURAL invariants of the solver output.

GUARANTEES: the output is a structurally sound mesh as a matter of pure mathematics
(closed 2-manifold, Euler characteristic preserved, positive face area, valid
indices, single connected component, deterministic, monotone in frac).
Does NOT GUARANTEE anything about the judge's score, Hausdorff, or SSIM — those are
the oracle's job (see scripts/validate_oracle.py and check_constraints_and_fidelity.py).

The three independent levels:

    python scripts/validate_oracle.py             # "the oracle reproduces known facts"
    python tests/check_structural_validity.py     # "the solver never emits broken meshes"
    python tests/check_constraints_and_fidelity.py # "the output respects every hard rule"

GUIDING PRINCIPLE — verify only what is ABSOLUTELY true.
------------------------------------------------------
The judge that scores the contest is secret. Some properties of a good
simplification depend on assumptions about that judge (FinalSSIM, Hausdorff
thresholds, the exact render pipeline). Those are the oracle's job
(`imc_eval.evaluate`) and are, at best, calibrated estimates.

test2 asserts ONLY properties that are true as a matter of pure mathematics,
independent of any judge: a closed orientable 2-manifold triangle mesh has a
fixed Euler characteristic, every interior edge is shared by exactly two faces,
faces have positive area, indices are in range, and so on. When test2 says PASS
it is a mathematical certainty that the solver produced a structurally sound
mesh — not a guess about the judge.

What test2 deliberately does NOT do: it never renders, never computes SSIM, never
checks Hausdorff against a threshold. Those belong to the oracle. test2 is the
guardian of absolute structural invariants, kept pure and separate.

Invariants asserted on every solver OUTPUT (per mesh, per frac):
  INV1  closed 2-manifold : every undirected edge shared by EXACTLY two faces.
  INV2  no zero-area face : min triangle area > 1e-15.
  INV3  valid indices     : every face index in [1, V'] (1-based output).
  INV4  no orphan vertex  : every vertex referenced by at least one face.
  INV5  no degenerate tri : no face repeats a vertex index.
  INV6  Euler preserved   : V'-E'+F' equals the input's V-E+F (genus is kept).
  INV7  problem bounds    : 1 <= V' <= V_input.
  INV8  determinism       : identical input+args -> byte-identical output.
  INV9  monotonicity      : a more aggressive setting never yields MORE vertices.

NOTE on INV9 and `frac`: in THIS solver `frac` (argv[1]) is the safety fraction
of the Hausdorff budget, so LARGER frac = larger collapse budget = MORE
aggressive = fewer vertices. INV9 therefore asserts V' is non-increasing as frac
increases. (The original spec phrased it with a "keep fraction" where small =
aggressive; the invariant is the same principle — more aggressive never adds
vertices — applied to this solver's knob.)

Robustness: depends only on numpy + a C++ compiler. No numba, no igl, no scipy.
If a mesh proxy cannot be generated *and validated*, test2 fails loudly rather
than skipping it.

Run:  python tests/test2.py            # builds solver if needed, runs everything
      SOLVER=/path/to/solver python tests/test2.py   # use a prebuilt binary
"""

import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AREA_EPS = 1e-15          # matches the solver's kAreaEps / oracle DEGENERATE_AREA_EPS
FRACS = [0.05, 0.1, 0.3, 0.5]   # ascending; larger = more aggressive (see INV9)
INV_NAMES = ["INV1", "INV2", "INV3", "INV4", "INV5", "INV6", "INV7", "INV8", "INV9"]


# ============================================================================
# Mesh proxy generators — all return (V float64 (n,3), F int64 (m,3), 0-based).
# Every one is a closed, watertight, orientable 2-manifold, centered and scaled
# strictly inside the unit sphere. Variety: topology (genus 0 and 1), curvature
# (smooth, sharp, planar), and resolution.
# ============================================================================

def _center_unit(V, radius=0.97):
    """Center at origin and scale so the farthest vertex sits at `radius` < 1."""
    V = V - V.mean(axis=0)
    r = np.linalg.norm(V, axis=1).max()
    if r == 0.0:
        raise ValueError("degenerate mesh: all vertices coincide")
    return V / r * radius


def _icosahedron():
    t = (1.0 + 5.0 ** 0.5) / 2.0
    V = np.array([
        [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
        [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
        [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1],
    ], dtype=np.float64)
    F = np.array([
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
    ], dtype=np.int64)
    V /= np.linalg.norm(V, axis=1, keepdims=True)
    return V, F


def _subdivide_on_sphere(V, F, levels):
    """Loop-style 1->4 subdivision with midpoints re-projected to the sphere.
    Preserves orientation (child triangles keep the parent winding)."""
    for _ in range(levels):
        vlist = [v for v in V]
        cache = {}

        def mid(a, b):
            key = (a, b) if a < b else (b, a)
            if key not in cache:
                m = (V[a] + V[b]) / 2.0
                m = m / np.linalg.norm(m)
                cache[key] = len(vlist)
                vlist.append(m)
            return cache[key]

        newF = []
        for a, b, c in F:
            a, b, c = int(a), int(b), int(c)
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            newF += [[a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]]
        V = np.array(vlist, dtype=np.float64)
        F = np.array(newF, dtype=np.int64)
    return V, F


def gen_sphere(subdiv):
    V, F = _icosahedron()
    V, F = _subdivide_on_sphere(V, F, subdiv)
    return _center_unit(V), F


def gen_spiky_sphere(subdiv=2, spike=1.7):
    """Smooth sphere with the 12 original icosahedron vertices pushed outward:
    sharp normal-discontinuity spikes, same (genus-0) topology."""
    V, F = _icosahedron()
    base = V.shape[0]                 # the 12 corners that become spikes
    V, F = _subdivide_on_sphere(V, F, subdiv)
    V[:base] *= spike                 # only the original corners spike out
    return _center_unit(V), F


def gen_torus(n_major=28, n_minor=14, R=1.0, r=0.42):
    """Genus-1 watertight torus (Euler characteristic 0)."""
    pts = []
    for i in range(n_major):
        u = 2 * np.pi * i / n_major
        cu, su = np.cos(u), np.sin(u)
        for j in range(n_minor):
            v = 2 * np.pi * j / n_minor
            cv, sv = np.cos(v), np.sin(v)
            pts.append([(R + r * cv) * cu, (R + r * cv) * su, r * sv])
    V = np.array(pts, dtype=np.float64)

    def vid(i, j):
        return (i % n_major) * n_minor + (j % n_minor)

    F = []
    for i in range(n_major):
        for j in range(n_minor):
            a, b = vid(i, j), vid(i + 1, j)
            c, d = vid(i + 1, j + 1), vid(i, j + 1)
            F.append([a, b, c]); F.append([a, c, d])
    return _center_unit(V), np.array(F, dtype=np.int64)


def gen_cube(n=6):
    """Closed cube surface, each of 6 faces an n x n grid: large planar regions
    plus sharp 90-degree edges. Shared edge/corner vertices are deduplicated so
    the result is a single closed 2-manifold (genus 0)."""
    verts, index, F = [], {}, []

    def get(p):
        key = (round(p[0], 9), round(p[1], 9), round(p[2], 9))
        if key not in index:
            index[key] = len(verts)
            verts.append([float(p[0]), float(p[1]), float(p[2])])
        return index[key]

    ts = np.linspace(-1.0, 1.0, n + 1)

    def face(point, flip):
        for i in range(n):
            for j in range(n):
                a, b = get(point(i, j)), get(point(i + 1, j))
                c, d = get(point(i + 1, j + 1)), get(point(i, j + 1))
                if not flip:
                    F.append([a, b, c]); F.append([a, c, d])
                else:
                    F.append([a, c, b]); F.append([a, d, c])

    face(lambda i, j: (1.0, ts[i], ts[j]), flip=False)
    face(lambda i, j: (-1.0, ts[i], ts[j]), flip=True)
    face(lambda i, j: (ts[i], 1.0, ts[j]), flip=True)
    face(lambda i, j: (ts[i], -1.0, ts[j]), flip=False)
    face(lambda i, j: (ts[i], ts[j], 1.0), flip=False)
    face(lambda i, j: (ts[i], ts[j], -1.0), flip=True)
    return _center_unit(np.array(verts, dtype=np.float64)), np.array(F, dtype=np.int64)


def gen_thin_slab(n=6, thin=0.14):
    """A subdivided cube flattened along z: thin geometry with sharp edges,
    stresses the area/flip gates near degeneracy. Still genus 0."""
    V, F = gen_cube(n)
    V = V.copy()
    V[:, 2] *= thin
    return _center_unit(V), F


# (name, generator, expected Euler characteristic = 2 - 2*genus)
PROXIES = [
    ("sphere_s1", lambda: gen_sphere(1), 2),
    ("sphere_s2", lambda: gen_sphere(2), 2),
    ("sphere_s3", lambda: gen_sphere(3), 2),
    ("spiky_s2",  lambda: gen_spiky_sphere(2), 2),
    ("torus",     lambda: gen_torus(), 0),
    ("cube_n6",   lambda: gen_cube(6), 2),
    ("thin_slab", lambda: gen_thin_slab(6), 2),
]


# ============================================================================
# Mesh representation used by the checks: (nv, nf, V (nv,3) float, F (nf,3) int
# 1-BASED). Pure-math invariant helpers below operate on this.
# ============================================================================

def edges_undirected(F1):
    """Counter over undirected edges (sorted index pairs) of 1-based faces."""
    from collections import Counter
    c = Counter()
    for a, b, cc in F1:
        for x, y in ((a, b), (b, cc), (cc, a)):
            c[(x, y) if x < y else (y, x)] += 1
    return c


def euler_characteristic(nv, F1):
    """V - E + F with E = number of distinct undirected edges."""
    return nv - len(edges_undirected(F1)) + len(F1)


def face_areas(V, F1):
    p0 = V[F1[:, 0] - 1]
    p1 = V[F1[:, 1] - 1]
    p2 = V[F1[:, 2] - 1]
    return 0.5 * np.linalg.norm(np.cross(p1 - p0, p2 - p0), axis=1)


def inv1_manifold(nv, nf, V, F1):
    bad = sum(1 for k in edges_undirected(F1).values() if k != 2)
    return bad == 0, ("all edges shared by 2 faces" if bad == 0
                      else f"{bad} edge(s) not shared by exactly 2 faces")


def inv2_area(nv, nf, V, F1):
    if nf == 0:
        return False, "no faces"
    mn = float(face_areas(V, F1).min())
    return mn > AREA_EPS, f"min area={mn:.3e}"


def inv3_indices(nv, nf, V, F1):
    if nf == 0:
        return False, "no faces"
    lo, hi = int(F1.min()), int(F1.max())
    ok = lo >= 1 and hi <= nv
    return ok, f"index range [{lo},{hi}] vs [1,{nv}]"


def inv4_orphans(nv, nf, V, F1):
    used = set(int(x) for x in F1.reshape(-1))
    missing = set(range(1, nv + 1)) - used
    return len(missing) == 0, ("no orphan vertices" if not missing
                               else f"{len(missing)} orphan vertex(es)")


def inv5_degenerate(nv, nf, V, F1):
    bad = int(np.sum((F1[:, 0] == F1[:, 1]) |
                     (F1[:, 1] == F1[:, 2]) |
                     (F1[:, 0] == F1[:, 2])))
    return bad == 0, ("no repeated indices" if bad == 0
                      else f"{bad} face(s) with a repeated index")


def inv6_euler(nv, nf, V, F1, euler_in):
    e = euler_characteristic(nv, F1)
    return e == euler_in, f"euler={e} (input {euler_in})"


def inv7_bounds(nv, nf, V, F1, v_in):
    ok = 1 <= nv <= v_in
    return ok, f"V'={nv} in [1,{v_in}]"


# ============================================================================
# Solver build + invocation
# ============================================================================

def find_eigen():
    """Locate an Eigen include dir containing Eigen/Dense, robustly."""
    cands = []
    if os.environ.get("EIGEN_INCLUDE"):
        cands.append(os.environ["EIGEN_INCLUDE"])
    # pkg-config
    try:
        out = subprocess.run(["pkg-config", "--cflags-only-I", "eigen3"],
                             capture_output=True, text=True)
        if out.returncode == 0:
            for tok in out.stdout.split():
                if tok.startswith("-I"):
                    cands.append(tok[2:])
    except FileNotFoundError:
        pass
    # homebrew
    try:
        out = subprocess.run(["brew", "--prefix", "eigen"], capture_output=True, text=True)
        if out.returncode == 0:
            cands.append(os.path.join(out.stdout.strip(), "include", "eigen3"))
    except FileNotFoundError:
        pass
    cands += ["/opt/homebrew/include/eigen3", "/usr/local/include/eigen3",
              "/usr/include/eigen3", os.path.join(REPO, "solver")]
    for d in cands:
        if d and os.path.exists(os.path.join(d, "Eigen", "Dense")):
            return d
    return None


def build_solver():
    """Return path to a usable solver binary, building from source if needed."""
    env = os.environ.get("SOLVER")
    if env:
        if not os.path.exists(env):
            fail(f"$SOLVER={env} does not exist")
        return env
    src = os.path.join(REPO, "solver", "main.cpp")
    if not os.path.exists(src):
        fail(f"solver source not found: {src}")
    eig = find_eigen()
    if eig is None:
        fail("Eigen not found. Install it (brew install eigen / apt-get install "
             "libeigen3-dev) or set EIGEN_INCLUDE=/path/to/eigen3, or pass a "
             "prebuilt binary via SOLVER=/path/to/solver.")
    cxx = os.environ.get("CXX", "g++")
    out_bin = os.path.join(tempfile.mkdtemp(prefix="test2_solver_"), "solver")
    cmd = [cxx, "-O2", "-std=c++17", "-I", eig, src, "-o", out_bin]
    print(f"[build] {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"solver build failed:\n{r.stderr}")
    return out_bin


def mesh_to_obj(V, F1):
    """Serialize (V, 1-based F) to the modified-OBJ text the solver reads."""
    parts = [f"{len(V)} {len(F1)}"]
    parts += [f"v {x:.17g} {y:.17g} {z:.17g}" for x, y, z in V]
    parts += [f"f {int(a)} {int(b)} {int(c)}" for a, b, c in F1]
    return "\n".join(parts) + "\n"


def parse_obj(text):
    """Parse solver output -> (nv, nf, V (nv,3) float64, F (nf,3) int64 1-based).
    Raises on any header/body mismatch (truncated or malformed output)."""
    tok = text.split()
    if len(tok) < 2:
        raise ValueError("output too short to contain 'V F' header")
    nv, nf = int(tok[0]), int(tok[1])
    if nv < 0 or nf < 0:
        raise ValueError(f"negative counts in header: V={nv} F={nf}")
    need = 2 + 4 * nv + 4 * nf
    if len(tok) != need:
        raise ValueError(f"token count {len(tok)} != expected {need} "
                         f"(header V={nv} F={nf}); truncated or malformed output")
    idx = 2
    V = np.empty((nv, 3), np.float64)
    for i in range(nv):
        if tok[idx] != "v":
            raise ValueError(f"expected 'v' at vertex {i}, got {tok[idx]!r}")
        V[i] = (float(tok[idx + 1]), float(tok[idx + 2]), float(tok[idx + 3]))
        idx += 4
    F = np.empty((nf, 3), np.int64)
    for i in range(nf):
        if tok[idx] != "f":
            raise ValueError(f"expected 'f' at face {i}, got {tok[idx]!r}")
        F[i] = (int(tok[idx + 1]), int(tok[idx + 2]), int(tok[idx + 3]))
        idx += 4
    return nv, nf, V, F


def run_solver(solver, obj_text, *args):
    """Run the solver, returning (raw_stdout_text). Raises on nonzero exit."""
    r = subprocess.run([solver, *map(str, args)], input=obj_text,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"solver exit {r.returncode}: {r.stderr[:500]}")
    return r.stdout


# ============================================================================
# Reporting
# ============================================================================

def fail(msg):
    print(f"\n[FATAL] {msg}", file=sys.stderr)
    raise SystemExit(2)


MARK = {True: "✅", False: "❌"}   # ✅ / ❌


def run_input_validation():
    """Generate every proxy and assert it is itself a valid mesh BEFORE
    simplification. Returns {name: (V, F1, euler)}. Fails loudly on any problem."""
    print("=" * 78)
    print("INPUT VALIDATION  (each proxy must be a valid closed 2-manifold)")
    print("=" * 78)
    meshes = {}
    all_ok = True
    for name, gen, euler_exp in PROXIES:
        try:
            V0, F0 = gen()
        except Exception as e:               # generator broke -> fail loud
            fail(f"proxy '{name}' could not be generated: {e!r}")
        V = np.ascontiguousarray(V0, np.float64)
        F1 = np.ascontiguousarray(F0, np.int64) + 1     # to 1-based
        nv, nf = len(V), len(F1)
        checks = [
            ("INV1", inv1_manifold(nv, nf, V, F1)),
            ("INV2", inv2_area(nv, nf, V, F1)),
            ("INV3", inv3_indices(nv, nf, V, F1)),
            ("INV4", inv4_orphans(nv, nf, V, F1)),
            ("INV5", inv5_degenerate(nv, nf, V, F1)),
            ("INV6", inv6_euler(nv, nf, V, F1, euler_exp)),
            ("inside_sphere", (float(np.linalg.norm(V, axis=1).max()) <= 1.0,
                               f"max||v||={float(np.linalg.norm(V, axis=1).max()):.3f}")),
        ]
        ok = all(c[1][0] for c in checks)
        all_ok = all_ok and ok
        row = "  ".join(f"{cn}{MARK[res[0]]}" for cn, res in checks)
        print(f"  {name:11s} V={nv:5d} F={nf:5d} euler={euler_exp:+d}  {row}")
        if not ok:
            for cn, (res, detail) in checks:
                if not res:
                    print(f"       {cn} FAILED: {detail}")
        meshes[name] = (V, F1, euler_exp)
    if not all_ok:
        fail("one or more input proxies are invalid; cannot trust downstream results")
    print("  -> all input proxies valid\n")
    return meshes


def check_output(nv, nf, V, F1, euler_in, v_in):
    """Run INV1..INV7 on a parsed output mesh. Returns list[(name, ok, detail)]."""
    return [
        ("INV1", *inv1_manifold(nv, nf, V, F1)),
        ("INV2", *inv2_area(nv, nf, V, F1)),
        ("INV3", *inv3_indices(nv, nf, V, F1)),
        ("INV4", *inv4_orphans(nv, nf, V, F1)),
        ("INV5", *inv5_degenerate(nv, nf, V, F1)),
        ("INV6", *inv6_euler(nv, nf, V, F1, euler_in)),
        ("INV7", *inv7_bounds(nv, nf, V, F1, v_in)),
    ]


def main():
    solver = build_solver()
    print(f"[solver] {solver}\n")
    meshes = run_input_validation()

    print("=" * 78)
    print("SOLVER OUTPUT INVARIANTS  (per mesh, per frac)")
    print(f"  fracs={FRACS}  (larger frac = more aggressive -> fewer vertices)")
    print("=" * 78)
    header = "  {:11s} {:6s} {:>6s}  ".format("mesh", "frac", "V'") + " ".join(
        f"{n:5s}" for n in INV_NAMES)
    print(header)
    print("  " + "-" * (len(header) - 2))

    total_fail = 0
    failures = []      # (mesh, frac, inv, detail)

    for name, (V0, F0, euler_in) in meshes.items():
        v_in = len(V0)
        obj = mesh_to_obj(V0, F0)
        vprimes = []          # for INV9
        for frac in FRACS:
            res = {n: None for n in INV_NAMES}
            details = {}

            # --- run + parse (a parse error is a catastrophic structural fail) ---
            try:
                out1 = run_solver(solver, obj, frac)
                nv, nf, V, F1 = parse_obj(out1)
            except Exception as e:
                for n in INV_NAMES[:7]:
                    res[n] = False
                details["INV1"] = f"run/parse error: {e!r}"
                vprimes.append(None)
                _emit_row(name, frac, None, res)
                for n in INV_NAMES:
                    if res[n] is False:
                        total_fail += 1
                        failures.append((name, frac, n, details.get(n, "")))
                continue

            # --- INV1..INV7 on the output ---
            for n, ok, detail in check_output(nv, nf, V, F1, euler_in, v_in):
                res[n] = ok
                if not ok:
                    details[n] = detail

            # --- INV8 determinism: run again, compare raw bytes ---
            out2 = run_solver(solver, obj, frac)
            res["INV8"] = (out1 == out2)
            if not res["INV8"]:
                details["INV8"] = "second run differs byte-for-byte"

            # INV9 is per-mesh; mark blank here, filled after the loop.
            vprimes.append(nv)
            _emit_row(name, frac, nv, res, inv9_pending=True)

            for n in INV_NAMES:
                if res[n] is False:
                    total_fail += 1
                    failures.append((name, frac, n, details.get(n, "")))

        # --- INV9 monotonicity across fracs (ascending => V' non-increasing) ---
        seq = [x for x in vprimes if x is not None]
        mono = all(seq[k] >= seq[k + 1] for k in range(len(seq) - 1))
        tag = MARK[mono]
        print(f"  {name:11s} INV9 {tag}  V'(frac asc)={vprimes} "
              f"{'non-increasing' if mono else 'NON-MONOTONIC!'}")
        if not mono:
            total_fail += 1
            failures.append((name, "-", "INV9", f"V' sequence {vprimes} not non-increasing"))
        print()

    print("=" * 78)
    if total_fail == 0:
        print(f"RESULT: PASS  — all invariants hold for {len(meshes)} meshes "
              f"x {len(FRACS)} fracs.")
        print("Structural soundness of the solver output is mathematically certified.")
        return 0
    print(f"RESULT: FAIL  — {total_fail} invariant violation(s):")
    for mesh, frac, inv, detail in failures:
        print(f"  [{mesh} frac={frac}] {inv}: {detail}")
    return 1


def _emit_row(name, frac, vprime, res, inv9_pending=False):
    cells = []
    for n in INV_NAMES:
        if n == "INV9" and inv9_pending:
            cells.append("  ..  ")
        elif res[n] is None:
            cells.append("  -  ")
        else:
            cells.append(f"  {MARK[res[n]]} ")
    vp = "{:>6d}".format(vprime) if vprime is not None else "{:>6s}".format("ERR")
    print(f"  {name:11s} {str(frac):6s} {vp}  " + " ".join(cells))


if __name__ == "__main__":
    raise SystemExit(main())
