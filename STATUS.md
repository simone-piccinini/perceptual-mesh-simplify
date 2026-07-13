# STATUS — where the project is NOW

*Single source of truth for CURRENT state. Overwrite this on every judge verdict. Everything
else (why/history/theory) lives elsewhere and is NOT repeated here. Read `CLAUDE.md` for HOW to
work; this file is WHERE we are.*

**Last updated: 2026-07-13 (evening). Bank 90.516445 [JUDGE 20038116] = c3@6670 (RIM-BUDGET +
diag-sil2) + c4@4920-14dir + c5@4172. RIM-BUDGET (silhouette-normal verts collapse later) is the
day's mechanism: banked c3 6690->6680->6670, each a fresh judge cross. c3 wall NOT yet hit (6670
passes clean 22s); the BOTTLENECK is now the c4@4920 box-cut coin (SSIM-WA at wall, ~25-35%/roll
day), which gates every c3 rung's bank. Ladder descending 6660, rotating draw families to catch
the c4 coin. DEAD today (measured): rim on c4/c5/c7 (CAD/compression regime), rim x curvature,
lambda!=16, coordinated-move class (segments/big-steps/anneal all -ve on exact evaluator),
c2@28 x3 mechanisms. Day: 90.4326 -> 90.516 (+0.083, ~5 banks).**

---

## NIGHT UPDATE 2026-07-12 (supersedes the "practical ceiling" verdict)

1. **FIN PROBE concluded** [JUDGE 20029777]: judge INCLUDES background px in SSIM windows — D1
   closed, oracle convention right, depth-saturation exploit dead (ENVELOPE §10.6).
2. **c5 TLE regression found+fixed**: cov-tail cost ~+2.9s judge = the 21.5-22.2s c5 TLEs in
   ladder 20031261-336. c5 now tail-OFF @4172 (wall 4165 + 7v insurance): PASSES 17.7s [20031760].
3. **TAIL THROUGHPUT UNLOCK (prefix-sum windows in collapse_delta_local, O(121)→O(1)/window):**
   c3 11.4→7.2s local; the 6.5s tail box went from SATURATED to CONVERGED (~2.3s). The judge's
   tail was doing ~HALF the local work (wall box × slower CPU) — the "6775/6760 SSIM-closed" walls
   were measured with a STARVED tail. cval lines bit-identical pre/post refactor.
4. **Deep tail now affordable**: pool 300→1000-1200, T 200→500-600, MPC-classic back ON
   (+1.3e-4 marginal). Local family: +3.9e-4 over the starved config at 6760.
5. **K-READ [JUDGE 20031760]: S2_judge(deep@6775) ≈ 0.9145 (V'≈7011, K≈59) = +1.0e-3 OVER the
   0.9135 threshold. c3@6775 PASSES.** Slope 1.25e-5/v ⇒ zero-crossing ≈ 6695. MPC-aniso (via-2
   V6): local marginal ~0 (+3.4e-5/−1.6e-5) — parked, env mpcm=2.
6. **BANK LADDER (12-13/07): 6740 → 6720 (90.480527) → 6710-MPC3 (90.48771, sub 20033638).**
   MP-CONTINUOUS (line-search placement, last-64) judge-VALIDATED: 6710 was sub-wall, it crossed.
   c3@6705 passes 90% (18/20 across 4 draw families) — bankable, blocked all night by c4.
   c3@6700 = WA x3 even with mpc3 (typed; needs > +2.5e-4). c2@27 WA (wall x2 families).
   c5@4150 wall typed (WA x2); c5@4165-LAZY judge-WA x2 (local +0.7e-3 did NOT transfer!).
   **c4@4920 pass-rate CRASHED overnight (1/34, was ~30-50%): night judge machines are slower →
   the time-boxed c4 refine starves (V6 knew: "ladder SOLO di giorno"). Day harvest relaunched.**
   NIGHT FALSIFICATIONS [LOCAL, exact scorer]: sliver-paint (zero-vertex chord bags: legal but
   sigma-xy punishes constant paint, family closed); c7/c6 tails (VSA mesh near-optimal at their
   rungs — NOT starvation walls; evaders' +1.9 is NOT big-case tails).

## BANK (best all-green, mein.cpp decimation track)

```
BANK      90.487710  (7/7)   [JUDGE 20033638, 2026-07-13 03:38] — c3@6710 DEEP TAIL + MP-CONTINUOUS
                               (prefix-sum collapse_delta_local, pool 800/T 500/box 6.5/mpcm=3) +
                               c4@4920 + c5@4172 (tail OFF) + c2/c6/c7 banked. Read calib:
                               S2_judge(deep@6775)=0.9145 [20031760], slope 1.25e-5/v.
                               c3@6705 = 90% pass (bankable, day harvest running); 6700 = WA x3 typed.
PRIOR     90.466160  (7/7)   [~20031805] c3@6740, first prefix-sum family bank.
PRIOR     90.432575  (7/7)   [~20026xxx ladder 07-11] c3@6790 + c4@4920 + c5@4165. The "6775/6760
                               closed walls" of that era = STARVED-TAIL artifacts (judge did ~half
                               the local tail work in the 6.5s wall box) — fixed by prefix-sum.
                               Prior bank 90.421800: c3@6805 via ROAD A (image-driven collapse
                               tail: lazy-greedy, burst16 K64 T100, collapse_delta_local validated ratio 1.0)
                               + c4@4920 + c5@4165. JUDGE-VALIDATED: 6805 never passed under QEM order.
                               Calibration: S2_judge(deep@6830)=0.9140 [K-read 20025436], threshold ~0.9135.
                               c3 anisotropy median 3.59 (curved-half 4.91) -> Road A ceiling is high.
                               OVERNIGHT (07-11): judge ladder from 6790 w/ lazy-300 (auto-bank). CEILING MEASURED
                               [LOCAL, no time box]: plain lazy holds the banked level to ~6700 (pool 600);
                               MULTI-PLACEMENT (SSIM-driven position, 4 candidates) moves the wall to ~6650
                               = payout +0.13 = ~90.55 IN THE CURVE. MP costs 4x eval (42s local) -> MORNING
                               PLAN: MP at COMMIT-time only (~16/round = marginal cost), then continuous
                               line-search placement. c4 tail = negative (CAD prefers QEM). c5 lazy = +2e-4
                               at 4165, dies below (headroom +0.003-0.007). 91 needs S2n 0.788@6000 = 10x
                               below the curve -> only via constructive anisotropic remesh (days, not nights).
LEADER    91.48      [JUDGE, leaderboard 2026-07-09]   #1 希望ヶ峰学園 CG研究会.  gap to #1 = 1.17
                                                       (top-3 cluster 91.46; we were rank 12)
```

### Per-case (compression %, banked N) — [JUDGE], as of ARCHITECT-REVIEW 2026-07-08
```
c2  99.32%  N=28        SSIM wall @28 (27 WA)            — closed
c3  70.26%  N=6900      FLIP REMESHER broke the 6921-6940 wall — THE prize, probe deeper (6880/6860)
c4  85.71%  N~5044      box-cut coin, genus-0             — hard
c5  91.55%  N=4212      deterministic wall               — closed 0/12
c6  97.69%  N~8705      box-cut razor                    — hard
c7  97.14%  N~28822     deterministic, no refine         — hard
```
**The gap to the leader lives almost entirely in case-3.** Every other case is behind a
measured-hard wall. Attack case-3.

---

## LIVE code

```
solver/main.cpp   (BANK track — decimation)   sha256 d1d7e156206f  = v112 REMESH-SPEED (115.2 KiB)
                  = c3-det/c4-det/c7-SPEED base + INCREMENTAL FLIP REMESHER on the final c3 mesh
                  (flip_delta_local validated ratio~1.0; 2-ring-independent flips, no verify render)
                  + refine SPEED PASS (orig-stat cache + crop-restricted fills, −23% c3 CPU, gated
                  V≤100k so c6/c7 bit-identical). ACCEPTED 7/7 [JUDGE 20018842]: 90.314273.
                  Decode: only c3 moved (6940→6900, +0.1724 payout). The 6900 bare-mesh WA
                  (19935666) was an SSIM wall the FLIPS now cross; 19936152's 'x' was a TLE
                  (21.4s→19.3s). Snapshot: submissions/v112-remesh-speed-90314273/.
                  ⚠ CASETIME c3 19.3 / c5 19.4 / c7 19.9 — TLE-tight (margin 1.1–1.7s).
                  Prior: 38d98e8bd0b1 (c3-det+c4-det+c7-SPEED, 90.285538, sub 19934494; det-refine
                  c3 phase-B cap 16 + c4 cap 36, LOCK CONFIRMED 2 re-rolls bit-identical); earlier
                  bases: b940d1aa (c3-det), 32b9f515 (c4-det), bonifica ecbbe3c0b082, 68e22f048d07 (v111).
solver/main_v2.cpp (INDEPENDENT track — construction→carve)  all-green ~90.24 [JUDGE]
                  → best carve snapshot: solver/submissionv2/main_v2_90p24_sub19909317.cpp
                  ⚠ the banner inside main_v2.cpp still says 64.34 (construction era); the 90.24
                    carve state is the submissionv2 snapshot. Reconcile before editing main_v2.
```
`solver/main.cpp` is the ONLY file uploaded to the judge for the bank track.

---

## ACTIVE FRONT

**case-3** — lower its SSIM-structure wall. It is the only front with a large prize AND a
pipeline-relative wall (moves when the simplifier improves). See `docs/ROADS.md`.

## NEXT ACTIONS (ranked — full rationale in ARCHITECT-REVIEW.md §3/§7)

- **NEW 2026-07-10: c3 REMESH DESCENT — the live front.** v112 proved flips cross the SSIM wall
  (6900 passed where bare 6900 WA'd). Headroom untested: remesh box is only 1.1s (self-terminated
  at 72 flips locally), c3 margin 1.7s. Probe: (a) deeper N (6880, 6860 — deterministic c3 = one
  clean read each); (b) bigger remesh box / more rounds; (c) flip+re-polish alternation. Each -20
  verts ≈ +0.014. STOP at two consecutive deterministic WAs.

- ~~Bonifica main.cpp~~ **DONE r55, RE-BANKED 7/7 r56** (−19.3 KiB source, ~109 MB cc1plus reclaimed).
- **Road 3.B.1 Hoppe attribute-quadric placement → PARKED, NOT dead.** Built the full Vis'99 optimum;
  A/B was Δ≈0 on the *smooth (broken) proxy* and the judge c3 read was confounded by the box-cut
  re-roll (law 4). Per Process Law #2 (never DEAD on broken-instrument evidence): re-test on a
  transferring proxy once R-ι lands. `docs/ROADS.md` R-α.
- **Road 3.C.1 de-bias the proxy (R-θ) → ACTIVE, corrected.** Earlier "FALSIFIED" verdict RETRACTED
  (it was iter 2/10, white noise = refine-recoverable, on box-cut c3 = wrong case — the canonical
  Process-Law-#2 error). Corrected iter-3/4 on the deterministic c5 calibration target: synthetic
  coherent noise pushes R1 the WRONG way (+), but a **natural rougher armadillo (ab_orig, same c5
  model, 0.0302 roughness) flips R1 NEGATIVE = the judge's sign.** ⇒ "too-smooth proxy" hypothesis
  holds; synthetic noise retired; **the path is REAL rougher meshes (R-ι data-sourcing).** ROADS §3.
- **meshopt (LEGGIMI/) → not worth porting (R-μ); numbers SUSPECT.** Offline-eval scored below our
  VSA-lite on both proxies, BUT output non-manifold (driver missing lock-border flags) → confounded.
  Firm: not shippable (101 KiB + non-manifold). Soft: Hoppe (R-α) LOW-EV, **not dead-forever**. R-μ.
- ~~Graveyard re-screen on the ruler~~ **DONE**: R-ζ confirmed dead (selection maxed; our edge is
  placement); no wrongly-buried lever. R-ν densify/prune ruled VACUOUS (coplanar splits = 0 normal).
- ~~Deterministic refine c4~~ **DONE + SHIPPED + LOCKED** (sub 19934022/19934036, R-κ): c4 refine
  capped at 36 iters, Accepted 7/7 ×2 bit-identical. The session's judge-tested main.cpp diff.
- ~~Hoppe placement judge-tested~~ **DONE (R-α): no win** (sub 19934115 variant c3+c4 WA vs 19934130
  control 7/7). LOW-EV, de-prioritized.
- ~~c3 N-push on the deterministic base~~ **DONE: c3 WALL JUDGE-CONFIRMED** — 6900 (19935666) AND 6920
  (19935676) both deterministic-WA ⇒ wall 6921–6940, **no N-headroom**. 91.46 needs c3@~5300 (a
  24%-better MESH) = a breakthrough, NOT tuning. All measured levers maxed/dead; leader edge unexplained.
- **REALITY (2026-07-10):** the climb is measurement-bound, not idea-bound (CLAUDE.md closing line).
  Highest-value UNBLOCK = the SSIM-window judge question (#4 below): if the judge masks background in
  silhouette windows, the oracle is biased exactly where c3's deficit lives → hidden headroom the
  leader may exploit. HUMAN action. Everything else needs a genuinely-new mechanism (not yet conceived).
1. **DETERMINIZE c3 (extend R-κ) — THE PORTFOLIO UNLOCK.** c3 A/Bs are coin-dominated (c3 box-cut →
   ±0.001–0.002/draw, so single c3 reads can't resolve a lever). Cap the c3 1024 phase-B loop at a
   fixed iteration count (like c4's stock_pass cap) → c3 reads become clean/reproducible → EVERY c3
   lever (Hoppe re-test, σxy, nmetric=3) becomes judge-decidable in one submission. Razor case →
   read at a SAFE N (≥6980, above the 6941 wall), determinize the DEV/read base, keep bank on the coin.
2. **Then run the c3 PORTFOLIO as clean reads** (submissions free, batchable): σxy-direct ordering
   (nmetric=3 = analytic-SSIM/covariance, only ever killed locally −0.011 — judge-test it); Hoppe
   re-test cleanly; box-window covariance placement. Let the judge rule each.
3. **⚠ TLE RISK REALIZED:** c7 hit **21.3–21.4s** in both Hoppe binaries; bank c7 19.5–19.9s. A warm
   day WILL TLE. Verify per-case convergence; if c3/c6 box-cut, a THROUGHPUT pass (transfer-safe, §9.1)
   buys deeper refine = lower wall for free. Real bank-protection + prize lever.
4. **Send the SSIM-window judge question** — `docs/JUDGE-QUESTION.md`, ready. HUMAN action; free.
5. Out-of-family R-ξ (silhouette) DEMOTED: theory headwind (~90% deficit is INTERIOR not silhouette)
   + overlaps SIL/Pivot-A. Only if <1h to prototype+judge-test. `docs/ROADS.md`.

---

## Navigation (read in this order)
`STATUS.md` (this) → `CLAUDE.md` (how to work) → `docs/JUDGE-ENVELOPE.md` (judge facts) →
`docs/ROADS.md` (what to try) → `docs/THEORY.md` / `docs/WALL-MODEL.md` (the math). Code map:
`docs/SOLVER-INTERNALS.md` (main.cpp) · `docs/V2-CONSTRUCTION.md` (main_v2.cpp). History:
`handoff/ATTEMPT_LOG.md`. Strategy review (roads small/big/huge): `ARCHITECT-REVIEW.md` (root).

---

## LEADERBOARD snapshot — 2026-07-09 (reference only, to see where we stand)

*Kattis Problem B (100). We = **Proof By Intimidation, rank 12, 90.29, 432 tries**. Note our
try-count is LOW vs the field (top teams 800–6640) — consistent with measurement-bandwidth being
our bottleneck, not ideas (ARCHITECT-REVIEW §0.3). A `?` = a pending/queued judgement at snapshot.*

| # | team | score | tries | time |
|---|------|-------|-------|------|
| 1 | 希望ヶ峰学園 CG研究会 | 91.48 | 958 | 29038 |
| 2 | Time for the Moon Night | 91.46 | 826 | 23237 |
| 3 | SPBU-AMCP | 91.46 | 1899 | 30381 |
| 4 | Nuggie | 91.39 | 3865+1? | 24646 |
| 5 | Vamos, Argentina! | 91.23 | 499 | 23474 |
| 6 | turneja | 91.15 | 886 | 30402 |
| 7 | MeOwnHero | 91.12 | 324 | 28879 |
| 8 | TMNG | 90.90 | 159 | 29737 |
| 9 | Zazmuz | 90.85 | 6640 | 30122 |
| 10 | mulmutnab | 90.83 | 2002 | 8770 |
| 11 | q1w2e3r4 | 90.78 | 1469+1? | 30371 |
| **12** | **Proof By Intimidation (US)** | **90.29** | **432** | **27596** |
| 13 | miao | 90.18 | 3502 | 27935 |
| 14 | Y Ddraig Goch | 90.15 | 1083+1? | 30395 |
| 15 | Chrono | 90.12 | 1592 | 29305 |
| 16 | Loko | 89.89 | 954 | 27840 |
| 17 | no people | 89.84 | 346 | 28784 |
| 18 | Haumea | 89.66 | 877 | 28601 |
| 19 | err404 | 89.56 | 373 | 27599 |
| 20 | All in AI | 89.46 | 1597 | 25908 |
| 21 | CVmaxxing | 89.42 | 2055 | 28710 |
| 22 | Problem | 89.32 | 375 | 29410 |
| 23 | It's MyGO!!!!! | 89.15 | 374 | — |

**Read:** ~0.49 gap up to #11 (90.78), then a dense pack. Reaching ~90.9 (#8) would jump us ~4
places; the 91+ leaders (top 7) are a separate tier where case-3 must move (ARCHITECT-REVIEW §1).
