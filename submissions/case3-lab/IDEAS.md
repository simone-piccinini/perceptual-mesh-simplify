# case-3 IDEAS — ranked by expected value × confidence

Legend: [HARVEST] pushes N down at fixed mechanism; [WALL] lowers the wall via a better mechanism.
Every WALL idea MUST be A/B'd via an S-read pair on the judge (not local — proxies don't transfer).

## NOW (high confidence, automatable)
1. **[HARVEST] S-read descent 6941 -> ~6700.** Friend's read S2=0.9135@6940 => ~240 verts of
   headroom (~+0.17 total). Plan: read @6800, decode S2, anchor with one bank-attempt pass/fail,
   then jump N to the anchored 0.900 crossing and bank. ~3-4 submissions. Do this first.

## WALL-LOWERING mechanisms (the real gap to 85%; each needs an S-read A/B)
2. **Appearance quadric with placement (Hoppe, Vis'99).** Our VSA-lite only ORDERS collapses by
   normal distortion; the QEM PLACEMENT is still position-quadric. Hoppe's normal-attribute quadric
   fixes the placed vertex to minimize normal error too. Could render a better normal map at N=6941.
   Test: v111 vs +Hoppe-placement, two reads @6941, compare S2. Constants/small — risk of family
   re-roll (calibrate).
3. **Joint decimate<->refine (Road B item 1), STRONGER than R1.** R1 (mid-decimation refine bursts)
   was judge-NEGATIVE (proxies over-rewarded it). But a FULL re-decimate-after-refine cycle (refine
   to SSIM-optimal positions, then re-run VSA ordering on THAT geometry) explores a different basin.
   Test via S-read, not local.
4. **Differentiable co-optimization during reduction (Road B item 2).** The heavy build: interleave
   the analytic SSIM gradient (refine_score_grad exists) INTO the collapse loop. §9.1 warns
   position-space gains transfer poorly — but this is co-opt DURING, not refine-after. High effort.
5. **Metric-exploit angle (user's instinct).** Judge sees only 6 axial views; faces are Hausdorff-
   unconstrained (v2v). Look for a case-3 normal-map structure the current pipeline leaves on the
   table that a targeted mechanism could match with fewer faces. Speculative; frame a concrete test.

## Notes
- The S-read is a RELATIVE instrument (~+0.005 optimistic). Anchor per family before trusting margins.
- case 3 is a box-cut coin at the razor: a WA is a draw, not proof. Two WAs at a rung = wall.
- Any change beyond a constant = new binary family => re-rolls the box-cut mean; calibrate or carry margin.
