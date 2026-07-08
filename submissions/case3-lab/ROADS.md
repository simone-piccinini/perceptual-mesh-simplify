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
- Bank **90.285538** (7/7). case-3 = 70.083% (N=6941, V=23201).
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

**Lesson from VSA (steers the queue):** the winning case-3 mesh is **smooth + dense + adaptive**
(QEM family). Flat/partition topology is the wrong direction for an organic surface. Any road that
introduces large flat facets is pre-doomed for case-3.

## 3. QUEUED / ACTIVE roads (ranked by EV = odds × prize ÷ effort)
Ordering is the execution order. The agent works the top non-DEAD road.

### R-α — Curvature/anisotropy-aware PLACEMENT audit — `QUEUED` · cheap · odds med
Before any heavy build, verify the current normal-placement is actually maxed. `g_nplace` claims
"normal-optimal collapse placement (+0.0006 c3)". Test on the organic proxy: ablate/strengthen
placement, and try a Hoppe normal-attribute quadric for the PLACED vertex (IDEAS.md #2). In-family
(smooth), cheap, reuses main.cpp. If it moves the oracle normal-SSIM at fixed V, it's a judge A/B
candidate. **Next step:** measure nplace on/off + a normal-quadric placement variant at matched V.

### R-β — Curvature-adaptive isotropic/anisotropic remesh — `QUEUED` · heavy · odds med
A smooth NEW triangulation (Botsch-Kobbelt loop: split long / collapse short / flip-to-Delaunay /
tangential relax), edge-length ∝ local feature size, optionally anisotropic (align to principal
curvature to tile the normal field with fewer facets). In the RIGHT family (smooth, quality
triangles), unlike VSA. Might beat QEM's error-driven triangle shapes on the normal map. Build
standalone like vsa_remesh.cpp; score vs QEM on the oracle. **Next step:** build the manifold-safe
remesh loop, iter 1 = valid output at target V, then compare.

### R-γ — Dynamic in-loop metric — `QUEUED` · cheap · odds low
Re-render the Pivot-A steering deficit as the mesh decimates (currently frozen on the original), so
steering tracks the current mesh. Cheap, reuses infra; but a variant of banked steering → likely
marginal. **Next step:** add periodic re-render to the steering; measure at matched V.

### R-δ — Differentiable co-opt DURING reduction (full) — `QUEUED` · heavy · odds low
Interleave `refine_score_grad` position-ascent INTO the collapse loop (not refine-after). Stays
smooth. But ≈ R1 (judge-negative) and refine is already converged post-hoc → low odds. Last resort.

### R-ε — Cross-case gap hunt (premise-correction lens) — `QUEUED` · med · odds med
The 7.05-pt gap is likely SPREAD, not all case-3. Re-audit c4 (genus floor 85.7), c5 (razor 91.5),
c6/c7 for a cheap point each — a shared ε across cases may beat squeezing exhausted case-3. Honest
given the arithmetic; but those walls were measured hard. **Next step:** per-case headroom re-audit.

## 4. Execution log (newest first)
- **2026-07-08** — External research report audited (§5): 0 new levers, validates our oracle,
  reinforces R-α. ROAD 1 (VSA remesh) built + measured DEAD (§2). Premise corrected (85%→77%).
  Registry created. Next: R-α (placement audit, cheap) → R-β (isotropic remesh) if R-α is flat.

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
