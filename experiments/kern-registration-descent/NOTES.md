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

## Session 2 (2026-07-11, same day) — in-box engineering + the full channel ledger

**Kernel v2:** narrow-column boxsum (`kboxsum_rect`) + cropped `kern_begin` →
**1,241 edits/s @512** (was 381), begin 0.15 s (was 0.40), exactness UNCHANGED at
machine epsilon. Stage-A gate now fully passed. Hooks in the c3 emit flow (all
env-gated, judge-inert): `G_KERNOPT2` (deficit-prioritized budgeted descent),
`G_KERNOPT512` (512-descent → 1024-survival), `G_KERNFLIP` (true-metric flip sweep).

**Result 1 — THE RESOLUTION-BRITTLENESS LAW (theory-level, measured same-run):**
512-descent gains INVERT at 1024: +0.000725@512 → −0.000120@1024; +0.001460@512 →
−0.000815@1024 (transfer ≈ **−0.5×**). Registration optimization fits the pixel
assignment of the resolution it runs at. This is the measured mechanism behind the
R1 / 768-native / SILv3 judge failures: **any registration/position optimization must
run at judge resolution (1024). Sub-resolution local gains are not just unreliable —
they are anti-signals.**

**Result 2 — in-box per-vertex descent is uneconomic.** At 1024: ~350 trials/s;
3.5 s slice = +0.00033, 8 s = +0.00061 (vs +0.0044 unconstrained ≈ 140 s). The deficit
is spatially broad (Phase-0 Gini 0.237), so prioritization concentrates only ~4×.
Net of stealing box time from phase-B (+0.0013/~6 s), in-box moves ≈ zero-sum.

**Result 3 — TRUE-METRIC FLIPS WORK (the connectivity half).** The graveyard killed
cheap-PROXY flips; kernel-scored flips at 1024 on the final read-state mesh (V=6940):

| budget | ΔSn | flips accepted / trialled |
|---|---|---|
| 8 s | **+0.001968** | 442 / 4,936 (53% of full yield) |
| full sweep (25 s) | **+0.003715** | 1,268 / 17,392 of 20,812 edges |

~9% of legal flips are net-positive under the true metric; 660 trials/s (cheaper than
moves); measured natively at 1024 → no resolution-transfer risk in the local setup.

**Result 4 — the channels are ADDITIVE.** Stacked run: descent 45 s (+0.00272) then
flip sweep (+0.00351; standalone +0.00372 → ~5% overlap). Final proxy S2 = **0.899621**
(baseline ≈ 0.8962). Full unconstrained channel ≈ **+0.008 Sn ≈ +0.004 Final ≈
~114 c3-verts ≈ +0.08 mean** — if it could be captured in-box and transferred.

## The strategic picture after the ledger

- The kernel program proved ~+0.008 Sn of registration+connectivity headroom exists
  above the converged pipeline at judge resolution — the leaders-hypothesis mechanism
  is real. But the **21 s CPU box caps in-box capture at ~+0.002–0.0025 Sn**
  (~30 verts ≈ +0.025 mean): an order of magnitude short of 91 by itself.
- Capturing the full channel in-box needs per-trial cost ↓ ~10×: the **analytic
  boundary gradient** (edge-sampling / nvdiffrast-style edge term on the CPU
  rasterizer, driving moves+flips directly instead of probing) — the heavy build,
  and the only visible route to 91+ inside the time limit.

## Stage C — the clean A/B design (2 zero-risk reads, when pursued)

The box-cut on c3 makes with/without comparisons ~0.5σ readable. Fix: in BOTH read
arms disable phase-B (the box-cut source) so both runs are deterministic-per-binary;
arm B replaces phase-B time with the flip slice (+ short descent). Judge-side S2 then
compares at ±1 quantum (5e-4) cleanly, and simultaneously answers "slice vs phase-B"
allocation. If arm B > banked-config S2, wire it and ladder the wall down.
