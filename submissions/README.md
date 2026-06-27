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
| [v1-keep-ratio](v1-keep-ratio/RESULT.md) | blind 50% vertex ratio | 6/7 | ~50 | **best real score**; sample fails on deviation |
| [v2-cost-budget](v2-cost-budget/RESULT.md) | quadric cost budget (frac 0.5) | 2/7 | 16.52 | sample fixed, over-compresses 5/6 (deviation) |
| [v3-coverage-guard](v3-coverage-guard/RESULT.md) | vertex-coverage Hausdorff guard | 2/7 | 16.54 | Hausdorff fixed, but SSIM now binds -> over-compresses 5/6 |

## Rolling back

To resubmit a past version: `cp submissions/vN-.../main.cpp solver/main.cpp`,
rebuild, submit.
