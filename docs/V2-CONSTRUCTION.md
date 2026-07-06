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
