# case-3 RESULTS — mechanisms tried and their judge outcome

Current: **v111, N=6941, 70.08%** (S-read S2=0.9135@6940). All levers below are ON in v111 and
TOGETHER produce 6941. History/why-dead detail: docs/THEORY.md, docs/ATTEMPT_LOG.md.

## Mechanisms IN the banked case-3 pipeline (v111)
| lever | role | status |
|---|---|---|
| free-QEM keep 0.2997 | base decimation | on |
| VSA-lite (g_ndecim/g_nplace) | order+place collapses by normal distortion (L2,1) | on (helped) |
| Pivot-A lambda=16 | metric-in-the-loop contrast-deficit steering | on |
| per-channel steering | nx/ny/nz separately | on |
| hybrid-1024 | re-render original at 1024 for the final refine | on (c3-only) |
| s-def | structure-deficit steering variant | on (judge-proven c3) |
| inverse-render refine | analytic-SSIM vertex ascent, time-boxed | on |

## Judge-NEGATIVE / dead on case 3 (do NOT repeat without a new angle)
| idea | result |
|---|---|
| R1 interleaved decimate<->refine | +0.0015-0.002 local, WA'd banked rung x2 (19897009/024) — proxies over-reward |
| 768-native refine | local +0.00067, judge-negative |
| lambda 12/24 sweep | 70.06 rung WA'd both regimes -> c3 CLOSED at current lever set |
| descent 6931 / 6944 (R1-era) | WA'd — but mechanism-confounded (R1 was on); un-anchored below 6941 is OPEN |
| construction paradigm (main_v2) | capped ~64 globally; collapse-mesh rounds features; not a case-3 win |

## S-read log (Level B, judge-side self-score)
| date | N | K | S2 | note |
|---|---|---|---|---|
| 2026-07-06 | 6940 | 57 | 0.9135 | friend's read 19898572; the 0.9135 is FAMILY-ANCHORED, not harvestable |
| 2026-07-07 | 6700 | -- | WA  | 19912623; c4 also coin-lost that run (unrelated) |
| 2026-07-07 | 6800 | -- | WA  | 19912949; only c3 failed |
| 2026-07-07 | 6900 | -- | WA  | 19912982; only c3 failed |

## The open harvest — CLOSED 2026-07-07
Wall PINNED at **(6912, 6941]**. Four probes below 6941 all WA (6912 friend, 6900/6800/6700 this
session) + 3 mechanisms falsified below 6941 in prior sessions (ATTEMPT_LOG line 772). The apparent
+0.0135 headroom from S2=0.9135@6940 was NOT real: it is anchored to the banked-primary float family
(ATTEMPT_LOG line 736), so any deeper cut re-rolls it away — which is exactly why 6900 WA'd. Harvest
below 6941 = **0**. Lesson: trust judge pass/fail over the optimistic S2 near the wall (S2 ~+0.010
optimistic here, not the doc's +0.005). The real 70->85% gap needs a BETTER MECHANISM (IDEAS.md
#2-4), A/B'd via S-read at a SAFE N (>wall) so the read passes. See LIMITS.md for the full map.
Automation note: a box-cut coin loss on an UNTOUCHED case (c4 @6700) breaks harness auto-decode
-> the agent must decode manually (attribute the extra WA to the coin).

## Mechanism screens 2026-07-07 (local self-score @6940 on the 21068->6313 proxy)
The case-3 pipeline is at a MATURE local optimum — every cheap mechanism tweak screens NEGATIVE:
| variant | S2 (local) | vs banked nmetric=0 (0.894342) |
|---|---|---|
| nmetric=3 (true closed-form SSIM-loss) | 0.884266 | -0.010 (matches doc's -0.011) |
| nmetric=4 (tempered SSIM-loss) | 0.893044 | -0.0013 |
| SIL on (silhouette/depth channel) | 0.893097 | -0.0012 (depth +0.0005, normal -0.003 — SIL rim damages interior normals) |
Note: local is a KNOWN-BIASED screen (§9.1) — these could still flip on the judge, but §9.1's evidence
is local-POSITIVE-not-transferring; a large local loss flipping to a judge win is unsupported. nmetric=4
(-0.0013) is the only plausible transfer flip, and it's a weak, low-odds one-submission bet.
depth is nearly saturated (0.984, only +0.0005 reachable via SIL) -> the depth channel is NOT the lever.

## Where that leaves case 3 (measured, this session)
Cheap mechanism tweaks are exhausted (all local-negative). The +-0.013 better-mesh spread (ENVELOPE
§6.1) exists but is unreachable by local tweaks — it needs a GLOBALLY-better optimizer (THEORY Road B
item 2: differentiable co-optimization DURING reduction, not refine-after). That is the one door with
real headroom, but it is heavy AND §9.1 warns position-space gains transfer poorly -> low odds.
The leaders' ~2x case-3 efficiency (70->85%) is not explained by anything in our measured mechanism space.

## ROAD 1 — Full VSA remesh (retriangulation) — log (2026-07-08)
Standalone `solver/vsa_remesh.cpp`. Reuses the VSA partition (`lloyd_partition`), adds the NEW part:
anchor-mesher that retriangulates each region into fresh topology. Tested on the ORGANIC proxy
(armadillo 49990v ~ case-3 class) scored by the local oracle `imc_eval` (per-view normal/depth SSIM).

Iterations:
1. pipeline end-to-end: partition->anchors->fan-triangulate->validate. 237 bad-loops, 41 non-manifold.
2. anchor insertion for <3-anchor loops (Cohen-Steiner) + skip zero-area: bad-loops 237->77, degen 31->0.
3. lens fix (arcs sharing an anchor pair -> m=4 edge). Bug 1: akey overflow -> 5285 false splits.
4. Bug 2: middle-vertex signature is direction-dependent (arc walked opposite from its 2 regions).
   Fixed with a reversal-invariant signature (min interior vertex). armadillo: bad-loops=0,
   boundary=0, non-manifold 25 (residual = 5 multiloop + pinch + unsplittable). ~99.9% manifold.
5-7. MEASUREMENT vs the banked pipeline at equal V (the decisive test):

| mesh            | V     | normal | depth | FinalSSIM |
|-----------------|-------|--------|-------|-----------|
| **QEM banked**  | 4212  | 0.72   | 0.98  | **0.8504** |
| VSA remesh      | 1925  | ~0.47  | ~0.92 | 0.6615 |
| VSA remesh      | 4378  | 0.52   | 0.94  | 0.7329 |
| VSA remesh      | 7233  | 0.60   | 0.965 | 0.7831 |
| VSA remesh      | 10438 | ~0.66  | ~0.97 | 0.8153 |

**VERDICT: VSA remesh is >2.5x LESS efficient than QEM on organic meshes.** At equal V (4212 vs 4378)
VSA loses -0.117 FinalSSIM (normal -0.20). It needs >10438 verts just to match QEM's 4212-vert score.
MECHANISM (fundamental, not a tuning bug): VSA tiles the surface into large piecewise-FLAT facets ->
a staircased normal map; SSIM's structure term rewards matching the SMOOTH normal gradient of an
organic surface, which QEM's dense adaptive triangulation does far better per vertex. VSA's strength
is CAD/mechanical (piecewise-planar), the OPPOSITE of case-3. NOTE: this confirms VSA-*lite* (+0.0128,
banked) worked by ORDERING collapses of a still-smooth QEM mesh — NOT by flat retriangulation. The
remaining manifold defects (25 edges) are fixable but irrelevant: no triangulation of the same anchors
closes a 0.12 normal gap. Road 1 status decision: see IDEAS.md (recommend strike -> Road 2/3).
