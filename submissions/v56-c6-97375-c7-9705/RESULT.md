# v56 — case6 97.375 (VSA+refine) + case7 97.05 (VSA-only) + TLE guard — PENDING

v55 verdicts folded in: case4 wall CLOSED at 85.0 (85.25 WA); case7 TLE root-caused
(refine_init renders the 2.2M-face original UNBOXED before the 16s wall-clock cap) →
refine now excluded >400k + elapsed>6s guard skips refine entirely on slow starts.
case6+refine PASSED on the judge in v55 (97.25) → pushing 97.375 (local 0.8627, +0.003 anchor).
case7 97.05 VSA-only: v53 proved VSA fits case7's budget (WA, not TLE, at 97.2).

Config: 99.25 | 69.5 | 85.0 | 90.75 | 97.375? | 97.05?
| all pass | 538.925/6 = **89.821** | case6 WA | 73.59 | case7 WA | 73.65 | both WA | 57.42 |
