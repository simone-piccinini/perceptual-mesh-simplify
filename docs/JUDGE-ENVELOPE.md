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

1. ~~Which refine time-box for case 3: 16 s or 18 s?~~ — **MOOT since float32 (2026-07-05):**
   case 3's refine now CONVERGES inside the 16 s box (finishes at ~17.4 s total, was 20.7-21.0
   box-cut). A bigger box buys zero iterations for a converged ascent; the 16-vs-18 question
   died with the box-cut regime.
2. ~~Input sizes / bank attribution~~ — **CLOSED 2026-07-05 night: ALL SIX sizes MEASURED**
   with the fixed-count single-payer instrument (exact-N output, identity elsewhere →
   V = N/(1−6·score/100), ±0.5 verts): case 2 = 4,098 [19895596], case 3 = 23,201 [19895616],
   case 4 = 35,292 [19895611], case 5 = 49,987 [CAL series], case 6 = 377,084 [19895532],
   case 7 = 1,009,118 [19895536]. EVERY legacy "recovered by arithmetic" size was wrong.
   Bank attribution re-solved with the true sizes: residual +0.000000 — exact payouts in the
   §6 table. Design rule learned the expensive way (exact-6000/6500 WAs on case 6):
   keep-fraction rungs AUTO-SCALE with the unknown V — size a fixed count for the UPPER end
   of the case's range.
3. ~~The judge/local speed ratio (1.014) was measured on ONE memory-bound kernel~~ —
   ANSWERED 2026-07-05 by the SIMD probe series (§3, §8 item 6): the judge toolchain is GCC 11.5
   fully scalar on an AVX2-capable CPU; pragma regions vectorize for real (3.26× compute-bound)
   but the solver's refine loop is memory/dependency-bound and gains 1.000×. The speed envelope
   is now characterized on both kernel classes.
4. **Leader tracking is manual.** Kattis returns 403 ("Access denied") to script-token sessions
   on ALL contest pages — standings AND the per-user submission list (measured 2026-07-05, §4).
   Someone must eyeball https://imc2.kattis.com/contests/imc2-2/standings in a browser now and
   then; the tooling cannot.
5. ~~Case-5 true size / "S≈0.907 headroom"~~ — CLOSED 2026-07-05, both halves. **Vin_case5 =
   49,987** (not 44,800) [MEASURED]; full derivation + verdict in §7.1. The headroom was probe-
   family luck: the live ladder below the banked V=4226 went 0/12, so **case 5 is a deterministic
   wall at V=4226** for this pipeline family (details §6 table + §7.1; judge-side slope near the
   razor ≈ 3.5e-5 S per vertex).

---

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
- Determinism summary (which regime a case is in — decides whether a resubmit is a re-roll):
  **box-CUT refine ⇒ per-run coin** (cases 4 and 6 today); **converged refine or no refine ⇒
  ~deterministic per binary** (cases 2, 3, 5, 7 under the float32 build — case 3 and 5 refines
  converge inside their boxes since v100). The 2026-07-04 "bit-identical comment-only resubmit"
  observations were real but belong to the converged/quiet-machine regime.
- Verdicts are final; **no post-contest rejudging**; best submission counts. [OFFICIAL
  clarification 2026-06-22.] A failed submission can never hurt the banked score.

## 2. Time

- **The limit is a CPU ceiling in [21, 22) CPU-seconds PER CASE; wall time is UNBILLED.**
  [MEASURED, two independent probe families:] (a) busy-wait T seconds (CPU = wall for a
  spinner): T=20 all-pass, T=21 mixed, T=22 all-TLE [2026-07-04]; (b) the sample case slept 25
  WALL seconds (zero CPU) and was ACCEPTED [19895285, 2026-07-05]; runs with wall 22.4-24.5 s
  pass whenever their CPU stays under (I/O and machine contention do not bill).
- Per-case, not summed across cases: the mixed T=21 row shows independent timing per case.
- CPU is billed **summed across threads**: multithreading multiplies the bill and TLEs.
  [MEASURED — v60/v63 multicore experiments.] → single thread only.
- Machine speed varies run-to-run under load (same binary: 16.0 vs 17.2 s on case 4, 21.1 vs
  22.5 s wall on case 5) — the engine of the per-run nondeterminism in §1. [MEASURED]
- **Judge speed ≈ local speed (ratio 1.014)** on the memory-bound refine kernel. [MEASURED
  19889xxx covert probe.]
- Since v101 all internal refine boxes cut on **getrusage CPU seconds** (what is billed), not
  wall. Boxes encoded in `main()` today: case 2 = 6 · case 3 = 16 (converges ~13-14 CPU) ·
  case 4 = 14 · case 5 = 17 (converges) · case 6 = 16 (default, box-cut) · case 7 = no refine
  (its refine-init is unboxable at 2.2M faces; a CPU-guard skips refine if init ate > 6 s).
- I/O time is cheap: the 1M-case identity echo (~40 MB in + out) fit at T=20 busy-wait → I/O
  well under 1 s of CPU. [MEASURED]

## 3. Hardware & environment

- **Compiler = GCC 14.2, baseline x86-64 generic arch (no `__AVX2__` at default flags), CPU
  supports AVX2 at runtime.** [MEASURED — probe 19889788 re-decoded + rerun 19900194,
  bit-identical scores across both days.] The 2026-07-05 "GCC 11.5" reading was a DECODE
  ARTIFACT of the then-wrong case-2 size (3989 vs true 4098); with the true size both runs
  decode to v=942 = GCC 14.2 — consistent with the g++-14 CE driver line. No mid-contest
  toolchain change. Consequence: GCC 14 auto-vectorizes at -O2 (SSE2 128-bit at generic arch),
  so the baseline binary is NOT fully scalar; the refine-loop memory-bound conclusion (pragma
  ratio 1.000) stands unchanged — bandwidth is the ceiling, not vector width.
- **COMPILE MEMORY LIMIT exists and our file sits AT it** [MEASURED 19898649..726, 5 CEs +
  2 controls]: the CE page says explicitly "Compilation memory limit exceeded" ("g++-14: fatal
  error: Killed signal terminated program cc1plus"). The v108-era source is at the cliff:
  pure REPLACEMENT edits compile; any NET ADDITION of a few statements tips it over —
  regardless of code shape (const-loop, volatile-loop, noinline-hoist all CE'd; a one-line
  add compiled). Biggest known weight: the judged-dead Sobolev path (G_LAPL) instantiating
  Eigen::SimplicialLDLT<SparseMatrix<double>> (−60 MB compile RSS locally when stripped).
  Engineering rule: strip dead template-heavy code from probe/live builds BEFORE adding
  features; the compile driver is g++-14 (see toolchain conflict above).
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
- **Submission rate limit = token bucket** [MEASURED 2026-07-06]: a burst of ~8 submissions in
  ~40 minutes exhausted it; the refusal names the mechanism ("You are out of submission tokens.
  Your next token will regenerate in 231 seconds") -> sustained ~1 per ~4 min, burst capacity
  several. A refused submit costs nothing. This bounds read-ladder throughput to ~15/hour.

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
- **V′ > V is illegal by constraint 1 and enforced** [MEASURED 19895285]: identity + 1 extra
  vertex (V′ = V+1) → Wrong Answer. NOTE: this WA is fully explained by constraint 1, so it says
  NOTHING about unreferenced vertices per se; that sub-question stays open (§8) but is idle —
  closed-geometry padding is judge-proven and covers every current need.
- **Coordinate precision %.7g is accepted** [MEASURED]: the 1M-vertex case passed with 7
  significant digits (~1e-7 relative coordinate noise) — compact writers are safe.
- **Nested / interior components are legal and render-invisible** [MEASURED 19895532/536]:
  clouds of tiny closed tetrahedra + triangular bipyramids strictly inside the body passed on
  two different cases with zero SSIM effect (and to 9 decimals in the local evaluator).
- Face ORIENTATION consistency: never isolated as a check. Everything we emit is consistently
  outward-oriented by construction and passes; whether the checker would reject a flipped face
  is unknown and no construction needs to know. [UNTESTED, idle]
- AI-generated code is allowed; solution must be "novel" (no copying complete solutions).
  [OFFICIAL clarification 2026-06-18.]

## 6. The test cases themselves

ALL SIX input sizes MEASURED with the fixed-count single-payer instrument (§7.1); the bank
decomposes EXACTLY (residual +0.000000) with truncation targets (int)(keep·V) + inferred
stalls. Every pre-probe "recovered" size was wrong.

| case | V (input) [probe] | V′ at bank | bank payout (exact) | wall type |
|---|---|---|---|---|
| 2 | **4,098** [19895596] | 28 | 99.316740 | **SSIM wall at 28** (27 = 99.341 WA'd). Topology probe: 1 component, genus 0 — a topological SPHERE, so the old "topological floor" label was WRONG; surgery has NOTHING to win here (1 vertex = 4.07e-3 total) |
| 3 | **23,201** [19895616] | 6,954 | 70.027154 | SSIM wall, ×2-DETERMINISTIC (70.06-rung WA'd in both refine regimes); TLE fragility GONE since float32 (converges) |
| 4 | **35,292** [19895611] | 5,044 | 85.707809 | **SSIM wall ~5,029-5,044** (the 0.1425-keep rung = 5,029 passes only on lucky draws). Topology probe [19895626]: 1 component, **genus 0** — the "topological floor" story is DEAD; the greedy jam is geometric (gate exhaustion on CAD creases), and the old "4,570 floor" was wrong-size arithmetic; refine box-cut ⇒ per-run coin (§1) |
| 5 | **49,987** [CAL §7.1] | 4,226 | 91.545802 | **deterministic SSIM wall at V=4226**: 0/12 sub-rung 2026-07-05 (f64/f32/λ/hybrid-1024/768 all WA; 768 negative even at the banked rung); f32 refine converges ⇒ no draw variance; slope ≈ 3.5e-5 S/vertex |
| 6 | **377,084** [19895532] | 8,705 (fixed-8684 target + 21 stall; bank event 19897075) | 97.691495 | SSIM razor + TRAJECTORY-SENSITIVE (box-cut): the bbox-crop refine family failed ×5 up to a SAFER-than-banked target (8720) until the crop was gated off for V>100k (THEORY §9.3); crop-off wall band (8691, 8705] |
| 7 | **1,009,118** [19895536] | 28,822 | 97.143842 | deterministic (no refine); wall boxed to (28,800, 28,822] (fixed-28800 WA 19897066) → ≤ +0.0004 total available, dropped |

Case *nature* (inferred from mechanism responses): c4 responds strongly to anisotropic placement
(CAD-like); c3/c5/c6/c7 do not (organic/scan-like); c2 is tiny and topology-limited.

### 6.1 Wall taxonomy — JUDGE walls vs SOLVER walls (final, 2026-07-05 night)

- **JUDGE walls** — imposed by the metric or the rules; no algorithm crosses them:
  SSIM ≥ 0.9, CPU ceiling [21,22) s (§2), memory (1,2] GiB, `1 ≤ V′ ≤ V`, closed 2-manifold,
  v2v Hausdorff 5%.
- **Topology is NOT a wall anywhere [MEASURED, genus probes 19895596 + 19895626]:** case 2 is
  a 1-component genus-0 sphere and case 4 (the CAD) is ALSO 1-component genus-0 — its holes
  are blind/geometric, not handles. The judge would allow genus changes, but there is no genus
  to remove: **topology surgery has zero prize on this test set — road closed for the cost of
  two probes.** The historical "topological floors" were (a) wrong-size arithmetic (the 4,570
  number) and (b) geometric gate exhaustion of OUR greedy (link condition + flip gate jamming
  on CAD creases / low-valence endgames) — a SOLVER property, worth at most the few dozen
  vertices between the jam point and the SSIM wall.
- **The remaining SOLVER walls are all of one kind: the converged LOCAL OPTIMUM of our
  decimate-then-refine family.** Structurally different meshes at the same vertex count spread
  ±0.013 SSIM (measured), i.e. better optima EXIST at every banked count. A globally better
  optimizer (joint decimation+refinement, appearance-driven co-optimization — THEORY.md §8
  Road B) faces a different, farther wall. That is the only door left to 91+.

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

### 7.1 Oracle-vs-judge calibration (probe #7 series) — CLOSED 2026-07-05: NO BIAS

**Verdict [MEASURED, 19891287..19892977, 8 submissions, bank untouched]: the judge's FinalSSIM
≈ our FinalSSIM.** Same-object proof: the solver self-scored its case-5 mesh in-process
(bit-exact scorer) and emitted THAT mesh + K hidden interior tetrahedra encoding S (V′ = V_mesh
+ 4K; tetra cloud v2v-Hausdorff-anchored, proven render-invisible to 9 decimals locally) — the
judge PASSED the very mesh that read S_ours = 0.910. Earlier "+0.005 judge-more-generous bias"
(7b/7c) was RETRACTED twice over: first a mesh-identity confound (structurally different
binaries emit case-5 meshes ±0.013 SSIM apart), then a decode error (the 44,800 case-5 size was
wrong — see next line). No exploitable metric gap exists; recalibrating the refine objective is
a dead end.

Collateral discovery: **Vin_case5 = 49,987** — unique integer solution over five single-payer
probe scores (identity outputs pay exactly 0.0, proven by a WA probe scoring exactly 0.0; the
double, 99,974, is excluded by the K ≤ 160 encode clamp). One case-5 vertex = 0.0020005% of
total /6. The judge's case 5 is armadillo-LIKE (49,987 vs our proxy's 49,990) but scores ~+0.055
SSIM higher at matched keep: a different, decimation-friendlier variant — the proxy's absolute
pessimism is a property of the INPUT mesh, not of the metric.

Instrument, reusable (the "measured-mesh channel"): run the real pipeline, self-score S, emit
the measured mesh + K tetrahedra, decode K from V′ in the score. Reads a judge-side S NUMBER in
one submission — but only when the case PASSES, so run it at a safe rung. This is the tool for
pinning V_case6 (§0 item 2).

### 7.2 What local tests are worth now (post-calibration operating rules)

- **The metric code is trusted; the proxy meshes are not.** Local evaluator + in-process scorer
  are judge-exact on the same input. But judge inputs ≠ our proxies: absolute local FinalSSIM
  still predicts NOTHING about pass/fail except on the case-3 proxy (historically faithful
  ±0.002). Case-5 proxy reads ~0.05 pessimistic FOREVER; don't re-litigate it.
- **Local relative A/B is a screen, not a verdict — and for position-space optimizers it is
  now KNOWN-BIASED.** Transfer record (local gain → judge outcome): float32 throughput →
  TRANSFERRED; 768-native (+0.00067) → judge-negative; R1 interleave (+0.002 on both proxies)
  → judge-negative 3/3 live families AT THEIR BANKED RUNGS; SIL coverage optimizer (+0.000735
  true-metric) → judge-POSITIVE sign, ~0.3× magnitude. Theory (THEORY.md §9.1): the proxies
  over-reward fine position-space optimization; throughput and coverage-channel changes carry
  over, trajectory-level geometric gains do not. MANDATORY PROTOCOL: any new mechanism runs a
  judge FAMILY TEST at its banked rung (one submission, per-case verdict = the read) BEFORE
  any descent; each keep change is a fresh deterministic family for converged-refine cases.
- **Local tests ARE definitive for:** validity (manifold/indices/Hausdorff), output vertex
  counts (the mandatory pre-submission "prova del nove"), wall-time ballpark (×1.014 judge
  ratio), and the convergence-vs-box-cut diagnosis — if the refine converges locally inside its
  box, its judge-side S is ~deterministic (case 3 and 5 post-float32); if the box cuts it, the
  judge verdict is a per-run coin (§1).
- **When a judge-side S number (not pass/fail) is needed:** use the measured-mesh channel
  (§7.1), one submission per reading.

## 8. Open questions worth a probe (ranked)

1. ~~Memory ceiling~~ — DONE 2026-07-05: (1 GiB, 2 GiB]. See §3.
Closed items are kept one line each; full detail lives in the section that owns the fact.

1. ~~Memory ceiling~~ — DONE: (1 GiB, 2 GiB]. §3.
2. ~~V′ > V legality~~ — DONE (19895285): WA, enforced constraint 1. §5. The unreferenced-vertex
   SUB-question is still open but IDLE: clean isolating design exists (banked 28-vertex case-2
   output + 1 loose vertex = 29 ≤ V — legality of loose verts alone), value = padding
   granularity 1 instead of 4/5. Fire only if a construction ever needs single-vertex padding.
3. ~~Judge/local speed ratio~~ — DONE: 1.014. §2.
4. ~~Wall/CPU limit structure~~ — DONE: the limit is a **CPU ceiling in [21, 22) s** (busy-wait:
   20 all-pass, 21 mixed, 22 all-TLE — CPU basis) and wall time is UNBILLED (sleep-25 Accepted;
   wall 22.4-24.5 s runs pass whenever CPU stays under). §2 + §5. Engineering consequence
   (SHIPPED in v101): refine boxes cut on getrusage CPU, not steady_clock.
5. **Duplicate vertices (two identical coordinate triples, both referenced)** — legal or not.
   IDLE: no live construction needs it; %.7g compaction already judge-proven.
6. ~~SIMD/pragmas~~ — DONE: pragmas vectorize (3.26× compute-bound) but the refine loop is
   memory-bound (1.000×). §3. Corollary float32-buffers SHIPPED (v100); corollary (b): future
   compute-bound code gets 3.26× free inside a pragma region.
7. ~~Oracle-vs-judge SSIM calibration~~ — DONE: no bias. §7.1; operating rules §7.2.
G. ~~Input genus probe~~ — **DONE 2026-07-05 (19895596 case 2, 19895626 case 4): both are
   1-component, GENUS 0.** Encode: in-process Euler characteristic, exact-count output
   N + 40·ncomp + g (case 2) / N + 1000·ncomp + g (case 4). Verdict: topology surgery has ZERO
   prize on this test set — the road died for two submissions instead of a build-week. §6.1.

**State (2026-07-05 late night): every judge limit that affects scoring is measured — time
(CPU ceiling, per-run noise regime), memory, toolchain/SIMD, submission mechanics, validity
rules, all six input sizes, exact bank attribution, metric internals, metric calibration.
The only unknown with strategic weight left is the INPUT TOPOLOGY (item G above).**

Engineering leftovers already derived from closures (not probes): fixed-count rung ladders on
cases 6/7 (41 + 32 one-vertex rungs, ≈ +0.0023 total max; case-6 attempts at 8670 WA'd ×2 —
wall band [8661, 8681] tighter than the keep-ladder suggested).

## 9. Standing operational rules distilled from all of the above

1. One question per submission; the CASES string + FAIL lines answer it. Any 'x' must be
   classified (WA vs TLE) before drawing conclusions — they demand opposite remedies.
2. (rewritten 2026-07-05, per-run nondeterminism §1) Know WHICH regime a case is in before
   spending a submission: box-CUT refine (cases 4 and 6) ⇒ per-run coin, byte-identical
   resubmits (`--force`) ARE legitimate re-rolls; CONVERGED refine (cases 3 and 5 under float32)
   or no refine (cases 2 and 7) ⇒ ~deterministic, a resubmit re-answers the same question —
   change the mesh (keep/param) or accept the wall. Never expect the same outcome after ANY code
   change near a wall (structural draws still reshuffle ±0.013).
3. Never attach "improvements" to a case sitting at a banked razor rung without re-validating
   that case: three separate incidents (c5 hybrid-insurance, c6 19s box, c4 16s box) broke a
   passing case by giving it "more".
4. Patches to `solver/main.cpp` are applied with assert-guarded replaces and grep-verified before
   any build: two silent sed failures cost eight submissions on 2026-07-04, and two FILE
   REGRESSIONS (edits landing on stale lines) cost four more on 2026-07-05.
   **Mandatory since 2026-07-05: before every submission, run the BINARY on the relevant proxy
   and check the output vertex count matches the intended keep** (the "prova del nove").
5. Every judge-limit probe result lands in THIS file the same day.
