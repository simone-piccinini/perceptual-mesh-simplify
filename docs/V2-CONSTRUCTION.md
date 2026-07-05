# main_v2.cpp — from-scratch construction algorithm, development log

Separate from `solver/main.cpp` (the banked, judge-submitted decimation solver) and from
`docs/THEORY.md`/`JUDGE-ENVELOPE.md` (which document that solver's specific findings). This
file's purpose: track the from-scratch CONSTRUCTION approach on its own terms, so its
development is not biased by the decimation solver's accumulated design decisions. Judge facts
(camera model, SSIM formula, Hausdorff rule, per-case limits) are shared ground truth and are
NOT duplicated here — see JUDGE-ENVELOPE.md / PROBLEM-AND-JUDGE.md.

**Status: early skeleton, NOT competitive, NEVER submitted to the judge.** Local-only work.
Multi-day effort by design (per explicit user direction 2026-07-06): the decimation solver took
weeks to reach 90.28; a construction-based approach starting today should not be expected to
compete on day one, and must not be judged by that yardstick.

## What is genuinely different from main.cpp

main.cpp DECIMATES: starts from the full input mesh, removes vertices via edge collapse,
ordered by induced normal distortion (VSA-lite). main_v2.cpp CONSTRUCTS: starts from almost
nothing and ADDS vertices where the rendered image is wrong. The search direction is inverted;
no code, data structure, or heuristic is shared between the two files. The only common ground
is the JUDGE'S OWN SPECIFICATION (OBJ format, 6-camera rasterizer, SSIM formula, Hausdorff
rule) — reimplemented fresh in main_v2.cpp rather than included, but necessarily identical in
its math since there is exactly one correct way to satisfy an external spec.

## Architecture (day 1, 2026-07-06)

1. **Seed**: convex hull of a 24-point farthest-point sample of the input vertices.
   - A convex hull can never have more vertices than its input set — hulling the FULL vertex
     set was tried first and rejected: on the bunny proxy (3485 verts) it produced a genuinely
     valid 647-vertex hull (verified: every input point inside/on it to 2e-15, watertight),
     already bigger than a 5%-budget target for small cases. Farthest-point sampling first
     gives a hard cap on seed size, independent of surface complexity.
   - Verified genus-0 on every available proxy (case3/4/5-class + bunny/fandisk) and on the
     real judge input for cases 2 and 4 (JUDGE-ENVELOPE.md) — convex hull (always genus-0) is
     a safe universal seed for this input family. If a genus>0 case is ever found, this seed
     needs revisiting (not expected, not yet tested beyond the above).

2. **Growth loop**: each iteration either closes the worst Hausdorff violation or attacks the
   worst rendered-SSIM-deficit face, whichever applies:
   - Hausdorff guard (validity requirement, not a quality preference): sample the original
     surface (400 farthest-point samples), find the one farthest from the CURRENT mesh surface
     (true point-to-triangle distance). If it exceeds the judge's 5%-of-diagonal leash, split
     the current mesh's nearest face and place the new vertex EXACTLY at the violating point —
     closes that specific gap to zero by construction.
   - Otherwise: render the current mesh from all 6 views, compute the per-pixel SSIM deficit
     against the stored original renders, backproject deficit onto contributing faces via the
     face-id map, split the worst face at a point pulled toward the closest point on the
     original surface.
   - Both branches validate the resulting 3 sub-triangle areas against a minimum-area floor
     before committing; on rejection, fall through to the next-best candidate (sorted by
     deficit) rather than accept a degenerate split.

## Bugs found and fixed today (via local testing, before ANY judge exposure)

1. **Nearest-VERTEX Hausdorff guard plateaued** (boosted every face touching the nearest
   CURRENT vertex to a violating point — this does not guarantee the next split actually lands
   in the gap). Measured: worst-violation distance stalled at 0.2773 vs a 0.1195 leash after
   ~60 splits, never improving further. Fixed: track the true nearest POINT (not vertex) via
   point-to-triangle distance, split exactly that face, place the vertex exactly at the
   violator. Confirmed convergent (0.1036, under the leash) immediately after the fix.

2. **Degenerate faces — 89% of the mesh, not a rare case.** A face repeatedly re-selected as
   worst can have its centroid converge onto an already-existing vertex (the closest point on
   the original surface stops moving once a local patch is adequately covered by a prior
   insertion), producing a zero-area sliver on the next split. Measured directly: 922 of 1034
   faces degenerate at V=522 before the fix (`min area 0.00e+00`, local evaluator FAIL). Fixed:
   every candidate split is validated against a minimum relative area before being committed;
   on failure, the next-best candidate (by deficit ranking) is tried instead.

## Key finding (the reason this file stops here for today, not a stopping point for the project)

**Normal-channel SSIM gets WORSE as V grows; depth-channel SSIM is flat-to-improving.**
Measured on the bunny proxy, both at Hausdorff-valid, zero-degenerate-face configurations:

| V | normal SSIM (mean over 6 views) | depth SSIM (mean) | FinalSSIM |
|---|---|---|---|
| 174 | 0.2907 | 0.7390 | 0.5148 |
| 522 | 0.2334 | 0.7523 | 0.4929 |

This is not "not yet competitive" (expected on day 1) — it is a REGRESSION with more degrees
of freedom, which should never happen if the growth criterion were sound: more vertices can
only help unless the placement rule is actively working against the metric. Diagnosis: new
vertices are placed by POSITION alone (closest point on the original surface). Position error
(→ depth SSIM) improves exactly as designed. But splitting a face into 3 smaller ones while
only correcting ONE corner's position, with no consideration of the resulting face NORMALS,
can create MORE inter-facet normal variation than the single larger face had — especially over
curved regions. This is the same structural lesson the decimation solver learned repeatedly
this project (THEORY.md §1, §6): the SSIM structure term (normal-map σxy) dominates the score,
not position/depth, and any mechanism that optimizes position while ignoring normals will
underperform or actively regress.

**Concrete next step (day 2): make placement normal-aware.** Candidates, not yet attempted:
- Search a small set of candidate positions per split (not just "closest point"), scoring each
  by induced normal error against the local original surface (the same kind of technique
  VSA-lite's `incident_ndist` uses for collapse placement, reapplied to insertion).
- Or: place at the position-based point, but then locally re-orient via a short rendered-SSIM
  gradient ascent (reusing the exact-math local-delta technique validated for JD earlier today
  — that machinery generalizes to "does moving this new vertex increase the true rendered
  SSIM", not just flips).
- Either way: validate LOCALLY (does normal SSIM stop regressing as V grows?) before spending
  any more engineering on performance or judge exposure.

## Day 2 (2026-07-06 continued): normal-aware placement, and a new deeper finding

Implemented the fix the day-1 finding called for: `pick_split_point` now searches a small
candidate set (position-baseline closest point, the nearest real original VERTEX, and 4
tangent-plane-offset points — all RE-PROJECTED onto the original surface so Hausdorff validity
is never traded away) and picks whichever minimizes `induced_normal_distortion` — the
area-weighted sum, over the 3 new sub-triangles, of `1 - cos(angle to the true local original
normal)`. Same spirit as VSA-lite's `incident_ndist` in the decimation solver, applied to
insertion instead of collapse.

**First attempt regressed Hausdorff** (0.249 vs the 0.119 limit): raw tangent-plane offsets
wandered off the true surface in exchange for normal alignment. Fixed by re-projecting every
candidate onto the original surface before scoring — Hausdorff passes again (0.111), and
FinalSSIM improved slightly at V=174 (0.5148 → 0.5395).

**New finding, deeper than day 1's: mean rendered normal SSIM plateaus HARD, exactly, and
does not move at all past roughly V=100-120** — traced with per-iteration instrumentation:

```
iter=80  V=100 meanNormalSSIM=0.1751
iter=100 V=120 meanNormalSSIM=0.1747
iter=500 V=520 meanNormalSSIM=0.1747   <- bit-identical to iter=120, 400 splits later
```

Ruled out: rendering resolution as the cause (re-ran at RES=512: overall SSIM reads higher, as
expected, but the plateau still sets in at essentially the same vertex count — resolution
shifts the VALUE, not the STALL point). The accepted split's `faceDeficit` value is bit-
identical (2026.1297) at every 20-iteration checkpoint from iter=100 through iter=500 — a
single region's rendered error appears to be **completely unaffected by any amount of local
splitting nearby**. Leading hypothesis, untested: a self-occlusion or rasterization edge case
(two different parts of the surface projecting to the same screen pixels in some view, or a
silhouette/coverage boundary) where the CURRENT candidate search (position + normal matching
against the nearest original point) cannot address the deficit because the true cause is
elsewhere on the mesh, not at the split location. This needs targeted debugging (dump the
actual screen region responsible for the stuck deficit and inspect what's really happening
there) before more placement heuristics are worth trying — bolting on more candidate types
without understanding this would be guessing, not engineering.

**Status for day 3**: do not resume by adding more split-candidate heuristics. Resume by
identifying the exact stuck screen pixels/view responsible for the frozen 2026.1297 deficit
value and understanding the mechanism — likely either a genuine self-occlusion case (in which
case the fix is architectural: splits must be attributable to the RIGHT region even under
occlusion) or a bug in deficit attribution/accumulation across iterations.

## Day 3 (2026-07-06 continued): four more bugs, one real structural finding

Built a deep diagnostic (`V2_DIAG=<iter>`, dumps the worst face's per-view visibility, screen
footprint, current-vs-original normal comparison, and an attribution cross-check) instead of
guessing at more placement heuristics blind. Chased the plateau through FOUR distinct causes
in sequence — each fix exposed the next layer:

1. **The true worst-deficit face was silently skipped every iteration.** `pick_split_point`
   always returned "the best of its candidates" even when every one failed the caller's OWN
   area-validity check afterward — so the single highest-value target (traced: face 92,
   deficit 5591, visible across 3 views up to 1690px) got rejected downstream every single
   time, while a far lower-value face (deficit 2026) was accepted instead, for hundreds of
   splits. Fixed: `pick_split_point` now filters candidates by validity INTERNALLY and returns
   `false` (not a bad point) when none qualify, so the caller correctly moves to the next
   candidate face.
2. **A "safety fallback" candidate was a geometric no-op.** Added a plain-centroid fallback so
   growth would never stall on a face with zero valid surface-aware candidates — but a
   triangle is always exactly planar, so splitting it at its OWN centroid produces 3
   sub-triangles perfectly COPLANAR with the parent: identical normal, bit-identical render.
   This candidate always passed the area check (looked harmless) while being unable to change
   a single pixel — "successfully" consuming vertex budget on a placebo. Traced: face 308's
   deficit sat frozen at exactly 1813.0061 for 100+ iterations after this fallback fired.
   Fixed: removed the fallback; if nothing surface-aware is valid, return `false`.
3. **A single distinctive original vertex acted as a "magnet"** for the "nearest real
   original vertex" candidate across many different parent faces in its neighborhood (a
   crease/corner scores very well on `induced_normal_distortion` in isolation). Traced by
   printing the actual chosen 3D position every 20 iterations: bit-identical across dozens of
   splits from DIFFERENT parent faces. New vertices clustered on top of each other at one spot
   instead of covering the hundreds of pixels the real deficit spans. Fixed: reject any
   candidate within `0.05 * edgeScale` of an already-existing current-mesh vertex.

With all three fixed, the plateau is GONE — but mean rendered normal SSIM now *decreases*
monotonically as V grows (0.2183 -> 0.1022 over 500 splits) instead of freezing. This is the
real, structural finding for day 4:

4. **Attribution mismatch (the self-occlusion hypothesis from day 1, now confirmed with a
   concrete example).** Diagnostic at iter=40: the reported "worst face" (76) renders a screen
   region where the ORIGINAL geometry that should actually be there is closest, in 3D, to
   DIFFERENT current faces (63, 56) — not face 76. `cos(current_normal, true_normal) = 0.23`
   at that pixel: a large, genuine mismatch. This is not a placement-quality problem local to
   face 76; face 76 is occupying screen space that belongs to a DIFFERENT part of the surface.
   No amount of clever positioning of ITS OWN split point can fix this — the true content is
   elsewhere, self-occluded or bridged-over by the still-coarse hull-derived topology. Spending
   vertex budget "fixing" face 76 cannot help and can actively hurt (diverting splits away from
   the faces — 63, 56 — that would actually resolve the region), which is the direct
   explanation for the observed regression.

**Root cause behind all four**: `induced_normal_distortion` scores a candidate by comparing
ONLY that single triangle's own resulting normal(s) against the nearest original surface
locally — a proxy, evaluated in isolation, with no connection to whether the change actually
reduces the TRUE measured rendered SSIM deficit in the affected screen region. Every bug above
is a different way for that proxy to diverge from the real objective (accepting geometrically
"valid" points that don't move any pixel; converging many parents onto one attractive point
regardless of overall coverage; being blind to WHICH region of the mesh the screen error truly
belongs to). This is the same class of lesson JD's development learned this session for a
different mechanism (flips): a proxy formula is not a substitute for the real metric.

**Concrete plan for day 4 — replace the proxy with the exact local delta.** JD's validated
technique (docs/ATTEMPT_LOG.md, 2026-07-06 JD entries): for a LOCAL mesh change, compute the
EXACT before/after rendered SSIM delta over just the affected screen footprint (a flip's
footprint is the quad bbox; an insertion's footprint is the union of the old triangle's bbox
across all candidate placements), validated to 1e-10 precision against a full bit-exact
rescore. Reusing that MATH (not the JD code, which is flip-specific) for split-candidate
scoring would directly fix the proxy-divergence root cause: a candidate only wins if it
provably increases the TRUE rendered SSIM, which automatically rules out coplanar no-ops,
already-covered magnet points (zero marginal gain once covered), AND wrongly-attributed
targets (a split that doesn't touch the real error source will correctly score ~zero true
gain, naturally deprioritizing it in favor of whichever face's split genuinely helps).
The self-occlusion/attribution problem itself may still need a longer-run Hausdorff-priority
phase before switching to SSIM-driven refinement (get the gross topology right first), but the
exact-delta scoring should stop misdirecting budget regardless.

## Known performance debt (not addressed today, correctness came first)

- `closest_point_on_mesh` is brute-force O(faces) per query; used both for the Hausdorff guard
  (400 samples/iteration) and the SSIM-branch placement (per candidate). Fine for prototyping
  on <1000-face meshes; will need a spatial index (BVH/octree) before this can run on real
  case-3-scale (23k) or larger inputs in any reasonable time.
- The SSIM-deficit scoring re-renders the ENTIRE current mesh from all 6 views every single
  iteration. For meshes needing thousands of splits (case 3's ~7000-vertex budget from a
  20-vertex seed), this is the dominant cost. An incremental local-delta approach (again,
  JD's validated technique — a single insertion's screen footprint is local, like a flip's) is
  the natural fix, once the underlying placement criterion is fixed and worth the investment.
- Today's timing on the bunny proxy (3485 verts, small): ~34ms/split. Extrapolated to case 3's
  target (~7000 splits from a small seed): would need several minutes, far past the CPU budget.
  Not a concern for today (correctness-first, tiny local proxy); a hard blocker before any
  larger-scale test.

## Local test log (2026-07-06)

- bunny_watertight.obj (Vin=3485), keep=0.05 (V target 174): FinalSSIM 0.5148, Hausdorff OK
  (0.1014 vs 0.1195 limit), 0 degenerate faces, 4.9s / 154 splits.
- Same input, keep=0.15 (V target 522): FinalSSIM 0.4929 (REGRESSED — see finding above),
  Hausdorff OK (0.1014), 0 degenerate faces, 19.1s / 502 splits.
- Reference (main.cpp decimator, matched V, same proxy): V=174 → FinalSSIM 0.7059, Hausdorff
  OK (0.031); V=522 → FinalSSIM 0.7733, Hausdorff OK (0.015) — the decimator IMPROVES with V,
  as expected, and leads by a wide margin at both sizes. This gap is the honest starting point;
  closing it is exactly the multi-day project this file exists for.
