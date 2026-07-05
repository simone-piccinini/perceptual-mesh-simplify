# v55 — v54 keeps + inverse-rendering refine enabled on case6/case7 — PENDING

Same keeps as v54 (99.25 | 69.5 | 85.25? | 90.75 | 97.25 | 97.05?) but refine_for now covers
V>100k: case6 VSA+refine = +0.0053 local (0.8661 vs 0.8608), case7 +0.001. Monotonic accept →
can only raise SSIM; hard 16s wall-clock box unchanged (case7-size total 16.4s local).
STRICTLY DOMINATES v54 — if v54 not yet submitted, submit this instead (same decoder):
| all pass | 539.05/6 = **89.842** | case4 WA | 75.63 | case7 WA | 73.67 |
If v54 already out: submit v55 after its verdict (adjust case4/case7 keeps per decoder first).
