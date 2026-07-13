# NIGHT-91 CAMPAIGN — start 0713_2346, 1.42h, 12 subs

Bank at start **90.554824**. Submitting `solver/campaign.cpp`; `solver/mein.cpp` untouched.

**Best reachable so far: 90.567326**

## NEW BANKS
- **90.567326** — c7_push=0.0278 (sub 20039277)

## Per-family wall map
- **c6_push** (c6): WALL at 8600
- **c7_push** (c7): WALL at 0.0266 — best pass 0.0272
- **c3_det** (c3): WALL at 6600
- **c5_push** (c5): WALL at 4160 — best pass 4165

## Path-to-91 read
Reachable = start + sum(each family best-pass delta). Big-case walls that survive
plain+determinize+rim are TRUE SSIM walls. If the sum < 91, 91 needs a new representation
(construction), not tuning — and this map proves exactly how far tuning goes.