# NIGHT-91b — start 0714_1016, 4.83h, 42 subs

Bank at start **90.554824**. `solver/mein.cpp` untouched; experiments on `campaign.cpp`.

**Best all-green banked: 90.584998** (+0.030174)

## Current best rung per case (the combined config being banked)
- c3: 6610
- c4: 4921
- c5: 4163
- c6: 8680
- c7: 0.0271

## New banks
- **90.584998** (combined c5=4163 c7=0.0271 c6=8680, sub 20044366, 1.44h)

## Push fronts
- c7: deepest-pass 0.0271, next done, wa 0
- c5: deepest-pass 4163, next 4162, wa 6
- c6: deepest-pass 8680, next 8670, wa 6
- c4: deepest-pass 4921, next 4920, wa 2

## Path-to-91
Reachable = combined deepest-pass of every case. If < 91, the walls are
real SSIM limits (draws rotated, toxic filtered) and 91 needs a new representation, not tuning.