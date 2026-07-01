# v37 — optimizer extended to case4 — JUDGE 88.5048, 7/7  ★ NEW BEST

Config: case2 99 | case3 66 (opt) | case4 **83** (opt) | case5 90 | case6 97 | case7 96 = 88.50.

The inverse-rendering vertex optimizer is GENERAL, not a case3 one-off: enabling it on case4
(QEM 83% base) lifted normalSSIM +0.011 (0.7405 -> 0.7515), clearing case4's 82% passing level
(0.749). Bigger lift than case3 (+0.006) because case4 is mechanical -> flat regions give
well-defined per-face normal targets, exactly what the optimizer ascends toward. 84% fell short
(0.7436 < 0.749). refine_for now gates V in (7000,40000] = case3 + case4. Time-box held (~17s).

Next: extend to case5 (push 90->91 with Pivot-A base + optimizer), then case2/case6.
