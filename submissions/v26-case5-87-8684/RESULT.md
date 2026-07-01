# v26 — case5 87% — JUDGE 86.83757, 7/7  ★ NEW BEST

Config: case2 94 | case3 65 (PivA) | case4 82 | case5 **87** (PivA) | case6 97 | case7 96 = 86.84.
case5 Pivot-A streak: **79→87 (9 walls)**. Only change vs v25: case5 keep 0.14→0.13.

STRATEGY NOTE: case5 alone caps the score at ~88 (even at 100% it gives 528/6=88). To pass ~88
the OTHER cases must move. case3 (65%) is the prime target — Pivot-A only gave 64→65 there vs
+8 on case5, likely because case3's mesh is more uniformly detailed (less screen-space asymmetry
to exploit) and/or the 160² in-loop render is too coarse. Next big investment: per-case render
res, push case3 with res 256-384.
