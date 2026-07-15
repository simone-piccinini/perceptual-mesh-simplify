# NIGHT-91b — start 0714_1708, 6.89h, 49 subs

Bank at start **90.554824**. `solver/mein.cpp` untouched; experiments on `campaign.cpp`.

**Best all-green banked: 90.594083** (+0.039259)

## Current best rung per case (the combined config being banked)
- c3: 6610
- c4: 4921
- c5: 4140
- c6: 8680
- c7: 0.0271

## New banks
- **90.590349** (combined c5=4140 c7=0.0272 c6=8684, sub 20046662, 0.04h)
- **90.592194** (combined c5=4140 c7=0.0271 c6=8680, sub 20047219, 1.1h)
- **90.593139** (combined c5=4140 c7=0.0271 c6=8680, sub 20048038, 2.86h)
- **90.594083** (combined c5=4140 c7=0.0271 c6=8680, sub 20048851, 6.18h)

## Push fronts
- c7: deepest-pass 0.0271, next done, wa 0
- c5: deepest-pass 4140, next 4135, wa 7
- c6: deepest-pass 8680, next 8670, wa 7
- c4: deepest-pass 4921, next 4920, wa 1

## Path-to-91
Reachable = combined deepest-pass of every case. If < 91, the walls are
real SSIM limits (draws rotated, toxic filtered) and 91 needs a new representation, not tuning.