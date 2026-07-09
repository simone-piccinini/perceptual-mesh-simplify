# STATUS — where the project is NOW

*Single source of truth for CURRENT state. Overwrite this on every judge verdict. Everything
else (why/history/theory) lives elsewhere and is NOT repeated here. Read `CLAUDE.md` for HOW to
work; this file is WHERE we are.*

**Last updated: 2026-07-09.**

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
solver/main.cpp   (BANK track — decimation)   sha256 68e22f048d07  = the verified 90.285538 bank
                  banner: PROBE-RC3-READ 2026-07-06 (c5/c4 recipe on c3, banked-14 + 1024 polish)
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

1. **Compile/source bonification of main.cpp** (prereq) — strip dead env-gated code + `Eigen/Sparse`,
   verify byte-identical proxy output. Target ≥250 MB compile-headroom, ≥40 KiB source-headroom.
2. **Road 3.B.1 — Hoppe attribute-quadric placement**, A/B via S-read (1 submission-pair).
3. **Road 3.C.1 — de-bias the proxy** so local A/B transfers again (the real bottleneck; days, but
   multiplies research speed 10–100×).
4. Free, parallel: re-roll c4/c6 box-cut coins on "cold" judge days.

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
