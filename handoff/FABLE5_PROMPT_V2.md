# Orchestration brief V2 — mesh-simplification solver, 89.82 → 92

You are the third researcher on this problem. Session 1 (Sonnet 5) built the pipeline and wrote
`handoff/FABLE5_PROMPT.md` (V1 — still worth skimming for the metric derivations in its §4, but its
backlog is now fully executed; THIS document supersedes it). Session 2 (Fable 5, 2026-07-02) ran 13
judge submissions (v46–v58), closed most of V1's open questions with measurements, and moved the
score 89.49 → **89.8247 (banked, 7/7)**. You are being asked for the thing sessions 1–2 could not
find: **the idea class that gets +13 case-sum points. 92 is confirmed reachable — a competitor has
it — so the ceiling is in our method family, not the problem.** Be creative, be skeptical of our
"closed" labels where you have a genuinely different mechanism, and read the primary sources
yourself. But respect the measurements: don't redo an experiment that failed *for the same
mechanistic reason*.

**Deadline: July 18, 2026. Today is July 2. ~16 days.**

## 0. Current state (all judge-confirmed, per-case)

| case | V range | compression | config | wall status |
|---|---|---|---|---|
| 2 | ≤7k | **99.25** | pure QEM, keep 0.0075 | 99.5 WA'd → bracketed |
| 3 | 7–30k | **69.5** | VSA+nplace+Pivot-A+vis+refine, keep 0.305 | 69.75 WA'd → bracketed |
| 4 | 30–40k | **85.0** | VSA+nplace+vis+projw+refine, keep 0.150 | 85.25 WA'd → bracketed |
| 5 | 40–100k | **90.75** | VSA+nplace+Pivot-A, keep 0.0925 | 90.80 WA'd (with extra stack) → bracketed |
| 6 | 100–400k | **97.375** | VSA+nplace+refine, keep 0.02625 | 97.4375 UNTESTED with current stack |
| 7 | >400k (~1.1M) | **97.05** | 2-stage VSA (bulk-QEM to 5×target, then VSA), keep 0.0295 | 97.10 UNTESTED |
Sum 538.95 → **89.82**. Target 92 → sum 552 → **+13**.

Micro-headroom left in bisection: case6 97.4375, case7 97.10/97.15 → ~+0.15 sum total. Everything
else needs the SSIM-at-fixed-V curve itself to move.

## 1. Ground rules (unchanged from V1, all judge-verified)

- Judge = only oracle. Best-counts (a WA/TLE submission never costs banked score). Submit often.
- **The judge now provably NAMES failing cases and distinguishes WA from TLE** (v48/v50/v55/v56
  verdicts) — V1's §4.5 question is resolved. Multi-case probes are fine when every case's
  zeroed-compression drop is arithmetically distinguishable; always write the decoder table into
  the staged `submissions/vNN-*/RESULT.md` BEFORE submitting.
- User submits manually via Kattis web UI and reports back verdict text.
- Update `handoff/ATTEMPT_LOG.md`, `handoff/SOLVER_STATE.md`, `submissions/vNN-*/` every round.
- Local proxies: regenerate with
  `G_NDECIM=0 G_NOLAMBDA=1 ./solver/main k 0.045 0.5 < tests/data/armadillo_watertight.obj > proxy25k.obj`
  (0.7 → proxy35k; midpoint-subdivide armadillo ×1/×2 → big200k/big800k, script in ATTEMPT_LOG
  session notes). Fidelity: case3 faithful; case4/5 pessimistic-relative-ok; big proxies
  OVER-predict VSA gains (case7 97.2 WA'd despite +0.0034 local margin) — use judge-passing configs
  as anchors and demand bigger local margins on 6/7.
- Judge machine ≈ 1.5–2× slower than local M-series. Wall-clock-box every unbounded loop (the v55
  case7 TLE was `refine_init_orig` running UNBOXED before the 16s refine cap — fixed, but audit any
  new stage you add for the same bug).

## 2. What is now CLOSED with mechanism — do not redo the same mechanism

(Full data in `handoff/ATTEMPT_LOG.md` 2026-07-02 sections; mechanisms matter more than verdicts.)

1. **The normal deficit is ~100% the SSIM *structure* term (σxy correlation).** l≈0.999, c≈0.98,
   s≈0.74–0.82, and σ_simplified ≈ σ_original on all proxied cases. Any lever that only adds/keeps
   *dispersion* (unsharp — tested, picks α=0) or smooths the ascent direction (Sobolev/Laplacian
   preconditioning, Nicolet 2021 — tested λ=8/20/50, monotonically worse) is aimed at the wrong
   term. The deficit is *misplaced* normal texture, an information limit of N-piece flat
   approximation — with the current connectivity-inheriting collapse family.
2. **Closed-form flat-window SSIM collapse cost**: `area·(1−cosθ)` already IS the encoded-space
   squared-difference loss (2·127.5²·(1−cosθ)=Σ_c Δa_c²). The C1-denominator asymmetry over-protects
   encoded-0 normals and tanks +axis views at full AND half strength. Family closed.
3. **Lloyd/VSA partition as collapse protection (V1's B2)**: 6 configs, all ≤ baseline, monotone in
   penalty. The greedy heap already does global marginal-cost equalization on *fresh* geometry; any
   static partition can only distort it. Full retriangulating VSA remains untested (see §4).
4. **Silhouette-depth**: depth deficit is 73% silhouette windows but global scale peaks exactly at
   1.0 → chord sag already optimally balanced. Chord-vs-arc info limit. (Depth l/c/s ≈
   0.997/0.994/0.988 — nearly saturated anyway.)
5. **Silhouette protection for normals (M3)**: interior windows carry ~90% of the normal deficit.
6. **SSIM window = box**, established from judge data (Gaussian would read −0.047 at case3's
   passing point). ω_N=ω_D=0.5 fixed by the PDF. Don't recalibrate either.
7. Visibility culling >40k verts (512-res vis mis-hides sub-pixel faces, −0.058) and Pivot-A on
   case6 (+0.001, noise) — measured, not worth it.
8. All V1 §5.1 dead levers (9 QEM reweightings, meshoptimizer, probabilistic quadrics, edge flips
   scored by SSIM, multi-res optimizer...).

## 3. Assets you inherit (all in `solver/main.cpp`, env-gated, judge-safe)

- 2-stage decimation (`g_2stage`/`G_2STAGE`): bulk-QEM to k×target then VSA. 800k: 8.0s→3.9s at
  equal-or-BETTER quality (×5 beat full VSA). **Use it to buy time budget anywhere.**
- Inverse-rendering refine (`refine_for`/`G_REFINE`): analytic normal-SSIM ascent, bit-exact vs
  oracle, monotonic, 16s wall-boxed. Now on case3/4/6. Worth +0.005 on case6-size.
- Lloyd partition (`G_LLOYD*`), Sobolev preconditioner (`G_LAPL`), unsharp (`G_SHARP`),
  closed-form costs (`G_NMETRIC=3/4`), projected-area weighting (`G_PROJW`), Pivot-A override
  (`G_LAMBDA`) — all built, tested, dormant. Reusable as building blocks.
- Diagnostics: `scripts/deficit_split.py` (sil/int), l·c·s decomposition + fast-SSIM harness
  (inline scripts in ATTEMPT_LOG session notes; fastssim.py pattern: cache original renders, score
  many candidates).
- `Eigen/Dense` AND `Eigen/Sparse` compile on the judge (judge-proven).

## 4. Where I think the +13 must live — ranked, with honest odds

**A. Connectivity redistribution: edge SPLITS + collapses (never tested — my top pick).**
The whole pipeline only ever *removes* vertices from the inherited connectivity; refine only
*moves* them. Nobody has ever ADDED a vertex where the rendered SSIM deficit is largest, paid for
by a collapse elsewhere. Edge split is manifold-safe by construction (no link condition needed).
Loop: decimate below target → render true deficit map (Pivot-A machinery already computes it) →
split the K worst-deficit edges (midpoint + local refine) → collapse K cheapest elsewhere → repeat
within a wall-clock box. This directly attacks the structure term by *reallocating resolution*,
which is the one degree of freedom the current family never exercises. If the +13 exists inside
"triangle mesh, 21s", adaptive reallocation is the most plausible carrier. Validate on case3
(faithful proxy) at keep 0.305 vs the 0.8992 anchor.

**B. Anisotropic decimation.** Approximation theory: normal-field L2 error of an N-face isotropic
mesh scales O(N⁻¹); curvature-aligned anisotropic scales O(N⁻²) on smooth anisotropic regions.
Our collapses place vertices by QEM/nplace but nothing *rewards* long-thin-along-flat-direction
triangles. Cheap first probe: relax/remove the normal-flip gate `kFlipTau` and area gate for
collapses whose VSA cost is tiny; or add a curvature-tensor term steering placement along the
minimum-curvature eigenvector. Case4 (CAD-like, responded +1.05 to normal-ordering) and case6/7
are where anisotropy should bite. Risk: sliver triangles → volatile normals (the meshoptimizer
failure mode) — the difference here is slivers ALIGNED with the flat direction are safe; test,
don't assume.

**C. True retriangulating VSA / full remesh for ONE case.** B2's protection-signal form failed, but
the full "proxies → polygon → retriangulate" pipeline (with `orient_polygon_soup`-style repair) was
never attempted because of manifoldness risk. With 16 days and best-counts, a scoped attempt on
case3 or case6 is a legitimate big swing. The old "remesh ceiling ~88.5–89" analysis
(`docs/remesh-go-no-go.md`) predates VSA-lite, refine, and the structure-term diagnosis — treat it
as stale. This is high-effort/high-variance: only start it early, never in the last 5 days.

**D. Multithreading (V1's I1).** `std::thread::hardware_concurrency()`, degrade to 1. The 6-view
render/SSIM/gradient is embarrassingly parallel. Unlocks: refine at 1024 (judge-exact; the "1024
worse" result was explicitly under-convergence), refine on case5/7 (case5's optimizer WA history
was at pushed keeps with 512-res — a converged-1024 version is a different experiment), deeper
Pivot-A everywhere, and TLE margin for A/B/C above. Not +13 by itself; multiplies everything else.

**E. Fresh metric exploits.** You have `src/imc_eval/` — sit with `ssim.py`+`render.py` like
session 2 sat with the closed-form window loss. Unexplored corners: the foreground-union coverage
rule interacting with silhouette-adjacent windows (windows counted only when CENTER pixel is
covered — a mesh whose silhouette is 5px *inside* the original loses those windows from the
average; is that better or worse than matching?); the depth background constant 255 vs near-plane
~1.5 (SSIM on depth is scale-sensitive through C2 — huge dynamic range means interior depth detail
is nearly free); z-tie/edge_eps rasterization edges. Session 2 found one real thing this way
(box window) — there may be another.

**F. Keep-side arithmetic.** Compression is continuous in V_out: keep_for fractions are floor()ed
per mesh; ±1 vertex per case is free score at sixth-decimal granularity. Also: the judge V ranges
are known but the actual judge V values are only inferred — if case boundaries allow, per-case V
detection could sharpen keeps (e.g. if case3's real V is 25k, keep granularity is 1/25000).

## 5. Suggested opening sequence

1. Read `solver/main.cpp` (~1000 lines), `handoff/ATTEMPT_LOG.md`, `handoff/SOLVER_STATE.md`.
   Rebuild, regenerate proxies, reproduce case3 anchor 0.8992@0.305 (validates your setup).
2. Bank the free micro-probes early: case6 0.025938 (97.40625... use 0.0259) + case7 0.029
   (97.10) in one submission (distinct deltas). Expected +0.1–0.15.
3. Start A (splits) immediately — it reuses existing machinery (deficit render, collapse gates,
   refine) and is validatable on the faithful case3 proxy in hours.
4. D (threads) in parallel if bandwidth — it's mechanical and de-risks everything.
5. B/C as the big swing once A's verdict is in. E whenever you're blocked on compute.

Trust the judge over both of us. Submit early, submit often. — Fable 5, session 2
