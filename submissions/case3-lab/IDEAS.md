# case-3 IDEAS — ranked by expected value × confidence

Legend: [HARVEST] pushes N down at fixed mechanism; [WALL] lowers the wall via a better mechanism.
Every WALL idea MUST be A/B'd via an S-read pair on the judge (not local — proxies don't transfer).

---

## PARADIGM ROADS (tracked — the different-algorithm program)

Within-family is CLOSED (LIMITS.md: wall pinned at 6941, every cheap tweak dead). The only prize
left (70→85%) needs a *different algorithm*. These roads are worked one at a time.
**Protocol:** each road gets **≥10 iterations**. If it clearly fails after that, we ~~strike it
through~~ here (with the reason) and move to the next — so anyone reading knows exactly what has
been tried and why it died. Update the iteration counter every session.

### ROAD 1 — Full VSA remesh (RETRIANGULATION) — **iter 7/≥10 · MEASURED DEAD (awaiting strike call)**
> 2026-07-08: built + validated the mesher (99.9% manifold on organic). MEASURED vs banked QEM at
> equal V on the organic proxy: VSA loses **−0.117 FinalSSIM** (0.733 vs 0.850 @ ~4200v); the full
> K-curve shows VSA needs >10438v to match QEM's 4212v score = **>2.5× less efficient**. Mechanism
> is FUNDAMENTAL (flat facets vs smooth organic normal field), not a bug — see RESULTS.md log.
> Grinding to iter 10 (better triangulation / anchor-refine) cannot close a 0.12 normal gap.
Variational Shape Approximation with **new topology**: normal-field L2,1 partition (Lloyd) → one
anchor per region-corner → **retriangulate** into a fresh watertight manifold. NOT a collapse
subset — a genuinely different triangulation that can tile the normal field more efficiently
(plausible source of the leader's ~2× case-3 efficiency).
- **Why it might transfer where tweaks didn't:** structural changes DO transfer (the banked
  metric-in-the-loop steering was +0.0128; it's structural). Position-refine tweaks (R1/768) did
  NOT. VSA changes topology → structural → good transfer story.
- **What already exists:** the VSA *partition* is built (`lloyd_partition`, main.cpp:240). Two
  prior probes used it — B2 (soft boundary penalty) and C/`g_vsac` (hard intra-region collapse
  constraint) — but BOTH explicitly did *"no retriangulation"* and both measured DEAD. **The
  retriangulation is the unbuilt frontier.** That is exactly ROAD 1.
- **Build:** standalone `solver/vsa_remesh.cpp` (do NOT touch banked main.cpp — compile-cliff +
  bank safety). Reuse `load_obj` + `lloyd_partition`; add the anchor-mesher + manifold validator.
- **Test:** fandisk (6475v, canonical VSA benchmark) for manifold-validity first, then armadillo
  (organic, case-3-class). Self-score is a weak screen (§9.1) — a valid, competitive VSA mesh gets
  A/B'd on the judge via an S-read at a SAFE N. Real case-3 mesh is secret → cannot train on it.
- **Risk:** the retriangulation must stay watertight 2-manifold (judge requirement); anchor
  meshing is the fragile part (non-disk regions, <3-anchor regions, 4-region junctions).

### ROAD 2 — Differentiable co-optimization during reduction — *queued*
nvdiffmodeling-style: optimize positions DURING reduction on the rendered normal-SSIM gradient
(`refine_score_grad` exists). Heavy; connectivity isn't differentiable (the hard part); position-
space → transfer risk (§9.1). Start only if ROAD 1 dies.

### ROAD 3 — Dynamic in-loop metric — *queued*
Re-render the steering deficit map as the mesh decimates (current steering is frozen on the
original). Cheapest, reuses infra, but closest to the current pipeline → smallest "different".

---

## NOW (high confidence, automatable)
1. **[HARVEST] S-read descent 6941 -> ~6700.** Friend's read S2=0.9135@6940 => ~240 verts of
   headroom (~+0.17 total). Plan: read @6800, decode S2, anchor with one bank-attempt pass/fail,
   then jump N to the anchored 0.900 crossing and bank. ~3-4 submissions. Do this first.

## WALL-LOWERING mechanisms (the real gap to 85%; each needs an S-read A/B)
2. **Appearance quadric with placement (Hoppe, Vis'99).** Our VSA-lite only ORDERS collapses by
   normal distortion; the QEM PLACEMENT is still position-quadric. Hoppe's normal-attribute quadric
   fixes the placed vertex to minimize normal error too. Could render a better normal map at N=6941.
   Test: v111 vs +Hoppe-placement, two reads @6941, compare S2. Constants/small — risk of family
   re-roll (calibrate).
3. **Joint decimate<->refine (Road B item 1), STRONGER than R1.** R1 (mid-decimation refine bursts)
   was judge-NEGATIVE (proxies over-rewarded it). But a FULL re-decimate-after-refine cycle (refine
   to SSIM-optimal positions, then re-run VSA ordering on THAT geometry) explores a different basin.
   Test via S-read, not local.
4. **Differentiable co-optimization during reduction (Road B item 2).** The heavy build: interleave
   the analytic SSIM gradient (refine_score_grad exists) INTO the collapse loop. §9.1 warns
   position-space gains transfer poorly — but this is co-opt DURING, not refine-after. High effort.
5. **Metric-exploit angle (user's instinct).** Judge sees only 6 axial views; faces are Hausdorff-
   unconstrained (v2v). Look for a case-3 normal-map structure the current pipeline leaves on the
   table that a targeted mechanism could match with fewer faces. Speculative; frame a concrete test.

## Notes
- The S-read is a RELATIVE instrument (~+0.005 optimistic). Anchor per family before trusting margins.
- case 3 is a box-cut coin at the razor: a WA is a draw, not proof. Two WAs at a rung = wall.
- Any change beyond a constant = new binary family => re-rolls the box-cut mean; calibrate or carry margin.
