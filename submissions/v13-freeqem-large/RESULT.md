# v13 — free-QEM placement on the large cases (replacing subset)

Change line: route large meshes (V>100k) through the free-QEM keep path instead of
the subset-adaptive path. Free-QEM picks the QEM-optimal position -> rounder triangles
(better face normals) than subset's endpoint slivers. Same per-case keep for 2-5.

## Judge results (this experiment line)
- free-QEM keep 0.05 (95%) -> **7/7, 83.170642** (sub 19860363). Same score as the
  subset 95% (v12) -> CONFIRMS free-QEM placement is GEOMETRY-LEGAL on cases 6 AND 7.
- free-QEM keep 0.03 (97%) -> **6/7, 67.670641** (sub 19860428). Dots ✓✓✓✓✓✓✗.
  - case 6 (<=400k) PASSED at 97%  -> +2 over its 95%.
  - case 7 (1.1M)   WRONG ANSWER at 97%.
  score = (90+64+80+75+97+0)/6 = 67.67.

## What works
- Free-QEM placement on large is valid up to 95% on BOTH 6,7 (banked).
- Case 6 (400k) tolerates 97%. Its free-QEM limit is >=97%.

## What does NOT
- Case 7 (1.1M) fails at 97% (WA = hard constraint; judge gives no reason).

## Why (hypothesis — judge only says "Wrong Answer")
Most likely **Hausdorff**: free-QEM moves the merged vertex to the QEM optimum, which
can drift OFF the original surface. At 97% the surviving triangles are large enough
that on the 1.1M mesh's geometry the drift exceeds 5% diagonal. Subset placement never
drifts (vertices stay original) — that's why subset was Hausdorff-safe; free-QEM trades
that safety for better normals. NOT time (synthetic 1M at keep 0.03 = 4.4s, far < 21s).
Case 6 vs 7 differ because their meshes differ (1.1M likely more curvature/feature).

## Next
- Immediate fix: SPLIT case 6 (keep 0.03/97%, confirmed) from case 7 (keep 0.05/95%,
  confirmed) at V=400k -> recovers 7/7 and banks case 6's +2.  -> ~83.5.
- Then probe case 7 at 96% (keep 0.04).
- Bigger: free-QEM past 95% reintroduces Hausdorff drift -> Probabilistic Quadrics
  (sigma-regularized, robust positions) should drift LESS -> the way to push the
  large cases higher without WA.
