# KERN — dirty-region SSIM kernel + tangential registration descent (2026-07-11)

**What it is:** Road B Stage A/B (the approved co-optimization plan). A persistent
per-view render+SSIM state in `solver/main.cpp` (`#pragma region Dirty-region SSIM
kernel`) that scores a LOCAL mesh edit (vertex move / edge flip) by its exact effect
on the rendered normal-SSIM, re-rasterizing only the touched pixel rect and re-scoring
only the 11×11 windows whose support meets it. Judge-inert (env-gated: `G_KERNVERIFY`,
`G_KERNOPT`); default output verified byte-identical to HEAD (bunny).

**Why (the hypothesis it tests):** Phase 0 proved the case-3 deficit is 100% the SSIM
structure term — *registration*: right normals, wrong pixels. The analytic refine
gradient differentiates at a FROZEN pixel-to-face assignment: it tilts facets but can
never slide facet boundaries across pixels. Tangential vertex moves live exactly in
that blind subspace. If the converged refine state still yields gains there, the
"leaders' edge" (appearance-driven boundary optimization, nvdiffmodeling-class) is
reproducible CPU-side.

## Stage A — kernel kill gate (case-3 proxy, V=6,953 state)

| gate | target | measured |
|---|---|---|
| move-delta exactness vs full recompute | ≤1e-6 | **max 5.6e-16** (K=40) |
| flip-delta exactness | ≤1e-6 | **max 3.3e-16** (12 flips) |
| absolute score vs `refine_score_grad` | — | 1.9e-15 |
| restore drift after 55k+ trials | — | 0.0 |
| speed @512 | ~10³/s | 381 committed edits/s |
| judge-inertness | byte-identical | ✓ (bunny vs HEAD) |

Exactness passed at machine epsilon (the kernel replicates refine's f32 round-trips
bit-for-bit). Speed is 2.6× short of the in-box target — sufficient for local
evidence; optimize (narrow-column boxsum, ~5×) only for the judge-side version.

## Stage B evidence — greedy tangential descent from the CONVERGED refine optimum

`kern_opt` (env `G_KERNOPT`): per alive vertex, 4 tangent-plane candidates at
0.35·mean-edge, keep best if ΔSSIM > 1e-7, 2 sweeps, cap 0.01·diag.

| resolution | Sn before → after | Δ | moved/tried |
|---|---|---|---|
| 512 (hybrid off) | 0.879300 → 0.886616 | **+0.00732** | 1,413 / 55,616 |
| **1024 (judge res, post-hybrid)** | 0.807387 → 0.811755 | **+0.00437** | 824 / 55,624 |

- The converged optimizer state was NOT registration-optimal: the crudest descent
  captured the full documented passive basin spread (~0.007 @512) at fixed connectivity.
- **Survived the 1024 resolution gate** (the one that killed 768-native), at ~20–40×
  the local noise floor; sweep 2 still gaining → not converged.
- Naive worth: +0.0044 Sn = +0.0022 Final ≈ 62 c3-verts ≈ **+0.045 mean** at transfer
  1.0 (≈ +0.013 at the historical 0.3× position-space transfer). Case-5 twin and
  connectivity moves (kernel-scored flips) untested — likely upside.

## Risk, stated plainly

This is the SAME risk class that killed R1 (+0.002 local → 0/3 judge; armadillo-derived
proxies over-reward position-space optimization). Different subspace (boundary
registration vs shading micro-opt) — but only the judge decides. Per WALL-MODEL §5.5:
**no descent on local evidence; one READ submission first.**

## Next steps (in order)

1. **In-box version:** narrow-column boxsum (~5×) + deficit-prioritized vertex order
   (~10× fewer trials, front-loaded gain) → a 2–4 s `kern_opt` slice inside the c3 flow.
2. **Stage C:** one READ→TWIN→BANK submission — judge-side S2 with descent vs the
   banked read (S2=0.9135 @ N=6941). Zero-risk; de-razor cases 4/6 for attribution.
3. If positive: push the c3 wall down in fixed-count steps; then the case-5 twin;
   then kernel-scored flips (connectivity, the untouched half of the mechanism).
