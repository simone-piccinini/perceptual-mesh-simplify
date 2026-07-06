# D4 compile OOM — `cc1plus` killed on the judge

**Verdict (2026-07-05):** the D4 submission failed to **compile** on the judge:

```
g++-14: fatal error: Killed signal terminated program cc1plus
compilation terminated.
Compilation memory limit exceeded
```

A compile failure means the submission never runs — no per-case verdict, no score.
So the question was: did D4 cause it, and can it be fixed?

## Measurement — D4 is (almost certainly) NOT the cause

Compiled control (pre-D4) vs D4 with a real GCC (`g++-15 -O2`, the memory-hungry
family the judge uses; this Mac has no `g++-14` and only 8 GiB), peak resident set:

| build | lines | peak RSS (g++-15 -O2) |
|---|---|---|
| control (pre-D4, last-good 90.27 solver) | 1820 | **0.66 GB** |
| D4 (original `pq_accumulate`) | 1915 | **0.74 GB** (+80 MB) |
| D4 (slimmed `pq_accumulate`) | 1922 | **0.66 GB** (delta gone) |

(clang agrees on the shape: control 0.44 GB → D4 0.52 GB.)

**D4 added only ~80 MB, and 0.74 GB is nowhere near a multi-GB OOM.** The entire
+80 MB came from a single deep Eigen expression tree in `pq_accumulate`
(`s2*(k*I − vv^T − vv^T − vv^T)`); breaking it into small per-statement ops brought
the file back to the exact control footprint.

## Diagnosis — the judge's compile environment changed

Two facts point away from D4:
1. The error names **`g++-14`**, but `JUDGE-ENVELOPE.md` §3 records the judge compiler
   as **GCC 11.5** (measured, covert probe 19889788). A jump 11.5 → 14 is a judge-side
   change, and newer GCC + the provided Eigen 5.0.0 + the judge's own flags can use
   materially more memory than our local `g++-15 -O2`.
2. D4's own contribution is 80 MB on a 660 MB baseline — it cannot manufacture a
   multi-GB overflow by itself.

If the judge did change/tighten its compile toolchain, then the **pre-D4 90.27 solver
would fail to compile too** — this is a project-wide risk, not a D4 bug.

## The one test that decides everything

**Resubmit the banked pre-D4 solver** (`submissions/<best>/main.cpp`, the 90.27 build):

- **It compiles** → the judge is fine; the failure was D4's +80 MB tipping a razor-edge
  limit. The **slimmed** `pq_accumulate` (now at control footprint) removes that risk →
  the case-5 family test is viable again.
- **It also OOMs** → the judge's compiler/limit changed. D4 is a red herring; the real
  task is reducing the whole 1900-line single-TU Eigen compile footprint (options below),
  and `JUDGE-ENVELOPE.md` §3 must be updated (compiler = g++-14).

## Fix applied (D4 branch)

`pq_accumulate` rewritten to avoid the one large Eigen expression tree — same math,
built with small per-statement ops. Result: **D4 compile memory == control** (0.66 GB),
off-band cases byte-identical (verified: cow). Caveat: the rewrite changes the
floating-point *order* on the case-5 (PQ-active) path, so the +0.0009 armadillo screen
must be re-confirmed on the slimmed binary (re-run in flight).

## If it turns out to be judge-wide (whole file over the limit)

Levers to cut single-TU GCC compile memory, cheapest first (none change the algorithm):
- Per-function `__attribute__((optimize("O1")))` on the heaviest Eigen sites (placement
  candidate search, aniso `SelfAdjointEigenSolver`, PQ) — cuts optimizer memory where it
  is spent; these run outside the hot loop so runtime is unaffected.
- Replace remaining large Eigen *expressions* with explicit small-statement forms
  (as done for `pq_accumulate`) — cuts front-end template instantiation.
- If still over: precompute/hand-roll the 3×3/4×4 solves that pull in the heaviest Eigen
  headers (`LDLT`, `SelfAdjointEigenSolver`), or gate rarely-used solvers behind the paths
  that need them.

## The test ran — and it decided (2026-07-06)

The banked pre-D4 90.27 solver (`submissions/v108-c4-4990-90266754/main.cpp`) was
resubmitted: **it compiled and scored 90.266754**. So the judge's toolchain is fine —
the OOM is D4's delta tipping a razor-edge limit, not a judge-wide regression. Good news
for the project; bad news for the *slimmed* D4, because:

The slimmed D4 (per-statement `pq_accumulate`, but still `vector<Eigen::Matrix3d>` storage
and Matrix3d arithmetic on the collapse/eval paths) was **also resubmitted — and still
OOM'd** on g++-14. Local `g++-15` couldn't reproduce it (the delta looked "gone" at 0.66 GB),
which is exactly the trap: **g++-14 amplifies Eigen expression-template instantiation far
more than g++-15**, so a local footprint match is not a judge-side guarantee. The remaining
`Matrix3d` operators (`s*s.transpose()`, `ldlt()`, the `vector<Matrix3d>` accumulation) were
still pulling new template instantiations that g++-14 blows up on.

## Fix #2 — make D4 add ZERO new Eigen instantiations

Rather than chase footprint, the rewrite removes the *cause*: D4 now instantiates **no Eigen
template that v108 doesn't already use.**

- Storage: `vector<Eigen::Matrix3d> Apq; vector<Vec3> bpq; vector<double> cpq;`
  → `vector<double> pqA` (6 per vertex: a00 a01 a02 a11 a12 a22) + `vector<double> pqB`
  (3 per vertex). Dropped dead `cpq`.
- `pq_accumulate`: builds A's six entries and b's three entries as **plain `double`s**,
  entrywise, using only `Vec3` cross/dot (which v108 already instantiates). No `Matrix3d`
  ever constructed in the accumulate path.
- Collapse: adds the flat `double` arrays elementwise (6+3 adds) — no Matrix3d `operator+`.
- Solve site (once per candidate, off the hot storage path): reconstruct a local
  `Eigen::Matrix3d` from the flat entries and reuse v108's **existing** `ldlt().solve()`.
  That `LDLT<Matrix3d>` instantiation already lives in v108, so it costs nothing new.

Verification (this Mac, g++-15 -O2, and end-to-end):

| build | peak RSS (g++-15 -O2) |
|---|---|
| v108 (banked, compiles+scores on judge) | 0.684 GB |
| D4 Eigen-free (this fix) | **0.666 GB — below v108** |

- Entrywise A,b vs the reference Matrix3d formula, 500 random triangles:
  `max|ΔA|=1.4e-14, max|Δb|=7.1e-15` → exact transcription.
- Off-band (cases 2/3/4/6/7) byte-identical to v108 (cow/bunny/fandisk IDENTICAL).
- Case-5 screen reproduced exactly: σ=0.25 → SSIM 0.9276 vs control 0.9267 = **+0.0009**, valid.

D4 now compiles at-or-below the banked build that the judge already accepts, using only its
templates — so if v108 compiles on g++-14, D4 must too. Awaiting the judge resubmit to close.

## Takeaway

The file was already near the ceiling; a single fat Eigen expression is worth ~80 MB of
`cc1plus` memory — but the deeper lesson is that **local `g++-15` footprint parity does NOT
predict `g++-14`**: expression-template instantiation is the axis that diverges. The robust
fix for a compile-limited single-TU Eigen file is not "use less memory" but "**add no new
template instantiations**" — keep new math in plain scalars and reuse the solver types the
banked build already pays for. And **treat a compile verdict as a toolchain probe**: the
decisive read was whether the banked build still compiled (it did).
