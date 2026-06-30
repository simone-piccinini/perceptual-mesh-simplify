# v36 — inverse-rendering vertex optimizer breaks case3 — JUDGE 88.33810, 7/7  ★ NEW BEST

Config: case2 99 | case3 **66** (QEM + optimizer) | case4 82 | case5 90 | case6 97 | case7 96 = 88.34.
**case3 moved past 65% for the FIRST time this session.** 16 prior methods (every cost tweak,
Pivot-A grayscale/per-channel, res160/320, max-steering, depth, subset, meshopt) all WA'd at 66%.

## What the method is
After QEM decimation to 66%, run gradient ascent on the OUTPUT vertex positions to directly
maximize the real rendered normal-SSIM:
- C++ renderer + normal-SSIM verified bit-exact vs the Python oracle @1024 (0.801655 = 0.801655).
- Analytic gradient dSSIM/d(vertex) (SSIM-as-box-filters -> per-face-normal -> per-vertex
  Jacobian) verified vs finite-difference (ratio 1.000 every axis).
- Monotonic accept (keep a move only if real SSIM rises), displacement-capped at 2% AABB
  (Hausdorff), nondegenerate-guarded, HARD wall-clock time-boxed (16s) so it can never TLE.
- Proxy: normalSSIM 0.8017 -> 0.8080 @1024; passing-65% level is 0.8061, so optimized-66%
  (0.8080) scores ABOVE passing-65% -> crosses the wall. Confirmed on the real mesh: 7/7.

## WHY it worked (what I think — the honest reasoning)
1. **It optimizes the ACTUAL metric, not a proxy.** Every earlier method minimized a geometric
   surrogate (QEM plane distance, contrast deficit) and *hoped* it tracked SSIM. There's always a
   proxy gap. This computes the true rendered SSIM and its gradient and climbs it directly — no gap.
2. **It uses a degree of freedom decimation leaves on the table: vertex POSITION at fixed
   topology.** Decimation picks which vertices survive and drops them at the QEM-optimal
   (minimum geometric error) spot. But the geometric optimum is NOT the SSIM optimum. The
   optimizer slides those same vertices to positions that are geometrically "worse" yet make the
   coarse faces' normals match the original normal field better. Two different optima; nobody had
   optimized the second one.
3. **The loose vertex-to-vertex Hausdorff makes the moves nearly free.** Because the judge measures
   Hausdorff vertex-to-vertex (not surface), sliding vertices up to 2% of the diagonal costs almost
   no Hausdorff (stayed ~2%, limit 5%). So there's real room to move for SSIM. This is the lever the
   problem's own metric definition hands us, and it's why repositioning is cheap.
4. **Verified + monotonic = reliable.** Bit-exact SSIM/gradient and accept-only-if-better mean it
   can only help; it crossed on the real mesh because the proxy faithfully predicted the metric.

## Why the gain is only +1% (not "a lot" — yet)
The optimizer repositions a FIXED set of faces. It extracts the maximum SSIM from the faces 66%
gives (+0.006 normalSSIM = ~+1% compression at the wall), but it cannot CREATE faces. case3's
detail genuinely needs many faces; a coarse face holds one normal. So position-only optimization
tops out ~+1-2%. The next jump needs the TOPOLOGY half — SSIM-driven edge flips/splits that change
WHICH faces exist, not just where their vertices sit. That's the next build.

## Next
- Push case3 67% (bump optimizer to higher render res for more margin; check memory/timing).
- Then topology moves (edge flip/split scored by the same verified SSIM) for the real climb.
