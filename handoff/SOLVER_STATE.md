# Solver state — the current operating point

*Authoritative per-case dashboard. Regenerate the numbers from
[`probe/wall_model.json`](../probe/wall_model.json), which the probing harness updates on
every submission. Narrative history lives in [`ATTEMPT_LOG.md`](ATTEMPT_LOG.md); the raw
per-submission log is [`submissions.jsonl`](submissions.jsonl).*

**Standing: `90.285538`, all seven cases passing.** This is a *best-counts* figure — the
judge keeps the best result per case across all submissions, so it sits marginally above
the best single run (90.276093, id 19898599). Base binary:
[`submissions/v111-stack-c3-6941-c4-4970-90285538/main.cpp`](../submissions/v111-stack-c3-6941-c4-4970-90285538/main.cpp).

## Per-case walls — all six pinned

`N` is the lowest vertex count the judge has accepted. "Wall" is the bracket the probing
campaign established; below it, the case fails `FinalSSIM ≥ 0.90`.

| case | mesh | V | N | compression | wall | regime |
|---|---|---|---|---|---|---|
| 2 | tiny | 4,098 | 30 | 99.27% | ~99.32% WA'd — at the topology floor | not patchable |
| **3** | **organic** | 23,201 | **6,941** | **70.08%** | (6900, 6941] | box-cut coin |
| 4 | CAD | 35,292 | 4,970 | 85.92% | (4960, 4970] | box-cut coin |
| 5 | organic | 49,987 | 4,212 | 91.57% | ladder 0/12 below | ~deterministic |
| 6 | large | 377,084 | 8,684 | 97.70% | 6000/6500 WA'd | box-cut, stable |
| 7 | huge | 1,009,118 | 28,800 | 97.15% | (28800, 28822] | deterministic |

Mean of the six = 90.2809. **There is no vertex left to shave that is not a sub-coin
razor** — see [`docs/WALL-MODEL.md`](../docs/WALL-MODEL.md) for the mechanics and
[`docs/Future/STRUCTURAL-ROADMAP.md`](../docs/Future/STRUCTURAL-ROADMAP.md) for what a
structural move would have to buy.

## The deficit, quantified

Five cases are near-maxed; the gap is Case 3 at 70% against 86–99% elsewhere. Holding the
other five fixed:

| goal | case-3 compression needed | case-3 N | vs today's 6,941 |
|---|---|---|---|
| mean > 91.0 | 74.40% | ~5,940 | **−14%** |
| ~91.46 | 77.16% | ~5,300 | **−24%** |

Case 5 is the same organic regime, so any mechanism that lowers the organic wall helps
both. Diagnosis of why Case 3 is stuck:
[`docs/postmortems/case3-intrinsic-wall.md`](../docs/postmortems/case3-intrinsic-wall.md).

## Standing rules

These were each learned from a judge failure. Violating one has cost the project a
submission before.

- **Never ship `std::thread`.** The judge bills cumulative CPU across threads; v60/v63 TLE'd
  at `nthreads ×` the CPU bill. Single-threaded time boxes only.
- **`solver/main.cpp` is the only file submitted.** Snapshot it into `submissions/vN-.../`
  after every verdict; never edit a snapshot after the fact.
- **The judge names failing cases and distinguishes WA from TLE.** Classify every failure —
  WA is a quality wall, TLE is a time wall, and the remedies are opposite.
- **Position-space gains measured below 1024² are anti-signals.** They transfer at roughly
  −0.5× and invert sign; all registration work runs at judge resolution.
  ([measured](../experiments/kern-registration-descent/NOTES.md))
- **Near a wall, each new binary is a fresh draw.** The judge is deterministic given the
  binary, but any real code change re-rolls floating-point ordering (σ ≈ 0.0002–0.0003
  SSIM). Walls are distributions, not facts.
- **No descent on local evidence alone.** The local oracle over-rewards position-space
  gains; three transfer instruments were falsified against ground truth.

## Environment

- **Build:** `g++ -O2 -std=c++17 -I<eigen> solver/main.cpp`. Eigen is provided by the judge.
- **Budget:** ~21 s CPU per case, single-threaded.
- **Scoring:** pass/fail per case, best-counts across submissions, no rejudging — a failed
  submission is free forever.
- **Local evaluator:** [`src/imc_eval/`](../src/imc_eval/README.md) reproduces the judge's
  arithmetic at 1024². The *input meshes* are the only proxies; their fidelity varies by
  case and is documented per case in the attempt log.
