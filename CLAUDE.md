# CLAUDE.md — operating contract for the IMC2 Problem-B solver

**Read this fully before touching anything. It exists to stop you from hallucinating progress.**
This project has burned ~24 submissions on avoidable mistakes (stale files, mis-read verdicts,
trusting local tests that don't transfer). Every rule below is paid for in lost submissions.

---

## 0. What this project is (one paragraph)

Simplify 6 hidden closed meshes to the fewest vertices while the judge's 6-view perceptual score
stays `FinalSSIM ≥ 0.9` and the mesh stays a valid closed 2-manifold within 5% (vertex-to-vertex)
Hausdorff. Score per case = `100·(1 − N/V)`, mean over cases 2–7. **Bank and per-case state live in
`STATUS.md` — read that for "where are we now". This file is "how to work".** The judge truth is
`docs/JUDGE-ENVELOPE.md`; the metric math is `docs/THEORY.md`; the strategy is `docs/ROADS.md`.

---

## 1. THE FILE YOU EDIT

- **You edit exactly ONE file that reaches the judge: `solver/main.cpp`.** Nothing else is uploaded.
  It is a single C++17 translation unit, Eigen (Dense) provided by the judge.
- The local evaluator `src/imc_eval/` (the oracle) is **truth for the metric MATH but not for
  pass/fail** — never edit it to "make a test pass". It is your measuring stick, not your target.
- Everything is dispatched by input vertex count (`keep_for`, `lambda_for`, `refine_for`, … in the
  first ~200 lines). Per-case behaviour = per-count behaviour. To change one case, change its band.

---

## 2. THE ANTI-HALLUCINATION LAWS (do not violate these)

1. **A local proxy win is WEAK EVIDENCE, and for position-space optimizers it is KNOWN-BIASED to
   near zero.** Measured transfer ratio ≈ 0 to NEGATIVE across three mechanisms (JUDGE-ENVELOPE
   §9.1). The proxies (armadillo-derived) are smoother than the judge's raw scans, so they
   over-reward fine geometric optimization. **Never conclude "+0.002 locally → ship it".**
   - What DOES transfer: raw throughput (float32, more iterations of the *same* trajectory, ratio
     ≈1) and structural changes. A large *structural* local LOSS (e.g. VSA −0.10) is strong
     evidence of death; a small position-space local GAIN is not evidence of life.

2. **Trust the judge's pass/fail over any self-score.** The in-process self-score (S2) is ~+0.010
   OPTIMISTIC near the wall. It read 0.9135 at N=6940 yet N=6900 WA'd. Use S2 for RELATIVE A/B at a
   SAFE N above the wall — never to predict the absolute wall.

3. **Near a wall, a WA is a COIN DRAW, not proof.** Cases 3, 4, 6 are box-cut: the CPU-box timing
   jitter re-rolls the float order → a different mesh each run (σ ≈ 0.001–0.002 SSIM). One WA at a
   rung means nothing; **two consecutive WAs = wall.** Cases 2, 5, 7 are ~deterministic per binary.

4. **ANY code change beyond a single constant creates a new binary family and re-rolls the box-cut
   MEAN of EVERY case** — not just the one you touched. This is why an isolated case-3 edit can WA
   case-4. Prefer one-constant diffs inside the proven family; if you must change more, expect to
   re-validate every box-cut case.

5. **The file is at the compile-memory cliff (~110 MB margin, gcc:14) and the 128 KiB source limit
   (~15 KiB margin).** Before ADDING any mechanism: strip dead env-gated code (G_ADAM, G_SHARP,
   G_HOP, G_LAPL, G_LLOYD, G_VSAC, tcand, nplace2, mask, `Eigen/Sparse`) and verify byte-identical
   output on the proxy. Adding new Eigen instantiations will OOM the judge compile — hand-roll small
   solves in plain doubles.

6. **Every quantitative claim you write gets a provenance tag:** `[JUDGE]` (real submission id),
   `[LOCAL]` (proxy — weak), `[INFERRED]` (arithmetic), `[UNTESTED]`. No tag = not allowed.

---

## 3. THE WORKFLOW (every change follows this, no shortcuts)

```
  EDIT solver/main.cpp   (assert-guarded Edit, then grep-verify the change landed)
     ↓
  BUILD                  g++ -O2 -std=c++17 -I<eigen> solver/main.cpp -o solver/main
     ↓
  PROVA DEL NOVE         run the binary on the relevant proxy; CHECK the output vertex count
     ↓ (mandatory)       matches the intended keep. Two silent sed/stale-line failures cost 12 subs.
  LOCAL ORACLE           imc-score / validate_oracle.py — for VALIDITY (manifold, indices,
     ↓                   Hausdorff, vertex count) and convergence-vs-box-cut diagnosis ONLY.
                         NOT for pass/fail prediction (rule 2.1).
  COMPILE-CHECK          if you added code: compile in a gcc:14 container, confirm no OOM,
     ↓                   confirm source ≤128 KiB.
  JUDGE TEST             submit via scripts/judge_submit.py (token in ~/.kattisrc; 403 is only
     ↓                   for standings, NOT submit). For a NEW MECHANISM: family test at the
                         banked rung (one submission, per-case verdict = the read) BEFORE any
                         descent. For a NUMBER: use the S-read (mesh + K tetras, WALL-MODEL §5).
  DECODE                 paste the score; decode per-case N (exact), K→S for reads, attribute any
     ↓                   WA (classify WA vs TLE — opposite remedies!). Watch for coin-loss on an
                         untouched case breaking auto-decode.
  RECORD                 see §4. Update STATUS.md, ATTEMPT_LOG, submissions.jsonl, ROADS.md.
```

**Local tests are DEFINITIVE for:** validity (manifold/indices/Hausdorff), output vertex counts (the
prova del nove), wall-time ballpark (×1.014 judge ratio), convergence-vs-box-cut. **Local tests are
NOT definitive for:** whether a change passes the judge. That is the whole trap.

**Golden rule for near-wall work (paid for ×3):** never attach an "improvement" to a case sitting at
a banked razor rung without re-validating THAT case in the same run. Giving a passing case "more"
has broken it three times (c5 hybrid, c6 19s box, c4 16s box).

---

## 4. WHERE RESULTS GO, AND IN WHAT FORMAT

After every judge verdict, update ALL of these (they serve different readers):

1. **`STATUS.md` (root)** — the single source of truth for CURRENT state. Overwrite the bank,
   per-case line, live-main.cpp sha256+banner, active front, next action. ≤1 screen. **This is the
   file the next agent reads first.**

2. **`handoff/submissions.jsonl`** — one JSON line, machine-readable:
   `{id, utc, sha256, banner, note (the ONE question this run asks), score, cases, typed_fails,
   casetimes}`. Appended automatically by judge_submit.py. **Note: it does NOT capture web-UI
   submissions — never infer the team bank from this ledger; verify on Kattis.**

3. **`handoff/ATTEMPT_LOG.md`** — the human narrative, newest-first. What you tried, the verdict,
   the takeaway. One entry per submission.

4. **`docs/ROADS.md`** — if the change tested a ROAD: update its status (`QUEUED`/`ACTIVE`+iter/
   `DEAD`+reason/`BANKED`). A road needs ≥10 iterations before it can be called DEAD.

5. **If it's a NEW BANK:** snapshot `solver/main.cpp` → `submissions/current/vN-<what>-<score>/main.cpp`
   plus a `RESULT.md` (verdict, per-case, decode, what changed). Keep `submissions/current/` to ≤5
   entries; everything older lives in `archive/submissions/`.

**Format discipline that prevents drift:** the bank number appears as a literal ONLY in STATUS.md.
Every other doc writes "the bank (see STATUS.md)". This is why the repo currently shows 5 different
"bank" numbers — do not add a 6th.

---

## 5. THE SUBMISSION ECONOMY (submissions are CHEAP — the scarce thing is time and a working ruler)

**⚠ Corrected 2026-07-09. The old framing "spend like it's scarce" was a strategic error that helped
freeze the score.** The numbers: failed submissions are FREE FOREVER (best-counts protects the bank),
the rate limit allows ~hundreds/day, and the leaders have 800–6,640 tries while we have ~432. They
climbed by probing an order of magnitude harder. **The scarce resources are TIME-TO-DEADLINE and a
measurement instrument that transfers — NOT submission slots.** Stop hoarding a free resource.

- **Best-counts + no rejudging** → a failed submission can never hurt the bank. Probe AGGRESSIVELY.
  If an idea is worth thinking about, it is worth a judge test — the judge is the only ruler that
  doesn't lie (§2.1).
- **Rate limit ≈ 1 submit / 4 min** (token bucket, burst ~8). A refused submit costs nothing.
- **One question per submission.** The CASES string + FAIL lines answer exactly one question — decide
  it before you submit. Every 'x' must be classified WA vs TLE before you conclude anything.
- **A read is worth more than a blind rung.** One S-read = a point on the S(N) curve on the real
  judge mesh. Build a JUDGE-SIDE dataset of reads; that is the only unbiased signal you have. Prefer
  read→jump→bank over bisecting blind, and run control/variant read PAIRS to A/B new mechanisms.
- **Batch across the 6 cases.** One submission carries up to 6 independent case-reads. Never spend a
  whole submission on one case's question when the other 5 bands can answer their own.
- The genuine judgment call is "is this bank attempt worth a warm-day coin re-roll tonight" — surface
  that. It is NOT "can I afford to test an idea." You can always afford to test an idea.

---

## 6. STRATEGIC ORIENTATION (so you don't re-dig dead holes)

- **The prize is case-3.** Every other case is 85–99% behind a MEASURED-hard wall. 1 pt of case-3
  compression = 0.167 on the total. Read `ARCHITECT-REVIEW.md` for the roads (small/big/huge).
- **The winning case-3 mesh is smooth + dense + adaptive (the QEM family).** Flat/partition topology
  (VSA remesh) is measured DEAD on organic surfaces — do not rebuild it.
- **The binding term is the normal-map STRUCTURE (σxy correlation).** Depth is saturated (~0.984),
  Hausdorff is loose (v2v), topology is genus-0. Do not spend effort on depth, Hausdorff, or handle
  surgery — all measured zero-prize.
- **Before reviving any "clever" idea, check `docs/ROADS.md` §2 (DEAD roads) and THEORY §7
  (cimitero).** If it's there, it needs a genuinely NEW angle, not a re-run.
- **The real bottleneck is measurement bandwidth, not algorithm cleverness.** The two highest-value
  project-level moves are DATA (matched/raw judge-class proxies so local A/B transfers again —
  ARCHITECT-REVIEW §3.C.2) and DETERMINIZING refine (kill the box-cut coin — §8.3). Do these before
  chasing any new mechanism; see §8 for why the score has been flat.

---

## 7. FILE HYGIENE (keep the repo cheap to navigate)

- Active `submissions/current/` ≤ 5 entries; the rest in `archive/submissions/` (don't read it
  unless doing historical forensics).
- Don't create a new doc when an existing one owns the topic. State→STATUS.md, judge facts→
  JUDGE-ENVELOPE, metric math→THEORY, roads→ROADS. Adding a parallel doc is how drift starts.
- Every doc opens with a 3-line `STATE:` block (bank ref, active front, last action) so a reader
  knows in one glance if it's fresh.
- If you find a stale doc (a number that contradicts STATUS.md, a link to a missing file): fix it or
  flag it in the same session. Stale state docs are the #1 cause of an agent starting wrong.

---

## 8. THE PROCESS LAWS (read this if the score has been flat — it has)

*Added 2026-07-09 after a process review. The score plateaued not because the ideas ran out but
because the METHOD drifted. These laws exist to correct that. They override any habit to the contrary.*

1. **The objective is SCORE, not a defensible dead-end.** Closing a road with rigor FEELS like
   progress and reads well in ROADS.md, but the graveyard has grown every session while the number
   has not. Do not reward yourself for killing ideas. A session with zero new banks and five
   beautifully-argued closures is a FAILED session. Optimize for "what did I try on the judge that
   might win," not "what did I prove impossible."

2. **Never close a road on local-proxy evidence alone.** The proxy is a KNOWN-BROKEN ruler for
   position-space work (§2.1). Killing a mechanism because it lost a local A/B is measuring the ruler,
   not the territory. A road is DEAD only after (a) a judge-side test (S-read pair or family test), or
   (b) a test on a proxy PROVEN to transfer. Until the instrument transfers, "local-negative" =
   "unknown," not "dead." (The de-bias road was declared dead at iter 2/10 on the broken proxy — the
   canonical instance of this error. Don't repeat it.)

3. **Fix the instrument before trusting any measurement.** Two concrete, unglamorous engineering jobs
   outrank any new mechanism, because every mechanism depends on them:
   - **A transferring proxy** — real/matched judge-class meshes, not decimated-clean-armadillo
     (ARCHITECT-REVIEW §3.C.2). Without this you cannot iterate offline, full stop.
   - **A deterministic refine** — the box-cut "coin" is SELF-INFLICTED by wall/CPU time-boxing. Run
     refine for a FIXED iteration count sized to the budget with margin → output deterministic per
     binary → the bank reproduces every run and A/B noise drops. You have been *managing* a coin you
     could *delete*.

4. **Don't shrink the target to fit the plateau.** The "leader_c3 is 77% not 85%" re-estimate lowers
   urgency exactly when you're stuck — classic motivated stopping. Treat the gap as fully open
   (leader ≥91.46 proves a better mesh exists) until judge evidence says otherwise.

5. **Run a portfolio, not a monomania.** Case-3 is the biggest single lever, but "the prize is case-3"
   became blinders. In every working session ALSO harvest the free coin re-rolls on c4/c6 and any
   1-vertex rungs — bank every cheap fraction WHILE hunting the big one.

6. **The oracle has one unverified seam at the binding term.** `ssim.py` includes background pixels
   (gray 127.5 / depth 255) in the μ/σ/σxy of silhouette-straddling windows. If the judge masks them,
   the oracle is wrong exactly where case-3's structure deficit lives, and §7.1's calibration would
   not catch it. This is why the SSIM-window judge question matters — send it.

7. **You are your own only referee — so be adversarial.** Before writing "DEAD" or "at ceiling," argue
   the opposite case in one paragraph and see if it survives. Most of this project's closures have
   never been red-teamed; the first outside look found one wrong in a day.

---

*If you are about to conclude "we're at the ceiling": you are not. The leader at 91.46 proves a
better mesh exists. You are at the limit of what you can currently MEASURE, with a method that rewards
closing doors over opening them. Fix the instrument, spend the free submissions, stop shrinking the
target — then the ceiling moves.*
