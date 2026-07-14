# NIGHT-91b — start 0714_1708, 2.75h, 24 subs

Bank at start **90.554824**. `solver/mein.cpp` untouched; experiments on `campaign.cpp`.

**Best all-green banked: 90.592194** (+0.03737)

## Current best rung per case (the combined config being banked)
- c3: 6610
- c4: 4923
- c5: 4140
- c6: 8680
- c7: 0.0271

## New banks
- **90.590349** (combined c5=4140 c7=0.0272 c6=8684, sub 20046662, 0.04h)
- **90.592194** (combined c5=4140 c7=0.0271 c6=8680, sub 20047219, 1.1h)

## Push fronts
- c7: deepest-pass 0.0271, next done, wa 0
- c5: deepest-pass 4140, next 4135, wa 3
- c6: deepest-pass 8680, next 8670, wa 3
- c4: deepest-pass 4923, next 4922, wa 1

## Path-to-91
Reachable = combined deepest-pass of every case. If < 91, the walls are
real SSIM limits (draws rotated, toxic filtered) and 91 needs a new representation, not tuning.