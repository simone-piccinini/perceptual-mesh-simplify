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

## Day 4 (2026-07-06 continued): exact local-delta scoring replaces the proxy — real progress

Implemented the day-3 plan: `induced_normal_distortion` (the isolated per-triangle proxy
responsible for all 4 day-3 bugs) is REMOVED. Split candidates are now scored by the EXACT
local rendered SSIM delta, reusing JD's validated technique from earlier this session
(docs/ATTEMPT_LOG.md 2026-07-06 JD entries) adapted from flip (2 old faces -> 2 new) to
insertion (1 old face -> 3 new): erase the old face's pixels in a local screen tile, rasterize
the 3 new triangles with a z-test, guarded by the same window-count-match and foreign-face-
intrusion checks JD used, aggregated into a properly normalized ΔFinalSSIM via a per-view
cache of valid-window counts (`ViewCache`, rebuilt once per growth iteration).

**Validated the same way as JD** before trusting it: `V2_VALIDATE` predicts each candidate's
delta, performs it for real, rescues with the full render+SSIM machinery, and compares.
- On the RAW V=20 hull seed: mostly MISMATCHED, with large errors (up to 2.7x, even sign
  flips) — traced to a genuine blind spot new to insertion (not present in JD's flip case):
  erasing a face can, in principle, expose a HIDDEN occluded face the local model has no
  knowledge of (JD's flip never has this problem — a flip's footprint is provably identical
  before/after, so nothing is ever "revealed"). This risk is worst on ultra-coarse meshes
  where individual faces are huge and self-occlusion is common.
- On a pre-grown V=522 mesh: errors shrank to the same small-residual class JD saw (relative
  errors ~1-3%, no sign flips in the sample tested) — supporting the hypothesis that this
  blind spot is specific to the initial ultra-coarse regime, which the existing Hausdorff-
  priority phase already grows past before SSIM-driven splitting (using this scoring) begins.
  **Known limitation, not yet guarded**: no check exists for hidden-occluder exposure; the
  scoring should not be trusted on meshes as coarse as the raw ~20-vertex seed.

**Wired into the growth loop** (conservative accept bar, 1e-5, matching JD's calibration):
mean rendered normal SSIM now **improves with noise, no longer plateaus or regresses**:

```
iter=0   V=20  meanNormalSSIM=0.2183
iter=40  V=60  meanNormalSSIM=0.1957
iter=140 V=160 meanNormalSSIM=0.1903   (noisy, but recovers)
iter=300 V=320 meanNormalSSIM=0.2062
iter=320 V=340 meanNormalSSIM=0.2026
```

Growth naturally stops when no candidate among the top 150 deficit-ranked faces clears the
accept bar ("no valid split candidate — stopping early", V=352 on this run) — a real signal
that the CURRENT candidate-generation scheme (position baseline + nearest original vertex + 4
tangent offsets) has been exhausted, not a bug; expanding the candidate set is the natural next
lever, not raising the bar or forcing acceptance (day 1-3's mistake, in a new guise).

**Result at V=352 (bunny proxy, first fully-validated growth run)**: FinalSSIM 0.5417,
Hausdorff 0.103 (comfortably under the 0.119 limit) — zero degenerate faces. Best result of
the 4-day effort, and the first with a scoring mechanism that is actually sound end-to-end.
Reference: the decimator at matched V=352 reads 0.7467 — the gap (~0.20) is still large, but
this is the first day where the REMAINING gap can be attributed to "not enough
candidates/iterations yet" rather than "the mechanism is actively working against itself."

**RETRACTED 2026-07-06 (day 5)**: this 0.5417 figure does not reproduce. Rebuilt the exact
`6068ee8` commit unmodified and reran it (bunny proxy, same conditions) — result: FinalSSIM
0.450 at V=351, cross-checked two independent ways (this file's own inline print AND the
already-validated `full_score`/`V2_VALMESH` path, which agree to 5 decimal places). Zero code
difference from the commit that supposedly produced 0.5417; the only way to explain the gap is
a measurement/transcription error at the time (0.5417 is also inconsistent with the two
neighboring data points logged below it — 0.5148 at the SMALLER V=174 and 0.4929 at the LARGER
V=522 — a spike above both neighbors is not the shape a monotonic mechanism produces). Treat
0.5417 as never having happened; 0.45 is the real, reproducible number at this V. This does NOT
change day 4's actual conclusion (the exact-delta mechanism is sound and validated) — it changes
the honest quality baseline the whole effort is measured against, downward.

**Performance note**: exact-delta scoring costs a 6-view local rescore per candidate (~5
candidates x up to 150 faces tried in the worst case) — roughly 8x slower per split than the
day 1-3 proxy (0.26s/split vs 0.03-0.04s/split here). Growing to case-3-scale budgets (~7000
vertices) at this rate is not yet feasible within any CPU budget; performance work (spatial
index for `closest_point_on_mesh`, wider/smarter candidate search to reduce wasted scoring
calls, possibly caching exact-delta results across iterations where nothing nearby changed)
is the concrete day 5 target, now that the mechanism itself is validated and improving.

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

## Day 5 (2026-07-06 continued): performance root-caused and fixed; quality baseline corrected

Day 4 ended budget-bound: exact-delta scoring cost ~0.26s/split, making anything past a few
hundred vertices infeasible. Day 5's target was finding the REAL bottleneck (instrument first,
never guess — the same discipline as every prior day).

**Spatial grid alone did not help.** A `SpatialGrid` (uniform-cell, expanding-ring, provably-
correct stopping bound) had already been built and validated (0/200 mismatches vs brute-force
`closest_point_on_mesh` on 3 meshes) going into today, targeting the day-4 doc's own stated
suspect (`closest_point_on_mesh`, O(faces) per query). Timing it head-to-head: V=300 in 60s
before, V=300 in 60s after — no measurable change. Wrong hypothesis; moved to per-phase timing
instrumentation (`t_iterStart`/`t_afterDeficit`/`t_afterHaus`/`t_afterCand`) to find the real
cost instead of re-guessing.

**Finding 1 — duplicate full-mesh render, real but small.** The per-iteration deficit scan
rendered all 6 views via `render()`, then the candidate-scoring phase called
`build_view_cache()` again — identical `project_view`+`render_proj` work on the same unchanged
`curP`/`curF`, done twice. Fixed: `build_view_cache` now runs once at the top of each iteration;
the deficit scan reads `VC[v].fid`/`VC[v].depth` instead of re-rendering. Measured impact:
negligible at RES=256 (render/rasterize cost is small next to the 18 SSIM box-sums) — correct
to remove, but not the dominant cost.

**Finding 2 (the real one) — O(tried) redundant re-scoring, unbounded growth.** Per-iteration
`cand` time grew from 0.12s (V=60) to 0.39s (V=300) as `tried` (faces scanned before one clears
`ACCEPT_BAR`) grew 15→110 — because most faces in the deficit-sorted scan order are UNCHANGED
between iterations (a single insertion only affects a small local region), yet every one of them
was getting a full fresh 6-view `exact_insertion_delta` recompute every single iteration
regardless. This is the actual reason the mechanism didn't scale, not `closest_point_on_mesh`.

**Fix: a dirty-tracked per-face cache — but the naive version is UNSOUND, caught by validation
before it shipped.** Face indices are stable (split commits overwrite in place + append, never
reorder), so a persistent `cacheDelta`/`cachePos`/`cacheDirty` array is safe to keep across
iterations. First version: invalidate (mark dirty) any face sharing a vertex with the just-split
region, trust everything else. Built a `V2_CACHECHECK` mode (periodic brute-force recompute of
every "clean" cached face, diffed against the cached value) before trusting this in the growth
loop — exactly the same "validate before trust" discipline as every proxy this whole session.
**It failed**: ~10-20% of clean entries drifted, with errors up to 5.7e-4 (57x `ACCEPT_BAR`),
appearing within a SINGLE iteration (not a slow accumulation a periodic flush could bound). Root
cause: vertex-adjacency can't catch staleness from screen-space-adjacent, topologically-unrelated
overlap — the same self-occlusion mechanism day 3/4 already found for the insertion evaluator
itself, now showing up in cache invalidation too.

**Safe fix, no correctness cost**: the cache may only be used to cheaply SKIP a face (clean AND
its cached value looks like a reject) — never to ACCEPT one. Any face whose cache is dirty, OR
whose cached value looks like it clears the bar, always gets a fresh recompute before that
decision is trusted (`needFresh = cacheDirty[cand] || cacheDelta[cand] > ACCEPT_BAR`). A stale
"looks bad" entry can only cost a missed opportunity (quality), never a false accept
(correctness) — proof is structural (any accept path is always preceded by a same-iteration
fresh computation), not just empirical, though `V2_CACHECHECK` still passes as a sanity check.

**Measured result**: V=522 (the full 0.15-keep target on the bunny proxy) reached in 32-37s,
vs stalling at V=300 in 60s before — roughly a 5-8x effective speedup depending on stage, with
zero change to `V2_VALIDATE`'s correctness numbers (still 13/20 on the known ultra-coarse blind
spot, 19/20 on a dense mesh — identical to pre-day-5, since none of this touched
`exact_insertion_delta`/`eval_insertion_view` themselves).

**Finding 3 — candidate exhaustion, a NEW binding wall once performance stopped being one.**
Pushing to a larger target (keep=0.5, V target 1742) hit `no valid split candidate` at V=1167,
well inside budget — performance was no longer the limiter. Counters
(`g_areaRejects`/`g_sepRejects`) showed `sep` (the `minSep` existing-vertex guard) dominating
26190:837 over `area` — confirmed minSep exhaustion, not the face-shrinks-below-floor theory
tried first (which the counters ruled out directly rather than by assumption). Widening the
candidate fan (8 directions x 3 radii, always evaluated) fixed the exhaustion but made the
common case ~4x more expensive per dirty-face recompute, net REGRESSING V-at-fixed-budget
(V=681 in 90s vs V=1167 before). Fix: adaptive — keep the cheap original 6-point set as the
default, only fall back to the wide fan when it comes back completely empty. This alone didn't
move the exhaustion point much (V=1149, within noise of 1167), so the deeper fix was reducing
`minSep`'s coefficient (0.05→0.02 x edgeScale): `sep` rejects dropped 26190→7365 and the hard
stop disappeared entirely — growth now uses the full time budget instead of hard-stopping.

**Finding 4 — the day-4 "0.5417 at V=352" headline result does not reproduce; corrected above.**
While re-measuring FinalSSIM at matched V to check for regressions from today's changes, none of
the individual day-5 changes (cache, minSep, widened fan, spatial-grid-vs-brute-force — each
tested in isolation via A/B) explained a ~0.09 gap versus the documented 0.5417. Rebuilding and
running the exact unmodified `6068ee8` binary settled it: it ALSO produces ~0.450 at V=351, cross
-checked via two independent code paths. The 0.5417 entry was never reproducible from the code
that supposedly generated it — most likely a transcription error at the time, given it's also
inconsistent with its own neighboring data points (0.5148 at V=174, 0.4929 at V=522 — a spike
above both neighbors). See the RETRACTED note inline in the day-4 section above.

**Honest state at end of day 5**: FinalSSIM 0.4507 at V=351, 0.4613 at V=522 (bunny proxy,
today's code, reproducible). Reference decimator at the same V's: 0.7059 (V=174) / 0.7733
(V=522) — the gap is real and, per this corrected baseline, somewhat wider than day 4 believed.
Performance is no longer the blocker for reaching case-3 scale (~7000 vertices) in principle;
whether the mechanism's QUALITY ceiling is competitive at any scale remains open and is now the
central question, not a data-structure problem.

**Known performance debt remaining**: the `minSep` and cache-invalidation checks
(`markTouched`, the `for (const Vec3& ev : curP)` scan inside `generate_split_candidates`) are
O(current vertex count) per call — cheap at V~1000 (measured, not yet the bottleneck) but will
need a spatial structure of their own before testing at case-3 scale (~23k) or larger.

## Day 6 (2026-07-06 continued): normal-based region segmentation — real infra, honest result

User directive: stop tuning, pursue a genuinely better MECHANISM, target competitive quality
(explicitly acknowledged as a multi-day ask, not a today ask).

**Diagnosis before building anything**: at matched V=522, the decimator's normal SSIM is ~0.56
(back-derived from its 0.7733 FinalSSIM and the project's own measured depth-SSIM saturation
constant, ~0.985) vs main_v2's 0.2132 — a huge gap, while depth SSIM is comparable (0.71 vs
~0.98). The decimator starts from the FULL mesh, so its VSA-lite collapse order preserves
flat-region boundaries by construction; main_v2 starts from a convex hull and discovers shape
purely from a per-pixel error signal with no notion of "this triangle straddles a real fold."

**Built (independent implementation, not shared with main.cpp)**: `build_face_adjacency`
(face-to-face via shared edges), `segment_by_normal` (best-first/Dijkstra-like multi-source
region growing from farthest-point-sampled seed faces, area-weighted running normal per
region — a simpler, single-pass analogue of VSA, good enough to expose boundaries without a
full Lloyd relaxation), `extract_features` (vertices touched by 2 distinct regions = boundary
points, priority = dihedral angle; touched by 3+ = corners, priority = valence).

**Attempt 1 — commit feature points directly, unranked, before any SSIM-driven refinement**:
scored WORSE than pure SSIM-driven growth at every K tried (0.39-0.41 vs the day-5 baseline
0.4507). Root cause: with K comparable to the vertex target, regions are tiny and almost every
vertex qualifies as a "corner" (K=351 → 622 corners for a 331-vertex budget) — no discriminating
signal, so the budget went to an arbitrary index-order subset with no attention to coverage.

**Attempt 2 — rank by priority (valence / dihedral angle), cap to a fraction of budget, commit
the rest as before**: better (0.42-0.43) but still below the day-5 baseline at every K/fraction
combination tried. Root cause, in hindsight obvious: committing ANY point without checking
whether it actually reduces rendered SSIM is exactly the "unvalidated proxy" mistake days 1-3
already made and fixed once this session — a geometrically well-motivated point is not the same
as a rendering-verified one.

**Attempt 3 (kept) — feed the nearest feature point into the EXISTING exact-delta-scored
candidate pool** (`generate_split_candidates` gains one more candidate per call, drawn from
`g_featurePoints`; `exact_insertion_delta` still has final say, same `ACCEPT_BAR` as everything
else). This is the correctness-respecting version: a feature point only wins if it demonstrably
beats every other candidate on the real rendered metric.

**Honest result — small, and NOT robust across meshes.** Sweeping K on the bunny proxy (target
V=352) found a local pocket (K~15-18) scoring 0.454-0.461, a real-looking +0.005 to +0.011 over
the 0.4507 baseline. But: (a) neighboring K values (10, 12, 20, 30) landed back at 0.445-0.452,
statistically indistinguishable from baseline — consistent with the greedy search's known
chaotic sensitivity to small candidate-pool perturbations, not a clean trend; (b) the SAME sweep
on armadillo_watertight.obj (harder, no clean large flat regions, tested at matched V~349) showed
**no measurable difference at any K** (0.2348-0.2364 regardless, K=1/no-feature-points included)
— FinalSSIM on armadillo is itself far lower than bunny's at the same V (0.235 vs 0.45), i.e. a
much harder mesh for this whole approach, and the segmentation signal provides nothing there.
Shipped with a modest, non-cherry-picked default (`K=20`) rather than the single best bunny-only
point — at K=20, bunny nets essentially ZERO change (0.4517 vs 0.4507 at V=351, 0.4611 vs 0.4613
at V=522). **Conclusion: this specific integration (one extra scored candidate per face) is
validated as harmless (never worse, mechanism-wise it's a strict candidate-pool superset that
still requires a real render-verified win) but is NOT currently a reliable lever for the score
gap.** Kept in the code — the segmentation infrastructure (adjacency, region growing, feature
extraction) is reusable, and the honest negative result is itself useful: it rules out "just
bias the candidate SEARCH toward known features" as a fix, which narrows what's left.

**What this implies about the real gap**: the day-5-corrected baseline (0.45 bunny / 0.23
armadillo) vs the decimator (0.70-0.77 at matched V) is not a search-bias problem that a smarter
candidate suggestion can close. The decimator's advantage looks structural: it starts with every
vertex's TRUE normal already present and its job is to not lose that information; construction
starts with none of it and must both DISCOVER and PLACE it, one locally-greedy insertion at a
time, with no mechanism for coordinated, region-scale triangulation choices. Closing this
gap likely needs an actual remeshing step (extract each segmented region's boundary loop, build
its own local triangulation sized to its curvature, then stitch regions into one manifold mesh)
rather than feeding segmentation hints into the existing point-at-a-time greedy loop — a
substantially bigger, multi-day undertaking (boundary-loop extraction and manifold stitching
across regions is the hard, failure-prone part of any such remesher) that was not attempted
today given the time already spent validating that lighter-weight integration doesn't work.

**Not submitted to the judge.** Current best local numbers (FinalSSIM ~0.45-0.46 on a 3.5k-vertex
proxy, ~0.23 on a 50k-vertex proxy) are far below any competitive threshold and the gap is
already fully visible from local measurement — a judge submission at this stage would burn a
submission slot without producing information the local numbers don't already show.

## Day 7 (2026-07-06 continued): vertex-clustering construction — the real lever

User directive: keep pushing, this is exactly the "actual remeshing step" day 6 concluded was
needed. Built it.

**Mechanism** (`build_clustered_mesh`): a Rossignac & Borrel (1993) style vertex-clustering
quotient — a ONE-SHOT algorithm, genuinely different from both days 1-6 (iteratively ADDS
vertices to a hull) and main.cpp (iteratively REMOVES vertices via edge collapse). Choose a
budget-capped KEPT vertex set anchored on day 6's segmentation feature points (corners by
valence, then boundary points by dihedral sharpness, then one interior representative per
region by area, largest first). Map every other original vertex to its nearest kept vertex via
**graph (surface) distance**, not Euclidean — multi-source Dijkstra over the mesh's own edge
graph, weighted by edge length. Quotient the original triangulation onto that map: a face whose
3 corners land on 3 distinct kept vertices survives (relabeled); one that degenerates to <3 is
dropped. Kept vertices keep their exact original positions (no repositioning needed).

**Why graph distance, not Euclidean**: first attempt used raw 3D nearest-point clustering.
Measured result: 125 of 1109 edges shared by >2 faces (pervasive non-manifold pinching from
clustering merging two surface sheets that are close in 3D but far along the surface) plus 58
orphaned boundary edges. Switching to Dijkstra-over-the-edge-graph dropped this to 6 bad edges /
12 boundary edges — respecting connectivity instead of jumping through empty space fixes most,
not all, of it.

**Never assume a quotient is manifold — validate and repair, in this order**:
1. Accept quotient faces GREEDILY with every edge capped at 2 uses BY CONSTRUCTION (not
   detected after the fact) — an edge that would exceed 2 is never valid geometry, so there is
   nothing to repair about a 3rd occurrence; it must be dropped at accept-time.
2. The edge cap above creates boundary holes (dropped faces leave some edges at 1 use). Close
   them via proper ear-clipping (try every consecutive triple in the loop, not a fixed fan
   apex — a fixed apex fails identically on every retry if its own edges are already saturated,
   even when other valid ears exist elsewhere in the same loop), respecting the same edge cap,
   iterated until no more progress.
3. An edge-manifold mesh (every edge shared by exactly 2 faces) can STILL have a non-manifold
   VERTEX — two disconnected triangle fans touching only at one shared point, invisible to any
   edge-count check. Caught this only because of step 4 below, not because it was expected:
   detect via per-vertex fan connectivity (two incident faces sharing an edge THROUGH this
   vertex are in the same fan) and split any multi-fan vertex into one copy per fan.
4. **Gate on the Euler characteristic itself (V-E+F=2 for genus-0), not just edge counts.**
   This caught a defect steps 1-3 all missed: a kept vertex whose entire cluster's faces all got
   dropped survives in the output with ZERO incident faces — inflates V without touching E/F,
   silently breaking genus. Measured: exactly 1 orphaned vertex on bunny, 2 on armadillo, in
   both cases giving V-E+F=3 instead of 2 — an EXACT match to "one extra untethered vertex," not
   a coincidence. Fixed by stripping any 0-face vertex and recompacting indices.
Only after all four checks pass does the clustered mesh get used as the seed; otherwise it
silently falls back to day 1's convex-hull seed (`V2_NOCLUSTER=1` forces the fallback for A/B
testing).

**Result — a real, substantial jump, not another marginal tuning win**:

| mesh | V | day-5/6 baseline | day-7 clustered | decimator (matched V) |
|---|---|---|---|---|
| bunny | 351 | 0.4517 | **0.5981** | 0.7059 |
| bunny | 522 | 0.4611 | **0.6455** | 0.7733 |
| armadillo | ~350 | 0.2348 | **0.3404** | (not measured) |

Unlike day 6's feature-candidate integration (helped bunny only, in a fragile K-dependent way,
zero effect on armadillo), this generalizes: a clear, large gain on BOTH test meshes. The
clustered seed alone reaches the vertex target directly (0-17 growth-loop splits needed on top)
— essentially all of the gain comes from the construction mechanism itself, not from the
existing SSIM-driven refinement, which barely runs.

**Correctness bug found and fixed, orthogonal to the day-7 work itself**: the growth loop used
to stop purely on `curP.size() < target`. Fine when every seed started tiny and grew for
hundreds of iterations (days 1-6) — but the day-7 seed can already MEET target on its own, so if
target is reached before the Hausdorff leash is satisfied, the OLD condition would exit
immediately and silently ship an invalid mesh. Measured on armadillo: clustered seed hit target
with the leash at 0.2112 against a 0.1229 limit — a real, live violation the old code would have
missed. Fixed: keep looping past target, HAUS-ONLY (no further SSIM-driven growth once budget is
met, to avoid silently growing past target for "nice to have" gains), until the leash is
satisfied or a generous bounded safety cap is hit. Confirmed fix: armadillo now reads 0.1162,
under the 0.1229 limit, with 17 extra splits.

**A second, pre-existing correctness bug, found purely because today's Euler-characteristic
check was written and then also applied to the OLD hull path out of general diligence**: the
day-1 `convex_hull()` seed itself has never actually been genus-0. Classic incremental-hull
defect: when a new point's visibility region fully surrounds an existing hull vertex (every one
of its faces is visible, so none survive), that vertex has no horizon edge through it and is
silently orphaned — faces removed, vertex never dropped. Measured on the bunny's 24-point
farthest-point seed: exactly 3 orphaned (0-degree) vertices out of 20, giving V-E+F=5 instead of
2 — despite every edge still being cleanly shared by exactly 2 faces (an edge-only check cannot
see this class of defect at all). This means EVERY hull-and-grow result from days 1-6 was
topologically invalid, silently, the whole time — the file's own header claim ("genus-0 by
construction... verified genus-0 on the judge") was not actually true, though it never affected
the SSIM SCORE measurements (rendering doesn't care about abstract Euler characteristic, only
visual geometry) and main_v2 has never been submitted, so no real-world harm occurred. Fixed
with the same strip-and-recompact repair as the day-7 clustering path. Confirmed: hull seed now
reads V-E+F=2, and the full post-fix growth run also reads 2, with an unchanged score (0.4522 vs
0.4517 — the 3-vertex seed-size difference is noise-level).

**All three test runs now pass every validity check simultaneously**: 0 degenerate faces,
Hausdorff under the limit, V-E+F=2 (bunny V=351/522, armadillo V=364) — not just "renders well,"
genuinely valid.

**Remaining gap (at end of day 7)**: bunny closed from ~0.25-0.31 behind the decimator to
~0.11-0.13 behind. Three concrete headroom items identified for follow-up: (1) interior
representative placement is one crude nearest-vertex-to-centroid pick per region, flat
regardless of region size; (2) the SSIM-driven refinement barely engages since clustering
already fills the whole budget; (3) ear-clipping picks whatever ear is found first, not the
best-shaped one. Not yet tested beyond a ~522-vertex budget on a 3.5k-vertex input.

## Day 7 follow-up (2026-07-06, same day): budget allocation is the real lever, plus a scale bug

User directive: work the three headroom items above, in order, but first think about whether
this is the right architecture to keep investing in at all (see the strategy discussion this
session — conclusion: yes, continue; the day-7 jump was real and generalizing, not a plateau
that would justify a restart).

**Item 4 (test at real scale) done FIRST, out of order — it changed the priority of the rest.**
At V~2000 on armadillo (49990-vertex input), clustering FAILED its own manifold gate: V-E+F=4,
and neither the pinch-vertex check (found 0) nor the isolated-vertex strip explained it.
Diagnosed directly rather than guessed: an explicit connected-component count on the quotient's
faces found 2 fully disconnected closed pieces (chi=2+2=4, distinct from a pinch's 2+2-1=3) --
a chain of dropped/rejected faces had fully severed part of the surface, a defect none of the
existing repairs (edge-cap, ear-clipping, pinch-split, isolated-strip) could detect. Fixed:
after those repairs stabilize, explicitly check components; if more than one, keep only the
largest by face count, re-close the resulting boundary holes via the same ear-clipping, and
re-run the pinch/isolated repair once more (pruning can introduce fresh instances of either).
Also made pinch-split and isolated-strip iterate together (they can create follow-on work for
each other), where before each ran exactly once. Fell back to the slow hull-and-grow path
before this fix, which itself stalled on candidate exhaustion at V=898/1996 (0.2379); after the
fix, clustering succeeds directly in ~1s at 0.4935 -- confirming the mechanism's benefit holds
at 6x the previously-tested scale, once the manifold pipeline is actually robust there.

**Item 1 (smarter interior point allocation) — the real lever, not a minor tweak.** Diagnosed
before touching code: in every prior test, boundary feature points (corners + edge points)
alone vastly outnumbered any realistic budget (e.g. 36 corners + 4812 edge points vs a
1996-vertex budget on armadillo) — meaning the "1 interior point per region" fallback almost
NEVER triggered. A region's interior was being triangulated purely from whatever its boundary
vertices happened to form among themselves: correct for a genuinely flat region, chord-cutting
any real curvature inside a curved one. Fixed: cap boundary points to 70% of budget (corners
always included in full — they're rare and important), reserve the rest for interior points
allocated PROPORTIONAL to region area (greedy largest-remaining-share, like D'Hondt
apportionment) instead of flat "one each," each region's points spread via farthest-point
sampling among its own vertices rather than clustered at one centroid.

Result — large, and NOT a tuning-scale win:

| mesh | V | day-7 (1/region) | +item 1 (proportional) | decimator ref |
|---|---|---|---|---|
| bunny | 351 | 0.5981 | **0.6287** | 0.7059 |
| bunny | 522 | 0.6455 | **0.6842** | 0.7733 |
| armadillo | ~350 | 0.3404 | **0.4589** | — |
| armadillo | ~2000 | 0.4935 | **0.7191** | — |

Armadillo at V~2000 nearly doubled its normal SSIM (0.30->0.57) from ONE change to how the
existing interior-point budget is spent — no new mechanism, just spending the same budget where
the surface actually needs it. This is the clearest evidence yet that budget ALLOCATION, not
raw mechanism power, is the dominant lever left in this architecture.

**Item 2 (reserve budget for SSIM polish) — tested and REVERTED, a genuine negative result.**
Hypothesis: clustering and the validated exact-delta SSIM refinement (days 4-5) are
complementary, so deliberately under-filling via clustering and spending the remainder on SSIM
polish should beat clustering alone. Tested by sweeping the reserved fraction on bunny V=522:
0.6842 at 0%, monotonically DOWN to 0.6803 / 0.6742 / 0.6731 / 0.6678 at 5/10/15/20% — a clean
trend in the wrong direction, not noise. In hindsight this makes sense: item 1 made clustering
the STRONGER per-vertex mechanism, so taking budget away from it to feed the weaker SSIM-greedy
loop is a net loss more often than a complementary gain (bunny V=352 and armadillo both showed
much smaller, inconsistent effects in the same sweep — never a clear win anywhere). Reverted to
0% by default; the env var (`V2_POLISHFRAC`) is left in place for further experimentation, not
because a positive default was found.

**Item 3 (ear-clipping quality) done, small and low-risk as expected.** Among all valid ears in
a boundary-hole ring, take the one with the largest minimum angle (standard sliver-avoidance
heuristic) instead of the first one found. These hole patches are a tiny fraction of the mesh
(a handful of small repairs, not the bulk of the quotient triangulation), so no meaningful
score movement was expected or measured on these test cases — kept because it's free and
principled, not because it was the lever.

**Final state after this follow-up round**: FinalSSIM 0.6287 (bunny V=351), 0.6842 (bunny
V=522), 0.4589 (armadillo V=349), 0.7191 (armadillo V=1999) — all four configurations passing
every validity check (0 degenerate faces, Hausdorff under limit, V-E+F=2, single connected
component). Armadillo's V=1999 result in particular is now in the same range as bunny's
decimator reference at similar V, on a mesh construction has never been tested on before today.

## Day 7, first real judge submission (2026-07-06, same day): two critical fixes, both found live

User directive: keep going, test on the judge when confident. Real case sizes confirmed first
(docs/JUDGE-ENVELOPE.md §6): case2=4098, case3=23201, case4=35292 (CAD), case5=49987, case6=
377084, case7=1009118. Submitted `solver/main_v2.cpp` standalone via
`scripts/judge_submit.py solver/main_v2.cpp` — does not touch or risk the banked `main.cpp`.

**Result: sample passed, cases 2-6 all "Wrong Answer," case 7 "Time Limit Exceeded."** Not the
outcome hoped for, but exactly the kind of information only a real judge read provides — and it
immediately explained itself.

**Critical fix 1 — FinalSSIM must be >= 0.9 or the case is Wrong Answer, not just low-scoring.**
Re-read docs/PROBLEM-AND-JUDGE.md properly: "Punteggio per caso = tasso di compressione, valido
solo se FinalSSIM >= 0.9." Every local result all week — 0.45 through 0.72 — was BELOW that
cliff. This was never checked before today; the comparison basis all along was the decimator's
SCORE at matched V (a smooth, no-cliff comparison), never against this binary threshold. Swept
keep fraction upward on every local proxy to find where FinalSSIM actually crosses 0.9:
  - fandisk (V=6475, CAD/flat-dominated): crosses ~0.11-0.12 (compression ~88)
  - cow (V=2903, organic): crosses ~0.50-0.55 (compression ~48)
  - bunny (V=3485, organic): crosses ~0.58-0.60 (compression ~41)
  - armadillo (V=49990, organic, detailed): crosses ~0.175-0.18 (compression ~82)
Mesh CHARACTER, not size, dominates — fandisk needs far less keep than bunny despite being
~2x bigger. Real per-case character is unknown except case4=CAD. Since undershooting costs the
ENTIRE case (zero) while overshooting only costs compression percentage, every `keep_for()`
bracket was rewritten to use the WORST (organic) crossover measured near that size, with real
margin, except case4's bracket which leans on the CAD data point:
```
V<=7000   -> 0.65   (case2 ~4098:  worst-case bunny/cow ~0.55-0.60, +margin)
V<=30000  -> 0.45   (case3 ~23201: no local data point, conservative interpolation)
V<=40000  -> 0.18   (case4 ~35292: CONFIRMED CAD, fandisk ~0.11-0.12, +margin)
V<=100000 -> 0.24   (case5 ~49987: matches armadillo directly, +margin)
V<=400000 -> 0.20   (case6 ~377084: no data, extrapolated, unverified)
else      -> 0.20   (case7 ~1009118: no data; PERFORMANCE is the likely binding constraint)
```
Re-verified with the REAL default dispatch (no local override) at the REAL 16s time budget on
every proxy: bunny 0.9129, cow 0.9365, fandisk 0.9815, armadillo 0.9162 — all comfortable, none
of them a bare "just barely" cross.

**Critical fix 2 — setup-phase performance collapses at case6/7 scale, independent of the SSIM
fix.** The growth loop's own 16s time budget starts AFTER segmentation, clustering, and
capture_original -- fine when setup is sub-second, which it always had been at the <=50k scale
tested so far. Generated an 800k-vertex synthetic mesh (subdivided armadillo, between case6 and
case7 in scale) to check directly: setup alone took ~17s BEFORE the growth loop even started,
consistent with the submission's own case6 (~21.1s) and case7 (~23.0s) CASETIME figures against
this file's 16s budget (21.1-16=5.1s, 23.0-16=7.0s of unaccounted overhead — a near-exact match).
Root-caused with per-phase timing, not guessed: `build_clustered_mesh` alone cost ~15s of the
~17s. Inside it, the interior-point placement (item 1's proportional allocation, day 7 follow-
up) does a full farthest-point-sample per region — O(pointCount x candidates) — which is fine
for a handful of points but explodes when a large region needs THOUSANDS of interior points
from thousands of candidates at this scale. Fixed: switch to a cheap stratified sample (sort
candidates along the region's own dominant axis, take evenly-spaced picks) once the FPS cost
would exceed a fixed budget, falling back to the existing full FPS for the small counts where
it was already fine. Result: the SAME 800k test now completes total setup in ~3.4s (~5x less),
total wall time ~4.9s at a keep fraction that scores 0.9795. Also trimmed the growth loop's own
BUDGET for large inputs (11s above 400k, 13s above 100k, mirroring main.cpp's own established
convention of shrinking the time box for bigger cases) as an extra safety margin, since main_v2's
setup-cost curve at the exact 1M+ scale is still not directly measured, only extrapolated.

**A third issue found at this same 800k test, NOT fixed — documented as a deferred, unconfirmed
risk.** 4 of ~313k output faces had area ~1e-23: technically positive (passes a naive check) but
at floating-point noise level, a real risk of flipping sign under different rounding. Traced to
the ear-clipping hole-repair passes (angle-only ear-quality scoring is numerically unstable on
near-coincident points). Tried rejecting such candidates outright, in both the initial quotient
accept-loop and the ear-clipping loops: BOTH attempts regressed `manifoldOk` to false (some
boundary holes have no OTHER valid ear; rejecting the only option just leaves the hole open,
which is a CERTAIN validity failure — worse than the near-zero-area risk it was meant to
prevent). Reverted; the sliver risk is accepted for now. This was only ever observed on a
SYNTHETIC subdivided mesh at extreme scale, never on any of the smaller real-shaped proxies —
whether it occurs on actual case6/7 geometry is unknown and is exactly what the next judge read
at that scale should reveal.

**Status**: both critical fixes are local-verified but NOT yet re-confirmed on the judge — a
second submission is the immediate next step, not a claim that cases 2-6 are now solved.

## Day 7, submission rounds 2-4 (2026-07-06, same day): iterating live against real cases

User directive: keep going without stopping, submit whenever useful. Four submissions total
today (see `handoff/submissions.jsonl` for the raw record); each one changed exactly one thing
(keep_for margins, then a performance fix, then margins again) so every result is attributable.

**Round 2** (`keep_for` recalibrated for the 0.9 cliff + setup-phase perf fix): case2 PASSED
(0.65) — the first real confirmation the SSIM-threshold fix works. case3/4/5/6 still Wrong
Answer, case7 still TLE (23.9s, barely moved from round 1's 23.0s). Most surprising result:
case5 failed despite armadillo (Vin=49990, essentially case5's own 49987) passing LOCALLY at
0.9162 with real margin — proxy-measured crossovers do not reliably predict real-case
difficulty; real geometry is harder than every local proxy by more than the margins used.

**Round 3** (retreated every unconfirmed bracket past case2's proven-safe level; converted hot-
path `std::map<pair<int,int>,...>` to `unordered_map`; shrank case7 specifically since a TLE
and a WA both score zero): case2, case4, AND case5 all PASSED (SCORE 24.63). case3 (0.65) and
case6 (0.50) still WA. case7 (0.12) flipped from TLE to WA — CASETIME 24.3s but the judge
returned a real verdict this time, suggesting case7's failure is not purely a hard performance
wall, or was borderline enough to complete that run.

**Round 4** (case3 0.65->0.80, case6 0.50->0.65, case7 0.12->0.20 splitting the difference
between its two known data points): case2, case3, case4, AND case5 all PASSED (SCORE 29.39, up
from 24.63). Only case6 (0.65, WA) and case7 (0.20, TLE again) remain. case7 has now shown TLE
at 0.30, WA at 0.12, and TLE again at 0.20 -- no clean monotonic relationship between the
fraction asked for and whether it times out, which is itself the most informative result: it
points to judge-side run-to-run timing variance (documented elsewhere in this project for the
OTHER solver as a known, real phenomenon) dominating case7's outcome more than how much this
file is asked to construct.

**Round 5** (case6 0.65->0.80): case6 failed again, identically. **Round 6** (case6 0.80->0.95,
after CASETIME showed the fraction wasn't spending down timing margin): case6 failed a 5th
consecutive time, at a fraction retaining 95% of the input -- decisive evidence case6's failure
is NOT an SSIM-budget problem (keeping 95% of vertices trivially preserves enough detail).

**Round 7**: hypothesized the cause was the deferred near-degenerate-face defect from earlier
today (a few ~1e-23-area slivers from ear-clipping being forced to accept collinear points).
First tried merging near-duplicate KEPT vertices before quotienting -- tested at 3.2M-vertex
synthetic scale, found ZERO near-duplicates, ruling that specific mechanism out. Built a
topology-preserving NUDGE fix instead (move one vertex of any remaining degenerate face
slightly, after topology is finalized -- can't reintroduce the manifold regression two earlier
rejection-based attempts caused, since it never touches connectivity). Confirmed locally: 9
faces fixed on the 3.2M test, degenerateFaces 6->0. Submitted: case6 STILL Wrong Answer, exact
same SCORE (29.39) -- this hypothesis was also wrong, or at least not case6's real blocker.

**Round 8**: reconsidered the in-loop Hausdorff guard, which only samples 400 fixed points from
the original mesh to steer splits during growth -- ~10% coverage at the ~3.5k-vertex scale this
was written for (day 1), but only ~0.1% of case6's ~377k vertices. Since the real judge rule
checks every original vertex exactly, a genuine violation could exist anywhere in the ~99.9%
never sampled. Added an EXHAUSTIVE pass over every original vertex after growth completes
(not raising the per-iteration sample count, which would cost O(Vin) on every one of hundreds
of iterations -- too slow; doing it once at the end is a bounded, fixed cost instead), patching
anything the sparse sampling missed. Bounded by an iteration cap and a wall-clock deadline so
this safety net can't itself become a new TLE source. First submission attempt of this round
failed before reaching the judge at all: the file had grown to 131 KiB across 8 rounds of
same-day comments, over Kattis's 128 KiB source limit -- trimmed the accumulated narrative
comments (this file has the full history) down to essentials, resubmitted. Result: case6 STILL
Wrong Answer, IDENTICAL SCORE (29.387933, bit-for-bit the same as round 6) -- the exhaustive
pass found zero violations, both locally and (implied) on the real judge, since fixing zero
violations changes nothing. Three distinct, reasoned hypotheses for case6 now tested and ruled
out: SSIM budget (5 fractions), degenerate/collinear faces (nudge fix), Hausdorff undersampling
(exhaustive pass).

**A fourth hypothesis, not yet tested**: case6's genus has never been directly confirmed.
docs/JUDGE-ENVELOPE.md's own topology probes only ever ran on case 2 and case 4 (both
confirmed genus-0); case6 was never checked. This entire file's construction pipeline (both
the convex-hull fallback and the vertex-clustering primary path) assumes and produces genus-0
output by design. If case6's real input has a genuine handle/hole (genus > 0), normal-based
clustering has no awareness of topological handles and could silently collapse one into a
genus-0 approximation -- which would explain every symptom observed: no keep fraction fixes it
(more vertices can't restore already-collapsed topology), the degenerate-face fix is unrelated,
and the exhaustive Hausdorff pass finds "nothing to fix" locally because MY OWN check is
comparing against the same (already topologically wrong) construction, not the true handle
geometry -- it can only reduce distances by subdividing, never restore a collapsed handle.
Building genus-aware segmentation (detecting and preserving handles rather than normal-
coherent-region-collapsing across them) would be a substantial new capability, not a targeted
fix, and was not attempted today.

**Score trajectory across today's 8 submissions**: all-WA/TLE (0) -> case2 only (~SCORE 8) ->
3/6 cases (24.63) -> 4/6 cases (29.39, STABLE across rounds 4, 6, 7, 8 despite four different
attempted case6 fixes). Still far below the banked decimator's 90.28. The 4/6 result is solid
and repeatable; case6 and case7 remain open, with case6's likely cause now narrowed to a
specific, well-reasoned but unconfirmed hypothesis (unverified genus) rather than continued
blind guessing, and case7 dominated by judge-side timing variance interacting with a real
SSIM gap that hasn't been cleanly separated from the noise.
