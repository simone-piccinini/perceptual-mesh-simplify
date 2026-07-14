# NIGHT-91b — start 0714_0119, 8.68h, 97 subs

Bank at start **90.554824**. `solver/mein.cpp` untouched; experiments on `campaign.cpp`.

**Best all-green banked: 90.580319** (+0.025495)

## Current best rung per case (the combined config being banked)
- c3: 6610
- c4: 4915
- c5: 4163 — WALL below 4161
- c6: 8550
- c7: 0.026

## New banks
- **90.580319** (combined c5=4163 c7=0.0272 c6=8684, sub 20039589, 0.39h)

## Push fronts
- c7: deepest-pass 0.026, next done, wa 0
- c5: deepest-pass 4163, next 4161, wa 8, WALL 4161
- c6: deepest-pass 8550, next done, wa 0
- c4: deepest-pass 4915, next done, wa 0

## Path-to-91
Reachable = combined deepest-pass of every case. If < 91, the walls are
real SSIM limits (draws rotated, toxic filtered) and 91 needs a new representation, not tuning.