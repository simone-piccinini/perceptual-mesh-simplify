# Submission v3 — evolved (cost-budget + deviation guard + normal term)

## Judge result (REGRESSION)
- 2 / 7 test cases passed — score ~16.
- Cases 1-2 (small) passed.
- Cases 3-6 FAILED — "Wrong Answer: too much geometric deviation" (pushed ~99%
  compression on local proxies, blew the 5% Hausdorff on the judge's detailed meshes).
- Case 7 (1.1M) FAILED — Time Limit Exceeded (> 21 s): the extra per-collapse work
  (2-ring re-queue, deviation guard, normal-attribute quadric) did not scale.

## Takeaway
Compressing more made 5 cases INVALID -> 0 points each. A valid 50% beats an invalid
99%. Reverted to the v1 keep-ratio baseline (simplifygeometry.cpp) which scored ~50 at 6/7.
