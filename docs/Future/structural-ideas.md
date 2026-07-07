# Structural ideas to lower `V'_min` — the (b) lever

There are only two ways to raise the score: **(a)** bisect each case's wall harder,
and **(b)** invent structural ideas that let a case pass at fewer vertices. Every
point gained since 88.67 came from these two. This document is about **(b)** — new
mechanisms that lower `V'_min` (the smallest vertex count at which a case still
passes `FinalSSIM ≥ 0.9`).

The binding wall everywhere is the **contrast/variance term of the flat-shaded
normal-map SSIM** (depth is ≈free) — see [../theory/wang-ssim.md](../theory/wang-ssim.md).
So every idea below is judged by one question: *does it make the simplified mesh
render a better normal map at fixed face budget, while staying a valid closed
2-manifold within 5% Hausdorff?*

---

## The structural levers we already use (brief)

| # | Lever | Mechanism | Cases | Proven effect |
|---|---|---|---|---|
| 1 | Free-QEM placement | optimal merged position → rounder triangles → better face normals | all | large meshes 95→96–97% |
| 2 | Pivot-A steering | per-channel SSIM contrast deficit → per-vertex cost multiplier, 8 staged passes | 3, 5 | case 5 **79→90** |
| 3 | Visibility culling | camera-unseen edges collapse near-free (`×1e-4`) | 3 | case 3 **66→67** |
| 4 | Inverse-rendering optimizer | post-decimation position ascent on the real normal-SSIM gradient (monotonic, displacement-capped, time-boxed) | 3, 4 | polishes at fixed V′ |

Levers 1 and 4 improve *how well* a face budget renders; levers 2 and 3 improve
*where* the budget is spent. Full walkthrough:
[../theory/perception-aware-solver.md](../theory/perception-aware-solver.md).

## The graveyard (do not re-propose)

New ideas must stay clear of what the judge already killed:

- **All geometric cost reweightings** (area, dihedral, normal-quadric,
  silhouette-lock, image-driven λ12, "correct flat-normal cost") — the
  mean-vs-variance trap; 12 methods pin case 3.
- **Attribute / normal-preserving simplifiers** (GH/Hoppe, meshopt attributes) —
  *worse*: preserving vertex normals costs triangle quality, which hurts the
  flat-normal render.
- **Rejection gates that cap compression** (anti-sliver) — broke cases 5, 6.
- **Vertex clustering / `sloppy`** — worse than our QEM.
- **Adding vertices** (`V' ≤ V`) and **per-collapse full re-render** (TLE).

The graveyard is full of *cost reweightings* and *vertex-normal preservers*. It is
**not** full of better *placement geometry*, *connectivity changes*, or
*silhouette/depth exploits* — that is where the open space is.

---

## New ideas

> **2026-07-06 session outcomes (status of the ideas below):**
> - **D1 (widen displacement cap): LOCALLY INERT.** Sweeping the stock cap via `G_CAPA` ∈
>   {0.02…0.5} moves proxy SSIM ≤ 5e-6; the optimizer converges to <1% Hausdorff, far under
>   the 2% cap — the cap is not the binding constraint. Not worth a submission.
> - **D4 (probabilistic quadrics): SHELVED.** Implemented (Eigen-free, on
>   `feat/d4-probabilistic-quadrics`), +0.0009 local on one case, but 4 judge compile-OOMs and
>   weak-transfer EV. See [../postmortems/d4-compile-oom.md](../postmortems/d4-compile-oom.md).
> - **D5 (edge flips in the loop): SHELVED.** Cheap `flip_tricost` proxy is anti-correlated with
>   rendered SSIM (mean-vs-variance trap; even K=1 loses). Real-SSIM version needs a dirty-region
>   renderer. See [d5-flip-optimizer.md](d5-flip-optimizer.md).
> - **Road B (transfer instrument): FALSIFIED.** Three local screens can't predict judge transfer;
>   structural dev stays measurement-blocked. See [transfer-instrument.md](transfer-instrument.md),
>   [roadb-assessment.md](roadb-assessment.md).
> - **Score levers that DID land:** case-4 razor harvest → v110 **90.276200** (bank); the friend's
>   case-3 harvest (6940) stacks with it (master's merged solver targets ~90.2855). See
>   [c4-harvest-ladder.md](c4-harvest-ladder.md).

### Group 0 — Diagnose first (cheap; tells you where to aim)

**D0. Per-view, per-channel SSIM breakdown at each wall.** Using the local oracle
(trustworthy for *relative* structure, not absolute pass/fail), dump for each case
at its current wall: normal-SSIM and depth-SSIM per view, per channel. Answers the
three questions that direct everything else: (i) is depth actually saturated or is
there 0.01–0.03 of slack? (ii) which views are weakest (silhouette erosion vs
interior contrast)? (iii) which channel (nx/ny/nz) drags? One afternoon; redirects
the rest of the work.

Tool: [`scripts/diagnose_breakdown.py`](../../scripts/diagnose_breakdown.py) (per-channel
accessor `ssim_normal_channels` added to the oracle). Runs on **local proxy meshes**
with a QEM decimator stand-in (no C++ toolchain here) — a hypothesis engine, not a
measurement of the hidden cases; relative structure only.

**D0 — first proxy run (findings).** Proxies matched by character, box window, 384 px:

| mesh @ compr | type | normal `N̄` | depth `D̄` | weakest view (Δ) | channels |
|---|---|---|---|---|---|
| fandisk @83% | mechanical | 0.976 | **0.998** | −Y (0.058) | ~balanced, nx low |
| bunny @67% | organic | 0.773 | 0.980 | +Z (0.088) | balanced (≤0.03) |
| cow @67% | organic | 0.802 | 0.968 | −X (0.044) | balanced |
| bunny @90% | organic | 0.590 | 0.946 | −X (0.094) | balanced |
| cow @90% | organic | 0.587 | **0.905** | −X (0.043) | balanced |

Three redirects fall out (verify on the judge; proxies over-decimate vs our tuned solver):

1. **Depth is saturated ONLY on mechanical.** fandisk depth ≈ 0.998, but organic depth
   is 0.90–0.98 and **drops as compression rises** (cow @90% → 0.905). The repo-wide
   "depth ≈ free" assumption holds for case 4, **not** for cases 3/5. → **promote D3
   (joint depth) and D6 (silhouette coverage) for the organic cases** — recovering
   depth 0.905→0.97 is +0.03 on FinalSSIM, right at the gate, and cheaper than normal.
2. **The normal deficit still dominates** (`N̄` 0.59–0.98 ≫ its depth gap), so **D4
   (placement) / D5 (connectivity) stay primary** for the normal half.
3. **Channels degrade together** (spread ≤ 0.03) → per-channel steering has a *small*
   target, consistent with the earlier "per-channel added nothing." Don't over-invest.
   But **every mesh has a distinctly weak view** (0.04–0.09 below the best), suggesting
   a new lever: **per-view importance** (protect the weakest axial view's faces) — a
   different mechanism from the per-*region* image-driven steering that failed.

### Group 1 — Refine an existing lever (low risk, fast, likely tenths)

**D1. Widen the optimizer's displacement cap.** It is `0.02·diag`, but the
Hausdorff budget is 5% of the diagonal — you are using under half your room for the
one lever that provably improves the metric. Sweep the cap up (0.03, 0.04) on cases
3/4. Monotonic-accept protects you; best-counts makes it a free-roll.

**D2. Better optimizer than vanilla gradient ascent.** Lever 4 is plain gradient
ascent with step-halving. Swap in **momentum/Adam** and/or **coarse-to-fine
rendering** (optimize at 256 then 512): same gradient, more effective steps inside
the 16 s box, and multi-resolution escapes shallow local minima. Cases 3, 4.

**D3. Optimize depth-SSIM jointly, not just normal-SSIM.** The optimizer only
ascends the normal half. If D0 shows depth < ~0.99 on any view, add the depth
channel — its silhouette gradient is smooth and cheap points there are worth as
much as normal points (0.5/0.5 weighting). Conditional on D0.

*Status: JUDGE-TESTED → NULL RESULT (88.67146, net-neutral). See
[../postmortems/d3-depth-optimizer-null-result.md](../postmortems/d3-depth-optimizer-null-result.md).*
It was submitted on the **v38 (88.67) base, not the 90.24 best**, and with `keep`
**unchanged** — so a positions-only optimizer could not change the score by construction.
The optimizer is a validity tool: it pays off **only paired with a lower `keep`**. Prototype in `solver/main.cpp`: the optimizer's
objective is now `g_wn·normal + g_wd·depth` per view (`refine_depth_for`: 0.5/0.5 on
cases 3/5, 0 on case 4 → case 4 bit-identical); the optimizer itself is **extended to
case 5** (`refine_for` ≤ 100k). Depth gradient flows through the vertex camera-depths
only (barycentric/silhouette shifts non-differentiable → covered by the re-render
monotonic accept). Local A/B on armadillo (49,990→4,999, case-5 band, oracle @320):

| run | Final | normal | depth |
|---|---|---|---|
| control (no optimizer) | 0.9255 | 0.8694 | 0.9815 |
| optimizer, normal-only (wd=0) | **0.9297** | 0.8778 | 0.9815 |
| optimizer, blended (wd=0.5) | 0.9292 | 0.8770 | 0.9813 |

Read: **extending the optimizer to case 5 is the real win (+0.004 blended)**; the
depth term itself was neutral on armadillo (its depth was already 0.9815 — unlike the
cow proxy's 0.905, so the depth-slack hypothesis is mesh-dependent). Bunny/sample
regression: byte-identical. Judge probes should isolate: first case 5 only (set case 3's
`refine_depth_for` to 0), sweep `wd` ∈ {0, 0.5} there; the real case-5 mesh's depth
slack — not armadillo's — decides whether the depth term earns its keep.

### Group 2 — New mechanisms, still within greedy-collapse + optimize (medium)

**D4. Probabilistic Quadrics placement (Trettner–Kobbelt 2020).** The strongest
*untried* idea, and Eigen-ready (formulas in [../theory/paper-notes.md](../theory/paper-notes.md)).
Free-QEM's `A` is rank-deficient on flat/coplanar regions, so it *punts to the
midpoint* → slivers → bad face normals exactly where collapses concentrate at high
compression. PQ regularizes `A` to full rank (`+σ²I`), giving a well-defined
**rounder** triangle where free-QEM currently gambles. It is *not* the failed
normal-preserving family — it improves triangle quality, which the project's own
kill-shot says governs appearance. One knob (σ), ~50× cheaper than SVD (safe even
for cases 6/7), a drop-in swap of the placement in `Evaluate`. Candidate across
**all** cases, including the large ones where nothing else has moved.

*Status: SHELVED (2026-07-06).* Implemented + screened (+0.0009 on the armadillo case-5
proxy @σ=0.25, normalized), but it cost four judge submissions to compile-memory OOMs
(the file sat AT the judge's cc1plus limit; see
[../postmortems/d4-compile-oom.md](../postmortems/d4-compile-oom.md)) and the expected
transfer (~+0.004 best case, one case, judge-negative history for this gain class) never
justified the fight. The final Eigen-free implementation lives on
`feat/d4-probabilistic-quadrics` (+2 MB compile cost, entrywise-exact) — with the v109
compile headroom (~110 MB) it is now *compilable* if its EV ever changes; it remains
unjudged.

**D5. Connectivity in the optimizer loop.** Lever 4 freezes topology and only moves
vertices — stuck in the given triangulation's basin. Extend it: between
position-ascent steps allow a few **manifold-safe edge flips** (link condition,
trivially watertight) chosen by their measured effect on rendered SSIM, plus
occasional re-collapses of now-redundant edges. The one move that lets the
post-decimation mesh change its *face pattern* to fit the normal map, short of full
remeshing. Novel; cases 3, 4. Must use the periodic/coarse render (never per-flip)
to stay in budget.

**D6. Silhouette-coverage guarantee for the normal map.** At high compression the
simplified silhouette erodes *inside* the original's footprint; there a window is
object-normal in one image and background gray (127.5) in the other → a large
normal-SSIM hit at the contour. A rule that keeps the simplified footprint ⊇ the
original footprint from all 6 axes stabilizes the foreground-window set. This is
*not* the failed silhouette-*cost* term — it is a coverage constraint on the
boundary. Risk: it is a mild rejection mechanism (could cap compression like
anti-sliver), so isolate to one case and watch. Conditional on D0 showing
contour-driven loss.

### Group 3 — New representation (high effort/risk; the only thing greedy can't do)

**D7. Variational Shape Approximation / crease-aligned remesh, scoped to case 4.**
The one method that can *create new edges aligned to creases* that greedy collapse
can never introduce. Case 4 (mechanical, piecewise-planar + sharp creases) is its
home turf. Honest caveats: the watertight re-triangulation step is where VSA
implementations break manifoldness (the judge's hard gate), it is days of work, and
the go/no-go memo estimated only ~+0.7 mean *if it works* —
[../postmortems/remesh-go-no-go.md](../postmortems/remesh-go-no-go.md). But we have
already blown past that memo's ceiling once, so its pessimism is suspect.
**Prototype the manifold re-triangulation first** — that is the make-or-break risk.

**D8. Hard crease-anchoring (a cheaper cousin of D7 for case 4).** Instead of
remeshing, *forbid* collapse of vertices on high-dihedral (crease) edges, forcing
the kept-set onto the normal discontinuities that dominate the mechanical normal
map. This is an *anchor*, not a cost weight (the weights are dead) — but it is a
rejection gate, so same risk as D6. Cheap, case-4-isolated. If D7 is too heavy, this
captures part of its intuition.

---

## Suggested order of attack

1. **D0 — diagnose.** Aim before firing.
2. **D1 + D4.** Cheapest high-EV: widen the cap, and swap in Probabilistic Quadrics
   placement. Small changes, plausibly help *every* case including 6/7, neither
   risks validity.
3. **D2 / D3.** Optimizer upgrades on cases 3/4, guided by D0.
4. **D5.** Connectivity-in-loop, if D2/D3 show the position-only optimizer saturating.
5. **D6 / D8.** Only if D0 fingers contour/crease loss, isolated to one case.
6. **D7 (VSA).** The big swing, case 4 only; prototype the risky re-triangulation first.

### Confidence for *lowering `V'_min`*

- **D4 (probabilistic quadrics)** and **D1 (cap widening)** are the best
  risk-adjusted bets — untried, cheap, aligned with our own finding that triangle
  quality drives the normal map, and (unlike the graveyard) they change
  *placement/geometry*, not the dead *cost-weight* dimension.
- **D5** is the most interesting genuinely-novel idea.
- **D7 (VSA)** is the only route that changes the representation class — but it is a
  project, not an experiment.

Protocol for all of the above (from the strategic directive): **isolate every
experiment to one case** (others byte-identical), a red dot is *data not a verdict*,
and the judge is the only ground truth — the local oracle is for relative ranking
and deterministic validity checks only.
