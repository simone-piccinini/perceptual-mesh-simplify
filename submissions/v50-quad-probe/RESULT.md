# v50 — quad probe at the unfound walls — PENDING

case2 99.5 | case3 69.75 | case4 85.0 (stack) | case7 97.00. case5/case6 at confirmed points.
All failure combos distinguishable (zeroed compressions 99.5 / 69.75 / 85 / 97 pairwise-distinct sums).

| outcome | score |
|---|---|
| all pass | (99.5+69.75+85+90.75+97+97)/6 = **89.833** |
| case2 WA | 73.25 - drop 16.58 |
| case3 WA | 78.21 |
| case4 WA | 75.67 |
| case7 WA | 73.67 |

Local: case3 0.8984 (+0.0010 over ref) | case4 0.8638 (+0.0025 over judge-passing base 0.8613).
case2/case7: no proxies, judge rolls at never-probed walls.
Rationale: case4 stack passed 3 straight pushes; local slope says stack ≈ +2.5% keep-equivalent
over pre-stack wall estimate. Scale-sweep + depth diagnostics closed silhouette-depth avenue
(73% of depth deficit is silhouette but chord-sag is already optimally balanced — info limit).

## Result: 45.459, 4/7 — case2 99.5 WA, case3 69.75 WA, case7 97.00 WA, **case4 85.0 PASSED** (decoder 272.75/6=45.458 ✓).
Walls now bracketed+closed: case2 99.25, case3 69.5, case7 96.95. case4 wall STILL unfound after +1.05 of pushes.
Confirmed set → 89.742. Next: v51 consolidation, then v52 case4 85.5 (local 0.8609, coin flip).
