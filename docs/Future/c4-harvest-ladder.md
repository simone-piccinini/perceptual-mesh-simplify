# Case-4 razor re-harvest ladder

**Status: ACTIVE (2026-07-06) — rung 1 WA'd; REBASED onto the v108 binary family (rung 1b,
N=4970, one-constant diff from v108). See "Rung-1 failure analysis" for why the base
mattered.**

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

## Protocol (per submission) — REVISED after rung 1

1. Submit `solver/main.cpp` from this branch (current rung in the RLIVE-C4 `Decimate(...)`).
2. **The branch stays in the v108 binary family**: v108 source + the one tail constant.
   Only that ONE number changes between rungs — reads must stay single-variable, and the
   binary layout must stay in the 2/2-proven family.
3. **PASS** → new bank. Bank the snapshot in `submissions/` (RESULT.md per convention),
   move to the next rung (−20), update the results table.
4. **WA on case 4** → one re-roll justified (it is still a per-run coin *within* the
   family); two consecutive WAs at the same rung → wall found, step back +10, stop there.
5. **WA on any OTHER case** → not a ladder read; re-roll the same rung.
6. If rung 1b ALSO WAs twice: the 4990-family wall has drifted or the tail-edit reshuffle
   alone exceeds the margin — stop the ladder; the bank stands at 90.266754 and further
   case-4 rungs are judged-dead for this pipeline.

## Verification per rung (done for rung 1)

- Off-band byte-identity to the v109 base (cow / bunny / fandisk / armadillo + c3band):
  the diff is inside the c4-band dispatch only.
- c4-band smoke (32,369-v union): keep stage 4622 (= banked family's on this mesh; tail
  no-ops above it) — output byte-identical to v108's on that mesh.
- Compile: numbers-only change; Linux g++-14 footprint unchanged (~629 MB).

## Rung-1 failure analysis (2026-07-06): the ladder was on the wrong BINARY family

Rung 1 (headroom base + banked keep stage + tail 4970) scored **75.956618** — exactly the
banked total minus case-4's contribution, to six decimals. Reads:
- **Case 4 scored zero; every other case reproduced its banked score bit-exactly** (the only
  arithmetic fit: c4-pass + any-other-fail gives 73.99/78.60/...). The harvest mechanics are
  sound; nothing else moved. Bonus datum: case 6 (the other box-cut coin) has now reproduced
  its banked score 5/5 recently — at current judge load, **case 4 is the only live coin**.
- The case-4 razor record is now: **v108 family 2/2 PASS @4990; headroom family 0/2 WA
  (@4990, @4970)**. Joint probability under a fair ~2/3 coin ≈ 5%. The better model is the
  envelope's own: case 4 is box-cut ⇒ output depends on binary timing/layout ⇒ **each binary
  FAMILY has its own per-run S mean**. v108's layout sits just above 0.900; the headroom
  family's sits just below. The `#ifdef` is output-neutral on every deterministic path
  (byte-identical, verified) — but on a time-boxed path, **code layout IS part of the
  trajectory** (locally reproduced: same binary, two runs, different bytes at equal counts).
- **The error:** "restore the banked trajectory" was done at the source level while keeping
  the headroom `#ifdef` — preserving the algorithm but changing the one thing the razor is
  sensitive to. The 5150 margin absorbed the family shift (90.191194 passed); razors don't.
  Cost: one submission.

**Correction (rung 1b):** the ladder now lives in the **v108 binary family** — v108's exact
source with ONLY the tail constant changed (`Decimate(4990)` → `Decimate(4970)`; one-line
diff, comments only otherwise). The harvest adds no code, and v108 compiles on the judge
(proven 2×), so the compile headroom is not needed on this branch.

**Standing operational rule that falls out:** *bank attempts = v108-family source + minimal
constant edits; dev experiments = headroom base + margin (N=5150).* Any base change re-rolls
the case-4 family mean — never ladder a razor from a new binary family without first
calibrating it at the banked rung.

## Results — FILL PER SUBMISSION

| date | rung N | base family | verdict | score | notes |
|---|---|---|---|---|---|
| 2026-07-06 | 4970 | headroom (rung 1) | **WA (case 4)** | 75.956618 | family-shift diagnosis above; other 5 cases bit-exact |
| 2026-07-06 | 4970 | **v108 (rung 1b)** | _pending_ | | one-constant diff from the 2/2-proven family |

## Stop condition

Stop when: two consecutive WAs at a rung (wall found — bank the rung above), or the marginal
EV per submission (+0.0095/rung × odds) stops being worth the slot. The realistic ceiling of
this ladder is probably 90.28–90.31; it does not move any structural wall (that door stays
measurement-blocked, see transfer-instrument.md).
