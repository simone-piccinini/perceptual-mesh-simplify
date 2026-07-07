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
| 2026-07-06 | 6940 | 57 | 0.9135 | friend's read 19898572; anchor of the harvest |

## The open harvest
6941 was banked one rung into the coin; S2=0.9135 says ~240 verts remain to the true 0.900.
Next reads (6800, then anchored jump) fill this table and pin the harvestable floor.
