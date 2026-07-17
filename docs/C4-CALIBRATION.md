# Case-4 calibration & depth findings (team writeup)

STATE: 2026-07-13, branch `experiment/new-mechanism`. Author: automated session (Simone).
TL;DR: the old c4 local proxy was unfaithful; replaced it with real ABC CAD parts that reproduce
the judge wall; found the **c4 wall is depth-SSIM**; and proved **depth-aware *decimation* (order/
placement) is inert** — the lever is *allocation*, which is the next build.

---

## 1. The problem: the c4 proxy lied
`probe/cache/c4band.obj` (the local c4 testbed) is a **synthetic union of two fandisks**. It is
**unfaithful**: it collapses freely to N=6 (no topological floor), renders at **SSIM 0.9999 even at
the c4 rung** (fully saturated → no A/B gradient), and its Hausdorff is a two-component artifact.
Any c4 experiment measured on it produces **false positives**. This is why prior "c4 gate-exhaustion"
framing didn't reproduce locally.

## 2. The fix: real ABC CAD proxies (calibrated)
Extracted real **watertight, genus-0, 30–40k-vertex mechanical CAD parts** from the ABC dataset
(`probe/abc_tools/`, fully reproducible; see its README for the exact verified commands — note the
gotchas: curl not wget, `/data/` index path, `.7z`+7-Zip, and the **7.5 GB** obj chunk needs a drive
with space). Filtered by `#verts∈[30k,40k]` + `#parts==1` + mesh-level watertight/genus-0.

**Calibration (RC4 = solver rendered SSIM at N≈4920):** real CAD spans S2 **0.75–0.99** and
**reproduces the judge's ~0.90 wall** (the fandisk never could). Family in `probe/cache/c4/`:

| proxy | S2n | S2d | S2 | role |
|-------|-----|-----|-----|------|
| 00004867 | 0.741 | 0.752 | 0.747 | hard bracket (below wall) |
| 00005934 | 0.973 | 0.734 | 0.854 | **wall-region** |
| 00009281 | 0.973 | 0.924 | 0.949 | **wall-region** |
| 00001680 | 0.997 | 0.967 | 0.982 | easy control |

## 3. KEY FINDING #1 — the c4 wall is DEPTH-SSIM
On real CAD the loss is almost entirely in the **depth channel** (S2d → 0.73) while the **normal
channel stays high** (S2n ~0.97). So c4's binding term is DEPTH structure (steps/pockets/thin walls
at distinct z), **not** normals (like c3), **not** topology (no jam), **not** Hausdorff (that was a
proxy artifact). This reframes any c4 attack toward depth.

## 4. KEY FINDING #2 — depth-aware DECIMATION is inert (principled negative)
Implemented + A/B'd two decimation-time depth heuristics (env-gated, `solver/mein.cpp`):
- `G_ZPEN` — cost penalty deferring collapses that flatten distinct-Z features (edge-normalized).
- `G_SUBSET` — subset placement (keep the merged vertex on a real depth level vs QEM's mid-step average).

**Both are byte-identical to baseline** on the calibrated proxies (00005934 S2d=0.734167,
00009281 S2d=0.924041, across G_ZPEN {0,3,8} and G_SUBSET). Principled reasons:
1. **QEM ordering is already depth-optimal** — it collapses flat regions first and preserves feature
   vertices, so a "defer feature-collapse" penalty duplicates it.
2. **Refine runs after decimation** and re-optimizes positions to the same convergent optimum,
   washing out placement changes (which-verts-survive is the only thing refine can't undo).

⇒ **c4 depth-SSIM at the rung is bounded by the compression ratio + refine convergence, not by the
collapse logic.** The depth-*penalty* mechanism class is dead for c4. The real lever is **allocation**
— re-budget vertices toward depth-detailed regions (analogous to how RIM-BUDGET moved c3, which was
allocation not placement). That is the next build (Z-saliency quadric weighting, `G_ALLOC_WEIGHT`).

## 5. Caveats for the team
- These are *representative* hard CAD parts, not the judge's exact c4 mesh — "depth-SSIM" is a strong
  hypothesis from multiple faithful proxies, not certainty about the judge's model.
- Local S2d wins are weak evidence until judge-tested (§2.1). The calibrated proxy makes local A/B
  *more* meaningful for c4, but transfer is still unproven.
- This machine is severely CPU-throttled (>2 min/run) → iteration is background-only.

## 6. Reproduce / reuse
- Pipeline + scripts: `probe/abc_tools/` (README + `abc_stat_filter.py` + `abc_filter.py`).
- Calibrated proxies + full results: `probe/cache/c4/` (+ MANIFEST).
- The depth heuristics + verdict: `solver/mein.cpp` (search `G_ZPEN` / `g_zpen`).

## Phase 5 (2026-07-14) — the α map is trajectory-noise; allocation is a DEAD-END for the judge's c4
Wide α grid (14 CAD meshes × {0,0.5,1,2}) in two compiler families + a determinism test:
- **Deterministic per binary** (α=1 run twice = byte-identical) — no run-to-run noise. BUT **-O2 and
  -O3-march=native give OPPOSITE signs**: 00005934 α=1 = **+0.054 (-O2) vs −0.036 (-O3)**; even the
  baseline shifts ~0.03 between families. **The α effect (~0.04) ≈ the compiler trajectory variance (~0.03).**
  → the QEM decimation *trajectory* (float tie-breaking) dominates S2d; α perturbs it about as much as a
  compiler flag. ~half the meshes FLIP their helpful/harmful verdict between -O2 and -O3.
- **Judge-relevant (-O2) map:** only the 2 HARDEST meshes (base S2d 0.73–0.75) get a consistent
  meaningful gain (+0.054/+0.055); mid-baseline (0.87–0.97) no-help or **catastrophic** (00004629 α=1
  = −0.293); saturated (≈1.0) no room. "Helps" does NOT predict from baseline (00004629 breaks it).
- **Inference on the judge's c4:** it passes combined-SSIM ≥0.90 with S2n~0.97 → its rung S2d ≈0.83–0.92
  = the MID "no-help/harmful" regime, NOT the hardest-mesh "helps" regime. α>0 is predicted to no-help
  or hurt (and could catastrophically drop S2d like the same-baseline 00004629).

**VERDICT — principled negative on weight-based allocation for the judge's c4:** (a) trajectory-fragile
(compiler flip), (b) no baseline-predictable adaptive rule, (c) judge's c4 sits in the no-help regime.
Do NOT spend judge submissions on it. This is §2.1 shown empirically. Tooling (winbuild -O2, fast_sweep,
alpha_grid, config_optimizer, saliency_validator, +27 genus-0 proxies) stays reusable for any future
mechanism whose effect is LARGER than the trajectory noise floor (~0.03 S2d).
