# NIGHT-91 CAMPAIGN — start 0713_2346, 0.04h, 1 subs

Bank at start **90.554824**. Submitting `solver/campaign.cpp`; `solver/mein.cpp` untouched.

**Best reachable so far: 90.554824**

## Per-family wall map
- **c6_push** (c6): active idx 0/12 (det)
- **c7_push** (c7): active idx 0/12 (plain)
- **c3_det** (c3): active idx 0/4 (det)
- **c5_push** (c5): active idx 0/4 (plain)

## Path-to-91 read
Reachable = start + sum(each family best-pass delta). Big-case walls that survive
plain+determinize+rim are TRUE SSIM walls. If the sum < 91, 91 needs a new representation
(construction), not tuning — and this map proves exactly how far tuning goes.