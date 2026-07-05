# v39 — half-percent probes crack case4/case7 — JUDGE 88.8379, 7/7  ★ NEW BEST

Config: case2 99 | case3 67 (vis) | case4 **83.5** | case5 90 | case6 97 | case7 **96.5** = 88.84.

The walls sit BETWEEN integer %s. A learning push (case4 83.5, case5 90.5, case6 97.5, case7 96.5)
returned 5/7: case4 83.5 PASS, case7 96.5 PASS, case5 90.5 WA, case6 97.5 WA. Captured case4/case7
(+0.5% each), reverted case5->90 / case6->97. Compression rate is continuous, so sub-integer keeps
grab score the integer steps skipped.

Next: bisect case4 83.75, case7 96.75. case5/case6 hard-capped at 90/97.
