# v46 — case4 stack safety probe — JUDGE 89.487009, 7/7 (unchanged, by design)

Config: identical keeps to v45; case4 now runs VSA-lite + nplace + visibility culling +
projected-area weighting at its CONFIRMED keep 0.1605. Cases 2,3,5,6,7 byte-identical to v45.

## Purpose and result
Isolated method-safety probe: does the modern stack pass on the REAL case4 mesh at the
known-pass compression? YES — 7/7, same score. This de-confounds the old VSA-84.25 WA
(real fail at a *pushed* keep, not a method failure; score arithmetic in ATTEMPT_LOG 2026-07-02).

Local (proxy35k, matched keep 0.1605): base 0.8613 → +VSA+nplace 0.8657 → +vis 0.8689 →
+projw 0.8697. Every view improved.

## Also judge-confirmed by this submission
`#include "Eigen/Sparse"` compiles on the judge (Laplacian-preconditioner code, env-gated off).

## Next
v47: case4 keep 0.1590 (84.10%) + case3 keep 0.305 (69.5%) combined — all four verdict
outcomes distinguishable from the score alone.
