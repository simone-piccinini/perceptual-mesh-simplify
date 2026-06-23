# Discovery — QEM cost is not a Hausdorff bound

## What happened

The cost-budget submission scored **2/7 (~16.5/100)**, *down* from the mild
`keep = 0.5` run (**6/7, ~50/100**). The five regressed cases all report:

> Wrong Answer: too much geometric deviation

So the binding constraint is the **Hausdorff** limit ($d_H \le 5\% \times$ diagonal),
**not** SSIM. (We had expected SSIM to bind — it did not.)

## The discovery

We assumed the QEM collapse cost bounds geometric deviation, so a budget

$$
c_{\max} = \left( f \cdot 0.05 \cdot D \right)^{2}
$$

would keep us under the limit. **It does not.** The quadric cost

$$
\text{cost}(\bar{x}) = \bar{x}^{\top} Q\, \bar{x} = \sum_{p} \big( \text{dist}(\bar{x}, \text{plane}_p) \big)^{2}
$$

is a poor proxy for the true point-to-surface Hausdorff, for three reasons:

1. **Planes, not triangles.** The quadric measures distance to the *infinite
   supporting planes* of the original faces. A vertex can sit near those planes
   yet far from the *bounded* surface, so the cost under-reports real distance.
2. **Average, not worst-case.** The quadric is a sum of squared distances (an
   $L_2$ / average measure). Hausdorff is the **maximum** distance ($L_\infty$).
   Bounding the average never bounds the max.
3. **No coverage term.** Hausdorff also requires every *original* point to stay
   near the *simplified* surface. Per-vertex collapse cost does not track that
   direction at all.

Because the cost systematically under-estimates true deviation, the budget let
through collapses whose real Hausdorff exceeds $5\% \times D$. The result was
~99% compression and five cases over the geometric limit.

## Why the cube hid this

A cube decimates to the **exact** cube: true Hausdorff $= 0$ and SSIM $= 1.0$ at
*any* compression. It could never expose this failure mode. Real, smoothly-curved
meshes accumulate continuous deviation that the quadric cost underestimates.

## Takeaways

- **QEM cost is a good *ordering* heuristic** (which edge to collapse next) but
  **not a deviation certificate** (how far is safe to go).
- To respect the $5\%$ Hausdorff we must bound the **true point-to-surface
  deviation** during decimation — not the quadric cost.
- A single `frac` cannot fix this robustly: the cost-to-Hausdorff gap is
  mesh-dependent, so any value safe on one mesh over-compresses another.

## Status

- Best real score so far is still the mild `keep = 0.5` run (~50/100).
- Next: add a **true-deviation guard** (a per-collapse point-to-surface check),
  and fix the oracle's Hausdorff to point-to-surface so we can measure this
  locally instead of discovering it on the judge.
