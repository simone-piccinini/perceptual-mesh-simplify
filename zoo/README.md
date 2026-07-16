# The Variant Zoo — c3 mechanism screen on the calibrated instrument

STATE: 2026-07-14. Purpose: screen ~50 solver variants per night on `probe/cache/c3cand/dragon_n10.obj`
(the calibrated c3 proxy: S2(6775)=0.9143 vs judge 0.9145) instead of spending 2–8 judge submissions
per idea. **This is a SCREEN, not an oracle**: winners above the noise floor get judge K-read pairs
before anything ships; the embedded CONTROLS check the instrument's sign-fidelity every pass.

## How to run (tonight)
```bash
cd ~/Desktop/IMC/perceptual-mesh-simplify
py -3 zoo/run_zoo.py --list      # the catalog
py -3 zoo/run_zoo.py --smoke     # 3-variant sanity (~3 min): base + env-variant + patch-variant
py -3 zoo/run_zoo.py --all       # full zoo, resumable (first pass ~25-40 min)
py -3 zoo/run_zoo.py --report    # ranked table any time -> zoo/RANKED.md
# optional second passes:
py -3 zoo/run_zoo.py --all --mesh probe/cache/c3cand/happy_qem.obj   # cross-mesh check of winners
py -3 zoo/run_zoo.py --only mini_32 repair_20 --rung 6500            # winners at a deeper rung
```
Architecture: `zoo/variants.py` = the catalog as data · `run_zoo.py` = patch→build→run→rank ·
`zoo/build/mein_<name>.cpp` = **one generated source file per method** (never touches `solver/mein.cpp`)
· `zoo/results.jsonl` = append-only, resumable · `zoo/RANKED.md` = the morning read.

## How to read RANKED.md
- **NOISE FLOOR** = max(1.5e-3, 2σ) from base×3 + two trajectory re-rolls (traj_a/b). Anything inside
  it is *flat*, not a win — the c4 lesson (α ≈ trajectory noise) made quantitative.
- **Controls acceptance**: rim_off/tail_off/qw_005/nplace_off/mpc_off have JUDGE-known signs. If they
  MISS above the floor, distrust the whole pass (instrument problem), not just them.
- **DUPE(base)**: byte-identical S2 to base = the env knob didn't engage (wrong name/registered off).
- A **WIN** = candidate only. Next step is 2 judge K-reads (control+variant), not a bank attempt.

---

## The catalog (what each method is, and why it's here)

### Controls — instrument acceptance (judge-known signs)
| variant | what | why |
|---|---|---|
| base_a/b/c | banked config ×3 | reference + determinism check |
| traj_a/b | tail box ±0.05s | pure trajectory re-roll → measures the local draw σ (the noise floor) |
| rim_off / rim_035 | RIM-BUDGET off / half | judge-VALIDATED positive (wall 6700→6610) ⇒ must read NEGATIVE here, monotone |
| tail_off | image-driven tail off | judge-banked positive ⇒ must read NEGATIVE |
| qw_005 | qweight 0→0.05 | judge-WA'd (#19885312) ⇒ must read NEGATIVE |
| areaq | area-weighted quadrics | judge-HURT on c4/c6 ⇒ expect ≤0 |
| nplace_off | normal-optimal placement off | shipped +0.0006 ⇒ must read NEGATIVE |

### A. Ordering — *which edge collapses first* (the user's "shifting edge priority")
| variant | what | why |
|---|---|---|
| rim_100/140/200 | rim-budget 1.0/1.4/2.0 (banked 0.7) | the one judge-positive c3 allocation knob: find its peak |
| lam_8 / lam_24 | Pivot-A deficit-steering λ 16→8/24 | steering strength never swept on a faithful ruler |
| alloc_05/10 | steepness-scaled quadrics (G_ALLOC_WEIGHT) | c4-inert (noise-bound) but organic c3 is a different regime |
| zpen_3 | depth-steepness collapse deferral | same: re-screen the c4-dead mechanism on organic |
| hid_deep | hidden-pair factor 1e-4→1e-6 | collapse never-visible verts even earlier → budget to visible ones |

### B. Kernel / placement — *the error metric and where the merged vertex lands* (the user's "different kernel")
| variant | what | why |
|---|---|---|
| salcost_05/10 | **NEW**: steepness saliency as rim-style COST multiplier | allocation via ordering (not quadric scale) — the deficit-field idea, v1 |
| subset_c3 | kept verts stay on original positions | placement-freedom ablation (semi-control) |
| aniso_on | curvature-aligned placement candidates | banked on c4 CAD; "dead on organic" verdict came from the OLD ruler — re-screen |
| deteps_8/12 | QEM solve regularization ±2 decades | how often the optimal-point solve vs fallback fires — never swept |
| flip_m02 | relax the normal-flip gate to −0.2 | c3 default is strict 0.0; c4 profits from −0.5 — is c3's gate too tight? |

*Queued, not tonight:* full Hoppe attribute-quadric placement (kernel change; judge-tested ≈ no-win
[sub history 8fbffb0], recoverable from commit f10f2ab if we want it as another control).

### C. Tail — the image-driven last ~300 collapses
| variant | what | why |
|---|---|---|
| pool_400/1200/2500 | lazy-tail candidate pool (banked 700) | depth-vs-quality curve; 2500 = "what would an unaffordable tail buy?" |
| ctb_50 / ctb_85 | tail box 5.0s / 8.5s | convergence margin of the banked 6.5s box |
| rb_48 / rb_96 | re-render burst 24→48/96 | score-freshness vs commit-throughput tradeoff |
| mpc_off / mpc_classic | multi-placement off / classic-only | decompose the judge-validated MPC gain (which part is active?) |

### D. Polish / refine — **the re-priced family** (M0 measured +4.3e-3 S2n TLE-gated headroom here)
| variant | what | why |
|---|---|---|
| mini_16/32/64 | mini_refine iteration cap 8→… | the cap was chosen for TIME (determinism); the c5-POLISH transplant, axis 1 |
| repair_20/30 | repair-burst budget 1.2s→2.0/3.0 | axis 2 of the same transplant |
| lsiter_2/3 | guided-seed→refine cycles ×2/×3 | family read +1.35e-4 at 1 cycle — does it stack? |
| lsres_768 | guided seed at 768 | cheaper seed frees budget downstream |
| lac_05 | laplacian-of-residual (AC) seed | exploratory: the residual field's zigzag structure |
| budget_30 | refine wall-clock 16→30s | the in-pipeline convergence ceiling (TLE-irrelevant locally; sizes the prize for a throughput attack) |

### E. Schedule / structure
| variant | what | why |
|---|---|---|
| stage2_15/30 | bulk-QEM to 1.5×/3× then ordered finish | c7's speed trick — quality question on c3 |
| redecim | decimate→refine→RE-decimate (+400 overshoot) | Road-B item 2 lite: re-run the ordering on SSIM-optimal geometry (a different basin per cycle) |
| sil2_400 | silhouette pass 200→400 evals | judge-costed (+1.8s); what does it buy in quality? |
| c3t_6700/6500/6400 | rung sweep | S(N) curve: sanity (+) above, and the exact deficit any 91-mechanism must cover below |

---

## Provenance rules (unchanged)
Every number this produces is `[LOCAL]` on a calibrated-but-provisional instrument. A WIN here buys a
**judge K-read pair**, nothing more. The controls section is the instrument's ongoing acceptance test —
the first pass where controls read correctly is also the pass that upgrades the instrument from
"provisional" to "sign-validated" (ROADS R-θ/R-ι).

---
## PASS-1 VERDICT (2026-07-14 night, dragon_n10 @6610) — instrument REJECTED by its own controls
Infrastructure: all 53 variants ran (patch/env/reuse/rung all exercised); DUPE-detection caught a
dead knob (G_SUBSET force-disabled at mein.cpp:1984 — also corrects the c4 subset erratum) and the
fork-inert tail family. **Controls: 1 OK / 6 MISS — rim_off +0.0044 and nplace_off +0.0085 read
POSITIVE (judge says both mechanisms are positive, so removing them must read negative).**
dragon_n10 matches the judge's DIFFICULTY (level+slope) but INVERTS placement/allocation mechanism
signs ⇒ demoted to S(N)-difficulty studies only. The pass-1 "WINs" (aniso_on +0.0047, stage2_30
+0.0016) are THEREFORE UNTRUSTED — no K-reads on them. Next: acceptance-test other geometry classes
(happy_qem running; thai/lucy candidates next) — the controls subset is a 2-minute test per
candidate, which is the loop's whole point.

---
## EXTERNAL CHECK 2 (2026-07-15): field-aligned remeshing (Instant Meshes) — uniform-aligned LOSES big [LOCAL]

Testing the "leader uses a non-QEM base" hypothesis (ALGORITHM-LOGIC §9 open dim 1). Instant Meshes
(Jakob 2015, official Windows binary, batch `-r 6 -p 6 -v 6610 -d`) on happy_qem, oracle-scored at
equal-N vs the pass-2/3 baselines (same mesh, same oracle; ours re-confirmed 0.9524 this session):

| mesh | N | oracle FinalSSIM | notes |
|---|---|---|---|
| ours (full pipeline) | 6,610 | **0.9524** | refine+tail included |
| MeshLab QEM (raw) | ~6,453 | 0.9098 | no refine |
| **Instant Meshes (raw)** | 6,221 | **0.9005** | 4 non-manifold edges; Hausdorff OK; undershot -v 6610 |

Adjustments don't save it: vertex handicap (389v × 1.06e-5 ≈ +0.004) + a generous refine-class bonus
(+0.005–0.01) still leaves it ~0.035 below ours. Vs MeshLab at matched N it's a TIE (~0.907 vs 0.9098)
⇒ **edge ALIGNMENT alone adds ≈0 over plain greedy QEM; the pipeline's edge is ADAPTIVITY** (hidden-
first, deficit steering, rim budget), which uniform field-aligned meshing throws away. Structural
local LOSS = transferable evidence (CLAUDE §2.1). Artifact: `zoo/build/instantmeshes_6221.obj`.

**SAME DAY, TIER 2 — MMGS (MmgTools 5.6.0, INRIA metric-based remesher) closes the branch.**
Adaptive iso (`-nr`, hausd-bisected to N) and adaptive ANISO (`-A -nr`) at the same rung:

| mesh | N | oracle FinalSSIM | validity |
|---|---|---|---|
| ours (full) | 6,610 | **0.9524** | ok |
| MeshLab QEM raw | ~6,453 | 0.9098 | ok |
| Instant Meshes raw | 6,221 | 0.9005 | 4 nm edges |
| MMGS aniso raw | 6,581 | 0.8799 | 199 nm edges, near-degenerate slivers |
| MMGS iso raw | 6,585 | 0.8726 | 193 nm edges |

Most-generous stacking for the best remesh: 0.8799 + ~0.02 alignment bonus (Marcum–Alauzet IMR23
measure 30–50% fewer verts for aligned-vs-MMGS-class × happy slope 1.06e-5/v) + ~0.01 refine-class
≈ 0.91 ≪ 0.9524. **VERDICT: the "leader uses a from-scratch remesher" hypothesis is dead on the
sign-validated instrument across 3 instantiations (uniform-aligned / adaptive-iso / adaptive-aniso).**
Mechanism: remeshers RESAMPLE — they satisfy the non-binding constraint (Hausdorff, 3–4e-3 vs limit
1.14e-2 in every run) while low-pass-filtering the normal field that IS binding; QEM keeps surviving
vertices ON original detail. Nugget that survives: aniso beat iso by +0.007 *within* MMGS — elongation
is not poison; the only live descendant is IN-FAMILY anisotropy (flip-alignment prior class).
Artifacts: `zoo/build/mmgs_aniso_6581.obj`, `zoo/build/mmgs_iso_6585.obj`.

---
## PASS-2/3 VERDICT (2026-07-15, happy_qem = sign-validated instrument) — one path survives

**External validation closed:** on the validated mesh OUR pipeline beats MeshLab's independent QEM
by **+0.043** oracle-FinalSSIM at equal N (0.9524 vs 0.9098) — the dragon "meshlab win" was pure
inversion artifact. Oracle == self-score to 4 decimals on both meshes (the +0.010 judge-optimism is
mesh difference, not scoring math). Pipeline and instrument cross-validated in one test.

**stage2 DEMOTED to lottery-knob:** the ×k curve swings −0.0047…+0.0015…−0.0040 across adjacent
settings on happy — schedule changes re-roll the decimation basin with σ≈3e-3, so its lone +0.0015
spike is not evidence (it IS a useful draw-family generator for the team's ladder rotation).

**THE SURVIVOR — polish cap (G_MINI 8→16):** the dS2-vs-base map on happy:
| cap | @6610 | @6500 | @6400 |
|-----|-------|-------|-------|
| 12  | +0.0011 | +0.0025 | — |
| 16  | **+0.0014** | **+0.0026** | **+0.0022** |
| 24  | +0.0011 | +0.0025 | — |
| 32  | +0.0011 | +0.0026 | +0.0022 |
Saturates at cap≈12–16 (converged = M0's prediction; banked cap 8 is under-converged), gain GROWS
below the wall then plateaus, flat across caps = mechanism-monotone (no basin lottery), time cost
~0 (bounded by the existing 1.2s repair budget). If +0.0025 transfers: ≈200 c3-verts ≈ +0.14 total.

**Judge deliverable READY (not submitted — team gates):** `scripts/mini16_read_pair.sh` prepares +
compile-checks the control/variant K-read pair (only diff = cap 8 vs 16, same safe rung 6670);
`--submit` runs both with campaign-lock waits. Decode: dS2 = (K_var − K_ctrl)·5e-4 on the real c3
mesh. CAVEAT for banking (not for the read): this fork is 90.51-era; the team HEAD's c3 runs ~21s
(sil2-200) where "c3 polish TLEs" — the read answers TRANSFER; shipping to the bank needs the cap
re-timed on THEIR HEAD inside the box.

---
## VIEW-DECOUPLING SCREEN (2026-07-16) — CLOSED [LOCAL, exact metric, true scale]
Hypothesis (post-93.77 regime change): 6 per-view relief shells beat one multi-view mesh.
Instrument fixes en route: proxies are ~9.5x SMALLER than judge normalization (happy renders as
a 34px blob; unit-scaled, ours_6610 FinalSSIM drops 0.9524->0.7747 — pixel-scale-sensitive proxy
conclusions do NOT transfer); relief fitters: QEM shreds open sheets, heightfield needs correct
winding. VERDICT on happy_unit: heightfield relief Sn(+Z) = 0.21/0.31/0.40/0.50 at N=464/1273/
2626/5972 vs honest mesh 0.5627 at 6610-for-ALL-SIX-views. One view alone costs ~the whole honest
budget: 6-8x below parity, ~10x below the 6-shell arithmetic (adaptivity buys ~2-3x, not enough).
The honest mesh IS the near-optimal multi-view relief union — surface sharing is a benefit, not a
tax. Tools: zoo/relief_hf.py (heightfield), zoo/relief_test.py (QEM path). Undecimated-relief
sanity: 0.9945. The leaders' discovery is NOT view decoupling.

## COMPLETION (2026-07-16): closed-mesh curve at relief budgets — decoupling DOMINATED everywhere
+Z blend at N~480/1270/2600/6000: relief 0.471/0.565/0.630/0.704 vs closed 0.423/0.631/0.703/0.794.
At equal TOTAL budget (6 reliefs vs 1 closed): closed wins by ~0.27 blend; relief wins only in the
starved <500/view regime (absolute ~0.47, irrelevant vs the 0.90 gate). Closed curve = adaptivity
upper bound => no fitter escape. VIEW-DECOUPLING CLOSED AIRTIGHT.
⚠⚠ INSTRUMENT BOMBSHELL (same data): plain pymeshlab@5999 Final6=0.8028 BEATS ours_6610 (0.7747,
+611 verts) on the UNIT-SCALE proxy — ours_6610 was produced on the blob-scale input where every
image-driven mechanism saw ~34px renders. ALL local screening (incl. zoo sign-validation) ran at
~1/9.5 judge resolution. Unit-scale re-validation of image-driven-mechanism conclusions REQUIRED
(judge meshes are unit-normalized). Tools: zoo/relief_vs_closed.py.

## UNIT-SCALE RE-VALIDATION (2026-07-16) — controls 5 OK / 0 MISS, instrument PROMOTED
Proxies were ~9.2-9.5x below judge normalization (systematic; ply2solver never normalized).
happy_unit + dragon_unit created (AABB->origin, unit sphere). Controls on happy_unit @6610:
rim_off -0.0009 / rim_035 -0.0010 / areaq -0.0028 / nplace_off -0.0050 / qw_005 -0.0062 — ALL
sign-correct, margins 3-4x the blob-scale run (nplace/qw/areaq now well above the 1.5e-3 floor).
base S2 = 0.8556 (realistic band vs blob 0.9524). tail_off = DUPE on this fork (tail not engaging
at this config — engagement quirk, investigate before tail screens). VERDICT: graveyard signs
SURVIVE; blob-scale MAGNITUDES unreliable — re-read sub-floor verdicts on this ruler. **Screen on
happy_unit from now on.**

## FULL PASS on happy_unit (2026-07-16) — family CONVERGED on the faithful ruler
61 runs, base 0.8557, controls 6/6. NO mechanism above the 1.5e-3 floor: pool_2500 +0.0007,
sil2_400 +0.0004, all else flat/negative (c3t_6700 +0.0014 = rung sanity, correct sign).
VALIDATION: the ruler RETRODICTS the judge's mini16 dK=0 (blob ruler predicted +2-3 quanta, judge
said 0, unit ruler says ~0). RE-PRICING: the deep-tail "+4e-3 at +4.5s" was a blob-scale artifact
-> Phase-1 throughput prize ~+0.04 total, not +0.23 (parked). The current family's knob space is
exhausted on a judge-faithful instrument; the leaders' +3 lives OUTSIDE it — discovery hunt is the
only front. (Report tool caveat: run_zoo --report aggregates all meshes; filter results.jsonl by
mesh for per-instrument rankings.)

## dragon_unit CERTIFIED (2026-07-16 night) — the pass-1 "rejection" was the scale artifact
Controls 5 OK / 0 MISS on dragon_unit (rim_off -0.0007, rim_035 -0.0002, qw_005 -0.0055,
areaq -0.0057, nplace_off -0.0043). Blob-scale dragon_n10's inverted signs (pass-1: nplace_off
+0.0085 etc.) were caused ENTIRELY by the 9.1x under-normalization, not by geometry class.
TWO certified instruments now: happy_unit (harder) + dragon_unit — bracket every future screen.
