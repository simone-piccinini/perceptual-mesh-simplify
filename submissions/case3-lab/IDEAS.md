# case-3 IDEAS — ranked by expected value × confidence

Legend: [HARVEST] pushes N down at fixed mechanism; [WALL] lowers the wall via a better mechanism.
Every WALL idea MUST be A/B'd via an S-read pair on the judge (not local — proxies don't transfer).

---

## PARADIGM ROADS (tracked — the different-algorithm program)

Within-family is CLOSED (LIMITS.md: wall pinned at 6941, every cheap tweak dead). The remaining
prize needs a *different algorithm*. Roads are worked one at a time.
**Protocol:** each road gets **≥10 iterations**. If it fails after that, we ~~strike it through~~
here with the reason and move on — so anyone reading knows what was tried and why it died.

**⚠ PREMISE CORRECTION (2026-07-08).** The old motivation "case-3 must reach ~85% (2× efficiency)"
is arithmetically WRONG. Total gap to the leader (91.46 vs our 90.286) = 1.174 on the MEAN =
**7.05 summed** across 6 cases. If the *entire* gap were case-3: leader_c3 = 70.08 + 7.05 =
**77.1%**, not 85%. And it almost certainly spreads across c4/c5/c6/c7 too → the leader's case-3 is
plausibly **72–77%**, i.e. only **2–7 pts** above ours, not 15. There is no "2× efficiency
mystery." Case-3's realistic headroom is modest and hard (VSA/tweaks/refine all failed on it).
This does not kill the case-3 focus, but it right-sizes the prize and argues for cheap bets, not
heavy builds.

### ~~ROAD 1 — Full VSA remesh (RETRIANGULATION)~~ — **DEAD (iter 10/10, 2026-07-08)**
> **Struck.** Built the full mesher (standalone `solver/vsa_remesh.cpp`): VSA Lloyd partition →
> anchor insertion → lens-split → proxy-plane ear-clip → **watertight-manifold** output (valid).
> MEASURED vs the banked QEM on the organic proxy (armadillo) via the `imc_eval` oracle at equal V:
> best-VSA (ear-clip) = **0.747 @ 4378v** and **0.803 @ 7233v** vs QEM **0.850 @ 4212v**. VSA needs
> >2.5× the vertices to match QEM. Richer partition (40 Lloyd iters) added only +0.006; ear-clip
> +0.02 — nothing closes the −0.10 normal gap. **Mechanism is FUNDAMENTAL:** VSA tiles the surface
> into large piecewise-FLAT facets → a staircased normal map; case-3 is ORGANIC (smooth normal
> field), which QEM's dense adaptive triangulation matches far better per vertex. VSA wins on CAD
> (fandisk), the OPPOSITE of case-3. Confirms VSA-*lite* (+0.0128, banked) worked by *ordering* a
> smooth mesh, NOT by flat retriangulation. Full log: RESULTS.md. Code kept for reference/CAD reuse.
> **Lesson that redirects:** the winning case-3 mesh is smooth+dense+adaptive (QEM-family). Any next
> road must stay in that family — flat/partition topology is the wrong direction for organic.

### ROAD 2 — Differentiable co-optimization during reduction — *queued, but WEAKER than hoped*
nvdiffmodeling-style: optimize positions DURING reduction on the rendered normal-SSIM gradient
(`refine_score_grad` exists). Stays in the smooth family (good, avoids VSA's flaw). BUT: main.cpp's
refine already does post-decimation position-gradient ascent (converged, banked), and **R1
(interleaved decimate↔refine — co-opt-during-reduction in spirit) was judge-NEGATIVE ×2.** So this
is close to a measured-dead thing; the only new bit is "full" co-opt vs R1's bursts. Heavy build,
low odds.

### ROAD 3 — Dynamic in-loop metric — *queued, likely marginal*
Re-render the steering deficit map as the mesh decimates (current Pivot-A steering is frozen on the
original). Cheapest, reuses infra. But it's a variant of the already-banked steering, and every
steering tweak (nmetric/mask/projw/…) is dead → likely marginal. Cheap enough to try as a one-off.

### ROAD 4 — Curvature-adaptive isotropic remesh — *NEW (from the VSA lesson), untested*
A smooth NEW triangulation (not a QEM coarsening, not flat VSA): split/collapse/flip/tangential-
relax to a target edge length ∝ local feature size. In the RIGHT family (smooth, small triangles).
Might beat QEM if QEM's error-driven triangle shapes hurt the normal map. Heavy (manifold-safe
remesh loop), uncertain — but the only genuinely-untried idea in the smooth family.

---

## NOW (high confidence, automatable)
1. **[HARVEST] S-read descent 6941 -> ~6700.** Friend's read S2=0.9135@6940 => ~240 verts of
   headroom (~+0.17 total). Plan: read @6800, decode S2, anchor with one bank-attempt pass/fail,
   then jump N to the anchored 0.900 crossing and bank. ~3-4 submissions. Do this first.

## WALL-LOWERING mechanisms (small prize — leader_c3 ~72–77% not 85%; each needs an S-read A/B)
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
