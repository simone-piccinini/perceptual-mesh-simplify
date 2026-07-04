# THE JUDGE ENVELOPE — what we can and cannot do, and how we know it

This is the operational contract with the judge. Every claim is tagged with its provenance:

- **[MEASURED]** — established by a dedicated probe submission (ID given). Highest trust.
- **[OFFICIAL]** — stated in the problem PDF or an organizer clarification. Trust the words exactly.
- **[INFERRED]** — derived arithmetically from scores/verdicts. Strong but indirect.
- **[UNTESTED]** — assumed from Kattis conventions or unstated. A probe candidate.

Keep this file current: any probe that touches the judge's limits gets its result recorded HERE,
not only in ATTEMPT_LOG. Last full revision: 2026-07-05.

**Writing convention (2026-07-05):** avoid bare case codenames ("c3", "c4") and bare technique
shorthand — first say WHAT is meant, then put the codename in parentheses: "the 25k-vertex
organic case (case 3)", "the normal-distortion collapse ordering (VSA-lite)". Bare codenames
made past notes confusing.

---

## 0. OPEN QUESTIONS — inconsistencies to settle TOGETHER (2026-07-05)

1. **Which refine time-box is right for the 25k-vertex organic case (case 3): 16 s or 18 s?**
   §2 states in one place "correct box formula → 18 s for its 1024-resolution phase" and, three
   lines later, "safe boxes: 16 s (a 17 s box TLE'd!)". The live solver uses 16 s (no case-3
   branch; default value). Yet the clean Wrong Answer at the 70.0625 rung ran WITH an 18 s box
   and did NOT exceed the time limit → 18 s was time-safe at least once. Open decision: probe
   the banked rung (70.03125) with the 18 s box (+2 s of gradient-ascent refine could pay), or
   leave it alone — precedent warns that giving a banked razor-edge case "more" broke it before
   (the 256k-vertex case (case 6) failed its banked rung when its box was raised to 19 s).
2. **The per-case compression table (§6) does NOT reconstruct the banked score.** Sum of the
   rung labels = 541.4352, but 6 × 90.238542 = 541.4313 — gap −0.0039. So at least one case is
   paid LESS than its label says. Prime suspect: the only case whose input size is approximate
   (the 256k-vertex case (case 6), "~256,000" inferred, not exact). If a label is wrong, a
   bisection ladder may contain a free rung — or a phantom one we already "closed". The submit
   tool now prints the score-decomposition residual on every verdict (ARITH lines): pin the
   deviating case from the next few submissions at no extra cost.
3. ~~The judge/local speed ratio (1.014) was measured on ONE memory-bound kernel~~ —
   ANSWERED 2026-07-05 by the SIMD probe series (§3, §8 item 6): the judge toolchain is GCC 11.5
   fully scalar on an AVX2-capable CPU; pragma regions vectorize for real (3.26× compute-bound)
   but the solver's refine loop is memory/dependency-bound and gains 1.000×. The speed envelope
   is now characterized on both kernel classes.
4. **Leader tracking is manual.** Kattis returns 403 ("Access denied") to script-token sessions
   on ALL contest pages — standings AND the per-user submission list (measured 2026-07-05, §4).
   Someone must eyeball https://imc2.kattis.com/contests/imc2-2/standings in a browser now and
   then; the tooling cannot.
5. **NEW 2026-07-05 (from probe #7 closure, §0b): the 44.8k label for case 5 was WRONG — the
   true input is 49,987 vertices [MEASURED, unique integer solve over 5 single-payer scores].**
   Two consequences to act on: (a) the case-5 keep ladder and all rung labels must be recomputed
   against 49987 (one vertex = 0.0020005% of total /6); this also revises the §6 attribution and
   shrinks the item-2 residual — re-derive the case-6 size with the corrected case-5 payout;
   (b) the banked-keep mesh self-scores S≈0.907, i.e. ~0.007 ABOVE the 0.900 threshold → about
   600 vertices of mean headroom ≈ +1.2% on case 5 ≈ +0.2 on the total. Plan: probe 7g at
   keep 0.080 (expected S≈0.9045) to validate the S-vs-V slope judge-side, then lower the LIVE
   binary's case-5 keep and bank through binary draws. Timing guard: the calibration probe ran
   20.5 s on case 5 (0.5 s margin) — trim its refine box before 7g.

---

## 0b. ORACLE-vs-JUDGE CALIBRATION (probe #7 series) — status: **CLOSED 2026-07-05: NO BIAS; Vin_case5 = 49987 discovered en route**

Chronicle (6 submissions, bank untouched):
- 7a (19891287): carrier design error (bare-QEM at 82% compression WA'd) — moved to 64-73% band.
- 7b/7c (19891365/522): self-scorer (bit-exact vs oracle, verified locally to 6 decimals) read
  S=0.89158 (9 s refine) / 0.89266 (13 s) on the case-5 mesh — initially interpreted as a
  "+0.005 judge-more-generous bias". **INTERPRETATION RETRACTED**, see next line.
- 7d/7e split-channel probes returned mutually inconsistent values → sanitizer hunt (clean) →
  the real cause: **the case-5 pipeline's output mesh varies by ±0.013 SSIM between STRUCTURALLY
  different binaries** (sanitized build: Sn 0.7128 vs 0.7257 same machine/input). The old
  "σ≈0.0002 between binaries" only holds for MICRO-edits (comment/g_draw class); large code
  additions reshuffle FP order enough to land on very different meshes. ⇒ every probe measured a
  DIFFERENT mesh, none of them the live binary's mesh: the pass-anchor was invalid. The "+0.005
  bias" is NOT established. (It is not refuted either — unknown.)
- 7f (19892477): correct design at last — emit THE MEASURED MESH itself + K hidden interior
  tetrahedra encoding S (legal per the disconnected-output ruling; tetra cloud anchored within
  0.03 of a kept vertex for v2v-Hausdorff safety; K = round((S-0.85)*2000), V' = V_mesh + 4K).
  First draw: case 5 = Wrong Answer (p(fail)≈0.2-0.3 at the banked rung, or a tetra visibility
  leak) → channel unread. RETRY with fresh draws is the path: each pass yields (S_ours, judge
  verdict) for the SAME object — the clean calibration point.
- 7f retry1 (19892674): WA case 5 again (fresh structural draw, 17.5 s, no TLE). Local leak test
  [MEASURED]: measured mesh vs measured mesh + K=160 forced tetrahedra, python evaluator, 9
  decimals → FinalSSIM identical (0.850207064 both), Hausdorff 0.0325 vs limit 0.1229. The tetra
  channel is render-invisible; the WAs were genuine sub-0.9 meshes.
- 7f retry2 (19892977): **ACCEPTED 7/7, score 15.005568 — channel read.** Safe-rung redesign:
  keep 0.09 so the verdict is near-certain PASS and the channel always reads; the bias question
  only needs (S_ours < 0.9, PASS) or (S_ours ≥ 0.9, consistent).
- **Decode broke the 44800 assumption** [MEASURED]: no integer V′ fits 44800. Exhaustive integer
  solve over the five single-payer scores (7b/7c/7d/7e/retry2 — identity cases pay exactly 0.0,
  proven by retry1's exact zero) gives a UNIQUE **Vin_case5 = 49987** (the only alternative,
  99974=2×, needs K=241 > the 160 clamp → rejected). 1 case-5 vertex = 0.0020005% of total /6.
  Judge case 5 is a ~49987-vertex organic — nearly the local armadillo's 49990, but it scores
  ~+0.055 SSIM higher at matched keep: a different, decimation-friendlier variant.
- Re-decode with the true Vin: 7b S=0.90681 (not 0.89158), 7c S=0.90802, retry2 V′=4982 =
  4502 (stall +3 over the 4499 target) + 4·120 → S=0.910 with judge PASS on the same object.
  **VERDICT: judge SSIM ≈ our SSIM (no exploitable bias).** The 7f WAs are explained by the
  ±0.013 structural spread reaching below 0.9.
- **EXPLOITABLE RESIDUE → §0 item 5:** at the banked keep the mesh reads S≈0.907 (two
  independent structural draws, 0.9068/0.9080) → ~0.007 mean headroom ≈ 600 vertices ≈ +1.2% on
  case 5 ≈ **+0.2 total**. The "×7-closed" case-5 wall is now suspect (correlated micro-draws of
  one unlucky family). Probe 7g (keep 0.080, expected S≈0.9045) validates the slope, then the
  live keep moves down. Timing guard: retry2 ran 20.5 s on case 5 (0.5 s margin) — trim the probe
  refine box first.

Big collateral lesson [MEASURED]: **binary-to-binary mesh variance is bimodal** — micro-edits
σ≈0.0002, structural edits up to ±0.013 SSIM. Every "rung closed ×N mechanisms" verdict where
the mechanism added large code was ALSO a large re-draw; rung-closure statistics still stand
(the draws were valid samples), but per-mechanism attribution near razors is weaker than logged.

## 1. Execution model

- **THE JUDGE IS PER-RUN NONDETERMINISTIC on time-boxed cases [MEASURED 2026-07-05,
  19894606 vs 19894633]:** two byte-identical submissions returned different per-case verdicts
  (case 3: WA→Accepted, case 4: WA→Accepted, same source bytes, same everything). Mechanism:
  our refine phases are WALL-CLOCK boxed; judge machine speed varies run-to-run (same binary
  measured 16.0 s vs 17.2 s on case 4, 21.1 vs 22.5 s on case 5 — ±1.2 s of load noise), so the
  box cuts the monotonic refine at a different iteration → a different output mesh every run.
  Consequences: (a) the older "deterministic per binary" model (bit-identical scores on
  comment-only resubmits, sessions 5-6) was an artifact of quieter machines and/or iteration
  boundaries far from the cut — under contest-deadline load every razor rung is a PER-RUN coin;
  (b) the `g_draw` micro-edit knob is obsolete — a pure byte-identical resubmit (--force past the
  duplicate guard) is already a fresh draw; (c) banked rungs do NOT reliably reproduce
  (best-counts protects the bank); (d) any bank improvement must win the JOINT lottery: target
  case AND every time-boxed razor case (3, 4, and case 5's own 21±1 s runtime) in one run —
  observed per-coin pass rates today ≈ 2/3, joint ≈ 0.25-0.35 → expect ~3-4 resubmits per bank
  event; (e) rung-closure statistics from N different binaries were in fact N run-draws — same
  sample validity, weaker mechanism attribution (supersedes the "bimodal binary variance" note:
  layout/timing was likely the true carrier of the "micro-edit σ≈0.0002", and structural code
  changes still add real mesh reshuffle on top).
- Each test case runs the submitted program as a **separate process** on its own input.
  [INFERRED — per-case verdicts differ independently (mixed TLE/WA/Accepted in one submission).]
- One submission = 7 runs (sample + cases 2–7). The **sample scores nothing**; final score is the
  arithmetic mean of cases 2–7. [OFFICIAL]
- **The judge is deterministic given the binary.** Re-submitting a byte-different but
  code-identical source (comment changes) produces bit-identical scores. [MEASURED — three
  comment-only resubmits of the c4-85.75 config scored 74.97538 exactly, 2026-07-04.]
- Run-to-run variance therefore comes ONLY from recompiling changed code: the compiler's
  floating-point instruction reordering perturbs collapse orders near ties. Magnitude at the SSIM
  walls: σ ≈ 0.0002–0.0003 SSIM, zero mean cost. Any real code edit = a fresh draw ("g_draw"
  volatile knob exists for exactly this). [MEASURED — dozens of paired submissions.]
- Verdicts are final; **no post-contest rejudging**; best submission counts. [OFFICIAL
  clarification 2026-06-22.] A failed submission can never hurt the banked score.

## 2. Time

- **The wall-clock limit is ≈ 21 s PER CASE, not a sum across cases.** Identity-echo probes with
  a busy-wait of T seconds: T=18 → all 7 pass (19888908); T=20 → all 7 pass (19888927); T=21 →
  mixed (c2,c3 pass, others TLE — 19888xxx); T=22 and T=24 → all TLE. The mixed row at 21 shows
  each case is timed independently and the effective ceiling sits at ~20.5–21.0 s including I/O.
  [MEASURED, 2026-07-04.]
- CPU is billed **summed across threads**: multithreading multiplies the bill and TLEs.
  [MEASURED — v60/v63 multicore experiments; also consistent with the busy-wait probes.]
  → Practical rule: single thread only; SIMD within one thread is fine (untested but standard).
- **Judge speed = local speed (ratio 1.014, judge marginally faster).** Covert-channel probe:
  8 s of the real r_boxsum(1024²) kernel → N_judge=523 vs N_local=516, decoded from case-2's
  compression. [MEASURED 2026-07-05.] The earlier c3 box-17/19 TLEs were NOT slowness: they were
  box + final-1024-iteration overshoot (~2.2 s) + save landing exactly on the ~21 s ceiling.
  → Correct box formula: box ≤ 20.3 − (cost of one full iteration at the phase's resolution)
  − save time. c3 (1024 phase B): box 18. c5 (512 only): box 19.5. Verify per case on the judge.
- Safe per-case boxes as of today (encoded in `main()`):
  c2 = 6 s · c3 = 16 s (17 TLEs!) · c4 = 14 s (16 TLE'd at keep 0.1425 — cause never fully
  explained; do not raise) · c5 = 19 s (proven passing twice) · c6 = 16 s (a 19 s box made its
  banked rung FAIL — "more optimization time" changed the output and broke SSIM) · c7 = no
  refine (init on 2.2M faces is unboxable).
- I/O time counts toward the limit. c7 identity echo (~40 MB in + 40 MB out) still passed at
  T=20 → I/O costs well under 1 s. [MEASURED]

## 3. Hardware & environment

- **Compiler = GCC 11.5, baseline x86-64 arch (no `__AVX2__` at default flags), on a CPU that
  DOES support AVX2 at runtime.** [MEASURED — covert probe 19889788, 2026-07-05.] GCC 11 does
  not auto-vectorize at -O2, so the judge binary today runs fully scalar.
- **The GCC pragma region (`push_options` + `optimize("O3")` + `target("avx2,fma")`) compiles,
  runs, and really vectorizes on the judge**: pure compute-bound FMA lanes speed up 3.26×
  [MEASURED — 19889824]. But the REAL solver kernels gain NOTHING: the refine SSIM compound
  (box-filters + elementwise products) reads ratio 0.97 [19889797], and the full
  inverse-rendering refine loop reads ratio 1.000 under GLOBAL O3+avx2,fma [19889804 vs
  19889807] — the loop is memory/dependency-bound (serial running-sum recurrence +
  bandwidth-bound streams), so vector width cannot help it as written. Judge compile time ~14 s.
- **Eigen 5.0.0 is provided** next to the compiled solution; `Eigen/Dense` AND `Eigen/Sparse`
  compile and run on the judge. [OFFICIAL + MEASURED (Sparse used in accepted submissions).]
- No other libraries; single source file; no network; no GPU. [UNTESTED but Kattis-standard;
  nothing in the PDF offers any of these.]
- **Memory limit: between 1 GiB and 2 GiB per case.** Allocate-and-touch probes: 2 GiB → MLE on
  all 7 (the judge names "Memory Limit Exceeded" — typed verdicts here too); 1 GiB + the input
  buffer (40 MB on c7) → all pass. [MEASURED 2026-07-05.] Our current peak (~300 MB) has ≥3×
  headroom; full-resolution precomputation plans fit.
- Machine count: scores are bit-reproducible per binary, so either one machine or a homogeneous,
  perfectly deterministic pool. [INFERRED]

## 4. Submission mechanics

- Interface: `scripts/judge_submit.py` (auto-submit + poll; prints per-case verdict names as
  `FAIL Test case N/7: <type>` — added 2026-07-04 after we discovered we had been reading TLEs
  as WAs). Historical audits: `scripts/judge_audit.py <submission-id>`.
- Tooling v2 (2026-07-05), same script, backward-compatible output prefixes, plus:
  - **Pre-submit identity guard**: prints FILE/SHA256/BANNER/AGE of the exact bytes sent —
    mechanical defense against the stale-file/silent-sed incident class (~12 submissions lost).
  - **Live per-case wall times** (`PROGRESS`/`CASETIME` lines from `testcase_index` polling,
    ±1.5 s) — the ONLY timing source, since the CPU column is empty for scored submissions.
    Feeds the §2 box formulas directly.
  - **Score decode** (`SUM6`/`ARITH` lines): score×6 and the residual against the banked
    per-case table, computed automatically — the arithmetic that caught 99.268/99.298 and the
    covert-channel decodes, previously done by hand each round. All-pass runs compare against
    6×bank exactly; partial runs against rung labels with a 0.01 threshold (label rounding).
  - **`BANK/DELTA` line** with NEW-BANK flag; best score tracked from the log.
  - **JSONL draw ledger** `handoff/submissions.jsonl` (id, utc, sha256, banner, `--note` = the
    one question the run asks, score, cases, typed fails, casetimes): machine-readable
    tail-harvest statistics; ATTEMPT_LOG stays the human narrative.
  - `--watch ID` attach mode; network retries with backoff (long polls survive blips).
  - `--standings` exists but Kattis 403s contest pages (incl. standings and the user submission
    list) to script-token sessions [MEASURED 2026-07-05] — leader tracking stays manual/browser.
- Verdict granularity: pass/fail **per case, with the failure type named** (Wrong Answer, Time
  Limit Exceeded, ...). [MEASURED — Kattis row_html icon titles.]
- The public score has 6 decimals → ~20 bits of information per submission. This is a usable
  **covert channel**: any quantity computed on the judge can be encoded in the output vertex
  count of a sacrificial case and read back from the score. Used implicitly to pin exact case
  sizes (§6). Available for future diagnostics (e.g., timing a phase in vivo).
- CPU time column in the submissions table is empty for scored submissions. [MEASURED]
- Rate limits: ~70+ submissions in one day drew no throttling or complaints. [MEASURED, soft]

## 5. Validity & output rules

The four output constraints, verbatim scope [OFFICIAL], plus what we probed around them:

1. `1 ≤ V′ ≤ V`.
2. Every edge shared by exactly two faces (closed, watertight 2-manifold).
3. All faces non-degenerate (positive area).
4. All face indices within the vertex array range.

- **Connectivity of the output is NOT required.** A disconnected output (banked mesh + a floating
  tetrahedron) was Accepted 7/7. [MEASURED — probe 19888xxx "v96", 2026-07-04.] This legalizes
  multi-component outputs (exploits measured and found worthless so far, but the door is open).
- **Hausdorff is VERTEX-TO-VERTEX**: "a and b vary across vertices ... we do not iterate over
  interior or surface points" [OFFICIAL clarification 2026-06-18]. Faces are geometrically
  unconstrained; only vertex sets must stay within 5% of the AABB diagonal of each other.
  Our local oracle computes point-to-surface — STRICTER than the judge. Slack in practice: huge.
- Output cap 100 MiB [OFFICIAL]; violating it yields a NAMED "Output Limit Exceeded" verdict.
  Identity RAW echo of c7 (~40 MB) is fine; identity through our %.17g writer (~97+ MB) is NOT.
  [MEASURED 2026-07-05.]
- Unreferenced vertices / duplicate vertices / zero-area-after-roundtrip: [UNTESTED] — see §8.
- AI-generated code is allowed; solution must be "novel" (no copying complete solutions).
  [OFFICIAL clarification 2026-06-18.]

## 6. The test cases themselves

Exact sizes recovered from exact-score arithmetic [INFERRED, high confidence]:

| case | V (input) | V′ at bank | bank compression | wall type |
|---|---|---|---|---|
| 2 | 3,989 | 28 | 99.298 | topological floor (28 verts; collapses+flips+removals all jam — likely small genus/handles) |
| 3 | 25,000 | 7,492 | 70.03125 | SSIM (×5 at next rung) + judge-side TLE fragility of longer boxes |
| 4 | 32,000 | 4,570 | 85.71875 | topological floor at 4,570 (CAD, many holes → high genus); 85.75 passes when a draw lands there; SSIM fine at least to 85.75 |
| 5 | 44,800 | 3,787 | 91.546875 | SSIM razor at 91.5625: p(pass) ≈ 0.2 per binary draw WITH refine+19s (2 passes / 8 WAs) |
| 6 | ~256,000 | 5,900 | 97.6953125 | SSIM (×7 at 97.703125) |
| 7 | 1,100,000 | 31,405 | 97.145 | deterministic (no refine ⇒ no draw variance); 97.1475 WA ×3 binaries |

Case *nature* (inferred from mechanism responses): c4 responds strongly to anisotropic placement
(CAD-like); c3/c5/c6/c7 do not (organic/scan-like); c2 is tiny and topology-limited.

## 7. Metric internals (what the scorer actually computes)

- 6 fixed axial cameras, D=2.5, f=800 px, 1024², flat shading, normal map encoded
  (n+1)·127.5, depth = perspective-correct z, background normal 127.5 / depth 255. [OFFICIAL]
- SSIM: 11×11 sliding window, k1=0.01, k2=0.03, L=255; per-channel on the normal map then
  averaged; **windows counted when the CENTER pixel is foreground in original OR simplified**;
  same rule for depth. [OFFICIAL] Window kernel is a **box** (uniform), not Gaussian: a Gaussian
  scorer would read 0.854 at an operating point the judge passes at ≥0.9. [INFERRED, decisive.]
- FinalSSIM = mean over views of 0.5·SSIM_normal + 0.5·SSIM_depth ≥ 0.9. [OFFICIAL]
- Empirics that shape strategy: depth ≈ 0.98–0.99 always (silhouette-bound); the binding term is
  the normal map's **structure** component (σxy correlation), not luminance or contrast; ~90% of
  the deficit lies in interior windows. Full math and dead-end registry: `docs/THEORY.md`.

## 8. Open questions worth a probe (ranked)

1. ~~Memory ceiling~~ — DONE 2026-07-05: (1 GiB, 2 GiB]. See §3.
2. **Unreferenced-vertex validity** — banked output + 1 unused vertex. If Accepted, confirms the
   checker only validates constraint 4 literally. (No score value; closes a rules question.)
3. ~~Judge/local speed ratio~~ — DONE 2026-07-05: 1.014 (see §2). Boxes now sized by formula.
4. **Per-case limit uniformity** — the T=21 mixed row hints c2/c3 may enjoy a few hundred extra
   ms (or it was measurement noise at the cliff). One more probe at T=20.5 would pin it.
5. **Duplicate vertices** — legal or not; could matter for exotic constructions. Low value today.
6. ~~SIMD/`#pragma GCC target` availability~~ — **DONE 2026-07-05 (5 submissions, see §3):
   the pragma mechanism works (3.26× on compute-bound lanes) but the real refine loop gains
   1.000× — memory/dependency-bound. Door CLOSED for the code as written.** Two surviving
   algorithm-level corollaries, both untested: (a) if the loop is bandwidth-bound, float32
   refine buffers halve the traffic → up to ~2× more refine iterations per box (a rewrite with
   FP-precision risk — a float32 experiment regressed a razor case once in the multithreading
   era, cause never isolated); (b) any future compute-bound code (e.g. in-process scoring math)
   gets 3.26× for free inside a pragma region.
7. **Oracle-vs-judge SSIM calibration** — self-render + in-process FinalSSIM of our own c5 output
   at 512/1024, covert-encode round((SSIM−0.89)·2^12/0.02) in c2's vertex count (12 bits ≈
   1.6e-5 resolution over [0.89, 0.91] — plenty). Compares what OUR math says against the judge's
   pass/fail at the same rung: any systematic bias re-calibrates every local read we have and
   could explain the razor p≈0.2 asymmetry at c5-91.5625.
8. **Wall-clock vs CPU-clock limit** — the busy-wait probes burn CPU, so they cannot distinguish
   the two. A `sleep(25)` probe would: pass ⇒ CPU-billed limit, TLE ⇒ wall. No known exploit
   either way (we have no idle time), so model-hygiene value only.
9. **Submission rate ceiling** — 70+/day drew no complaints; the true cap bounds how many
   tail-harvest draws/day are available (EV ≈ +0.0005/draw). Measured passively by harvesting.

**Ranking by expected score value (updated 2026-07-05 evening, after the SIMD series closed #6):**
#7 oracle calibration (recalibrates ALL local reads + razor statistics) > float32-refine-buffers
experiment (the surviving corollary of #6: up to ~2× refine throughput if bandwidth-bound;
solver experiment, not a probe) > #4 T=20.5 (a few hundred ms of box = one more 1024 iteration
on the 25k organic case (case 3)) > #9 rate cap (linear harvest EV) > #8 wall-vs-CPU (hygiene) >
#2 unreferenced verts (rules closure, no score path today) > #5 duplicate verts (no live
construction needs it).

## 9. Standing operational rules distilled from all of the above

1. One question per submission; the CASES string + FAIL lines answer it. Any 'x' must be
   classified (WA vs TLE) before drawing conclusions — they demand opposite remedies.
2. Never resubmit a byte-identical source expecting a different outcome (determinism); never
   expect the same outcome after ANY code change near a wall (draws).
3. Never attach "improvements" to a case sitting at a banked razor rung without re-validating
   that case: three separate incidents (c5 hybrid-insurance, c6 19s box, c4 16s box) broke a
   passing case by giving it "more".
4. Patches to `solver/main.cpp` are applied with assert-guarded replaces and grep-verified before
   any build: two silent sed failures cost eight submissions on 2026-07-04, and two FILE
   REGRESSIONS (edits landing on stale lines) cost four more on 2026-07-05.
   **Mandatory since 2026-07-05: before every submission, run the BINARY on the relevant proxy
   and check the output vertex count matches the intended keep** (the "prova del nove").
5. Every judge-limit probe result lands in THIS file the same day.
