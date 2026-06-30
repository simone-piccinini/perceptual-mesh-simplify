# v31 — case2 96% — JUDGE 87.671193, 7/7  ★ NEW BEST

Config: case2 **96** | case3 65 | case4 82 | case5 90 | case6 97 | case7 96 = 87.67.
Only change vs v30: keep_for(V<=7000) 0.05 -> 0.04.

## What moved
case2 keeps giving: 93->94->95->96 all held. The old "geometry-capped ~94" label was
wrong. Oracle box deltas are small but ACCELERATING (94->95 -0.0096, 95->96 -0.0174),
so a cliff is near. Real case2 mesh (<=5000v) is larger than the bunny proxy (3485v),
so each % keeps more verts on the judge than locally -> proxy underestimates survival.

## Next
- case2 97% (keep 0.03): last case2 free-roll; delta accelerating, odds lower, but still
  free (best-counts). If it WAs, case2 maxes at 96.
- After case2 is exhausted: only case3 (65% anchor) has real upside, low confidence.
