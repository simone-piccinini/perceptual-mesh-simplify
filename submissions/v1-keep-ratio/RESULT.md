# Submission v1 — blind vertex ratio (keep 50%)

First submission.

## Approach

Decimate to a fixed fraction of the vertices: `Decimate(target = 0.5 * V)`. No
quality or deviation awareness — the same 50% reduction on every mesh,
regardless of size or shape.

## Judge result

- **6 / 7 test cases passed.**
- **Test 1 (SAMPLE) FAILED** — *"Wrong Answer: too much geometric deviation."*
  50% of the 9-vertex cube = 4 vertices, i.e. a tetrahedron ~0.5 model-units off
  the surface, far past the `5% × diagonal` Hausdorff limit. The sample is worth
  **0 points**, so no score was lost.
- **Secret 6 / 6 passed**, each at ~50% compression.
- **Score ≈ 50 / 100** (each scored case ~50% compression; exact value in the
  platform submission history).

## Takeaway

A mild, uniform 50% reduction is *safe* on the big meshes (plenty of vertices
remain, so geometric deviation stays small) but *fatal* on tiny meshes whose
only valid simplification is removing one or two vertices.

This motivated making the stop deviation-aware — attempted in **v2**, which
over-corrected. As of now this v1 is still our **best real score**.
