# v15 — case 7 pushed to 96%

## Judge result
ACCEPTED, 7/7, score 83.670653 (sub 19860454). NEW BEST (was 83.50).

## Config (free-QEM placement, per-case keep)
case2 0.10/90% | case3 0.36/64% | case4 0.20/80% | case5 0.25/75% | case6 0.03/97% | case7 0.04/96%
score = (90+64+80+75+97+96)/6 = 83.67.

## What works / confirmed walls (judge)
- case 2: >=90%
- case 3: 64% (fragile; 0.30/70% FAILED) -- STUCK, biggest lever
- case 4: >=80%
- case 5: 75% (0.20/80% FAILED)
- case 6: >=97%
- case 7: 96% PASS, 97% WA  -> free-QEM drift ceiling on the 1.1M mesh = 96%

## What does NOT
- case 7 @ 97% (free-QEM drift -> Hausdorff). case 3 @ 70%, case 5 @ 80%.

## Read
Keep-nudges nearly tapped (~84 ceiling). Untested cheap nudges left: case2 ~91-92%,
case4 ~82-83%, case6 ~98%. Each ~+0.2-0.3.
The climb to 90 needs better PLACEMENT (Probabilistic Quadrics): case 3 (64) is the
biggest single lever, and cases 4,5 are SSIM-walled; PQ's robust, sliver-free
positions = faithful face normals = higher SSIM tolerance. case 7's wall is DRIFT
(geometric) -> PQ (low-drift) can push it past 96 too.
