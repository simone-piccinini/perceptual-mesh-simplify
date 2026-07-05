# SIL — coverage/silhouette optimizer (experiment, 2026-07-06)

**What it is:** the first optimizer in this project that can MOVE the silhouette. The analytic
refine gradient is coverage-blind (pixel-to-face assignment frozen) and optimizes normal-SSIM
only; ~all of the residual depth deficit sits in silhouette windows (chords of the decimated
mesh lie systematically INSIDE convex arcs → coverage too small).

**Mechanism (new vs the graveyard):**
1. accept metric = FULL FinalSSIM (0.5·Sn + 0.5·Sd, depth scorer ported from the probe line);
2. per-view coverage-DIFFERENCE map (original-foreground missing → push rim vertices OUT;
   excess coverage → push IN), votes splatted to the nearest rim vertex (binned grid);
3. one global step-size line search along per-vertex signed rim directions, Final-accepted;
4. alternated with the normal-SSIM ascent which repairs any interior damage.
Uniform (unsigned) displacement does NOT work — measured zero, consistent with the old
global-scale sweep peaking at 1.0: half the chords are inside, half outside.

**First results (case-5 proxy, equal count V=4225):**
- in-process Final at 512: 0.901982 → 0.903889 (+0.0019), one-shot correction then converged;
- TRUE evaluator at 1024: 0.850098 → 0.850833 (**+0.000735 real**), Hausdorff 0.0076 (fine).

**Discipline:** after the R1 lesson (local +0.002 on c3/c5 inverted by the judge meshes, three
live families 0/3 at their banked rungs), NO descent on local evidence: next step is a judge
family test at the banked case-5 rung with SIL hardwired, then a measured-mesh S read.
