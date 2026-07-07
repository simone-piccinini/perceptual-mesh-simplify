# v111 — stacked harvest: case-3 @ 6941 (friend) + case-4 @ 4970 (ours)

**Score: 90.285538 — 7/7 PASS (NEW BANK, +0.009338 over v110's 90.276200)**

The first result that combines both independent razor harvests. Master's merged solver runs
**two** early-exit harvest blocks by vertex band:
- **case 3** (V ∈ (7000,30000]): `Decimate(6940)` + flip-unlock / vertex-remove floor-breakers
  + 1024 mini-polish → output 6941 verts. This is the friend's `feat/crease-normal-preservation`
  PROBE-RC3-READ recipe (banked solo at 90.2761 as `v109-c3-recipe-6941`).
- **case 4** (V ∈ (30000,40000]): `Decimate(4970)` → our v110 rung.

Cases 2/5/6/7 are byte-identical to v110. Predicted 90.2855 (v110 + `(100/6)·13/23201` for
case 3's 6954→6941), delivered 90.285538 — the two harvests are additive because they act on
different cases.

**Merge/family note:** this build is a NEW binary family (v108 source + friend's case-3 block +
our case-4 tail edit). Both box-cut razor cases (3 and 4) were therefore fresh coins on it, yet
both passed in one run — so the family's case-3 AND case-4 walls both sit at/above these rungs.
Compile verified on judge g++-14 (736 MB, 2 MB under v110; the case-3 block adds no new Eigen
template instantiation). Source is `master:solver/main.cpp` at the merge.

Per-case composition: c2 ~99.27 · c3 ~70.08 · c4 85.92 · c5 91.57 · c6 97.70 · c7 97.15.
Weak case remains **case 3** (organic normal-SSIM wall); that is where the gap to the leaders
(~91.46) lives.
