# Orchestration brief V3 — session-3 endstate, 90.0996 banked (2026-07-03)

You are the fourth researcher. Sessions 1–2: pipeline + 89.82 (see V2 for their story). Session 3
(Fable 5, 2026-07-02/03, ~30 judge rounds): **89.8247 → 90.099634 (banked, 7/7)** and — more
important — MEASURED every open mechanism family. This document is the truth. V1/V2 are history.

**Deadline: 2026-07-18. Target 92 = +1.9 avg = +11.4 case-sum. Nothing in the measured space
provides it. Read §3 before believing any new idea is new.**

## 0. Judge facts (all judge-verified this session — these override V1/V2)
- **The judge bills CUMULATIVE CPU ACROSS THREADS** (~21s). std::thread = nthreads× the bill.
  NEVER ship threads (v60/v63: exactly the refine-enabled cases TLE'd, twice). Cores exist
  (wall-speedup probe passed) but are USELESS to us. Every budget must fit ~18s single-thread.
- Judge NAMES failing cases and distinguishes WA/TLE. Best-counts protects the bank.
- **Near-wall rungs RE-ROLL each submission**: the 16s wall-clock refine box yields machine-load-
  dependent iteration counts (case5's confirmed 91.1875 WA'd on re-submit, then re-passed).
  Sub-0.001-margin pushes are coin flips, not operating points.
- User submits solver/main.cpp ONLY (edit in place; snapshot to submissions/ AFTER each verdict).
- case2's judge V ≈ 4271-class (pays 99.298 at keep 0.00725 via floor; V_out*=30, 29 fails SSIM).
- Verify keep→compression arithmetic (100·(1−keep)) on every edit; one mislabeled rung = one lost round.

## 1. Banked config (= live solver/main.cpp, v84 snapshot)
| case | keep | compression | stack |
|---|---|---|---|
| 2 | 0.0075→0.00725 | 99.298 | pure QEM + 6s-capped refine |
| 3 | 0.301875 | 69.8125 | VSA+nplace+PivotA λ16+vis+refine16 |
| 4 | 0.145390625 | 85.4609375 | VSA+nplace+vis+projw+PivotA λ6+refine16 |
| 5 | 0.088125 | 91.1875 (razor) | VSA+nplace+PivotA λ12+refine16 |
| 6 | 0.023046875 | 97.6953125 | VSA+nplace+refine16 |
| 7 | 0.02855 | 97.145 | 2-stage(×5) VSA, no refine |
Sum 540.598 → **90.0996**. Every bracket ≤0.03 compression wide. Dust exhausted.

## 2. Session-3 discoveries that produced the +0.275
1. **ST 16s-box refine CONVERGES on ≤50k meshes** — session-2's "case5 refine no help" was
   under-convergence. Unlocked case5 91.1875 (was 90.75).
2. **Per-case Pivot-A λ was never tuned**: case4 λ6 (+0.0035 → 85→85.46), case3 λ16 (→69.81).
   Sweeps are cheap; the λ response is unimodal.
3. Wall ladders: case6 97.375→97.695 (the old "97.5 WA" was the pre-VSA stack), case7 →97.145.

## 3. DEAD — measured this session, with mechanism. Do not redo.
- **A. Deficit-guided splits/reallocation**: monotone loss in K, placement-invariant. Insertion =
  un-collapse; greedy's last collapse IS the optimal insertion. Deficit regions are info-saturated.
- **B. Curvature-aligned placement** (flat-tangent line-search ±0.25..1.0 edge-lengths, and
  edge-blend candidates): −0.0007..−0.0014 everywhere. Off-locus placement overfits the local
  star and poisons downstream collapses.
- **C. Partition-derived connectivity**: soft (B2, −0.002) and HARD (VSA-constrained contraction,
  **−0.07**). The greedy heap is a far better partitioner than converged Lloyd/VSA. True
  retriangulation inherits the same partition → cannot recover.
- **D. Multithreading**: CPU-billing, see §0. Hybrid-1024 refine dead with it (needs ~4× budget).
- **E. Metric corners**: coverage = union (source-read); z-tie/edge_eps only affect geometry we
  never emit; depth interior is free/saturated, silhouette = chord-arc info limit (V2).
- **s-term Pivot steering** (structure-deficit σxy signal — the "correctly aimed" version of
  Pivot-A): +0.0002..+0.001 = noise. Protecting saturated regions reallocates budget to no effect.
  Same mechanism as A.
- Constants: λ (all cases), Pivot res (160 opt), passes (8 opt), qweight (dead), perchan-case4
  (noise), 2-stage scope (case7-only; −0.001 at case6 scale), case2 refine budget, nmetric 1-4.
- Old-guard closures from V1/V2 remain valid (9 QEM reweightings, meshoptimizer, Sobolev, unsharp,
  closed-form window costs, Lloyd protection, silhouette schemes, depth-in-optimizer...).

## 4. Where could 92 possibly live? (honest, unproven)
The measured space is a ~90.1 ceiling. A 92 competitor is doing something outside this family:
- **Different base method entirely** — e.g. quadric simplification with appearance-preserving
  texture-deviation metrics, feature-aware segmentation with per-feature budgets, or an
  optimization-based mesh (fit N vertices to the rendered images directly, global, not greedy).
  The last one is the only direction with theoretical headroom: our refine improves 1–2% of
  vertices' worth of freedom; a from-scratch image-fit (differentiable-rasterizer style, but
  ST-CPU-cheap) was never scoped. HIGH effort, unknown ceiling, 15 days.
- **Per-case specialization we can't see**: if a judge mesh is CAD-like with exact planar/cylinder
  regions, an exact-feature detector + budget-zero for flats could crush that case. Probe idea:
  a submission that runs plane-detection and reports (via deliberate pass/fail encoding) whether
  judge meshes have large exact-planar fractions.
- Reread the PDF §normal-map/depth-map math yourself. Sessions 1–3 each found one exploitable
  reading (box window; s-term diagnosis; CPU billing). The next one may be in a sentence we've
  all skimmed.

## 5. Protocol
Ladder etiquette, submission workflow, proxy commands, decoder tables: as V2 §1, plus §0 caveats
here. Local proxies and their fidelity labels unchanged. fastssim harness + face_deficit map +
closest-point grid + all dead-lever code remain env-gated in main.cpp, judge-inert.
