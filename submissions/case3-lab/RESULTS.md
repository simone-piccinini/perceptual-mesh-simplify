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
optimistic here, not the doc's +0.005). Lowering the wall needs a BETTER MECHANISM (IDEAS.md
#2-4), A/B'd via S-read at a SAFE N (>wall) so the read passes — but the prize is small (leader_c3
~72-77%, see premise correction below) and VSA (the first paradigm try) is dead. See LIMITS.md.
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
(NOTE 2026-07-08: the "~2x case-3 efficiency / 70->85%" framing is RETRACTED — see the premise
correction below. Leader_c3 is plausibly ~72-77%, a small gap likely shared across cases.)

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

8. proxy-plane EAR-CLIP triangulation (replaces the 3D fan). Two wins: (a) killed the manifold
   defects -> WATERTIGHT-MANIFOLD (judge-valid, non-manifold 25->0); (b) +0.02 FinalSSIM from better
   triangle shapes. 9-10. best-VSA (ear-clip) efficiency curve + a richer (40-iter) partition:

| mesh (ear-clip)        | V     | FinalSSIM |
|------------------------|-------|-----------|
| **QEM banked**         | 4212  | **0.8504** |
| VSA iters=12           | 4378  | 0.7472 |
| VSA iters=40 (richer)  | 4381  | 0.7528  (+0.006 from 3x the Lloyd iters) |
| VSA                    | 7233  | 0.8027 |
| VSA                    | 10438 | 0.8322 |

**VERDICT: DEAD (struck iter 10/10, 2026-07-08).** Best-VSA (ear-clip) is >2.5x LESS efficient than
QEM on organic. At equal V it loses ~-0.10 FinalSSIM (normal -0.20); even at 2.5x the vertices
(10438) it stays below QEM's 4212 score. Ear-clip lifted the curve +0.017 and made it valid; a 3x
richer partition added +0.006 -- nothing closes the gap. MECHANISM (fundamental, not a tuning bug):
VSA tiles the surface into large piecewise-FLAT facets -> a staircased normal map; SSIM's structure
term rewards matching the SMOOTH normal gradient of an organic surface, which QEM's dense adaptive
triangulation does far better per vertex. VSA wins on CAD (piecewise-planar), the OPPOSITE of case-3.
Confirms VSA-*lite* (+0.0128, banked) worked by ORDERING a still-smooth QEM mesh, NOT by flat
retriangulation. LESSON: the winning case-3 mesh is smooth+dense+adaptive (QEM-family); flat/partition
topology is wrong for organic. Next-road reassessment in IDEAS.md. Code kept (solver/vsa_remesh.cpp).

## Premise correction (2026-07-08): the "case-3 -> 85%" target is arithmetically wrong
Total gap to leader (91.46 vs our 90.286) = 1.174 on the MEAN = 7.05 SUMMED over 6 cases. If ALL of
it were case-3: leader_c3 = 70.08 + 7.05 = 77.1% (NOT 85%). It almost surely spreads across
c4/c5/c6/c7 too -> leader's case-3 is plausibly 72-77%, only 2-7 pts above ours. No "2x efficiency
mystery". Right-sizes the prize: case-3 headroom is modest and hard -> favor cheap bets over heavy builds.
