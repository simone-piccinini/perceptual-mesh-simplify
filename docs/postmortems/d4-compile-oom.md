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

## Takeaway

The file was already near the ceiling; a single fat Eigen expression is worth ~80 MB of
`cc1plus` memory. Keep new Eigen code in small per-statement ops, and **treat a compile
verdict as a toolchain probe** — the decisive read is whether the banked build still
compiles.
