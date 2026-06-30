# Wang 2004 (SSIM) — what it means for Case 3 (IMC Problem B)

Paper: Wang, Bovik, Sheikh, Simoncelli, "Image Quality Assessment: From Error Visibility
to Structural Similarity", IEEE TIP 13(4) 2004. The SSIM source. Confirmed: it's the
paper that governs our wall.

## The decomposition
`SSIM = l(x,y)·c(x,y)·s(x,y)` (with α=β=γ=1, C3=C2/2):
- **luminance** `l = (2μxμy+C1)/(μx²+μy²+C1)` — compares the local **mean**.
- **contrast** `c = (2σxσy+C2)/(σx²+σy²+C2)` — compares the local **std-dev** (variance).
- **structure** `s = (σxy+C3)/(σxσy+C3)` — correlation of the mean/variance-normalized signals.
Combined = exactly the judge's formula. C1=(0.01·255)²=6.5, C2=(0.03·255)²=58.5.

## Why every cost reweighting died (now proven, not just observed)
On the flat-shaded normal map, a window's pixels are the covering faces' constant normals.
- **μ (mean) is matched by QEM** — the optimal x̄ gives faces ≈ the area-weighted mean normal
  of their region. Every reweighting still yields the best-fit mean. ⇒ luminance term ≈ 1.
- **σy (simplified variance) is set by the FACE COUNT in the window**, i.e. by the compression
  ratio — NOT by the cost weight. In a detailed window few faces ⇒ σy≈0 while σx is large ⇒
  the **contrast term collapses** ⇒ SSIM drops. No reweighting restores σy at fixed face count.
- structure → 1 as σy→0. Not the killer.
⇒ The 9 dead methods optimize μ; SSIM bites on σ. **Orthogonal.** Wall = the contrast term.
Confirmed empirically: Case 3 SSIM-bound (validity ruled out via %.17g; Hausdorff ruled out
via subset @66%, both still red).

## Two facts the paper hands us (the exploits)
1. **Flat windows are free.** If σx is small (≲ √C2 ≈ 7.6 px ⇒ normal spread ≲ 0.06), C2
   dominates ⇒ c ≈ 1 regardless of σy. **Crush flat regions to nothing — zero SSIM cost.**
2. **Contrast-masking.** c is *less* sensitive to Δσ when base σx is high (paper p.605). So the
   penalty concentrates in **INTERMEDIATE-σx** windows (moderate curvature), and the most-detailed
   regions are partially self-masking. Don't over-protect peaks; protect the mid-band.

## Is the wall intrinsic?
At fixed compression you cannot raise σy in a window without putting more faces there. So the
only freedom is **allocation**: move face budget from flat windows (free) into the
intermediate-curvature windows that cost points. If Case 3 has flat area QEM isn't fully
exploiting → allocation helps. If Case 3 is ~uniformly intermediate-curvature → near-hard-capped.
We cannot know without the mesh. Allocation is the ceiling; reweighting the 3D proxy is not it.

## The only lever left = metric-in-the-loop (Pivot A)
The proxy (3D plane distance) is provably not the metric. The fix is to **measure the metric**:
render the current mesh's 6 normal maps periodically (coarse res), compute the per-region
**contrast deficit** (σx vs σy, i.e. SSIM's c-term) on the actual rendered foreground, and
steer collapse cost by it — cheap where c≈1 (flat or masked), expensive where the c-term is
mid-band and failing. This sees masking, the foreground mask, perspective and projected area —
everything the geometric proxies miss. Feasible on medium meshes (25–50k): render every N
collapses at 128–256², 6 views, is milliseconds. NOT per-collapse (≫21s).

Honest caveat: even Pivot A only reallocates; if Case 3 is uniformly mid-curvature it stays
near-capped. But it is the one method that optimizes the quantity SSIM actually penalizes.

## UPDATE — Pivot A built, validated, TESTED → no gain
C++ rasterizer validated 100% vs the oracle (6 views, fandisk+cow). Full metric-steered
simplifier (render passes → per-window contrast deficit σx−σy → per-vertex importance →
cost steering) tested on a mixed proxy (bumpy sphere, flat base + detail) at 66%:
  free-QEM Final=0.8224 | Pivot-A λ=2 0.8224 (identical) | λ=8 0.8218 (worse).
Steering is active but redundant: **when detail = curvature (the normal case), the
SSIM-critical windows ARE the high-QEM-cost regions** — QEM already keeps faces where the
contrast lives, so steering re-protects what's already protected. And there is no flat
budget to reallocate on a detail-dense mesh (if there were, QEM would have used it — which
is exactly why Case 3 caps low). ⇒ **The variance wall is intrinsic to the vertex budget,
not an objective we can out-optimize at V'≤V.** Conclusion: ~85.17 is the real ceiling for
this metric via simplification; 92/98 is not reachable by reducing a mesh to fewer vertices.
