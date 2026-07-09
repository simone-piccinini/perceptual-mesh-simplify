# case-3 ROADS — the living registry of algorithms/strategies (autonomously driven)

**Contract.** This is the master list of *roads* (algorithm/strategy directions) for beating our
score. The agent picks the top `QUEUED` road, works it, and updates its status here — WITHOUT
asking each time. **Policy: never stop, never "bank near the ceiling."** When a road dies it moves
to §2 with the reason; when a new idea appears it enters §3 ranked. Every claim carries provenance:
`[JUDGE]` real submission · `[LOCAL]` oracle/proxy (weak, §9.1 transfer) · `[INFERRED]` arithmetic.

**Status legend:** `QUEUED` (not started) · `ACTIVE` (being worked, with iter counter) ·
`DEAD` (measured/argued dead, struck) · `BANKED` (shipped a gain). Protocol: a road gets **≥10
iterations** before it can be called DEAD.

**Prize context (⚠ corrected 2026-07-08).** Leader total ≈ 91.46 vs our 90.286 → gap = 1.174 on the
MEAN = **7.05 summed** over 6 cases. If ALL of it were case-3: leader_c3 = 77.1% (NOT the 85% the old
docs claimed); it likely spreads across c4–c7 too → leader_c3 ~**72–77%**, a ≤7-pt case-3 gap. So
the prize is real but modest — cheap high-odds bets beat heavy low-odds builds. `[INFERRED]`

---

## 1. Current state
- **Bank = 90.285538 (7/7 Accepted).** Real. ⚠ `handoff/submissions.jsonl` is INCOMPLETE — it logs
  only judge_submit.py runs; web-UI submissions (incl. the bank) are NOT in it. **Never infer the team
  bank from the local ledger** — check Kattis.
- Reproducing 90.285538 in a draw is a per-DAY lottery: 2026-07-08 draws (8 subs) all landed c3/c5/c6/c7
  (SUM6 byte-identical 455.795742 → those cases deterministic per-binary) but WA'd **c4** (c4@4970 0/5,
  c4@4980 0/1; c4@5040 all-green but only 90.2525). So **c4's wall is higher on a cold judge day**;
  best-counts holds 90.285538 regardless; retry on a warm day.
- case-3 = 70.083% (N=6941, V=23201).
- case-3 compression wall PINNED at (6912, 6941] `[JUDGE]` — harvest below 6941 = 0 (LIMITS.md §A).
- The battlefield is the **normal-map STRUCTURE** term (σxy); depth saturated; topology genus-0;
  Hausdorff loose; CPU quality-bound not time-bound (LIMITS.md §C/§D).
- Local screens are known-biased (§9.1): position-space gains transfer ≈ 0; **structural** changes
  and throughput transfer. A structural LOCAL loss (e.g. VSA −0.10) is strong evidence of death.

## 2. DEAD roads (do NOT rebuild without a genuinely new angle)
| road | verdict | provenance |
|---|---|---|
| Cheap steering tweaks (nmetric/mask/projw/Lloyd/unsharp/qweight) | all local-negative | `[LOCAL]`+`[JUDGE]` |
| λ (Pivot-A strength) sweeps 12/24 | 70.06 rung WA'd both | `[JUDGE]` |
| R1 interleaved decimate↔refine | WA'd banked rung ×2 (proxies over-reward) | `[JUDGE]` |
| 768-native refine | judge-negative | `[JUDGE]` |
| Topology surgery / handle removal (Road A old) | genus-0 everywhere → zero prize | `[JUDGE]` |
| Construction paradigm (main_v2, cluster+grow) | caps ~64% on case-3 | `[JUDGE]` |
| VSA-guided collapse: B2 soft penalty, C/`g_vsac` hard constraint | dead (no retriangulation) | `[LOCAL]` |
| **Full VSA remesh (retriangulation)** — ROAD 1 | **>2.5× less efficient than QEM on organic; flat facets vs smooth normals (fundamental). Struck iter 10/10 2026-07-08.** | `[LOCAL]` decisive |
| Explicit jitter / basin-diversity (cost-jitter) | +0.0005, worse with more | `[JUDGE]`/`[LOCAL]` |
| Depth-complete optimizer | WA'd case4 | `[JUDGE]` |
| Deficit-guided edge-split reallocation (A/E1) | closed, no transfer | `[LOCAL]` |
| STAGE-2 free-layout 2D image fit (impostors) | 0.689 vs 0.810 mesh — continuity IS the σxy | `[LOCAL]` |
| **Normal-attribute quadric PLACEMENT (R-α, Hoppe/meshopt) — DEAD (neutral, no win)** | ARCHITECT-REVIEW §3.B.1 reopened it. Built the FULL Hoppe Vis'99 continuous attribute-quadric optimum (Schur 3×3 solve, plain doubles) under true incident_ndist; c3 band, env G_HOPPE. Judge: strip+Hoppe (r55/r55b) c3@6940 WA ×2; strip-ONLY (r55c) c3 PASS. **⚠ NOT cleanly attributable to the mechanism: Hoppe is a code change ⇒ re-rolls c3's box-cut family (law 4), so the WA can be a coin loss, not the mechanism.** The de-biased-proxy A/B (see 3.C.1 below) settles it: at c3's real operating point (proxy SSIM ~0.86) Hoppe Δ ≈ 0 (±0.0003, sign-unstable) — **neutral**, matching the smooth proxy. Verdict: no win (neutral); the r55 WA was the re-roll coin. Code removed (neutral + ~6 KiB at the cliff). | `[LOCAL]`+`[JUDGE]` |
| Dynamic in-loop metric steering (R-γ) | already implemented: Pivot-A runs 8 passes (main.cpp:1715), each re-renders the CURRENT mesh's deficit and re-steers; passes tuned (14 = −0.0002). | code |
| Curvature-adaptive isotropic remesh (R-β) | low-odds by theory: flat-shaded normal-SSIM favors ANISOTROPIC triangles (elongated along low-curvature) which QEM already gives; explicit aniso placement (g_aniso) is banked c4 but DEAD on organic c3/c6/c7. Isotropic is likely worse than our mild anisotropy. Demoted (not built). | `[JUDGE]`/theory |
| **True per-collapse box-SSIM selection (R-ζ)** | built + fail-fast tested (solver/ssim_greedy.cpp, QEM-sel vs true-rendered-SSIM-sel, same gates/placement). cow @700: +0.0022 (K8) / +0.0026 (K16); **organic bunny @800: +0.0001 (~zero)**. Real but tiny and mesh-dependent — ~0 on the SMOOTH-ORGANIC case-3 class (QEM already near-optimal there); won't survive transfer. Closes the collapse-SELECTION-metric family. Code kept. | `[LOCAL]` |

**Lesson from VSA (steers the queue):** the winning case-3 mesh is **smooth + dense + adaptive**
(QEM family). Flat/partition topology is the wrong direction for an organic surface. Any road that
introduces large flat facets is pre-doomed for case-3.

## 3. QUEUED / ACTIVE roads (ranked by EV = odds × prize ÷ effort)
Ordering is the execution order. The agent works the top non-DEAD road. NOTE: R-α, R-γ, R-β moved
to §2 (already maxed/implemented/theory-dead). The in-family smooth-QEM levers are now exhausted —
our pipeline already implements the report's *and* my own proposed improvements. What remains is
genuinely-new or out-of-family, all low-odds but that's the honest frontier.

### R-ζ — TRUE per-collapse box-SSIM selection — **CLOSED → §2** (fail-fast 2026-07-08)
Built solver/ssim_greedy.cpp (QEM-sel vs true-rendered-normal-SSIM-sel, same gates/placement).
cow +0.0022/+0.0026 (K8/K16) but organic bunny +0.0001 (~0) → dead for the smooth-organic case-3
class. Closes the collapse-SELECTION-metric family. The fail-fast (small-mesh brute-force) avoided
the heavy incremental build for a signal that isn't there. Code kept for reference.

### R-δ — Differentiable co-opt DURING reduction (full) — `QUEUED` · heavy · odds low · TOP
Interleave `refine_score_grad` position-ascent INTO the collapse loop (not refine-after). Stays
smooth. But ≈ R1 (judge-negative ×2) and refine is already converged post-hoc → low odds.

### R-ε — Cross-case gap reasoning (premise-correction lens) — `QUEUED` · analysis · odds low
The 7.05-pt gap is likely SPREAD, not all case-3. BUT we can't measure the leader's per-case scores
(Kattis 403s script tokens — leader tracking is manual/browser only). So this is reasoning-only:
our per-case room to 100% is c3=30 > c4=14 > c5=8.5 > c7=2.9 > c6=2.3 > c2=0.7, but every case sits
behind a MEASURED-hard wall (c3 all-levers-dead, c4 genus, c5 razor). No cheap point identified.

### R-θ — DE-BIAS the c3 proxy (ARCHITECT-REVIEW 3.C.1) — simple form FALSIFIED (iter 2/10) · odds dropped
The review's §9.1 diagnosis: proxies too smooth → position-space gains over-rewarded → don't
transfer. Its cure (§3.C.1): add scan-like high-freq displacement ALONG the normal until a known
judge A/B reproduces locally. Built `probe/make_noisy_debias.py` (seeded, topology-preserving),
calibrated against TWO judge signals at c3's operating point (proxy SSIM ~0.86, amp 0.0005):
- **Hoppe/R-α** (iter 1): Δ ≈ 0 (±0.0003, sign-unstable). Judge: ~neutral (WA confounded by re-roll).
- **R1** (iter 2, the CLEAN target — R1 is genuinely judge-negative incl. a DETERMINISTIC c5 WA
  19897122, not just a c3 coin): de-biased proxy reads R1 **+0.0029** (positive!) at the operating
  point — SAME sign as the smooth proxy, OPPOSITE the judge.
**Verdict: white-noise-along-normal de-bias does NOT reproduce the judge's transfer failures. 2/2
mechanisms fail to flip. The simple §3.C.1 recipe is falsified.** Likely because the injected noise
is RECOVERABLE by refine (it's on the original's vertices, so refine chases it) — unlike the
judge's real sub-triangle scan detail which the coarse mesh genuinely can't represent. Two deeper
obstacles: (a) box-cut nondeterminism (law 4) confounds every c3 mechanism A/B on the judge, so
clean c3 calibration targets barely exist; (b) validating a de-biased proxy needs clean judge
signals, which c3 (box-cut) denies. iter-3 (band-limited / unrecoverable-detail noise, calibrate
at c5-scale where signals are deterministic) is the only remaining variant — LOW odds now, and even
a c5-validated instrument may not transfer to c3. Instrument NOT trustworthy; not a screening tool.

### R-η — OUT-OF-FAMILY ideas (open slot — keep generating) — `QUEUED`
The in/near-family is exhausted, so real gains (if any) are out-of-family. Candidates to develop:
metric-exploit of the box-window covariance (normal dithering to match σxy at fewer verts —
speculative); silhouette-exact interior-starvation (lock the exact fg/bg boundary, starve interior).
Add here as ideas form. **Policy: this slot never empties — never conclude "at ceiling".**

## 4. Execution log (newest first)
- **2026-07-09 (R-θ iter 2)** — de-bias proxy (review's #1 lever) simple form **FALSIFIED**: built
  R1-toggle binary, measured R1 A/B on de-biased c3band across amplitudes. At c3's operating point
  (SSIM 0.86) R1 = **+0.0029** (positive, matching the SMOOTH proxy, opposite the judge). 2/2
  mechanisms (Hoppe, R1) fail to flip on the noised proxy. White-noise-along-normal doesn't
  reproduce the transfer failure (noise is refine-recoverable; judge scan detail isn't). Plus the
  box-cut confound denies clean c3 calibration targets. R-θ demoted to low-odds iter-3 only (§3).
- **2026-07-09 (r55)** — ARCHITECT-REVIEW §2 prerequisite DONE: **bonifica** stripped all
  judged-dead env gates + Eigen/Sparse from main.cpp (115.7→96.4 KiB source; re-applies v109's
  judge-validated ~109 MB cc1plus strip that the v111 bank lineage had lost). Byte-identical on
  every deterministic proxy; **judge-validated** (r55/r55c compiled, no OOM; c2/c5/c6/c7 paid
  banked rungs). Then **R-α (Hoppe attribute-quadric placement, the review's top pick #1)**
  built + judge-A/B'd: strip+Hoppe c3@6940 WA ×2 vs strip-ONLY c3 PASS. First read "Hoppe
  regresses"; corrected same day — the WA is confounded by the box-cut re-roll (law 4), and the
  **de-biased-proxy A/B (R-θ) shows Hoppe ≈ 0 at c3's operating point ⇒ NEUTRAL, no win** (§2).
  Hoppe code removed; bonifica kept as base. Also opened **R-θ (3.C.1 de-bias proxy)**: scan-noise
  un-saturates c3band but doesn't reproduce the judge signal at the right operating point (§3).
  c4 WA'd all three (cold-day coin, bank protected by best-counts).
- **2026-07-08 (cont².)** — R-ζ built (solver/ssim_greedy.cpp) + fail-fast tested + CLOSED: true
  rendered-SSIM collapse selection beats QEM by +0.0022 on cow but +0.0001 on organic bunny (~0 for
  the case-3 class). Collapse-selection-metric family definitively closed. R-δ now top (low odds).
- **2026-07-08 (cont.)** — R-α CLOSED (placement ablation on organic proxy @V=4212: nplace on/off
  neutral 0.8497/0.8498, qweight 0.1 worse 0.8446 → pure-normal already optimal). R-γ CLOSED (already
  implemented: 8-pass dynamic re-steering, main.cpp:1715). R-β demoted (theory: isotropic worse than
  our anisotropic; g_aniso dead on organic). → the in-family smooth-QEM levers are EXHAUSTED. Queued
  R-ζ (true per-collapse box-SSIM-delta, the one genuinely-new mechanism) as TOP; opened R-η
  out-of-family slot (never empties). Next: build R-ζ incremental-render delta.
- **2026-07-08** — External research report audited (§5): 0 new levers, validates our oracle.
  ROAD 1 (VSA remesh) built + measured DEAD (§2). Premise corrected (85%→77%). Registry created.

## 5. External research audit (2026-07-08) — a long report on Problem B, checked vs our measured data
Verdict: **0 new levers.** The report is a solid synthesis of the PUBLIC spec + generic mesh-simp
knowledge, but we are ahead on every measured specific. Value: it independently VALIDATES our oracle.

**CONFIRMS our judge model exactly** (→ `imc_eval` oracle is trustworthy): 6 axial cams D=2.5,
f=800, 1024², pp(512,512); normal (n+1)·127.5, bg gray; depth perspective 1/z, bg 255; SSIM 11×11,
C1=(.01·255)², C2=(.03·255)²; FinalSSIM = mean-6 of (0.5·N+0.5·D) ≥ 0.9; compression 100(1−V'/V);
case-size brackets. All match our measurements.

**WRONG where our data is authoritative — do NOT adopt:**
- Hausdorff: report says point-to-SURFACE ("every original vertex close to the simplified surface").
  Official clarification (2026-06-18, we hold it) = **vertex-to-vertex** ("a,b vary across vertices;
  not interior/surface points"). v2v is LOOSER. The report's stricter generic def would waste budget.
- "Optimal placement = minimize screen-space 1/z depth error": low value — **depth is SATURATED**
  (~0.984) on our cases; the binding term is normal STRUCTURE. The report doesn't know this.
- "Occlusion culling makes compression skyrocket": our cases are **genus-0 organic** (little hidden
  geometry); vis-culling gave case3 66→67 (small) and is DEAD >40k (sub-pixel false-hide −0.058).

**Already in our pipeline** (report frames as frontier): FA-QEM normal/silhouette weighting =
Pivot-A + s-def + per-channel + VSA-lite; curvature-aware cost; half-edge; Eigen (we STRIPPED it —
compile-cliff); local-oracle-with-rollback (+ we know the transfer wall it doesn't).

**Report is MISSING our hard-won edge:** per-run box-cut nondeterminism, transfer wall (§9.1), exact
walls, depth saturation, genus-0, VSA-remesh-dead, the 77%-not-85% correction.

**One convergent signal → reinforces R-α:** the report (and meshoptimizer's attribute-aware simplify)
independently point at a **normal-attribute quadric for PLACEMENT** (Hoppe). That is exactly R-α. So
R-α's priority is confirmed. (Fetching meshoptimizer for a head-to-head = low-EV/confirmatory — our
tuned perception-aware pipeline already exceeds vanilla QEM; no net access anyway.)
