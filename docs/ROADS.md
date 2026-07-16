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
| **Normal-attribute quadric PLACEMENT (R-α, Hoppe) — PARKED: neutral on an unreliable instrument, NOT killed** | Built the FULL Hoppe Vis'99 continuous attribute-quadric optimum (Schur 3×3 solve); c3 band, env G_HOPPE. Judge r55/r55b c3 WA vs r55c PASS is confounded by the box-cut re-roll (law 4), NOT clean. Local Δ≈0 was on the SMOOTH proxy — the very instrument §9.1 says is unreliable for position-space. So "neutral on a broken ruler," which is NOT "dead" (Process Law #2). Code removed for now (6 KiB at the cliff) but the finding is UNPROVEN. **Re-test on the transferring proxy once R-θ iter-3 yields one**, before any final verdict. | `[LOCAL-weak]` |
| Dynamic in-loop metric steering (R-γ) | already implemented: Pivot-A runs 8 passes (main.cpp:1715), each re-renders the CURRENT mesh's deficit and re-steers; passes tuned (14 = −0.0002). | code |
| Curvature-adaptive isotropic remesh (R-β) | low-odds by theory: flat-shaded normal-SSIM favors ANISOTROPIC triangles (elongated along low-curvature) which QEM already gives; explicit aniso placement (g_aniso) is banked c4 but DEAD on organic c3/c6/c7. Isotropic is likely worse than our mild anisotropy. Demoted (not built). | `[JUDGE]`/theory |
| **True per-collapse box-SSIM selection (R-ζ) — DEAD, CONFIRMED on the discriminating ruler 2026-07-10** | built + fail-fast tested (solver/ssim_greedy.cpp, QEM-sel vs true-rendered-SSIM-sel, same gates/placement). cow @700 +0.0022/+0.0026; smooth bunny @800 +0.0001. **RE-SCREENED on the ROUGH ruler (20k→4212, K16 R96): SSIM-sel − QEM-sel = −0.0003 — still ~zero.** Two independent scales agree ⇒ collapse-SELECTION-metric is genuinely maxed (QEM ordering near-optimal), NOT a blind-proxy artifact (Process Law #2 satisfied). **Meta: on the same test VSA-lite 0.6805 > both selection modes ~0.675 (+0.005) — our edge is normal-optimal PLACEMENT, not selection search.** Code kept. | `[LOCAL×2]` |

| **VIEW-DECOUPLING / per-view relief shells (open dim 5 + PROBLEM-AND-JUDGE's "componenti-rilievo per vista") — DEAD 2026-07-16, dominated at EVERY budget** | Hypothesis: 6 cheap per-view shells (each satisfying ONE camera, grazing band omitted, others hidden behind) beat one multi-view mesh; legality was sound (disconnected components judge-proven). MEASURED on happy_unit (unit scale, exact oracle, +Z view): relief blend 0.4709/0.5648/0.6304/0.7039 at N=480/1270/2600/6000 vs the CLOSED mesh at the same N = 0.4232/**0.6305**/**0.7032**/**0.7943**. At equal TOTAL budget (6 reliefs x1000 vs 1 closed x6000): each view gets ~0.53 from a shell vs ~0.79 from the shared closed mesh = **-0.27 blend**. Relief wins ONLY at <500v/view (0.47 absolute = irrelevant vs the 0.90 gate). The closed curve IS the adaptivity upper bound => no better-fitter escape. Sanity: undecimated relief scores 0.9945 (premise sound, economics fatal). **The old doc's guess "EV incerto per la perdita di condivisione multi-vista" is now MEASURED: surface sharing across views is a BENEFIT, not a tax.** Tools: `zoo/relief_hf.py` (heightfield fitter), `zoo/relief_vs_closed.py` (the equal-N closed curve), `zoo/relief_test.py` (QEM path: shreds open sheets — 7,441 boundary edges). Instrument note: the first 4 runs were invalid (proxies 9.5x under-normalized -> 34px blob renders). | `[LOCAL]` exact metric, true scale |

| **Constructive sigma-xy redistribution (edge_split at high rendered-deficit + collapse at saturated) — DEAD, JUDGE-falsified x4 (Alberto, session/all)** | Built from scratch + manifold-validated locally, then WA x4 on c3 with confounds excluded one at a time: 20043585 (completed, WA), 20044274 (QEM placement, excludes midpoint), 20044330 (byte-identical re-roll, excludes machine coin), 20044572 (ample refine + freed tail: WA at 16.6s with +4.4s margin, excludes starvation AND time). Verdict: **the c3 deficit is RESOLUTION-bound, not reallocatable.** Independently confirmed 2026-07-16: LT-2000 teleports on the faithful ruler = +0.0013 (per-mille). Reusable: `edge_split` primitive, per-face deficit measurement, and THE COMPILE-CLIFF UNLOCK (hand-rolled Eigen: power-iteration + Cramer 3x3 = 692MB, 14MB BELOW baseline, judge-validated) -> `sigmaxy-handroll/SIGMAXY-LOG.md`. | `[JUDGE x4]` |

| **From-scratch REMESH as c3 base (open dim 1: field-aligned / adaptive / anisotropic) — DEAD 2026-07-15** | Offline screen on the sign-validated instrument (happy_qem, equal N ~6.6k, oracle-scored, raw-vs-raw + ours-full as bound): ours 0.9524 / MeshLab QEM 0.9098 / **Instant Meshes (aligned+uniform) 0.9005** / **MMGS `-A` (adaptive+aniso) 0.8799** / MMGS iso 0.8726. Three instantiations span the design space; structural A/B ⇒ sign transfers (§2.1). Most-generous stacking (Marcum–Alauzet IMR23 alignment bonus 30–50% verts ≈ +0.02 + refine +0.01) lands ~0.91 ≪ 0.9524. **Mechanism: remeshers RESAMPLE — optimize the non-binding term (Hausdorff 3–4e-3 vs limit 1.14e-2) and low-pass the binding normal field; QEM keeps vertices ON original detail.** Both MMGS outputs also invalid (~195 non-manifold edges). Survivor: aniso > iso by +0.007 *within* MMGS ⇒ in-family anisotropy (flip-alignment prior) stays live; bears on ROAD B2's shape. Repro: `zoo/mmgs_screen.py` + `zoo/README.md` external checks; artifacts `zoo/build/{instantmeshes_6221,mmgs_aniso_6581,mmgs_iso_6585}.obj` (untracked). | `[LOCAL×3]` sign-validated ruler |

| **c4 DEPTH-REFINE gradient (G_WD blended proposal+accept) — DEAD 2026-07-15, judge-typed** | First mechanism to ascend c4's depth channel (weave in sil_score_depth + blended_sg; zpres killed only normal-sacrificing trades). Judge dose-response: wd=0.5 = +5e-4 [20055153/197 @4980], wd=1.0 = WA (gradient real). BUT sign FLIPS across rungs (wd=0.5 WA at 4950 where ctrl passes [20055312/371]) ⇒ trajectory-noise-dominated, no stable payoff — the same verdict class as allocation, now judge-side. Untested descendant: interior depth-contour SIL2 (coverage/directed-move class, not gradient). Tooling: scripts/c4wd_read_pair.sh + patch_wd_team.py; compile-cliff playbook in ATTEMPT_LOG 2026-07-15. | `[JUDGE ×6 reads]` |

| **c4 DEPTH attack (Z-saliency ALLOCATION `G_ALLOC_WEIGHT` + depth-PENALTY `G_ZPEN`/subset) — DEAD 2026-07-14** | Calibrated c4 proxy sourced (27 genus-0 ABC CAD parts, `probe/abc_tools/`, replacing the unfaithful fandisk) → c4 wall confirmed **DEPTH-SSIM**. **PENALTY + subset placement = INERT** (QEM ordering already depth-optimal; refine washes placement out). **ALLOCATION** (scale `Q[v]` by local depth-steepness) helps ONLY the 2 hardest proxies (base S2d 0.73–0.75: +0.054/+0.055), no-help or **CATASTROPHIC** on mid-baseline (00004629 α=1 = −0.293). Determinism test: deterministic per-binary yet **-O2 vs -O3-native FLIP the sign** (00005934 α=1 = +0.054/−0.036); α (~0.04) ≈ compiler trajectory variance (~0.03) ⇒ **TRAJECTORY-NOISE-dominated (§2.1 empirical)**. Judge c4 passes ≥0.90 ⇒ rung S2d~0.83–0.92 = no-help regime; NO baseline-predictable adaptive rule. Writeup `docs/C4-CALIBRATION.md`. Tooling kept (winbuild -O2, fast_sweep, alpha_grid, config_optimizer, saliency_validator). | `[LOCAL×2 grids]` |

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

### R-ξ — Silhouette-priority allocation (OUT-OF-FAMILY) — `QUEUED` · **COMMITTED next build**
The SSIM structure term is dominated by the per-view fg/bg SILHOUETTE (sharp normal discontinuity at
the boundary); the interior smooth-normal regions are near-saturated. Hypothesis: at fixed N, spend
the budget on the boundary — PROTECT vertices that project near a per-view coverage edge (lock/expensive
collapse), STARVE the interior (cheap collapse). Genuinely out-of-family: not selection (R-ζ dead),
not placement/position (refine maxed), and ≠ projw (projected-AREA protects grazing faces, not the
exact fg/bg boundary). Build: reuse the refine 6-view coverage render (g_orig_cov); mark a vertex
"silhouette" if it projects within k px of a coverage boundary in any view; multiply its collapse
cost. Env-gate `G_SILA`. Process (user): write env-gated → **screen ONCE on the rough ruler** (does
it beat VSA-lite 0.7039 at equal N?) → if yes, **JUDGE-TEST via an S-read pair on c3**. Alt if flat:
a direct box-window σxy-correlation objective (but refine already ascends full SSIM incl. s, and
s-def steers s — so verify that premise first). NOTE R-ν (densify/prune) is VACUOUS — coplanar
sub-faces = zero rendered-normal content (judge sees face normals); the non-vacuous part = Pivot-A
(done). Skip R-ν.

### R-ν — Content-adaptive densify/prune (vertex-budget REALLOCATION) — **DEAD (vacuous by construction)**
The discriminating ruler showed SELECTION is maxed and our edge is PLACEMENT — so the un-tried axis
is WHERE the budget is spent. Mechanism: after decimating to N, render the per-region rendered-normal
SSIM deficit, then reallocate net-neutral — extra-collapse in SATURATED regions, split/keep verts in
DEFICIT regions. Distinct from Pivot-A (which re-steers the COST, not the count allocation) and from
the graveyard's A/E1 edge-split (killed on the BLIND smooth proxy — so it deserves a rough-ruler
re-test, but the code is gone → rebuild). NOT built. **Screen on ab_orig (rough) BEFORE any judge
spend** (baseline VSA-lite refine-off 0.7039 / refine-on 0.7094). Effort: real build (~a session).
Odds: unknown but it's the honest frontier — the one lever the good ruler hasn't yet judged.

### R-δ — Differentiable co-opt DURING reduction (full) — `QUEUED` · heavy · odds low
Interleave `refine_score_grad` position-ascent INTO the collapse loop (not refine-after). Stays
smooth. But ≈ R1 (judge-negative ×2) and refine is already converged post-hoc → low odds.

### R-ε — Cross-case gap reasoning (premise-correction lens) — `QUEUED` · analysis · odds low
The 7.05-pt gap is likely SPREAD, not all case-3. BUT we can't measure the leader's per-case scores
(Kattis 403s script tokens — leader tracking is manual/browser only). So this is reasoning-only:
our per-case room to 100% is c3=30 > c4=14 > c5=8.5 > c7=2.9 > c6=2.3 > c2=0.7, but every case sits
behind a MEASURED-hard wall (c3 all-levers-dead, c4 genus, c5 razor). No cheap point identified.

### R-θ — DE-BIAS the proxy so local A/B transfers (ARCHITECT-REVIEW 3.C.1) — `ACTIVE` iter 3, CORRECTED protocol · the review's #1 lever
The review's §9.1 diagnosis: proxies too smooth → position-space gains over-rewarded → don't
transfer. **iter 1-2 (2026-07-09) were WRONG-DESIGNED and their "falsified" verdict is RETRACTED**
(architect handoff / Process Law #2 — don't close on a broken instrument at 2/10):
- WRONG NOISE: white-noise-along-normal is per-vertex independent → refine recovers it (SSIM's 11×11
  box averages it into a chaseable signal). That's why R1 still read +0.0029 — the instrument was
  still broken, not the road.
- WRONG CASE: calibrated on c3 (box-cut → judge A/B is a coin). The CLEAN target is **R1's
  DETERMINISTIC c5 WA (19897122)**; c5's proxy is armadillo ≈ the real judge input.
- WEAK SAMPLE: only R1 is a usable signal (Hoppe Δ≈0 discriminates nothing). 2/10, not DEAD.

**Corrected iter-3 protocol (in progress):**
1. Noise = COHERENT/band-limited (window-scale correlated, refine-UN-recoverable), not white.
   Tool: `probe/make_corr_noise.py` (white → graph-Laplacian smoothed S× → correlation length ~S
   edges → coarse mesh can't reproduce it).
2. Calibrate on **c5 (deterministic)** against R1's clean c5-negative — NOT c3.
3. **Decisive free shortcut (handoff C.2b):** a RAW Stanford range scan (real sensor noise) is the
   literal de-biased proxy, zero synthesis. Test: does R1 read NEGATIVE on a raw/native proxy
   out-of-the-box? If yes → "too smooth" confirmed + transferring instrument for free.
Success = R1 flips negative at the c5 operating point on the corrected proxy. Then this becomes the
offline screen that reopens 1-idea-per-submission → cheap iteration (the true bottleneck).

**iter 3-4 results (2026-07-09), clean c5 R1 baseline = +0.0004 on smooth armadillo (judge c5 =
deterministic NEGATIVE → a genuine transfer failure, the right target):**
| proxy | roughness | R1 Δ |
|-------|-----------|------|
| clean armadillo (smooth) | 0.0180 | +0.0004 |
| coherent-noise armadillo (make_corr_noise, amp .002-.004 sm6-12) | synthetic | **+0.0018 … +0.0043** |
| ab_orig = ARMADILLO @62,938 (rougher processing, SAME c5 model) | 0.0302 | **−0.0003** |

*(ab_orig identified: identical aspect [0.839,1.0,0.763] + centroid to clean armadillo ⇒ it IS the
c5 model, just a rougher 62,938-v processing. So on the ACTUAL c5 model, rougher processing → R1
negative = judge sign; smooth → positive. Concrete R-ι target: source/make a rougher armadillo at
c5's 49,987 count. Delta is tiny (−0.0003) so confirm with a cleaner-separated rough proxy.)*

**Two findings.** (1) SYNTHETIC displacement noise (white iter1-2 AND coherent iter3) makes R1 read
MORE positive, not negative — it ADDS refine-recoverable structure (the coarse mesh CAN chase
window-scale bumps; SSIM's 11×11 box averages sub-window white noise into a chaseable signal). So
synthetic-noise de-bias is the WRONG tool — retired. (2) The one NATURAL rougher closed mesh on
hand (ab_orig, 62938 v, unknown provenance) is the ONLY proxy where R1 flips NEGATIVE, matching the
judge. Tiny (−0.0003) + unidentified mesh ⇒ suggestive, not conclusive — but it points the road at
**real rougher judge-class meshes (DATA-SOURCING §3.C.2), NOT synthesis.** Mechanistic reason the
transfer-killer is narrow-band (sub-coarse-triangle yet box-surviving detail) that real scans have
intrinsically and displacement noise misses. Road ACTIVE; next = §3.C.2 data-sourcing (below).

### R-ι — DATA-SOURCING: real judge-class meshes (ARCHITECT-REVIEW §3.C.2) — `ACTIVE` · c4 arm DELIVERED 2026-07-14 (27 genus-0 ABC CAD parts, `probe/abc_tools/`; c4 wall reproduced — but the c4 mechanisms it enabled all died, ROADS §2); c3/c5/c6/c7 arms still `QUEUED`
The de-bias's RIGHT form (R-θ iter-4 showed synthesis is wrong; natural roughness flips R1). Get
the judge's actual STANDARD models at its vertex counts, not decimations-of-clean-armadillo:
- c5=49,987 ≈ Stanford armadillo (49,990) — ours reads "+0.055 friendlier" ⇒ judge uses a DIFFERENT
  (rougher) processing. Source a rougher/native ~50k armadillo, re-run the R1 A/B — the clean
  deterministic calibration target.
- c6≈377k→dragon(~437-566k) decimated; c7≈1M→dragon/buddha/lucy/thai to 1M; c3≈23k→a NATIVE ~23k
  organic (not decimated-from-50k) for a faithful c3 SSIM screen; c4→CAD/ABC class.
- **Decisive free shortcut:** a RAW Stanford range scan (real sensor noise) = literal de-biased
  proxy. Does R1 read NEGATIVE out-of-the-box? If yes → "too smooth" confirmed, transferring
  instrument for free. (Caveat: raw scans are OPEN/partial; the judge input is closed — closing via
  Poisson re-smooths, so use the native scan directly for the SSIM A/B, not as solver input.)
Net access confirmed (graphics.stanford.edu 200). Effort: hours (download+reprocess). Highest-value
concrete task (handoff Part E.3). Identify ab_orig too — it may already be a usable rougher proxy.

### R-κ — DETERMINISTIC REFINE (kill the box-cut coin) — `ACTIVE` iter 3 · c4 + c3 SHIPPED + Accepted
**c3 DETERMINISM SHIPPED 2026-07-10 (sub 19934300, ACCEPTED 90.285538 7/7, SUM6 bit-identical).**
c3 refine = 3 loops: phase-A(512)=27 converges (uncapped), phase-B(1024)=18 = coin → `g_phaseb_maxit`
cap 16, RC3 mini_refine=2 → `g_mini_maxit` cap 2 (both c3-band default, env G_PHASEB/G_MINI). c3 mesh
UNCHANGED (16 vs 18 = trailing rejects) → deterministic at zero cost. **This is the PORTFOLIO UNLOCK:
c3 A/Bs are now clean (variant−control = the lever, not the coin).** ⚠ c7 21.0s (margin 0.0) = TLE
live — c7 is unaffected by this diff (deterministic/no-refine); needs a throughput/decimation-speed
pass, not a refine cap. Next: run σxy/nmetric=3 + Hoppe-retest as clean c3 reads on this base.
Below = earlier iters:
**SHIPPED 2026-07-10 (sub 19934022, ACCEPTED 90.285538 7/7).** `maxit_for(V)` caps c4-band
stock_pass at 36 iters (default; env `G_MAXIT` overrides). c4 = the box-cut coin, JUDGE-ONLY (dev
converges at 38 iters/7.7s; judge ~1.4× slower → wall-box cuts ~37 jittered). Cap 36 (near-converged,
NOT sub-wall) → deterministic c4 by construction. Judge: c4 V'=4970 (banked rung), Accepted, CASETIME
16.2s (cap bound near prior op point). c2/c3/c5/c6/c7 byte-identical to bonifica base (only c4 input
35292 ∈ 30k–40k). Repro force-re-roll in flight. TODO: confirm lock (c4 reproduces); optionally
extend to c3 (1024 phase-B) — but c3 is the prize + razor, and c6/c7 are TLE-tight (19.2/19.9s), so
leave them on the coin unless a clean margin appears. R-κ was iter 1 below:
Replace the refine wall-clock time-box with a fixed ITERATION COUNT → same mesh every run →
de-confounds every A/B (law 4) and stabilises the bank. Env-gated mechanism wired 2026-07-10
(`g_refine_maxit`, env `G_MAXIT`; `G_ITERDBG` prints iters); default huge = legacy behavior, ZERO
bank risk. Findings iter-1:
- **c5 is NOT the coin**: converges at exactly **94 stock_pass iters, byte-identical mesh** across
  runs (CPU jittered 14.9–17.1s but iters/mesh fixed). Matches "c5 deterministic".
- The coin lives in the loop that does NOT converge in budget: c3's 1024 phase-B, c4/c6 plain
  stock_pass. The current per-call `it>=maxit` cap is correct but must target THAT loop; SIL calls
  stock_pass 4× (each <50) so a total-iter intuition misleads.
- **Value = de-confounding future A/Bs + DEV-BASE reproducibility, NOT bank harvest** (best-counts
  already re-rolls the coin for free). Not where points come from — keep it cheap/parallel (Law §8.1).
- **⚠ HAZARD: never determinize a RAZOR case (c4/c6) at a sub-wall iteration count** — that converts a
  passing coin into a deterministic WA. Determinize the DEV base with MARGIN; keep BANK attempts on
  the free coin (submit the time-boxed binary, let best-counts catch the good draw).
- TODO: cap phase-B / c4 / c6 loops; size maxit per case (their meshes OR free judge CASETIME probes
  — NOT proxy-gated); raise g_refine_budget to a pure TLE backstop above maxit·cost. `ATTEMPT_LOG` 07-10.

### R-μ — meshopt (LEGGIMI/) as OFFLINE REFERENCE → revive PARKED Hoppe — **PARKED / not worth porting** (2026-07-10)
meshoptimizer's `simplifier.cpp` = SOTA QEM + attribute-quadrics (= Hoppe's appearance metric) +
Lindström–Turk volume term. Two findings (NOTE: numbers below are SUSPECT — see caveat):
- **C2 not shippable**: 101 KiB alone, +our I/O ≈121 KiB at the 7 KiB cliff margin (drops refine);
  output non-manifold — judge needs closed 2-manifold. So there is no reason to PORT it. (This is the
  firm conclusion; the SSIM ranking below is not.)
- **⚠ SUSPECT NUMBERS:** the meshopt output was NON-MANIFOLD → `mo_driver.cpp` likely misses
  lock-border / attribute-seam / error-absolute flags, so the SSIM losses are partly holes, not the
  algorithm. Do NOT read this as "attribute-quadric is fundamentally dead." It means "not worth
  porting + no clean win seen." To claim the mechanism dead, re-run with correct manifold flags.
- **C1 offline eval (indicative, on the TRANSFERRING ruler)** — decimate ab_orig(rough) &
  clean armadillo → N≈4212 with meshopt vs our VSA-lite (refine off), oracle rendered-normal SSIM:

  | N≈4212 | ROUGH nSSIM | CLEAN nSSIM |
  |---|---|---|
  | **ours (VSA-lite)** | **0.7039** | **0.7176** |
  | meshopt nw=0 (pure QEM) | 0.6486 | 0.6579 |
  | meshopt nw=1 | 0.5239 | — |
  | meshopt nw=5 (attr-quadric) | 0.5131 | 0.5006 |

  meshopt scores below ours here, and attribute weight monotonically lowers rendered nSSIM — but the
  non-manifold caveat above means this is INDICATIVE, not a clean kill. Hypothesised mechanism (if
  real): attribute quadric minimizes VERTEX-normal L2, trading position accuracy → worse
  silhouettes/face-normals → worse RENDERED SSIM; our VSA-lite orders by induced RENDERED-normal
  distortion (the right objective).
- **Knock-on to R-α (Hoppe, parked): LOW-EV, NOT dead-forever.** Same attribute-quadric family; no
  clean win seen on the transferring ruler, but the evidence is confounded (non-manifold). Re-test
  only with a genuinely new angle OR a manifold-correct meshopt re-run. Driver kept:
  `LEGGIMI/mo_driver.cpp` (+ fetched header) — add lock-border/seam flags before trusting its SSIM.
- **The real yield: a TRANSFERRING RULER.** ab_orig(rough) DISCRIMINATES (0.70 clearly separable
  from meshopt 0.51–0.65), unlike the saturated smooth proxy (all ~0.85). Sign-validated (ab_orig
  R1=−0.0003 = judge sign). Use it to screen pipeline changes offline (see R-ι, R-κ).

### R-η — OUT-OF-FAMILY ideas (open slot — keep generating) — `QUEUED`
The in/near-family is exhausted, so real gains (if any) are out-of-family. Candidates to develop:
metric-exploit of the box-window covariance (normal dithering to match σxy at fewer verts —
speculative); silhouette-exact interior-starvation (lock the exact fg/bg boundary, starve interior).
Add here as ideas form. **Policy: this slot never empties — never conclude "at ceiling".**

## 4. Execution log (newest first)
- **2026-07-10 (meshopt + instrument, user Option-3+4-constraints)** — LEGGIMI/ = meshoptimizer.
  C2 shippability: NOT a ship candidate (101 KiB + non-manifold) → offline reference. C1 eval on
  ROUGHER proxy (the user's key constraint — smooth misleads): meshopt scores below our VSA-lite on
  BOTH rough (0.51–0.65 vs 0.70) and clean — BUT its output is non-manifold (driver missing
  lock-border flags) ⇒ **R-μ not-worth-porting (not shippable); numbers SUSPECT; R-α Hoppe LOW-EV,
  not dead**. Yield = a TRANSFERRING RULER (ab_orig rough proxy discriminates + is
  sign-validated). C3 det-refine mechanism wired (env `G_MAXIT`/`G_ITERDBG`, bank-safe): c5 confirmed
  NOT the coin (94 iters, byte-identical); coin is c3/c4/c6 non-converging loops → R-κ ACTIVE.
  r56: bonifica base RE-BANKED 7/7 (90.285538). Bank untouched. THEN re-screened the graveyard on
  the ruler: R-ζ (top pick) SSIM-sel−QEM-sel = −0.0003 on rough (bunny +0.0001) ⇒ selection-metric
  CONFIRMED dead on a discriminating ruler; meta = our edge is PLACEMENT not selection. No buried
  lever resurrected. Next = R-ν content-adaptive densify/prune (REALLOCATION axis; must be BUILT).
- **2026-07-09 (R-θ iter 3-4, CORRECTED per handoff)** — "falsified" RETRACTED. Rebuilt with
  coherent noise (`make_corr_noise.py`) + calibrated on the CLEAN deterministic target (R1's c5
  WA). Clean c5 R1 = +0.0004; coherent-noise armadillo R1 = +0.0018..+0.0043 (synthesis ADDS
  recoverable structure → wrong way, retired); **ab_orig (natural rougher mesh) R1 = −0.0003, the
  ONLY sign-match to the judge.** ⇒ de-bias direction confirmed ("too smooth" real), synthetic
  noise is the wrong tool, path = DATA-SOURCING (R-ι, real rougher meshes). Road stays ACTIVE
  (not buried — Process Law #2). Audited refine_score_grad (Part E.1): sound + fused, no bug.
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

---

## ROAD B2 — CONSTRUCTIVE ANISOTROPIC TAIL (the 90.6+ / leader-gap project) — QUEUED 2026-07-12

**Why this and not more tuning:** the incremental paradigm's ceiling is MEASURED ten ways
(2026-07-11..12 lab campaign): every tail/placement/cycle refinement yields e-5..e-4; the
no-time-limit ceiling of image-driven collapse ordering is N≈6650 (S-calibrated); the leader
needs N≈5300-6300 = an e-3-class structural gain. The missing e-3 is ANISOTROPY: case 3's
curvature ratio |k1|/|k2| has median 3.59 (curved-half 4.91), and mesh-adaptation theory gives
~sqrt(aniso) vertex savings (1.9-2.2x) for curvature-aligned stretched triangles — exactly the
leader's edge size. Our collapse-based pipeline cannot reach it: QEM/SSIM collapse ORDER produces
isotropic-ish meshes; the anisotropy must come from PLACEMENT+CONNECTIVITY built along the
curvature field.

**Design sketch (build order):**
1. Per-vertex curvature frame field on the INPUT mesh (2-ring quadric fit — the aniso.py pass
   ported to C++, ~80 lines, done once, ~0.3s).
2. Anisotropic edge-length metric M(v) = diag(1, 1/a(v)) in the principal frame (clamp a to
   [1,4]); use METRIC edge length in the collapse ORDER (replaces/augments QEM cost) and in the
   collapse PLACEMENT (optimal point under M, not Euclidean QEM).
3. Tangential smoothing pass in metric space every K collapses (Palfinger-style relocation,
   but accepted on the rendered score like mini_refine — we have the machinery).
4. The existing lazy image-driven tail stays as the FINISHER (last 200) — it corrects the
   metric heuristic's mistakes against the true rendered SSIM.
5. Gate per band; c3 first; K-read calibration at each milestone (threshold 0.9135 self-score).

**Risks:** VSA-remesh died on organic (flat facets) — but that was PARTITION-flat, not
curvature-aligned smooth; Hoppe/meshopt died as METRICS, not as anisotropic placement. Neither
buries this. The real risk is time-to-build (~1-2 days) vs contest end.

**Falsifier (cheap, do FIRST):** before building the full metric pipeline, test anisotropy's
value directly: scale the QEM quadrics per-vertex by the curvature frame (a 20-line change to
Initialize's quadric accumulation) and measure S2n at fixed N on the c3 proxy. If metric-weighted
quadrics gain nothing at e-4 scale, the anisotropy thesis needs rework before the big build.

**ROAD B2 FALSIFIER VERDICT (2026-07-12, K-read 20029030):** naive anisotropic quadrics (normal-
covariance frame, w=2) read S_judge = 0.911 at N=6790 vs 0.91356 baseline = **−2.6e-3 on the real
judge mesh** while gaining +8e-4 (family mean) on the smooth proxy — the canonical proxy-bias
signature (§9.1). NOT dead-forever: the thesis requires a NOISE-ROBUST curvature field (bilateral/
multi-ring smoothing of the frame) before the metric is trustworthy on raw scans. That is the
real Road B2 build; budget days, use K-reads at every milestone.

**ROAD B2 SECOND VERDICT (2026-07-12, K-read 20029061):** the noise-robust frame (3-iter bilateral
normal smoothing) read S_judge = **0.9095 = −4e-3** — WORSE than naive. Quadric-level anisotropy is
judge-dead in both forms. ⚠ The rough proxy (ab_orig) PREDICTED +8.7e-4 and was wrong for this
mechanism class — its transfer validity is mechanism-dependent (held for collapse-ordering metrics,
failed for quadric-term additions). Any B2 revival must (a) put anisotropy in the image-driven TAIL
(which self-corrects against the true rendered metric) not in global quadrics, and (b) trust only
K-reads. The collapse-paradigm ceiling (~6650 = ~90.55) stands as the roof until a mechanism of a
different class exists.

## 2026-07-13 pm — coordinated-move class CLOSED (local, exact evaluator)
After refine+SIL2 the c3 silhouette is a MEASURED local optimum: all 6700 exact evals of
3-6-vertex coordinated segment slides (14 dirs x {1,2,4}el) are NEGATIVE (-2e-5..-1e-4, gate
working, distribution instrumented). Big single steps (4x/8x el): negative. Barrier-crossing
anneal (accept >-thr in r1, positive r2-r3, bug-fixed): -1.8e-4 vs pos-only. The residual rim
deficit is RESOLUTION (polygonal rim vs smooth arc), not position — needs more rim verts
(realloc: judge-dead) or different tessellation. DEAD: sil3 segments, sil2-big-steps,
sil2-anneal. Code: /tmp/mein_seg.cpp (scratch).

## c2@28 CLOSED x3 mechanisms [JUDGE 20036392/20036456/20037066]
bare WA, +SIL2 WA (9.3s clean), +RIM-BUDGET WA (4.0s clean). c2 floor = 29 verts, final.
