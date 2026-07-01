# v16 — anti-sliver gate + case 5 -> 80%  — FAILED (big regression)

## Judge result
ACCEPTED, 5/7, score 40.000459 (sub 19860521). Dots: case5 RED, case6 RED, rest green.
DOWN from 83.67. (best-counts keeps 83.67.)

## Change
- Added a collapse gate: reject any collapse whose new face quality
  (2*sqrt(3)*area / sum(edge^2)) < kMinQuality = 0.05  (reject slivers).
- Pushed case 5 keep 0.25 -> 0.20 (80%).
- case 4 back to 0.20 (clean base). Everything else at v15 values.

## What FAILED
- case 5 (pushed to 80%): RED.
- case 6 (unchanged keep 0.03/97%): RED — the GATE broke a case I did not even touch.
- Score 40 (not ~55 with only 5,6 at 0) => the passing cases also LOST compression:
  they could not reach their keep target because the gate rejected the collapses
  needed to get there.

## Why it failed (hypothesis; judge gives only WA / scores)
Rejecting collapses is the WRONG lever. Aggressive compression REQUIRES creating some
thin triangles; the gate blocks exactly those, so:
  (a) every case stalls before its keep target -> less compression -> lower score even
      where it stays valid;
  (b) on the aggressive cases (5 @ 80%, 6 @ 97%) the solver, forced off the cheapest
      collapses onto worse alternatives, drifts -> WA (likely Hausdorff) or cannot
      reach a valid target.
Net: a quality FLOOR fights compression head-on. The lever must improve placement
WITHOUT removing collapses (e.g. Probabilistic Quadrics: same collapses, better
positions). Anti-sliver-by-rejection is abandoned.

## Action
Reverted to v15 (83.67). Resume single safe keep-nudges; placement improvement must be
non-blocking (PQ-style), not a rejection gate.
