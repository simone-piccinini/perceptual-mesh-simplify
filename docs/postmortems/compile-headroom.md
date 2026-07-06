# Compile headroom — the solver was at the judge's cc1plus ceiling

**Result (2026-07-06):** reclaimed **107 MB** of judge compile memory
(736 → 629 MB on Linux g++-14) with **zero change to judged output** (byte-identical on
every proxy), by compiling out a dead env-gated Eigen-sparse path. This moves the
submission clear of the razor-thin compile-memory limit it was sitting on.

## Why this matters

The D4 saga (see [d4-compile-oom.md](d4-compile-oom.md)) ended with a hard fact: the banked
90.27 solver compiles on the judge's g++-14 at **~738 MB**, and the judge's
compile-memory limit sits **right at that footprint** — any addition (D4's +2 MB, or any
future feature) risks `cc1plus` being killed. The solver had no headroom. Before adding
*anything*, we needed to create some.

## How the cost was actually located (stop guessing)

Every earlier compile-memory claim was measured on local **g++-15**, which has gigabytes of
headroom and a different template-memory profile — it never predicted the judge. This time
the profiling was done on the judge's real compiler family, sampling the **`cc1plus` child**
peak RSS directly (the process the judge kills):

- Homebrew **`g++-14`** (14.4.0) locally, and
- a Linux **`gcc:14`** (GCC 14.4.0) Docker container + Eigen 5.0.1 (the judge's OS/compiler).

Linux g++-14, single 1820-line TU:

| config | peak cc1plus | vs `-O2` |
|---|---|---|
| baseline `-O2` | 740 MB | — |
| baseline `-O1` | 701 MB | −39 |
| baseline `-O0` | 705 MB | −35 |
| **no-sparse `-O2`** | **631 MB** | **−109** |

Two findings drove everything:

1. **The memory is front-end template instantiation, not the optimizer.** `-O1`/`-O0` save
   only ~40 MB. So per-function `optimize` pragmas are nearly useless here *and* would break
   the banked cases' byte-identity — ruled out. The lever is **reducing template
   instantiations**, not lowering optimization.
2. **One dead path dominated.** Eigen's sparse Cholesky
   `SimplicialLDLT<SparseMatrix<double>>` (plus the `Eigen/Sparse` module include,
   `SparseMatrix`, `Triplet`, `MatrixXd`) costs **~109 MB just to instantiate** — and it is
   **dead on the judge**: it lives in `refine_positions()` behind `use_lapl = g_lapl > 0`,
   and `g_lapl` is set **only** by `getenv("G_LAPL")`. The judge passes no env, so it never
   runs. (Local macOS g++-14 hid this as a 21 MB delta — yet another reason macOS was the
   wrong yardstick; Linux is the judge.)

## The fix

The Sobolev/Laplacian gradient preconditioner (the sparse path) is wrapped in
`#ifdef IMC_ENABLE_SOBOLEV`, **undefined by default**:

- the `#include "Eigen/Sparse"`,
- the `SimplicialLDLT` declaration + Laplacian build/factor block in `refine_positions()`,
- the `ldlt.solve()` gradient-preconditioning block inside the ascent loop.

When the macro is undefined (the judge build), `use_lapl` is a plain `false` and none of the
sparse types are named, so the preprocessor strips them before instantiation — reclaiming the
107 MB. The research code is **preserved in-source** and re-enablable with
`-DIMC_ENABLE_SOBOLEV` (it was env-gated experimental preconditioning; never part of a judged
run).

## Verification

- **Byte-identical to v108** on cow / bunny / fandisk / armadillo, default build (the change
  is a provable no-op on every judged path — the guarded code never executed without
  `G_LAPL`).
- Compiles **both** ways (macro off = 629 MB; macro on = 738 MB, sparse restored).
- Real Linux g++-14: **736 → 629 MB (−107)**.

## The general principle

On a compile-memory-limited **single-TU (Kattis-style)** Eigen solver:

1. **Profile on the judge's actual compiler.** g++-15 peak-RSS with local headroom is not a
   predictor of a g++-14 hard limit. Docker `gcc:14` / Homebrew `gcc@14` reproduce it in
   minutes; sample the `cc1plus` child, not the `g++` driver.
2. **The cost is template instantiation (front-end), so cut instantiations, not
   optimization.** Optimization pragmas barely move it and break byte-identity.
3. **Dead env-gated Eigen-heavy code is free headroom.** Anything behind a `getenv` the judge
   never sets is compiled but never run — `#ifdef` it out (verify byte-identity) and reclaim
   its instantiation cost. The sparse Cholesky was 107 MB of exactly this.

This unblocks future features (including D4's +2 MB, if its marginal value ever justifies it):
the submission now compiles at 629 MB instead of 736.
