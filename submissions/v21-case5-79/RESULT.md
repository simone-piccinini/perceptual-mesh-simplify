# v21 — case 5 -> 79%

## Judge result
ACCEPTED, 7/7, score 85.170812. NEW BEST (was 85.0).

## Change
keep_for case 5 (40k<V<=100k): 0.22 -> 0.21 (78% -> 79%). One line. Everything else == v20.

## Walls now (judge-confirmed, all SSIM)
case2 93% | case3 64% (8 methods pinned) | case4 82% | case5 79% (80% FAILED) | case6 97% | case7 96%.
score = (93+64+82+79+97+96)/6 = 85.17.

## Established this session (what does NOT work, judge-confirmed)
case 3 pinned at exactly 64% across 8 greedy edge-collapse variants: free-QEM, area-weighted,
GH-normal quadric, silhouette-lock, anti-sliver, Delaunay edge-flips, AND the correct nonlinear
flat-shaded normal cost (approach-c). Degeneracy ruled out (free-QEM faces healthy, min area
~1e-5 even at 96%). => the medium walls (case 3,4) are SSIM-fundamental for edge-collapse;
reshuffling collapses by ANY geometric cost cannot recover the ~0.005 FinalSSIM needed.

## Next (the real swing)
All 8 dead methods are metric-BLIND (optimize geometry, never look at a rendered image).
Building IMAGE-DRIVEN: rasterize the original's 6 views once, per-face screen importance
(silhouette + normal/depth gradient pixels), weight the collapse cost by it -> preserve what
the cameras actually see. Only lever that attacks the metric-blindness. Cheap nudges tapped (~85).
