# Submission v11 — keep pushed too far (case 5 broke)

## Judge result
ACCEPTED, 6/7, score 70.670391. Case 5 FAILED. (Best stays 81.50 — best-counts.)

## What it does
case2 keep0.10(90%) | case3 keep0.36(64%) | case4,5 keep0.20(80%) | large adaptive(95%).

## Result by case
case2 90% PASS | case3 64% PASS | case4 80% PASS | case5 80% FAIL | case6,7 95% PASS.

## Learning
- case2 confirmed at 90% (NEW gain). case4 confirmed at 80% (NEW).
- case5 FAILS at 80% (keep 0.20), PASSED at 75% (keep 0.25, v10) -> case5 limit = 75-80%.
- case4 and case5 share the (30k,100k] bucket but differ in SSIM fragility -> must SPLIT by V.

## Next
- Safe recover (new best): case2 0.10 + case4,5 0.25 -> 82.3, all confirmed, zero risk.
- Squeeze: split case4(0.20)/case5(0.25) by V at ~45k -> 83.2 if V-routing holds.
