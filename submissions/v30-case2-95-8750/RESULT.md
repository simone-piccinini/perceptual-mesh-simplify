# v30 — case2 95% — JUDGE 87.504444, 7/7  ★ NEW BEST

Config: case2 **95** | case3 65 | case4 82 | case5 90 | case6 97 | case7 96 = 87.50.
Only change vs v29: keep_for(V<=7000) 0.06 -> 0.05.

## What moved
case2 (small mesh, V<=5000) was assumed "geometry-capped ~94". It is not: 93->94->95
all held. Each +1% = +0.17 mean. Oracle box delta 94->95 was only -0.0096 (no cliff),
and the judge's case2 mesh (up to 5000v) is LARGER than the bunny proxy (3485v) so 95%
there keeps ~250v vs bunny's 174v -> easier on the real mesh. Free-roll paid off.

## Caps confirmed this session (do not re-grind)
- case4 82% INTRINSIC: free-QEM, image-driven, AND per-channel Pivot-A all WA @83%.
- case3 65%: per-channel did not break 66% (organic anisotropy hypothesis dead here).
- case5 90%: per-channel CRACKED 79->90 (the session's big win); 91 WA'd.
- case6 97% (98 WA'd free-QEM+Pivot-A), case7 96% (97 TLE). Large front dead both sides.

## Next
- case2 96% (keep 0.04): another free-roll, same logic.
- case3 rebuild: only path to 89+, low confidence (anti-sliver already failed triangle-quality axis).
