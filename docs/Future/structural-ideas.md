# Structural ideas to lower `V'_min` — the (b) lever

There are only two ways to raise the score: **(a)** bisect each case's wall harder,
and **(b)** invent structural ideas that let a case pass at fewer vertices. Every
point gained since 88.67 came from these two. This document is about **(b)** — new
mechanisms that lower `V'_min` (the smallest vertex count at which a case still
passes `FinalSSIM ≥ 0.9`).

The binding wall everywhere is the **structure (σxy correlation) term of the
flat-shaded normal-map SSIM** — the σxy correlation between the original and the
simplified normal map, *not* luminance or contrast (JUDGE-ENVELOPE §7;
SOLVER-INTERNALS §4.5 / §11 `sdef_map`, "the measured true deficit"). Depth is ≈free
only on the mechanical case; on organic cases it can drop (see D0) — see
[../theory/wang-ssim.md](../theory/wang-ssim.md).
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
3/4. The **room is confirmed huge** (JUDGE-ENVELOPE §5: the judge's Hausdorff is
vertex-to-vertex with large slack — our oracle's point-to-surface leash is strictly
stricter), so 0.03–0.04·diag is safely legal. **But** this is a position-only
optimizer change, and both the D3 null result and JUDGE-ENVELOPE §7.2 warn that (a)
position-only optimizer moves are net-neutral on the judge *unless paired with a
lower `keep`*, and (b) local position-space gains are KNOWN-BIASED (over-rewarded on
proxies, do not transfer). So widen the cap *together with* a lower keep, and read
the outcome on the judge — monotonic-accept protects validity, not transfer.

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

*Status: IMPLEMENTED + LOCALLY SCREENED (2026-07-05) — ready for the judge family
test.* Implemented per the corrected recipe in
[../theory/paper-notes.md](../theory/paper-notes.md) (the notes' σ-powers were
dimensionally wrong; re-derived from Q(x)=E[(s̃·x−det̃)²] and verified: σ=0 ⇒ exact
GH triangle quadric @2e-14, Monte-Carlo match @5e-4, flat-patch minimizer exactly
on-plane). Integration follows the judge-proven **aniso pattern**: the PQ minimizer
(x* = A⁻¹b of the merged {A,b,c} triple) joins the placement **candidate set** in
`Evaluate`; `incident_ndist` arbitrates; heap ordering untouched. **Isolated to
case 5** (`pqs_for`: V ∈ (40k,100k]; 0 elsewhere; byte-identity of every off-band
proxy + the `G_PQS=0` kill-switch verified against the pre-D4 binary).

**Screen #1 (raw PQ, σ ∈ {0.5,1,2} × mean edge) — NEGATIVE, and diagnostic.** All σ
read below control on armadillo @ banked case-5 keep (best −0.0009 @ σ=2, worst
−0.0027 @ σ=0.5, all in the normal channel). The σ-trend exposed the cause: at σ→0
the raw PQ triangle quadric is exactly the **area²-weighted** GH quadric
(Q = 4·Area²·dist²) — and area-weighting is judged-dead in this engine (`Initialize`
comment: hurt cases 4/6). The active harmful ingredient was the implicit weighting,
not the regularization.

**Screen #2 (normalized PQ: each face triple ÷ (2·Area)², so σ=0 ⇒ the engine's own
UNWEIGHTED quadric) — POSITIVE at σ=0.25.** Armadillo @ keep 0.08453125, oracle @320,
control = 0.9267 (n 0.8758 / d 0.9775), V′=4212 all runs, all valid:

| σ (× mean edge) | FinalSSIM | normal | depth | Δ |
|---|---|---|---|---|
| 0.10 | 0.9256 | 0.8739 | 0.9772 | −0.0011 |
| **0.25** | **0.9276** | **0.8767** | **0.9786** | **+0.0009** |
| 0.50 | 0.9269 | 0.8749 | 0.9789 | +0.0002 |
| 1.00 | 0.9256 | 0.8742 | 0.9769 | −0.0011 |

Clean unimodal response peaking at 0.25, both channels up — a real knob, not noise.
Operating point shipped in `pqs_for` = **0.25, normalized** (`g_pqnorm=1` default;
`G_PQS`/`G_PQNORM` env overrides for local tests; no-env path verified byte-identical
to the sweep winner).

**Honest transfer framing (ENVELOPE §7.2):** +0.0009 local is in the range where
decimation-trajectory gains have both transferred (aniso) and not (R1: +0.002 local →
3/3 judge-negative). The proxies over-reward position-space changes. So the judge
family test is the only read that counts: **submit at the banked case-5 rung
(V′=4226) with PQnorm σ=0.25 on — one submission, one question: does case 5 still
pass?** If yes, descend one rung (~4200, using the 3.5e-5 S/vertex slope as the
sizing guide). If the family test WAs the banked rung, revert `pqs_for` to 0 (one
constant) and D4 is closed judge-negative. Expected value if it transfers: ~+0.004
total (small); the larger prize is that a validated PQ placement then becomes a
candidate for the *other* cases (3, 6, 7) where placement has never moved.

**D5. Connectivity in the optimizer loop.** Lever 4 freezes topology and only moves
vertices — stuck in the given triangulation's basin. Extend it: between
position-ascent steps allow a few **manifold-safe edge flips** (link condition,
trivially watertight) chosen by their measured effect on rendered SSIM, plus
occasional re-collapses of now-redundant edges. The one move that lets the
post-decimation mesh change its *face pattern* to fit the normal map, short of full
remeshing. Cases 3, 4. Must use the periodic/coarse render (never per-flip) to stay
in budget. **Prior art (SOLVER-INTERNALS §5.5 / §9 / §11): the flip component is
already tried and judge-inert** — `flip_pass` / `G_FLIP` (normal-match proxy,
+0.0005 local, zero judge) and "edge flips by real SSIM" is a listed dead optimizer
variant. So D5 is *not* genuinely-novel; its only untried part is the **interleave
with position ascent + re-collapse of redundant edges**. Treat it as a variation on
inert work — medium-low confidence.

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
   placement. Small changes, plausibly help *every* case including 6/7. Not a
   "free-roll", though: any placement/cap change reshuffles every case's mesh ±0.013
   SSIM and can WA a banked razor rung (§9.3 operating rule; the placement graveyard
   already has WA'd siblings — `G_TCAND`, `G_NPLACE2`), so run the mandatory judge
   family-test at the banked rung *before* descending.
3. **D2 / D3.** Optimizer upgrades on cases 3/4, guided by D0.
4. **D5.** Connectivity-in-loop, if D2/D3 show the position-only optimizer saturating.
5. **D6 / D8.** Only if D0 fingers contour/crease loss, isolated to one case.
6. **D7 (VSA).** The big swing, case 4 only; prototype the risky re-triangulation first.

### Confidence for *lowering `V'_min`*

- **D4 (probabilistic quadrics)** and **D1 (cap widening)** are the best
  risk-adjusted bets — cheap, aligned with our finding that triangle quality drives
  the normal-map *structure* term, and (unlike the graveyard) they change
  *placement/geometry*, not the dead *cost-weight* dimension. But they are
  **ceiling-limited**: JUDGE-ENVELOPE §6.1 says the only door to 91+ is a *globally
  better optimizer* (joint decimation+refinement, Road B) — D4/D1 buy tenths inside
  the current decimate-then-refine family, not the next wall. (D4 is a decimation-
  side placement change, so it is *less* exposed to §7.2's position-space transfer
  bias than D1, which is a refine-optimizer knob.)
- **D5** — its edge-flip core is already tried and judge-inert (see D5 above); only
  the interleave + re-collapse is new. The most interesting idea *in principle* (it
  is the closest thing here to Road B's joint optimizer), but medium-low confidence
  given that flip prior art.
- **D7 (VSA)** is the only route that changes the representation class — a project,
  not an experiment. It is well-aimed: it targets the *diagnosed* case-4 wall
  (crease gate-exhaustion, ENVELOPE §6.1); the manifold re-triangulation is the risk.

Protocol for all of the above (from the strategic directive): **isolate every
experiment to one case** (others byte-identical), a red dot is *data not a verdict*,
and the judge is the only ground truth — the local oracle is for relative ranking
and deterministic validity checks only.
