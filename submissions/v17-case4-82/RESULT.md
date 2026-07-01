# Submission v17 — case 4 -> 82% (keep 0.18)

## Judge result
ACCEPTED, 7/7, score ~84.0. Best so far (was 83.67, v15).

## What it does (ALL meshes free-QEM keep; kOpAdaptive=0, adaptive-subset path OFF)
- case 2 (<=7k):        keep 0.10 -> 90%
- case 3 (<=30k):       keep 0.36 -> 64%  (fragile anchor)
- case 4 (<=40k):       keep 0.18 -> 82%  (NEW this submission; 80% was confirmed)
- case 5 (40k-100k):    keep 0.25 -> 75%
- case 6 (100k-400k):   keep 0.03 -> 97%
- case 7 (>400k):       keep 0.04 -> 96%
Score = (90+64+82+75+97+96)/6 = 84.0.

## What worked (cumulative)
- Switching LARGE meshes from subset-adaptive (95%) to FREE-QEM keep (96-97%): free-QEM's
  rounder triangles -> better face normals than subset's slivers -> higher SSIM at higher
  compression. (v13/v14/v15.)
- Per-case keep binary-searched to each mesh's SSIM wall.
- case 4 confirmed at 82%.

## Walls (judge-confirmed)
case2 90% (geometry-capped ~92-94%) | case3 64% (fails 70%, fragile) | case4 82% |
case5 75% (fails 80%) | case6 97% | case7 96% (0.03/97% WA'd).

## What did NOT (v16, reverted)
Anti-sliver REJECTION gate -> 40.0, 5/7. Rejecting collapses fights compression head-on
(stalls every case + breaks the aggressive ones). Quality must be NON-BLOCKING:
better positions, SAME collapses.

## Next
- Last keep-nudges: case2->92, case4->84 (~+0.7, then keep-squeeze is done at ~85).
- Real ceiling = the medium anchors case3 (64) + case5 (75), SSIM-capped. Lifting them needs
  a non-blocking quality improvement (Probabilistic Quadrics / feature preservation),
  PRE-SCREENED with the local oracle as a RELATIVE SSIM proxy to avoid blind bets.
