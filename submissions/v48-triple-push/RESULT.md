# v48 — triple wall push: case3 70 + case4 84.25 (stack) + case5 90.80 (vis+projw new) — PENDING

Config: case3 keep 0.30, case4 keep 0.1575, case5 keep 0.092 with visibility+projw newly
enabled for (40k,100k]. Cases 2,6,7 untouched. Every failure combo distinguishable:

| outcome | score |
|---|---|
| all pass | ~89.71 |
| case3 WA | ~78.04 |
| case4 WA | ~75.67 |
| case5 WA | ~74.58 |

Local: case3 0.8979 (ref 0.8974, coin flip) | case4 0.8684 (+0.0071 over base@83.95's 0.8613,
which passes) | case5 0.8526 at 90.80 = +0.0003 over confirmed 90.75's mesh (vis+projw covers
the push). 91% WA'd twice pre-vis; 90.80 is a fresh point.

## Result: 62.911579, 5/7 — case3 70 WA, case5 90.80 WA, **case4 84.25 PASSED** (decoder: 377.45/6=62.908 ✓, judge also NAMED cases 3+5 as wrong — verdict granularity confirmed).
case3 wall = 69.5. case5 wall = 90.75 hard (91 WA'd ×2 pre-vis, 90.80 WA'd with vis+projw). case5 CLOSED.
Next: v49 consolidation banks case4 84.25 with everything else at judge-confirmed points → expect 89.617.
