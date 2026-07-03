# v58 — case7 97.05 with 2-stage VSA (TLE fix: 8.0s -> 3.9s on 800k) — PENDING

2-stage: bulk QEM-collapse to 5x target (cheap, order-insensitive), then VSA-lite on the remnant.
Local 800k: 3.9s (vs 8.0 full VSA, vs 3.7 pure QEM); quality 0.94816 >= full-VSA 0.94787.
Real case7 ~1.1M est. ~5.5s (v53's ~11s barely passed). case6/case5/case3 byte-identical to v57.

Config: 99.25 | 69.5 | 85 | 90.75 | 97.375 | 97.05?
| pass | 539.025/6 = **89.837** | case7 WA | 441.975/6 = 73.66 | case7 TLE again | same 73.66 |

## Result: 89.824722, 7/7 ★ NEW BEST — case7 97.05 with 2-stage VSA passed (real compressions round slightly under nominal 89.837).
