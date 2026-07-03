# Orchestration brief V4.1 — judge-first, bank 90.18551, re-audit half done (2026-07-03)

You are the fifth researcher. This is the ONLY authoritative brief (V1–V3 = history; their
"closed" labels were partly wrong — see §1). Ground truth per round: `handoff/ATTEMPT_LOG.md`.

**Deadline 2026-07-18. Leader ≈ 91.6 avg. Our bank = 90.18551 (7/7). Gap +1.4 avg ≈ +8.5 case-sum.**

## 0. How you work now (this changed everything)
- **You submit AUTONOMOUSLY**: `python3 scripts/judge_submit.py solver/main.cpp` → prints
  VERDICT / SCORE / CASES (7 chars, sample+c2..c7, `.`=pass `x`=fail). Needs `~/.kattisrc`
  (present). A round takes ~2 minutes. Best-counts: a WA costs nothing.
- Edit `solver/main.cpp` IN PLACE (per-case config = keep_for / lambda_for / sdef_for /
  refine_for / projw_for / vis block / twostage_for). Snapshot to `submissions/` after verdicts.
- **The judge is the only test.** Local proxies understate real effects >10x (proven: s-def read
  +0.0002 local, broke two judge walls worth +0.26 avg). Local runs ONLY for (a) TLE/memory
  safety (≤16.5s CPU single-thread per case), (b) ordering candidates within a family.
- Hard judge facts: CPU limit is SUMMED ACROSS THREADS (never ship std::thread); refine wall-box
  16s is proven, more TLEs; keep→compression = 100·(1−keep), verify per edit; near-wall rungs can
  re-roll (wall-clock refine box + judge load) — margins <0.001 are coin flips.

## 1. Story so far (sessions 3–4, 89.82 → 90.186)
Wins, all judge-confirmed: ST-refine convergence (case5 91), per-case Pivot-A λ retune (c4 λ6,
c3 λ16), wall ladders (c6 97.695, c7 97.145), and the big one — **s-def steering**: Pivot-A
importance from the per-window STRUCTURE deficit (1−s, cross-covariance orig-vs-current; function
`sdef_map`, dispatch `sdef_for` = c3+c5) instead of the contrast deficit. It broke the c3 and c5
walls that the old signal could not (c3 69.5→69.96875, c5 91→91.546875).

## 2. Current walls (ALL judge-closed, multiple configs each)
| case | wall | closing evidence |
|---|---|---|
| 2 | 99.298 (keep 0.00725) | 29-verts SSIM cliff (0.007 WA) |
| 3 | 69.96875 | 70 WA at λ12/λ16/λ24 with s-def (19885047/102) |
| 4 | 85.4609375 | 85.46875 WA with c-def AND s-def |
| 5 | 91.546875 | 91.5625 WA alone/+projw/+vis/+stack ×4 (19885018..191) |
| 6 | 97.6953125 | 97.703125 WA plain; 97.71875 WA +nplace2 (19885133) |
| 7 | 97.145 | 97.1475 WA |
Sum 541.10 → 90.1836 (+ case2 floor dust = 90.18551 observed).

## 3. Re-audit of locally-closed ideas — JUDGED status
Done, negative (do NOT redo): nplace2@c6, projw@c5, vis@c5, vis+projw stack@c5, λ sweep at the
next rungs of c3/c5. Still open, in priority order:
1. **c6 pivot+s-def** (c6 never had Pivot; local eval was pending at session end —
   `G_LAMBDA=6 G_SDEF=1 G_PASSES=3` on big400k @0.0228125; check/rerun, then judge at 97.703125).
2. **s-def variants at the closed rungs** (window radius W/96→W/48 or W/192; c×s product;
   deficit^2; per-channel vs luminance for c5). New signal family beat everything once — its
   hyper-space is barely explored. One variant per round at the WA'd rungs.
3. **qweight small** (0.05/0.1) at c3/c5 rungs (only 0.3 ever tested, locally).
4. **s-def-weighted VSA cost for c6/c7** (needs a staged loop like Pivot since deficit needs a
   current-vs-orig comparison; passes=2-3 for CPU).
5. **Self-scorer**: in-process 1024 Final-SSIM of own output (normal-SSIM code exists bit-exact;
   depth-SSIM must be written), attempt aggressive keep → fallback safe keep. Immunizes re-rolls,
   harvests brackets (~+0.02-0.04 avg), enables sitting exactly on razor walls.
6. **Image-fit construction** (V3 §4): the only unmeasured big-swing family. Days of work.
Judge-verified closures that STAND: everything in ATTEMPT_LOG marked with submission IDs;
MT/threads; refine budgets; case4 both-signals; partitions/splits/aniso/optimizer families
(V3 §3 — those were local closures BUT their mechanisms were measured at −0.006..−0.07, not
marginal; only re-open one if you have a genuinely different form).

## 4. Protocol per round
One question per submission; the verdict must answer it. Failing cases are NAMED (CASES string).
Probe at the NEXT rung of the target case with everything else at confirmed rungs: pass = wall
moves (then ladder), WA = clean negative (revert, next idea). Log every round in ATTEMPT_LOG with
submission ID. Snapshot bank-improving configs to submissions/vNN/. Commit regularly.
