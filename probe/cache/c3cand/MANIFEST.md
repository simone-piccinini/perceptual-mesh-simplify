# Calibrated c3 instrument (R-iota c3 arm, 2026-07-14)

**WINNER: `dragon_n10.obj`** = Stanford dragon_vrip (437,645v) ->pymeshlab QEM-> 24,124v
-> noisegen correlated noise amp=0.001*diag rings=2 seed=7. Reproduce: probe/abc_tools/
(ply2solver.py + noisegen.py), sources on E:/organic/.

## Anchor match (RC3 self-score, judge-family -O2 build, G_C3T rungs)
| anchor | judge [K-read 20031760 + wall] | dragon_n10 | old c3band | armadillo-QEM |
|---|---|---|---|---|
| S2(6775) | 0.9145 | **0.91426** | ~0.89 (team-side) | 0.9992 |
| S2(6695) | 0.9135 | 0.91161 | — | 0.9992 |
| slope /v | 1.25e-5 | 1.67e-5 | — | ~0 (flat) |

## The finding that produced it
The judge's c3 difficulty is DETAIL DENSITY (a large detailed model decimated hard, like c6/c7),
NOT scan noise: armadillo-derived candidates (clustered 0.9997 / QEM 0.9992 / +noise-to-0.004
0.9986) can NEVER reproduce the 0.9135 anchor; dragon at 24:1 lands at 0.9277 and a 0.001 noise
nudge closes it to 0.9143. Synthetic de-bias of a clean-smooth base (3.C.1 as originally specced)
is INSUFFICIENT ALONE - source detail-dense, then nudge.

## Caveats (honest)
- dragon has small handles (judge c3 is genus-0) - believed second-order for SSIM difficulty.
- Level matched to ~2e-3 (= the c3 draw sigma); slope 1.3x steep. Good enough to START; the real
  acceptance is reproducing a judge-measured mechanism SIGN (rim+ / MPC-aniso~0) - PENDING:
  G_RIMK env-set segfaults this Windows build (latent bug, also c3band.obj segfaults even pristine
  - flag to team). Sign-check on the team's Mac or after the Windows bug is fixed.
- happy_qem (0.952, slope 1.06e-5) kept as the friendlier bracket; dragon_qem (no noise) as base.

## FALSIFIER RE-RUN on dragon_n10 (2026-07-14 night) — the verdict, re-priced
M0: base S2n@6610 0.869463 -> heavy-converge **0.873729 (+4.27e-3)**; 8 perturbed restarts ALL
worse (0.841-0.855) -> no better position basin. M1 swap search: +7.7e-5 (1/20 accepted) -> flat.

1. CONFIRMED on the faithful ruler: no better position BASIN; local set-SWAPS ~flat. The
   DIFF-BUILD kill's core holds for global-set local search.
2. RE-PRICED: the biased ruler understated position-POLISH headroom 4x (c3band +1.06e-3 ->
   faithful +4.27e-3 S2n ~= +2.1e-3 S2 ~= 170 c3-verts ~= +0.12 total). It is TLE-gated, not
   optimality-gated: the SAME mechanism class as c5-POLISH (judge-validated TODAY, +0.0077).
   => the top c3 move is a THROUGHPUT attack on mini_refine (make the polish affordable in the
   19s box: subsampled windows / low-res-then-project / prefix-sum-class speedup), NOT a new
   representation.
3. UNTESTED still: deficit-field ALLOCATION (20 greedy swaps is not an allocation test). Now
   cheap to test: 7s/run on this instrument.
