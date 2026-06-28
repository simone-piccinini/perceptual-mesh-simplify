# Submission v7 — crease + normal preservation (algorithmic change)

First change to the COST function, not just keep. Two additive, manifold-safe
appearance protectors on top of the QEM:
- Crease preservation: sharp interior edges (face-normal dot < 0.7, ~45 deg) get a
  perpendicular-plane penalty holding their endpoints on the crease line -> silhouette
  and feature edges survive (what the flat-shaded normal-map / depth SSIM look at).
- Normal-aware quadric (wn = 1.0): penalizes collapses that swing face normals.

Both are ADDITIVE (only protect, never free a collapse), so they cannot regress the
proven keep-0.36 ordering; they change WHICH vertices survive at a given keep.

## Operating point
`kOpKeep = 0.32` (~68%), `kOpNormalWeight = 1.0`, `kCreaseWeight = 1.0`,
`kOpTargetError = 0.0`. Judge runs no argv.

## The experiment
Plain QEM at keep 0.32 scored 6/7 (56.67) — case 3 dropped. Same keep here, but the
cost now preserves features/normals. If case 3 recovers -> 7/7 (~68) and the cost
upgrade is proven to help; if still 6/7, features aren't case 3's bottleneck.

## Local checks (validity, not score)
All meshes manifold, Hausdorff under budget, scales (1.05M in ~2.7s / ~700MB).
Local SSIM on proxies is unchanged (~0) because they are smooth/trivial and not
representative of the judge's meshes. The judge is the test.

## Judge result
PENDING — record score + which of the 7 cases pass (especially case 3).
