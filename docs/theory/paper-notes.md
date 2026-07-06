# Paper notes — what's useful for IMC Problem B (private working notes)

**Our problem, fixed in mind while reading:** judge = SSIM on a flat per-face **normal map** + perspective **depth map**, 6 axial views, gate 0.9; hard constraints = closed 2-manifold + ≤5% AABB-diagonal Hausdorff; CPU only, up to 1.1M verts, ~21 s; **output is a bare mesh — no texture/normal maps allowed.** Baseline = uniform keep-0.36 QEM = 64, 7/7. Goal = 90% like the leaders.

## TL;DR (actionable)
- **Per-edge rendering is unaffordable** at our scale → can't use a true image metric. Use cheap **geometric proxies** for the two SSIM channels, which are also trustworthy (unlike the uncalibrated SSIM oracle):
  - normal map ↔ **Normal Consistency** `NC = mean |n·n_nearest|` + **triangle quality** (slivers → garbage face normals).
  - depth map ↔ **surface proximity** (Hausdorff) + **silhouette** preservation.
- Most likely lever for normal-map SSIM at high compression: **avoid slivers / preserve face normals.** Plain QEM creates slivers when pushed.
- Hausdorff safety: **subset placement** bounds both directions provably with no grid (see KEY INSIGHT below). Replaces the earlier free-QEM grid guard that had a dir-2 hole.
- **Judge gives no failure reason (only "Wrong Answer").** So we don't know if the wall is geometry or SSIM — the diagnostic engine (geometry provably safe) is how we find out. See CRITICAL section.

## 1. Lindstrom & Turk 2000 — Image-Driven Simplification (353981.353995)
- Cost of an edge collapse = **RMS pixel diff of rendered images**, orig vs simplified, over ~20 fixed views (dodecahedron), 256² GPU, luminance only, gray bg, light at viewer. Philosophy ≈ our judge (multi-view image compare).
- Beats geometry-only at equal poly count; **naturally preserves silhouettes + shading**, and gets good geometric fidelity as a side effect.
- **Not implementable for us** (render per candidate edge on CPU at 1.1M = far over 21 s). North star, not a method.
- **Usable piece — memoryless vertex placement (LT 1998/1999):** analytic, fast, no history/quadric storage. (1) volume-preserving: set Σ tetra-volume-change = 0 → a plane constraint on the new vertex; (2) minimize Σ per-triangle squared volume change → fully fixes it in planar regions; (3) in planar regions choose the position making triangles **near-equilateral → fewer slivers**. Drop-in alternative/complement to QEM placement, tiny cost. → candidate small change.

## 2. Cohen, Olano, Manocha 1998 — Appearance-Preserving Simplification (280814.280832)
- Decouples geometry from appearance: store normals/colors in **normal/texture maps**, bound their screen shift with a **texture-deviation metric** (≤ ε pixels), filter per-pixel at runtime.
- **Not usable:** we ship a bare mesh; the judge computes flat normals from geometry; no maps.
- Takeaway: appearance = adequately sampled normals + correct screen coverage (silhouette). Reinforces NC + silhouette as the things to protect.

## 3. Cohen 1999 PhD thesis — Appearance-Preserving Simplification of Polygonal Models (cohen.pdf, 147 pp)
- Houses **Simplification Envelopes** (SIGGRAPH'96) + **Successive Mappings**: build inner/outer offset surfaces at ±ε (no self-intersection), simplify staying between them ⇒ **guaranteed two-sided surface deviation ≤ ε** (true Hausdorff bound). Also notes Rossignac–Borrel vertex clustering bound (ε = cell diagonal).
- For us: the principled route to max compression within 5% Hausdorff. **Full algorithm is heavy** (offset-surface generation + self-intersection tests) — probably too heavy at 1.1M/21 s. Our bounding-sphere(dir-1)+grid(dir-2) guard is the lightweight analog; fix the conservative dir-2 and it plays the same role.
- Only read the envelope-construction chapters if we commit to guaranteed-bound aggressive decimation.

## 4. CWF 2024 — Consolidating Weak Features (2404.15661)
- Functional `E = λ_NA·E_NA + λ_CVT·E_CVT`: normal-anisotropy term (QEM-spirit: accuracy + feature alignment) + Centroidal-Voronoi term (even point distribution / triangle quality), with **decaying λ_CVT**; solved by L-BFGS, ~50 iters, Restricted Voronoi per iter. = high-quality **remeshing**.
- **Too heavy** for 21 s / 1.1M (global iterative).
- **Usable:** their eval metrics are exactly our proxies — **NC** and **TriangleQ** `= (6/√3)·Area/(half_perimeter·longest_edge)` (1 = equilateral). Use locally to rank engine variants without rendering. Confirms triangle quality + normal consistency ⇒ appearance.
- Method menu if we need something stronger than QEM: **PQ** (Trettner-Kobbelt 2020), LpCVT (Lévy-Liu 2010), SMS (Lescoat 2020, spectrum-preserving), IEM (Liu 2023), LPM (Chen 2023), MD (Kobbelt 1998).

## 5. Probabilistic Quadrics (the file given was the WRONG one)
- `2004.03207v2.pdf` was a physics paper (Lorenz gauge / EM waves) — ignore.
- Correct paper: **Trettner & Kobbelt 2020, "Fast and Robust QEF Minimization using Probabilistic Quadrics"** (Eurographics / CGF 39(2)). QEM where input is treated as Gaussian-uncertain → closed-form plane/triangle quadrics, minimized by a simple linear solve, robust positions, fewer slivers, ~50× faster than SVD. Variants prob_plane (PQP) / prob_triangle (PQT).
- **Reference C++ impl (header-only): https://github.com/Philip-Trettner/probabilistic-quadrics** — drop-in if we want better placement.
- Paper: https://onlinelibrary.wiley.com/doi/abs/10.1111/cgf.13933

### PQ implementation recipe (from the reference header) — ready to code in Eigen
Convention: **Q(x) = xᵀA x − 2 bᵀx + c**, A sym 3×3, b vec3, c scalar. (Note the −2b — NOT the GH homogeneous 4×4.) Combine = add {A,b,c}. Weight = scale {A,b,c}. Minimizer **x\* = A⁻¹ b** (LDLT). Cost(x) = x·(A x) − 2 b·x + c.

**Isotropic probabilistic TRIANGLE quadric** (vertices p,q,r; one stddev σ):
```
pq=p×q  qr=q×r  rp=r×p     s=pq+qr+rp     det=pq·r
δpq=p−q δqr=q−r δrp=r−p
A = s sᵀ + σ²·( ‖δpq‖²I − δpq δpqᵀ + ‖δqr‖²I − δqr δqrᵀ + ‖δrp‖²I − δrp δrpᵀ ) + 6σ⁴I
b = s·det − σ²·( δpq×pq + δqr×qr + δrp×rp ) + 2σ⁴·(p+q+r)
c = det² + σ²(‖pq‖²+‖qr‖²+‖rp‖²) + 2σ⁴(‖p‖²+‖q‖²+‖r‖²) + 6σ⁶
```
**(σ-power CORRECTION, 2026-07-05, during D4 implementation):** the first transcription
had σ² where the quadratic/cubic noise terms need σ⁴/σ⁶ (dimensionally inconsistent:
A~L⁴, b~L⁵, c~L⁶ must hold uniformly). Re-derived from Q(x)=E[(s̃·x−det̃)²] with vertices
~N(·,σ²I): Cov of the bilinear noise (a×b etc.) contributes 2σ⁴I per pair → 6σ⁴I in A,
2σ⁴(p+q+r) in b, 2σ⁴Σ‖·‖² in c; the trilinear term (a×b)·c gives 6σ⁶ in c. Verified in
`solver/main.cpp` (`pq_accumulate`) against 4M-sample Monte-Carlo (rel diff 5e-4) and
σ=0 ⇒ exactly (s·x−det)² = 4·Area²·dist² (rel err 2e-14).
(Isotropic PLANE quadric, mean p,n: A=nnᵀ+σ_n²I, b=n(p·n)+σ_n²p, c=(p·n)²+σ_n²‖p‖²+σ_p²‖n‖²+3σ_p²σ_n².)

**Why it fixes slivers:** the `+σ²(…)+6σ²I` makes A full-rank even on flat/coplanar regions (plain QEM is rank-1 there → position undetermined → slivers). σ regularizes → rounder triangles → better face normals → the normal-map SSIM lever.
- σ=0 ⇒ exact GH quadric. Bigger σ ⇒ rounder/more-regular, less geometrically tight. **σ is the single knob** (units = model length; start ~ mean edge length, tune ON THE JUDGE).
- Stability: A ← A + ε I (ε~1e-8); skip/endpoint-fallback if det(A) tiny. Double precision.
- **How we'd use it:** keep our manifold gates + per-case dispatch; swap only the per-edge *cost+position* (Q[i]+Q[j], minimize). Drift not provably bounded ⇒ keep a Hausdorff check OR only use where geometry is slack (which the judge says it is at our compression).

## Open-access PDFs worth pulling when coding
- Lindstrom-Turk 1998 (memoryless placement): http://mesh.brown.edu/DGP/pdfs/Lindstrom-vis98.pdf
- Memoryless eval: https://faculty.cc.gatech.edu/~turk/my_papers/memless_tvcg99.pdf
- Probabilistic Quadrics impl: https://github.com/Philip-Trettner/probabilistic-quadrics

## CRITICAL: the judge only says "Wrong Answer" — no reason (confirmed by user)
- So **every "failure reason" in the repo notes (v2/v5/v6 "geometric deviation", "case 3 = Hausdorff") was a GUESS, not a judge fact.** We do NOT know whether the wall is geometry or SSIM.
- Engine must be **self-diagnosing locally.** 3 of 4 fail-modes are exactly checkable + trustworthy (NOT the SSIM oracle): closed-2-manifold, non-degenerate, symmetric Hausdorff (exact point-to-triangle).
- **Diagnostic:** make geometry *provably* ≤ margin, verify locally on many meshes, submit. If it still WAs cases → those are **SSIM by elimination.** Binary verdict becomes the diagnosis.

## KEY INSIGHT — subset placement makes Hausdorff provably bounded, no grid
Collapse target = the cheaper of the two **original** endpoints (subset placement). Then:
- every surviving vertex is an original vertex ⇒ on the original surface ⇒ **dir-2 vertex term = 0**;
- **dir-1** (original verts → simplified surface): per-cluster **bounding sphere** of represented originals; bound `|center − xbar| + radius` is a sound upper bound;
- **dir-2** (a *modified* face bulging off the surface): its 3 vertices are on the surface, so every interior point is within `longest_edge` of one ⇒ if **longest edge ≤ margin** the whole face is within margin. Original untouched faces have 0 deviation (they *are* the surface).
- Both bounds are O(1)/O(valence), **no spatial grid**. The earlier free-QEM engine needed the grid + had the dir-2 hole; subset removes both. Margin 0.045 ⇒ provably ≤ 4.5% < 5%.

## Synthesis → plan
1. **Now (diagnostic):** provably-safe subset adaptive (above) at margin 0.045, keep-0.36 fallback (one constant). Verify locally: manifold + exact Hausdorff ≤ margin on a battery of meshes. Submit → diagnoses geometry vs SSIM.
2. **If SSIM is the wall:** raise quality — better placement (Probabilistic Quadrics / LT memoryless → fewer slivers), measured by geometric proxies NC + TriangleQ (no renderer). Subset's mediocre fit is the floor; free-QEM/PQ raises it.
3. **Geometric quality harness** (NC + TriangleQ + exact Hausdorff) to pre-screen variants offline — trustworthy, no SSIM oracle.
