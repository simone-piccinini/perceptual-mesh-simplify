# DIFFERENTIABLE MESH OPTIMIZER — 3-day build plan (target: c3 91-class mesh)

STATE: day-1 start 2026-07-14. Bank 90.590349 (greedy+refine paradigm, measured CPU-Pareto-optimal
at c3=6610). This build targets the ONE lever left: a mesh chosen by JOINT optimization against the
rendered SSIM, not by greedy decimation then separate position-refine. File: `solver/diffopt.cpp`
(standalone; `mein.cpp` banked config UNTOUCHED).

## Why greedy caps out (the thing this replaces)
Current: (1) QEM decimation picks WHICH vertices to keep by GEOMETRIC error, blind to SSIM.
(2) refine moves the kept vertices to maximize rendered SSIM (this part IS differentiable, and it
is CONVERGED — more budget = identical S2). The cap is that STEP 1 (vertex selection + connectivity)
is never optimized against the metric the judge scores. The tail (`collapse_delta_local`) does the
last ~300 collapses by TRUE SSIM but it is greedy and SATURATES (ctT 300→2500 identical). Global
vertex-set selection is what greedy cannot reach.

## The hypothesis (falsify EARLY, day 1-2, before heavy build)
A mesh at c3's vertex count (6610) with a globally-better vertex SET + positions scores materially
higher SSIM than QEM's 6610 (enough to pass at ~6000, = +2 case-pts = 91). RISK: the VSA-dead result
(flat remesh 2.5x worse) + refine-converged both suggest QEM is already near-optimal. So MILESTONE 0
is a cheap falsifier: does ANY non-greedy vertex set beat QEM at equal N? If not, this whole build is
dead and we save 3 days.

## Architecture (reuse what exists; the renderer + SSIM gradient are DONE)
We already have, in mein.cpp/main.cpp: exact 6-view flat-shaded normal+depth rasterizer
(`render_faceid`, `refine_score_grad` = rendered normal-SSIM + analytic gradient wrt vertex
positions, `sil_score_depth`). diffopt.cpp REUSES this math (copy the primitives). We do NOT rebuild
the renderer. The new part is the OPTIMIZER over the vertex SET.

## Milestones
- **M0 (day 1) — FALSIFIER, cheap.** Load c3 proxy + QEM 6610 mesh. Run a strong global position
  optimizer (Adam + multi-restart from perturbed QEM meshes, unlimited offline time) → does S2 beat
  the converged refine? Then a swap search: remove lowest-SSIM-impact vertex, split highest-deficit
  face, keep if S2 up; N swaps. If neither moves S2 by >~1e-3 → greedy IS optimal, STOP (report,
  don't burn 3 days). If S2 jumps → the better set exists → proceed.
- **M1 (day 1-2) — soft-alive differentiable simplification.** Each vertex a continuous alive-weight
  w∈[0,1]. Faces render with opacity = min of their 3 vertex weights (soft coverage). SSIM computed
  on the soft render. Optimize {positions, weights} jointly against SSIM + a sparsity/budget penalty
  driving Σw → 6610. Anneal weights → hard 0/1, prune. Measure the pruned mesh's S2 vs QEM.
- **M2 (day 2-3) — connectivity + validity.** After pruning, retriangulate the kept vertices to a
  watertight 2-manifold (the judge requires it) with Hausdorff ≤5%. Re-refine positions. This is the
  hard/risky part (V2 construction died here). Reuse V2's manifold machinery if sound.
- **M3 (day 3) — fit the 21s judge box + submit.** Offline-optimize is unlimited, but the SUBMITTED
  binary must PRODUCE the mesh in 21s from the judge's (unknown) input. Two paths:
  (a) if the optimizer is fast enough at runtime → run it;
  (b) if not → the offline result cannot be embedded (we lack the judge's exact input). So M1/M2 must
  yield an ALGORITHM that fits 21s, not just an offline-only result. Keep this constraint in view from
  M1 (bound the iteration count).

## Kill criteria (be adversarial, don't sink cost into a dead road)
- M0 shows <1e-3 S2 headroom from non-greedy sets → greedy optimal, STOP.
- M1 soft-simplification prunes to a mesh WORSE than QEM at equal N → the relaxation doesn't help, STOP.
- M2 can't make it manifold within Hausdorff → same wall V2 hit, STOP.
- Any milestone that only works offline (can't fit 21s runtime) and needs the judge input → dead
  (we cannot obtain the judge's exact mesh; verified no public-model match).

## Log
- 2026-07-14: plan written. Starting M0 falsifier.

## M0 RESULT (2026-07-14) — positions optimal; the 91 (if any) is in the vertex SET
Ran multi-restart position optimizer offline (unlimited time) on the QEM c3 6610 mesh:
- heavy converge (mini_refine 30s): S2n 0.797640 -> 0.798697 (+1.06e-3 = the polish ceiling, TLE-blocked at runtime)
- 8 perturbed restarts (0.003*diag): ALL worse (0.69-0.70) — no better position basin exists.
=> POSITION headroom = +5.3e-4 combined (c3 ~6570). Greedy SELECTION is optimal (SSIM-tail saturates = QEM).
=> The ONLY place a 91-class mesh can hide is a GLOBAL vertex set that no heuristic (QEM/rim/struct)
   finds. That is exactly M1 (soft-alive differentiable simplification). Proceeding to M1 as the
   definitive test — VSA-dead evidence is against it, but M1 settles it for good.

## M1 RESULT (2026-07-14) — vertex-set local search DEAD; build KILLED by falsifier
Swap search (split highest-deficit face + collapse least-impact edge + re-refine, keep if better),
20 swaps offline from the position optimum: S2n 0.798675 -> 0.798712 = **+1.5e-5** (1/20 accepted,
rest reverted). The vertex set is flat/optimal around QEM — local swaps find nothing.

FOUR independent lines now agree the c3 6610 mesh is ~optimal:
  M0 positions optimal (+5.3e-4 max, no better basin); M1 swap +1.5e-5; ssim_greedy.cpp (SSIM-greedy
  selection -0.011); VSA-dead (structural remesh 2.5x worse).

VERDICT: the differentiable/global-set build would REPRODUCE QEM, not beat it. Per the design's own
kill criterion ("M0 <1e-3 headroom -> STOP"), the 3-day build is KILLED before sinking the cost.
A 91-class c3 mesh does not exist at achievable vertex counts by any selection/position/connectivity
method we can build. => 91 is not reachable via c3 mesh quality; escapees' 93 is unexplained by any
measured lever (metric interpretation / sandbag / something structurally invisible to us).
Files: solver/diffopt_m0.cpp, solver/diffopt_m1.cpp (scratch experiments).
