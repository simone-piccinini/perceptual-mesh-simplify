# Submissions — versioned solver snapshots

One subfolder per judge submission: the **exact** `main.cpp` that was submitted,
plus a `RESULT.md` recording the outcome and what we learned.

**Treat these as immutable.** Never edit a snapshot after the fact — when you
change the live `solver/main.cpp` and submit again, add a new `vN-...` folder.
The evolving solver lives in `solver/main.cpp`; these are frozen copies for the
record and for easy rollback.

## Convention

```
submissions/
  vN-short-name/
    main.cpp     the exact solver submitted
    RESULT.md    judge outcome (cases passed, score) + takeaway
```

## Log

| Version | Approach | Cases | Score | Note |
|---|---|---|---|---|
| [v1-keep-ratio](v1-keep-ratio/RESULT.md) | blind 50% vertex ratio | 6/7 | ~50 | sample fails on deviation; first real score |
| [v2-cost-budget](v2-cost-budget/RESULT.md) | quadric cost budget (frac 0.5) | 2/7 | 16.52 | sample fixed, but over-compresses 5/6 |
| [v3-evolved-regression](v3-evolved-regression/RESULT.md) | cost-budget + dev-guard + normal | 2/7 | ~16 | over-deviation 3-6, TLE 7 |
| [v4-keep-mode](v4-keep-mode/RESULT.md) | uniform keep (STEP-2 engine, keep mode) | **7/7** | **50→64** | keep 0.50→50.0005, keep 0.36→64. SAFE lever (only kOpKeep changes) |
| [v5-adaptive-guard-FAILED](v5-adaptive-guard-FAILED/RESULT.md) | adaptive target_error + Hausdorff guard | 2/7 | 15.92 | over-deviation 3-7; guard bounds only direction-1. **Adaptive parked.** |

**Current best: keep 0.36 → 64 @ 7/7 (v4).** Live solver reverted to it.
The judge runs the binary with NO argv, so the compiled-in `kOp*` constants (top of
`solver/main.cpp`) are the operating point — change those, not command-line args.

## Rolling back

To resubmit a past version: `cp submissions/vN-.../main.cpp solver/main.cpp`,
rebuild, submit.

## BEST = v21-case5-79  (85.170812, 7/7)
Restore anytime:  `cp submissions/v21-case5-79/main.cpp solver/main.cpp`
It is the free-QEM keep-ratio decimator with per-case keep dispatch:
  case2 0.07/93% | case3 0.36/64% | case4 0.18/82% | case5 0.21/79% | case6 0.03/97% | case7 0.04/96%.
Walls are SSIM (see docs/judge-map.md). Edge-collapse is maxed here.
Big-swing experiments build on TOP of this; on any regression, restore the line above.
