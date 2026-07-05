# v43 — VSA-lite normal-error decimation breaks case3 67→69 — JUDGE 89.361976, 7/7  ★ NEW BEST

Config: case2 99.25 | case3 **69** (was 67) | case4 83.975 | case5 90 | case6 97 | case7 96.95 = **89.36**.
case3 moved off the 67% wall that **17 prior methods could not** (every cost tweak, Pivot-A
grayscale/per-channel, res variants, visibility, position-optimizer, depth-SSIM, edge-flips).

## The method — VSA-lite (normal-error collapse ordering)
Order edge-collapses by the **induced normal distortion** (Variational Shape Approximation's L2,1
objective) instead of the Garland-Heckbert **position** error. One line in `Evaluate`:

    if (g_ndecim) cost = incident_ndist(i,j,xbar) + g_qweight*cost;   // g_qweight=0 -> PURE normal

`incident_ndist` = Σ over surviving incident faces of `area_new · (1 − cos(n_old, n_new))`, i.e. the
area-weighted L2,1 normal change the collapse causes. Pure normal (qweight 0) beat blended; stacks with
Pivot-A. Placement stays QEM-optimal (xbar); only the ORDER of collapses changes → all manifold gates,
Hausdorff bound, and other cases are untouched.

## Why it worked (the honest reasoning)
1. **The judge measures per-face-normal SSIM. QEM minimizes POSITION error.** Those are different
   optima. Every prior method optimized position (or repositioned a fixed face set). VSA-lite is the
   first to make the DECIMATION itself minimize the normal metric — it chooses WHICH vertices survive
   to best preserve the normal field, not the geometry.
2. **It refuted the "uniform detail = no reallocation lever" hypothesis.** case3's detail is uniform,
   so curvature/contrast reallocation (Pivot-A) had little to grab. But normal-error ordering isn't
   reallocation by curvature — it directly protects the faces whose collapse would most distort the
   rendered normals. That found headroom position-based methods couldn't see.
3. **+0.0128 normal-SSIM at 68% (0.804 → 0.817)** on the faithful proxy — an order of magnitude more
   than every other lever this session (which gave +0.0001 to +0.0005). Crossed 0.9.

## Verified before submit (faithful proxy25k, oracle @1024)
- shipped 69% FINAL = 0.8996 (3 runs, stable) > known judge-pass 0.8974 → predicted PASS. **Confirmed 7/7.**
- Hausdorff 1.50% diag (≤5%; baseline 1.43%). Manifold/validity preserved. cases 2/4/5/6/7 byte-identical.
- timing 16.8s < ~21s.

## What did NOT work this session (banked as dead ends)
- **Depth-SSIM in the optimizer accept (build #1):** verified bit-exact vs oracle, but depth is
  SATURATED (~0.985) → gain ~0, and it **WA'd case4** (75.04) because case4 sits on its 0.9 wall and the
  depth-normal trade drops judge-Final. Reverted. Normal-SSIM is the sole binding constraint.
- Position-optimizer: converged (30s == 90s), maxed. Edge-flips (oracle-scored): +0.0005. Both exhausted.

## Next
- **Apply VSA-lite to case4 + case5** (organic, normal-bound — same physics as case3). Highest-leverage
  remaining move; case4 (83.975%) is the new worst case. (case4 is razor-edge/proxy-pessimistic → test
  relative gain, submit carefully; best-counts protects 89.36.)
- Push case3 70% (proxy 0.8969, just below known-pass — stretch).
