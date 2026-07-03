# Orchestration brief V4 — judge-first re-audit, bank 90.18551+ (2026-07-03)

You are the fifth researcher. Read this, then `handoff/ATTEMPT_LOG.md` (ground truth per round).
V3 documents the mechanism map; THIS document supersedes its "closed" labels — see §2.

**Deadline 2026-07-18. Leader ≈ 91.6. Bank ≥ 90.18551 (submission 19885042, 7/7).**

## 0. THE LESSON THAT DEFINES THIS SESSION (from the user, and he was right)
Local proxies UNDERSTATE real effects by >10x. The structure-term Pivot steering (s-def) read
**+0.0002 on the local proxy** — on the judge it **broke two walls that had been "CLOSED"**
(case3 69.875→69.96875+, case5 91→91.546875, worth +0.26 avg so far). Sessions 1–3 closed a
dozen idea families on local reads of ±0.001. Some of those closures are WRONG.

**Protocol now: the judge is the only test that counts.**
- Local runs ONLY for: (a) TLE/memory safety, (b) ORDERING candidates of a family (local ordering
  proved reliable even when magnitudes were wrong: λ unimodality, res/passes optima).
- Anything locally-marginal (|Δ| ≤ ~0.002) gets a judge round, not an archive entry.
- Submissions are FREE and AUTONOMOUS: `python3 scripts/judge_submit.py solver/main.cpp`
  (needs ~/.kattisrc; prints VERDICT/SCORE/CASES with per-case pass/fail: sample,c2..c7).
  Edit solver/main.cpp in place; snapshot to submissions/ after each verdict.

## 1. Current state
Walls (judge, with s-def steering on c3/c5): c2 99.298 | c3 69.96875 (70 WA'd at λ16 AND λ24) |
c4 85.4609375 (razor; WA'd with both signals) | c5 91.546875 (91.5625 WA'd at λ12 AND λ16) |
c6 97.6953125 | c7 97.145. Stack per case: see keep_for/lambda_for/sdef_for in solver/main.cpp.
Pending when session 3 ended: local λ-ordering sweeps (c3: 8/12/20 s-def @70; c5: 6/8/10 s-def
@91.5625) and case6 pivot+s-def λ6 passes3 @97.71875 — check scratchpad eval_* files or rerun.

## 2. RE-AUDIT LIST — "closed" only by LOCAL reads → each deserves ONE judge round
Ranked by (local read) × (plausibility). Test at the NEXT rung of the relevant case (a pass = wall
moves; a WA = clean negative). One family per case per submission; judge names failing cases.
1. **nplace2** (edge-blend placement candidates 0.25/0.75): local +0.0003 c4, **+0.0009 c6**.
   Never judged. Code exists only in v60 lineage — reimplement (5 lines in Evaluate's nplace block).
2. **projw beyond case4** (projected-screen-area VSA weighting): local c5 +0.0009, c3 0.0000,
   never judged on c5/c6/c7. Toggle projw_for.
3. **vis for case5** (visibility culling, 512-res): local +0.0003 "noise" — never judged at c5's
   current rungs. (vis>100k stays dead: −0.058 is not marginal.)
4. **G_PASSES/G_RES for Pivot on c3/c5** (local −0.0002/−0.0008 = marginal-negative but local!):
   one judge shot at passes=12 or res=240 on the c3 70 rung.
5. **qweight small** (0.05–0.1 blend; only 0.3 was swept locally at −0.008).
6. **s-def for case6/case7 ordering** (no Pivot loop there — but sdef could WEIGHT the VSA cost
   like projw does; new code, small).
7. **Aniso/curvature placement** (local −0.001..−0.0014): weakest case, but the s-def precedent
   says one judge round on c6 (its best local read) is honest.
8. **2-stage for case6** (local −0.001 at 200–400k): one judge shot at the 97.703125 rung.
Judge-verified closures that STAND (do not redo): all keep ladders/brackets in ATTEMPT_LOG;
λ∈{12,16,24} c3 / {12,16} c5 / 6 c4 at the listed rungs; MT/threads (CPU-billing, hard fact);
refine>16s budget (TLE'd); case2 29-verts (SSIM cliff); case4 85.46875 (both signals).

## 3. Beyond the re-audit (if the list exhausts)
- s-def variants: window radius (W/96 is arbitrary), luminance vs per-channel mix, c×s product
  steering, deficit^p powers. Cheap code, judge-probe each at the open rungs.
- Self-scorer (V3 §4): solver evaluates its own output at 1024 in-process, attempts aggressive
  keep, falls back if <0.90. Immunizes razor rungs (case5-style re-roll WAs) + harvests brackets.
- The out-of-family image-fit construction (V3 §4) remains the only unmeasured big swing.

## 4. Safety rails (unchanged, judge-proven)
Single-thread ONLY (CPU billed summed). ~16.5s local-CPU ceiling per case. No env vars reach the
judge — defaults in code decide. Keep→compression = 100·(1−keep): verify arithmetic every edit.
Best-counts protects the bank; a WA costs one round, nothing else.
