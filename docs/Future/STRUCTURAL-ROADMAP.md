# Structural roadmap — how to push past 91

*2026-07-07. Written at the end of the razor era: bank **90.285538** (v111), all six walls
pinned by the probing harness. This document says (1) why tuning is finished, (2) exactly
what "structural" has to buy, (3) the one prerequisite that killed every past attempt, and
(4) the ranked list of structural ideas to try, honest about each. Companion to
[WALL-MODEL.md](../WALL-MODEL.md) (the razor mechanics), [structural-ideas.md](structural-ideas.md)
(the older idea list + graveyard), and [transfer-instrument.md](transfer-instrument.md)
(why local measurement fails).*

---

## 1. The razor is exhausted — proof

Every case is pinned or nearly so; the probing harness closed the last bracket this session:

| case | mesh | V | N (bank) | compression | wall | regime |
|---|---|---|---|---|---|---|
| 2 | dust | 4,098 | 30 | ~99.27 % | ~99.32% WA'd → at floor | topology floor |
| **3** | **organic** | 23,201 | 6,941 | **~70.08 %** | **(6900, 6941]** | box-cut coin |
| 4 | CAD | 35,292 | 4,970 | 85.92 % | (4960, 4970] | box-cut coin |
| 5 | organic | 49,987 | 4,212 | 91.57 % | ladder 0/12 below | ~deterministic |
| 6 | big | 377,084 | 8,684 | 97.70 % | 6000/6500 WA'd | box-cut, stable |
| 7 | huge | 1,009,118 | 28,800 | 97.15 % | (28800, 28822] | deterministic |

There is no vertex left to shave that isn't a sub-coin razor. Tuning is over. See
[c4-harvest-ladder.md](c4-harvest-ladder.md) and the harness log
([../probe/wall_model.json](../probe/wall_model.json)).

## 2. What "structural" must buy — quantified

Score = mean of the six compressions `100·(1 − N/V)`. The deficit is **not spread evenly —
it is almost entirely case 3** (70 % while everything else is 86–99 %). Targets, holding the
other five fixed:

| goal | case-3 compression needed | case-3 N | vs today's 6,941 |
|---|---|---|---|
| **> 91.0** | 74.40 % | **~5,940** | **−14 %** |
| leaders (~91.46) | 77.16 % | **~5,300** | **−24 %** |

So the whole game reduces to one sentence: **make case 3 pass at ~5,300–5,940 vertices
instead of 6,941 — a 14–24 % better organic normal-map simplification at fixed quality.**
That is a *wall move*: the same mesh must render an SSIM-0.9 normal map at far fewer
vertices. Tuning where we sit on the wall cannot do it; a better simplifier can.

**Leverage:** case 5 is also organic (91.57 %). Any mechanism that lowers the organic wall
helps case 3 **and** case 5, easing the case-3 target. Case 3 is the test bed; case 5 is the
free second win. (Cases 2/6/7 are near-maxed; case 4 is CAD, a different regime.)

**Why case 3 is stuck at 70 %:** the binding term is the flat-shaded **normal-map SSIM
*structure* (σxy / local normal variance)**, not depth and not the mean (D0 diagnostics,
[structural-ideas.md](structural-ideas.md) §Group 0). At 70 % the greedy-QEM mesh can no
longer reproduce the *local normal contrast* of an organic surface. Depth on organic has
slack (0.90–0.98, not saturated) — a secondary lever.

## 3. The prerequisite that killed everything before: measurement

**Read this before building anything.** Every prior structural attempt — D3 (depth), D4
(quadrics), D5 (flips), R1 (interleave), and *three* transfer instruments — failed not
because the idea was wrong but because **we could not tell locally whether it helped the
judge.** The local oracle over-rewards position-space gains and does not transfer
([transfer-instrument.md](transfer-instrument.md): three formulations falsified against
ground truth). A mechanism that reads +0.002 locally routinely reads 0 or negative on the
judge.

This session proved it again, hard: the Level-B judge-side read said case-3 `S2 = 0.9135`
at N=6940 (implying ~240 vertices of headroom); the actual judge wall was ~20 vertices below
the bank. **S2 is a *relative* instrument, badly optimistic and uncalibrated.**

So the roadmap's Tier 0 is not a mesh idea — it is fixing measurement:

- **E1 — Anchor the Level-B S-read.** Pair reads with pass/fail crossings on the *same
  binary family* to find the self-score value that corresponds to the true 0.900 threshold
  (e.g. "on this family S2=0.905 ⇒ judge S=0.900"). One anchor per case per family, and
  pass/fail outcomes arrive free with every submission. After anchoring, a read *predicts*
  the wall instead of merely ranking. Cost: a handful of submissions; the harness already
  logs everything.
- **E2 — Judge-side A/B for mechanisms.** Submit control and variant as two anchored reads
  at the same N; compare judge-side S directly. Two submissions per A/B — expensive, but
  *correct*, which no local screen ever was. This is the only trustworthy way to evaluate a
  new case-3 mechanism, and it is the harness's real purpose now that the walls are pinned
  ([WALL-MODEL.md](../WALL-MODEL.md) §5.5).

**Everything in Tiers 2–4 is gated on E1/E2.** Building a structural mechanism without
judge-side measurement is how the graveyard got full.

## 4. The graveyard — do not re-propose

Killed by the judge (do not resurrect without a genuinely different mechanism):

- **All mean-based geometric cost reweightings** — area, dihedral, normal-quadric,
  silhouette-*cost*, image-driven λ12, "correct flat-normal cost". 12 methods pin case 3.
  (The lesson: the wall is *variance/structure*, and mean-matching objectives fight it.)
- **Attribute / normal-preserving simplifiers** (GH/Hoppe, meshopt attributes) — preserving
  vertex normals costs triangle quality, which *hurts* the flat-shaded render.
- **Cheap-proxy edge flips** (D5) — `flip_tricost` is a mean objective, anti-correlated with
  SSIM (even the single best flip loses). See [d5-flip-optimizer.md](d5-flip-optimizer.md).
- **Displacement-cap widening** (D1) — the optimizer plateaus well within the 2 % cap.
- **Rejection gates / anti-sliver, vertex clustering, per-region image steering, adding
  vertices, per-collapse full re-render (TLE).**
- **Local-screen transfer instruments** (naive noise model, armadillo monoculture,
  cross-proxy sign) — all three falsified.
- **The construct/carve second solver** (`main_v2`, friend's line) — reached 90.24, below
  v111; a parallel paradigm kept as a fallback / idea bank, not a lead.

## 5. The structural ideas, ranked

Ordered by (expected wall-move on case 3) ÷ (effort), each honest about odds. The unifying
thesis: **fold the *rendered normal-SSIM structure term* into the parts of the pipeline that
are still geometry-driven.** Greedy QEM optimizes geometric error; the refine optimizes
rendered SSIM but only *positions*, *after* the topology is frozen. The leaders' 15–24 %
edge almost certainly lives in the gap between those two.

### Tier 0 — Measurement (cheap, unblocks all of Tier 2–4)
- **E1 anchor the S-read, E2 judge-side A/B** (see §3). Do first. Low effort, high leverage.

### Tier 1 — Perception-aware decimation (most likely the leaders' edge)
The collapse *ordering and placement* are QEM (geometric), re-rendered only at refine time.
Move the real metric into the collapse loop.

- **S1. Structure-aware collapse ordering.** Order/penalize collapses by their measured
  effect on the *local normal-variance* the SSIM structure term rewards — re-rendered
  periodically (VSA-lite cadence, never per-collapse → TLE). This is *not* the failed
  mean-based λ12: the objective is variance match, not average-normal match. Pivot-A already
  proves per-vertex SSIM-deficit steering works (case 5: 79→90); S1 promotes it from a
  *multiplier* to the *primary* collapse metric on case 3. **Effort: medium. Odds: the best
  bet** — it is the smallest step from what already works toward what the leaders likely do.
- **S2. Joint decimate–refine (Road B, full).** Interleave collapse and position-ascent
  tightly so the geometry is SSIM-optimal *as* it is simplified, not polished afterward — the
  one mechanism the graveyard never contained. A light version (R1) was judge-negative, but
  R1 only re-ran the refine mid-decimation; the real thing lets the *ascended geometry change
  the collapse choices*. **Effort: high. Odds: high ceiling, needs E2 to avoid R1's fate.**

### Tier 2 — Vertex-budget allocation (attack the specific deficits D0 found)
Spend the few vertices where the normal map actually needs them.
- **S3. Weakest-view protection.** D0: every mesh has one axial view 0.04–0.09 SSIM below
  the best. Protect the faces feeding the weakest of the 6 views (a per-*view* importance,
  distinct from the failed per-*region* steering). **Effort: low–medium. Odds: modest but
  cheap; a natural first A/B once E2 exists.**
- **S4. Silhouette-coverage guarantee (D6).** At high compression the simplified silhouette
  erodes *inside* the original footprint → object-normal vs background-gray (127.5) mismatch
  at the contour → a large structure-term hit exactly at the outline. Constrain the
  simplified footprint ⊇ original from all 6 axes (a *coverage constraint*, not the failed
  silhouette-*cost*). **Effort: medium. Odds: plausible; targets a concrete, located loss.**
- **S5. Normal-variance-driven density.** Allocate the vertex budget proportional to local
  normal *variance* (the structure target), not curvature *magnitude* (a mean). **Effort:
  low. Odds: modest — but it is the allocation analogue of the S1 thesis.**

### Tier 3 — Connectivity & representation (highest ceiling, biggest build)
- **S6. Localized-SSIM edge flips (D5 done right).** D5 died on the cheap proxy; the real
  version selects flips by the *rendered* SSIM delta. The blocker is cost: a full re-render
  per candidate is TLE. The enabling primitive is a **dirty-region SSIM kernel** — a flip
  touches only a small image window, so score just that window. **This kernel is the single
  highest-leverage build in the whole roadmap**: it also makes S1/S2 candidate evaluation
  cheap and turns the local A/B fast. **Effort: high (real renderer work). Odds: good, and
  reusable.**
- **S7. Global optimization / patch remeshing.** Replace greedy edge-collapse on the worst
  organic patches with a global vertex-placement + connectivity optimization minimizing
  rendered-normal-SSIM error (or retriangulate high-error patches from scratch). The thing
  greedy structurally cannot do. **Effort: very high. Odds: highest ceiling, most
  uncertain — a research project.**

### Tier 4 — Secondary levers (smaller, opportunistic)
- **S8. Joint depth+normal optimization (D3 revisited).** D0 found organic depth has slack
  (0.90–0.98). D3 was judge-null — but on the wrong base and *without lowering keep*, so a
  positions-only change could not move the score by construction. Re-try: optimize depth+
  normal jointly *and* lower the case-3/5 keep to convert the recovered depth slack into
  compression. **Effort: low (code exists). Odds: conditional on the slack being real on the
  hidden mesh — measure with E2 first.**
- **S9. Case 6/7 micro-squeeze.** 97 %→ a hair more via better large-mesh ordering; ~4e-5
  and ~1.7e-5 pts/vertex respectively — only worth it as a free rider on another change.

## 6. Recommended sequence

1. **E1 + E2 — anchor measurement** (Tier 0). Nothing structural is trustworthy without it,
   and it is cheap. *Deliverable: a read whose decoded S predicts the wall to ±few vertices,
   and a two-submission A/B that reports judge-side ΔS for a mechanism.*
2. **S6 — build the dirty-region SSIM kernel.** It is the reusable substrate: it unblocks
   flips (S6), makes S1/S2 candidate scoring affordable, and accelerates every A/B. Build
   once, use everywhere.
3. **S1 — perception-aware collapse on case 3**, evaluated by E2. This is the highest-EV
   *mechanism*; the kernel from step 2 makes it cheap to try.
4. If S1 moves case 3, **generalize to case 5** (free organic win) and layer **S3/S4/S5**.
5. Only if 1–4 stall, escalate to **S2 (full joint optimizer)** or **S7 (global/remesh)** —
   the big builds.

## 7. Honest odds

This is research-grade, not tuning. The leaders' 15–24 % better organic simplification is a
real algorithmic edge we have not cracked, and the graveyard shows the obvious geometric
ideas are dead. But the diagnosis is now sharp — **one case, one term (normal-SSIM
structure), one quantified target (case 3 at ~5,940 for 91.0), and one root obstacle
(measurement, now addressable via E1/E2)** — which is far more than the project had at 88.67.

The single most likely path to >91: **anchored judge-side measurement (E1/E2) → dirty-region
SSIM kernel (S6) → perception-aware collapse (S1), generalized to case 5.** Everything else
is a variation on, or an escalation of, that spine. No guarantee — but it is the only door
left, and it is finally a well-lit one.
