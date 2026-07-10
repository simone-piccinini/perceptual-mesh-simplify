# STATUS — where the project is NOW

*Single source of truth for CURRENT state. Overwrite this on every judge verdict. Everything
else (why/history/theory) lives elsewhere and is NOT repeated here. Read `CLAUDE.md` for HOW to
work; this file is WHERE we are.*

**Last updated: 2026-07-10.**

---

## BANK (best all-green, main.cpp decimation track)

```
BANK      90.285538  (7/7)   [JUDGE] — VERIFIED on Kattis 2026-07-09 (team "Proof By Intimidation",
                               Accepted 90.285538, 7/7, C++). This is the authoritative bank.
                               (submissions.jsonl is only a partial ledger — no web-UI submits;
                               its last logged all-green was 90.252481. Kattis is the truth.)
LEADER    91.48      [JUDGE, leaderboard 2026-07-09]   #1 希望ヶ峰学園 CG研究会.  gap to #1 = 1.19
                                                       (top-3 cluster 91.46; we are rank 12)
```

### Per-case (compression %, banked N) — [JUDGE], as of ARCHITECT-REVIEW 2026-07-08
```
c2  99.32%  N=28        SSIM wall @28 (27 WA)            — closed
c3  70.08%  N=6941      SSIM-structure, MECHANISM-LIMITED — THE prize (1 pt c3 = 0.167 total)
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
solver/main.cpp   (BANK track — decimation)   sha256 32b9f515d2ce  = det-refine c4 (98.5 KiB)
                  = bonifica base + C3 DETERMINISTIC REFINE on c4 (stock_pass capped at 36 iters).
                  ACCEPTED 7/7 [JUDGE 19934022, 2026-07-10]: 90.285538, c4 V'=4970 (banked rung),
                  CASETIME c4 16.2s. c4 refine now deterministic by construction (cap, not the
                  wall-clock box, terminates) → kills the c4 box-cut coin. c2/c3/c5/c6/c7 byte-
                  identical to the bonifica base (maxit_for=1<<30 for all non-c4 bands; only c4's
                  input 35292 lands in 30k–40k). ⚠ c6/c7 CASETIME 19.2/19.9s = TLE-tight. c3/c6
                  still on the box-cut coin (left time-boxed this ship). LOCK CONFIRMED: 2 force
                  re-rolls (19934022, 19934036) BIT-IDENTICAL SUM6 541.713228 → reproduces the bank.
                  ⚠ c3/c6/c7 CASETIME 19.5–19.9s = TLE-tight (latent bank risk, unchanged by diff).
                  Prior bank base: bonifica ecbbe3c0b082 (re-banked r56 19932030); pre-bonifica
                  68e22f048d07 (v111).
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
  control 7/7). Judge didn't favor Hoppe; LOW-EV, de-prioritized. Coin-confounded (see #1).
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
