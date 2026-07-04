# THE JUDGE ENVELOPE — what we can and cannot do, and how we know it

This is the operational contract with the judge. Every claim is tagged with its provenance:

- **[MEASURED]** — established by a dedicated probe submission (ID given). Highest trust.
- **[OFFICIAL]** — stated in the problem PDF or an organizer clarification. Trust the words exactly.
- **[INFERRED]** — derived arithmetically from scores/verdicts. Strong but indirect.
- **[UNTESTED]** — assumed from Kattis conventions or unstated. A probe candidate.

Keep this file current: any probe that touches the judge's limits gets its result recorded HERE,
not only in ATTEMPT_LOG. Last full revision: 2026-07-05.

---

## 1. Execution model

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

- Compiler/flags: Kattis-controlled; we cannot pass flags. Behavior consistent with g++ -O2.
  [UNTESTED — exact flags unknown; irrelevant so far.]
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

## 9. Standing operational rules distilled from all of the above

1. One question per submission; the CASES string + FAIL lines answer it. Any 'x' must be
   classified (WA vs TLE) before drawing conclusions — they demand opposite remedies.
2. Never resubmit a byte-identical source expecting a different outcome (determinism); never
   expect the same outcome after ANY code change near a wall (draws).
3. Never attach "improvements" to a case sitting at a banked razor rung without re-validating
   that case: three separate incidents (c5 hybrid-insurance, c6 19s box, c4 16s box) broke a
   passing case by giving it "more".
4. Patches to `solver/main.cpp` are applied with assert-guarded replaces and grep-verified before
   any build: two silent sed failures cost eight submissions on 2026-07-04.
5. Every judge-limit probe result lands in THIS file the same day.
