# STEP 1 gate — meshoptimizer as decimation engine: NO-GO (direct use)

meshoptimizer v1.1, `meshopt_simplify` with `meshopt_SimplifyErrorAbsolute`,
error-bounded (`target_index_count = 0`). Evaluated on the real watertight bench.

## The gate

| sub-gate | verdict | evidence |
|---|---|---|
| (b) **scale** | ✅ PASS | 1.05M-vertex torus → **0.70 s, 411 MB** (limits 21 s / 2048 MB) |
| (c) **compression vs Hausdorff** | ✅ PASS *where watertight* | reaches 90%+ well under the 5% Hausdorff (fandisk 96.5% @ 7.3% of budget; bunny 82% @ 14%) |
| (a) **watertight 2-manifold** | ❌ **FAIL on organic meshes** | see below |

## The watertight failure (the #1 risk, realized)

All four input meshes are **clean** watertight 2-manifold (border=0, nonman=0).
meshopt output, edges shared by ≠2 faces:

| mesh | terr | compr | manifold? | non-manifold edges |
|---|---|---|---|---|
| bunny | 0.005 | 57% | ✅ | 0 |
| bunny | 0.01 | 82% | ✅ | 0 |
| bunny | **0.02** | 92% | ❌ | **1** |
| bunny | 0.04 | 97% | ✅ | 0 |
| bunny | **0.08** | 99% | ❌ | **2** |
| **cow** | **0.005** | **64%** | ❌ | **1** |
| cow | 0.01 | 83% | ❌ | 1 |
| cow | 0.02 | 93% | ❌ | 7 |
| cow | 0.04 | 97% | ❌ | 5 |
| fandisk | all | 96–99% | ✅ | 0 |
| torus 1.05M | 0.01 | 99.97% | ✅ | 0 |

- **cow is non-manifold at every level tested, including 64% compression.**
- **bunny is inconsistent** — watertight at some error levels, non-manifold at
  others. There is no monotone "safe" threshold.
- CAD/regular meshes (fandisk, torus) stay watertight.

## Root cause (pinned)

meshopt does **not enforce the link condition** on edge collapses. Collapsing an
edge whose endpoints share neighbours beyond the two edge-adjacent triangles
creates an edge incident to >2 faces (a fold/fin). Our hand-written QEM solver
*rejects* exactly these collapses (`SafeToCollapse` link gate) — that is its
manifold guarantee. meshopt trades that safety for LOD speed/quality. v1.1 flags
(`LockBorder/Sparse/ErrorAbsolute/Prune/Regularize/Permissive`) include **no
manifold-preserving option**; `Permissive` makes it worse, `LockBorder` is moot
(closed meshes have no border).

## Verdict

**NO-GO for using meshopt output directly as the submission.** On the judge's
hidden organic meshes (cases 3–6 are detailed surfaces, like cow/bunny) the
output would very likely be non-manifold → **Wrong Answer**. meshopt is fast and
geometrically excellent, but its output is not a closed 2-manifold.

**Do not submit a meshopt output** as the "conservative" baseline — it would burn
a submission on a Wrong Answer. The manifold-guaranteed conservative output stays
the current v1 solver (`solver/main.cpp`, keep-ratio, 7/7 @ 64%).

## Options (user's call before STEP 2)

- **A — meshopt + manifold repair.** Keep meshopt as the engine, add a repair
  pass that removes the few non-manifold edges and re-closes the surface within
  Hausdorff. Pro: meshopt's speed + adaptive quality. Con: robust non-manifold
  repair that stays watertight + non-degenerate + under 5% Hausdorff is real work
  and **unverified on the judge**; the repair could fail on harder hidden meshes.
- **B — enhance the manifold-guaranteed hand solver.** Add error-bounded stopping
  + normal-aware ordering to the current QEM (which guarantees manifold by the
  link condition). Pro: manifold for free, full control. Con: this is the family
  that regressed once (16/2-7) — must be done carefully and verified on the judge.
- **C — hybrid.** Use meshopt's error ordering but the link-condition-gated
  collapse. Largest effort.

Recommendation: **A first** (meshopt's quality is worth a repair attempt, and the
repair is small — 1–7 edges), with **B as the safe fallback** if repair proves
unreliable on the bench. Either way: verify on the judge before trusting it.
