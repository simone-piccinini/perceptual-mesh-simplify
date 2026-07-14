# NIGHT-91b — start 0714_1708, 0.04h, 1 subs

Bank at start **90.554824**. `solver/mein.cpp` untouched; experiments on `campaign.cpp`.

**Best all-green banked: 90.590349** (+0.035525)

## Current best rung per case (the combined config being banked)
- c3: 6610
- c4: 4925
- c5: 4140
- c6: 8684
- c7: 0.0272

## New banks
- **90.590349** (combined c5=4140 c7=0.0272 c6=8684, sub 20046662, 0.04h)

## Push fronts
- c7: deepest-pass 0.0272, next 0.0271, wa 0
- c5: deepest-pass 4140, next 4135, wa 0
- c6: deepest-pass 8684, next 8680, wa 0
- c4: deepest-pass 4925, next 4924, wa 0

## Path-to-91
Reachable = combined deepest-pass of every case. If < 91, the walls are
real SSIM limits (draws rotated, toxic filtered) and 91 needs a new representation, not tuning.