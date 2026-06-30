# v33 — case2 98% — JUDGE 88.004689, 7/7  ★ NEW BEST (broke 88)

Config: case2 **98** | case3 65 | case4 82 | case5 90 | case6 97 | case7 96 = 88.00.
Only change vs v32: keep_for(V<=7000) 0.03 -> 0.02.

## case2 run: 93->94->95->96->97->98 ALL HELD (+0.85 total)
The original "geometry-capped ~94" label was completely wrong. case2 is the most
compressible case by far. Bunny-proxy diagnostics @98%: 69v, manifold ok, Hausdorff
0.0871/0.1195 (73%), box SSIM delta 97->98 = -0.0308 (doubled vs -0.0159 prior = cliff
arriving). Real case2 mesh (<=5000v) larger than bunny (3485v) => judge keeps more verts
per %, so proxy underestimates survival (why 95/96/97/98 all held despite scary proxy SSIM).

## Next
- case2 99% (keep 0.01): last possible; Hausdorff likely binds (~35v on bunny). Free-roll.
- Then case2 done; case3 (65%) the only remaining lever.
