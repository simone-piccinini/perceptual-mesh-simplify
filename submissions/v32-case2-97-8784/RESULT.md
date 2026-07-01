# v32 — case2 97% — JUDGE 87.837941, 7/7  ★ NEW BEST

Config: case2 **97** | case3 65 | case4 82 | case5 90 | case6 97 | case7 96 = 87.84.
Only change vs v31: keep_for(V<=7000) 0.04 -> 0.03.

## case2 run so far
93->94->95->96->97 ALL HELD. Oracle box deltas: 94->95 -0.0096, 95->96 -0.0174,
96->97 -0.0159 (plateaued, NOT a cliff). Bunny-proxy Hausdorff climbing
0.030->0.049->0.0615 (limit 0.1195) - still half. Real case2 mesh (<=5000v) > bunny
(3485v), so judge keeps more verts per % than the proxy -> survival underestimated.

## Next
- case2 98% (keep 0.02): keep free-rolling until WA. Watch Hausdorff (could bind near 70v
  on bunny, but real mesh larger -> lower Hausdorff).
- case3 (65%) still the only big lever once case2 caps.
