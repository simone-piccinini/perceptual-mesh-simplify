# Submission v18 — case 2 -> 92% (keep 0.08)

## Judge result
ACCEPTED, 7/7, score 84.337558. Best so far (was 84.0).

## Config (all free-QEM keep)
case2 0.08/92% | case3 0.36/64% | case4 0.18/82% | case5 0.25/75% | case6 0.03/97% | case7 0.04/96%.
Score = (92+64+82+75+97+96)/6 = 84.34.

## Walls (judge-confirmed)
case2 92% (geometry-capped ~92-94%) | case3 64% (fails 70%) | case4 82% (fails 84%) |
case5 75% (fails 80%) | case6 97% | case7 96% (fails 97%).

## State
Keep-squeezing is essentially done (~85 ceiling with fine bisection). The score is now
anchored by case3 (64) and case5 (75) -> SSIM-capped MEDIUM meshes. Reaching 90+ needs a
real QUALITY method (hold flat-shaded normal-map SSIM at high compression), not more keep.

## Next
Build a relative-SSIM SCREEN (existing oracle, A-vs-B on proxy meshes so calibration
ambiguity cancels), develop a quality method that beats free-QEM on it (area-weighted /
normal-aware QEM / Probabilistic Quadrics), submit only screen-winners. Target 90+.
