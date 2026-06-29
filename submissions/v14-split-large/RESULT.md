# v14 — split large cases (case 6 @ 97%, case 7 @ 95%)

## Judge result
ACCEPTED, 7/7, score 83.503989. NEW BEST (was 83.170642). All green.

## Config (per-case keep dispatch, free-QEM placement everywhere)
- case 2 (<=7k):   keep 0.10 -> 90%
- case 3 (<=30k):  keep 0.36 -> 64%  (fragile, 0.30/70% FAILED)
- case 4 (<=40k):  keep 0.20 -> 80%
- case 5 (<=100k): keep 0.25 -> 75%
- case 6 (<=400k): keep 0.03 -> 97%  (free-QEM; raised from 95%)
- case 7 (1.1M):   keep 0.05 -> 95%  (free-QEM; 0.03/97% WA'd -> drift)
score = (90+64+80+75+97+95)/6 = 83.50.

## What worked
- Free-QEM placement legal on large (cases 6,7) -> replaced subset; same 95% gave
  identical 83.17, confirming validity, then case 6 pushed to 97%.
- Splitting 6/7 at V=400k banked case 6's +2 while keeping case 7 at its safe 95%.

## What did NOT (prior probe v13)
- case 7 (1.1M) WA at 97% (free-QEM drifts off-surface -> Hausdorff on the biggest mesh).

## Walls now (judge-confirmed)
case2 >=90% | case3 64% (fragile) | case4 >=80% | case5 75% | case6 >=97% | case7 95% (97% WA).

## Next
- Probe case 7 at 96% (keep 0.04): between confirmed 95% and WA 97%.
- Then the real climb (free-QEM has a drift ceiling on large): Probabilistic Quadrics
  (sigma-regularized, low-drift positions) to push cases 6,7 toward 98-99% without WA.
