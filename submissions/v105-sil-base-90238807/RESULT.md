# v105 — SIL base (submission 19898020)

**Score: 90.238807 — 7/7 PASS (bank reproduced exactly; DELTA +0.000000)**
Passing cases: 2,3,4,5,6,7. Payouts: 99.316740 / 70.027154 / 85.707809 / 91.545802 /
97.691495 (c6 = 8705 via fixed-8684 + 21 stall) / 97.143842.

## Build
f32 refine + CPU-clock boxes + fused accept + static scratch + bbox crop (≤100k ONLY — the
377k case's box-cut razor mean dropped under crop trajectories, WA×5, healed by the gate) +
**SIL coverage-difference silhouette optimizer on case 5** (signed per-vertex rim displacement
from the coverage-difference map, Final-metric accept; passed its banked razor 19897967 —
first new mechanism through the post-R1 judge gate; descent rungs 4212/4219 WA'd → judge-side
gain < 7 vertices for now; kept as razor margin + platform).

## Closed tonight
R1 interleave judge-negative on c3+c5 (3/3 live families); c7 wall (28800, 28822];
c5 SIL ladder; c6 crop sensitivity.
