# Go/No-Go: can a remesh / VSA rebuild beat the case3 (65%) and case4 (82%) walls?

Decision memo (research-first). Grounds the call in the metric (Wang-2004 SSIM),
the method (Cohen-Steiner-2004 VSA), and our own 16-method failure dataset.

## 1. What the wall actually is (Wang-2004 SSIM)
FinalSSIM's binding term is the **structure** factor of normal-map SSIM:
`(2·σ_xy + c2) / (σ_x² + σ_y² + c2)` per 11×11 window = a **local Pearson correlation**
of the original vs simplified per-face normal pattern, after mean/variance normalization.
- The luminance term (mean normal) is preserved by any reasonable method -> not the wall.
- The wall is whether each window's **local normal pattern** is reconstructed. That is set by
  how many faces (and how well-placed) project into that window. It is **information-theoretic**:
  below some face density per window, the local correlation collapses and SSIM drops under 0.9.

## 2. Why QEM caps, and why our 16 tries didn't move it
QEM minimizes a **geometric** quadric (squared distance to planes), which is only a *proxy* for
normal-map error. We already attacked the metric-mismatch from inside the greedy collapse framework:
- **approach-c** (correct flat-shaded normal cost), **GH-normal quadric** — normal-aware cost. Failed.
- **Pivot-A** (screen-space normal-contrast-deficit steering, grayscale + per-channel, res160+res320,
  image-driven importance λ12) — steers collapses by the *actual rendered normal deficit*. Failed on
  case3 and case4.
The Pivot-A failure is the key datum: it explicitly weights by screen-space normal importance, so if
case3/case4 had an exploitable low-importance region, Pivot-A would have found it. It didn't ->
**case3 has no importance gradient (uniform detail); case4's gradient is already captured by QEM.**

## 3. What VSA does that greedy collapse cannot (Cohen-Steiner 2004)
VSA = global variational partition into **geometric proxies** under an **L²,¹ normal-deviation metric**
that "demonstrates superior behaviour at capturing anisotropy" (stretched proxies on parabolic/creased
regions). Two things it does that nothing we tried does:
1. **Optimizes a normal metric globally** (Lloyd relaxation), not greedily — closer to the judge's
   normal-map objective than QEM's geometric quadric.
2. **Re-triangulates with NEW edges aligned to proxy boundaries (creases).** Greedy collapse can only
   delete original edges; it can never *create* a crease-aligned edge that wasn't in the input.

## 4. Per-case verdict
| case | wall | VSA/remesh verdict | why |
|---|---|---|---|
| 3 | 65% | **NO-GO** | Uniform detail (Pivot-A importance steering failed). VSA partitions degenerate to ~uniform tiny proxies -> no anisotropy to exploit. Wall is pure per-window information content; no method adds information. |
| 4 | 82% | **WEAK-GO (~30-40%)** | Mechanical = piecewise-planar + sharp creases = VSA's home turf. Judge-aligned normal metric + ability to place crease-aligned edges is the ONE mechanism QEM/Pivot-A structurally lack. Plausible +2-4%. |
| 2,5,6,7 | maxed/capped | NO-GO | case2 at geometry floor; case5 organic detail (no planar proxies); case6/7 dense organic + already 96-97%. No VSA story. |

## 5. The ceiling math — the decisive finding
To reach **mean 90** we need the 6-case sum to go 529 -> 540 (**+11**). The only movable case is case4.
Even a *fully successful* case4 VSA rebuild (82 -> ~86, optimistic) is **+4 sum = +0.67 mean -> ~88.8**.
case3 (the lowest case, 65%) is the anchor and is **immovable** (uniform detail). Therefore:

> **90 is unreachable.** The realistic ceiling of ANY rebuild is ~88.5-89, gated by case3.

## 6. Effort / risk
A manifold-safe VSA pipeline = the biggest build of the project: variational partition (Lloyd) +
proxy fitting + **watertight re-triangulation of proxy regions** (the hard, failure-prone step) +
vertex-to-vertex Hausdorff guard + the 21s/2GB budget. The meshing step is where VSA implementations
usually break manifoldness — exactly the judge's hard gate.

## 6b. EMPIRICAL KILL-SHOT — genuinely different simplifiers tested (oracle, box)
Applied the case2 lesson properly: tested simplifiers that are NOT QEM-variants, on the 25k (case3)
and 35k (case4) proxies, at each wall. normalSSIM = mean rendered normal-map SSIM (the binding term).

case3 @66%:  our-QEM 0.8017 (manifold) > meshopt-s 0.7912 (NON-manifold) > mo-attr nw1..8 0.66-0.70 > sloppy 0.665
case4 @83%:  our-QEM 0.7405 (manifold) > meshopt-s 0.7167 (NON-manifold) > mo-attr 0.593 > sloppy 0.567

Findings:
1. **Our free-QEM is the BEST simplifier on the judge's metric at both walls.** Nothing beats it.
2. **`sloppy` (vertex-clustering = non-greedy, non-QEM, the "ceiling probe") is WORSE**, not better.
   So there is no better simplification hiding behind a different topology strategy.
3. **Normal-metric-driven simplification (meshopt attributes) is DRAMATICALLY worse (-0.10 to -0.15).**
   Preserving vertex normals costs triangle quality, which HURTS the rendered flat-normal map. This
   directly undercuts VSA's premise (its L²,¹ normal metric would face the same tension).
4. meshopt breaks manifold on organic meshes -> unusable regardless (judge hard-fail).
=> case3 AND case4 are **method-invariant** at the simplification level. The walls are information-
   theoretic, confirmed with 4 genuinely-different methods each (not just QEM parameter tweaks).

## 7. Recommendation
- **Expected value of the rebuild:** ~+0.7 mean (case4 only), **~35% success**, **days** of work,
  and it **cannot reach 90**.
- **Recommend: ACCEPT 88.17** as the final score unless the case4 VSA attempt is wanted for its own
  sake / the +0.7. If pursued, scope it to **case4 ONLY** (don't waste effort on case3) and treat the
  watertight re-triangulation as the make-or-break risk to prototype FIRST.
