# Submission v6 — keep mode 0.32 (uniform, ~68%)

Small step down from the proven v4 (keep 0.36 -> 64 @ 7/7). Uniform keep degrades
gracefully, so this is low risk.

## Operating point
`kOpKeep = 0.32`, `kOpTargetError = 0.0`, `kOpNormalWeight = 0.0`. Judge runs no argv.

## Local validity (guarantees, not score)
All outputs manifold (bad_edges = 0), Hausdorff well under the 5% budget:
bunny 6.7%, cow 15.5%, fandisk 0.0% of budget. Sample stays valid (skip).
Compression 68% on every mesh.

## Judge result
PENDING — submit and record: score + which of the 7 cases pass.
Expected ~68 if all 7 stay >= SSIM 0.90; the binding unknown is SSIM on the
hidden meshes.
