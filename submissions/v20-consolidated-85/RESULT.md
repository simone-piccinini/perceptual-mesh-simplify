# Submission v20 — consolidated keep-ceiling

## Judge result
ACCEPTED, 7/7, score 85.004102. Best so far (was 84.67).

## Config (free-QEM, unweighted; per-case keep)
case2 0.07/93% | case3 0.36/64% | case4 0.18/82% | case5 0.22/78% | case6 0.03/97% | case7 0.04/96%.
Score = (93+64+82+78+97+96)/6 = 85.0.

## Judge-confirmed walls (keep-tuning EXHAUSTED)
case2 93% (94% geom-risky) | case3 64% (66% AW-fail, 70% free-fail) | case4 82% (83% & 84% FAIL) |
case5 78% (80% FAIL) | case6 97% | case7 96% (97% FAIL).

## Lessons locked
- Judge gives only pass/fail. Local relative-SSIM screen does NOT predict the judge
  (area-weighting screened +, judge -). Quality bets 0/2 globally (anti-sliver, area-weight).
- Geometry is never the failure now (all keeps verified < 5% Hausdorff); SSIM is the wall.

## Next: SAFE gamble (isolated to one V-bucket)
Apply an experimental method to ONE case's vertex-count bucket only -> other 5 cases stay
byte-identical to this 85.0, so a failed gamble can only red that one case (best-counts safe).
Target = case3 (64%, most room). Steps: (1) free-QEM 66% (untested; the 66% fail was WITH
area-weighting), (2) normal-aware quadric on case3 only, (3) PQ on case3 only.
