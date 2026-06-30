# Submission v19 — case 5 -> 77%; area-weighting reverted

## Judge result
ACCEPTED, 7/7, score 84.670644. Best so far (was 84.34).

## Config (free-QEM, unweighted)
case2 0.08/92% | case3 0.36/64% | case4 0.18/82% | case5 0.23/77% | case6 0.03/97% | case7 0.04/96%.
Score = (92+64+82+77+97+96)/6 = 84.67.

## What worked
- case 5 confirmed at 77% (free-QEM).

## What did NOT (the submission before this, scored 44.3, reverted)
- AREA-WEIGHTED quadrics: broke cases 4 (82%) AND 6 (97%) -- both UNCHANGED keeps, so
  area-weighting alone flipped them confirmed-pass -> WA. Net negative on the judge.
- CRITICAL: the local relative-SSIM screen said area-weighting HELPS (proxy cow +0.011),
  but the judge says it HURT. The screen does NOT predict the judge (proxy meshes != the
  hidden meshes). Quality changes are now 0/2 (anti-sliver, area-weighting).

## Walls (judge-confirmed)
case2 92% | case3 64% (fails 70%) | case4 82% (fails 84%) | case5 77% | case6 97% | case7 96%.

## Next
- Consolidate: last keep-bisections (case2->93, case4->83, case5->78) -> ~85.
- Then the only untried lever for case3/the ceiling is a NON-blind quality method. With no
  reliable local test, it is a judge gamble (best-counts protects). PQ placement is the
  candidate but high-risk (global vertex-selection change = what broke cases 4,6).
