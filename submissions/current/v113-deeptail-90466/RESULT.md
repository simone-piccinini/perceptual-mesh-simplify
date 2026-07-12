# v113 DEEP TAIL — 90.466160 (7/7), sub ~20031805, 2026-07-12 night

**Verdict:** Accepted 7/7, SCORE 90.46616, SUM6 542.796960. NEW BANK (+0.033585 over 90.432575).

**Config:** c3@6740 (lazy image-driven tail: pool 800, T 500, box 6.5, MPC-classic on, kread 0)
+ c4@4920 (banked path) + c5@4172 (tail OFF — cov-tail TLE fix; wall 4165 + 7v insurance)
+ c2/c6/c7 banked.

**What changed (the unlock):** 2D prefix-sum windows in `collapse_delta_local` (O(121)→O(1) per
window). The 6.5s wall-clock tail box went from SATURATED to CONVERGED (c3 11.4→7.2s local): the
judge, at ~2x slower CPU, had been doing ~HALF the tail work — the "6775/6760 read-typed walls"
were starvation artifacts. Deep tail (pool 300→800-1200, T 200→500-600, MPC back on) = +3.9e-4
local; K-read 20031760 measured S2_judge(deep@6775)=0.9145 (+1.0e-3 over threshold).

**Margins:** c3 rung margin est +4e-4 at 6740 (slope 1.25e-5/v, zero-crossing ~6695).
⚠ c3 CASETIME 21.9s (hot; ladder toxic-filter handles slow draws). c5 17.8s ✓.
