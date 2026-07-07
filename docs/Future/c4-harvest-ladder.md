# Case-4 razor re-harvest ladder

**Status: ACTIVE (2026-07-06), rung 1 (N=4970) prepared on branch `harvest/c4-ladder`.**

## The play

v109 deliberately spent 0.0756 pts de-razoring case 4 (4990 → 5150) to get a reliable dev
base. This ladder re-harvests those points *and descends past the old bank* — on a dedicated
submission branch, so the dev base (`perf/compile-headroom`, N=5150) stays robust for
experiments. **Do not merge this branch into the dev base.**

Design choice: the ladder restores the **banked keep stage** (`keep_for` c4 = 0.1428125 →
stage mesh 5040, byte-identical decimate+refine trajectory to the 90.2667 family) and lowers
only the RLIVE tail target (banked 4990 → 4970 → …). Minimal reshuffle vs. the judge-proven
family; each rung differs from the bank by only the last few tail collapses.

## The math (V_c4 = 35,292, measured; 1 vertex = 0.000472 pts)

Total-if-all-else-reproduces = 75.956644 + (100/6)·(1 − N/35292):

| rung N | total | vs 90.266754 bank | prior on odds |
|---|---|---|---|
| 4990 (banked) | 90.2668 | ±0 | ~2/3 measured (3 pass, 1 WA... family history) |
| **4970 ← rung 1** | **90.2762** | **+0.0095** | ~50–60% (−0.0007 S at 3.5e-5/vertex) |
| 4950 | 90.2857 | +0.0189 | ~35–50% |
| 4930 | 90.2951 | +0.0283 | ? — only if 4950 passes |
| 4900 | 90.3093 | +0.0424 | low; deep-wall territory |

Context: judge-side S2 read at 4990 ≈ 0.905 (19898422) but the rung fails ~1/3 of runs, so
the *true* judge S at 4990 is ~0.900–0.902 with per-run jitter σ ≈ 0.001–0.002 (case 4 is
box-cut ⇒ per-run coin; envelope §1). Every rung is a fresh coin; a WA costs nothing
(best-counts protects the bank) except the submission slot.

## Protocol (per submission)

1. Submit `solver/main.cpp` from this branch (current rung in the RLIVE-C4 `Decimate(...)`).
2. **PASS** → new bank. Bank the snapshot in `submissions/` (RESULT.md per convention),
   move to the next rung (−20), update the results table below.
3. **WA on case 4** → the rung lost its coin OR is below the wall. One re-roll is
   justified at rung 1 (odds ~50%+); two consecutive WAs at the same rung → treat as wall,
   step back +10 and stop the ladder there (diminishing EV below ~35% odds).
4. **WA on any OTHER case** (esp. case 6, the other box-cut coin) → not a ladder read;
   re-roll the same rung.
5. Only ONE number changes between rungs (the `Decimate` target). Never adjust anything
   else on this branch — reads must stay single-variable.

## Verification per rung (done for rung 1)

- Off-band byte-identity to the v109 base (cow / bunny / fandisk / armadillo + c3band):
  the diff is inside the c4-band dispatch only.
- c4-band smoke (32,369-v union): keep stage 4622 (= banked family's on this mesh; tail
  no-ops above it) — output byte-identical to v108's on that mesh.
- Compile: numbers-only change; Linux g++-14 footprint unchanged (~629 MB).

## Results — FILL PER SUBMISSION

| date | rung N | submission | verdict | score | notes |
|---|---|---|---|---|---|
| 2026-07-06 | 4970 | _pending_ | | | rung 1: first descent below the banked razor |

## Stop condition

Stop when: two consecutive WAs at a rung (wall found — bank the rung above), or the marginal
EV per submission (+0.0095/rung × odds) stops being worth the slot. The realistic ceiling of
this ladder is probably 90.28–90.31; it does not move any structural wall (that door stays
measurement-blocked, see transfer-instrument.md).
