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
solver/main.cpp   (BANK track — decimation)   sha256 ecbbe3c0b082  = r55 BONIFICA base (96.4 KiB)
                  Output-identical to the 90.285538 bank on every deterministic proxy (byte-exact).
                  RE-BANKED 7/7 [JUDGE 19932030, 2026-07-10]: Accepted 90.285538, all 6 cases at
                  banked rungs → the bonifica base IS the live bank base (−19.3 KiB compile headroom
                  reclaimed, no score cost). c7 margin 0.4s (deterministic, holds); c5 2.6s tight.
                  Pre-bonifica bank binary was sha 68e22f048d07 (v111 lineage).
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
1. **RE-SCREEN THE GRAVEYARD on the discriminating ruler (MAIN THRUST).** Every road killed on the
   saturated smooth proxy was closed with a BLIND instrument (Process Law #2). Re-test on ab_orig
   (rough): **R-ζ** (true rendered-SSIM collapse selection — top pick, was "+0.0001 on smooth"),
   R1 interleave, SIL variants, nmetric, + the untested content-adaptive densify/prune (MeshSplatting).
   Any mechanism beating VSA-lite by a real margin → judge-test on c3 via S-read pair. `docs/ROADS.md`.
2. **PARALLEL: source a c3-NATIVE (~23k) rough organic proxy (R-ι)** for final confirmation — but do
   NOT block screening on it; the c5-scale rough ruler is a valid ORGANIC-CLASS screen NOW.
3. **Deterministic refine (R-κ)** — de-confounds future A/Bs + dev-base reproducibility, NOT bank
   harvest (best-counts already re-rolls the coin free). ⚠ do NOT determinize a razor case (c4/c6) at
   a sub-wall iter count (converts a passing coin → deterministic WA); determinize the DEV base with
   margin, keep bank attempts on the free coin. Cheap/parallel; NOT the focus (Process Law #1).
4. **Send the SSIM-window judge question** — `docs/JUDGE-QUESTION.md`, ready. HUMAN action; free.

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
