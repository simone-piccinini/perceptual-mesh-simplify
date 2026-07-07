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
| 2026-07-07 | 6700 | -- | WA  | read WA'd -> 6700 BELOW the passing wall this run (case 4 also coin-lost, unrelated). Harvest floor > 6700. |

## The open harvest
MEASURED 2026-07-07: read @6700 WA'd. So the ~+0.005 S2-optimism ate most of the apparent 0.0135
headroom: true wall is in (6700, 6941], harvest is SMALL (~+0.06-0.10, coin-noisy), NOT +0.17.
This CONFIRMS WALL-MODEL §7: probing case 3 is marginal; the real 70->85% gap needs a BETTER
MECHANISM (IDEAS.md #2-4), A/B'd via S-read at a SAFE N (>wall) so the read actually passes.
Automation note: a box-cut coin loss on an UNTOUCHED case (c4 here) breaks harness auto-decode
-> the agent must decode manually (attribute the extra WA to the coin).
