# Judge map — per-case behavior, walls, and what the judge does

The judge gives only pass/fail per case (no reason at our compression). This file is the
distilled model of its behavior so we never re-test a dead idea. Update it every submission.

## What the judge computes (deduced + 1 official clarification)
- Score = mean over the 6 secret cases of the compression `100*(1 - V'/V)`, but a case
  scores 0 unless it is VALID.
- Valid = manifold (each edge in exactly 2 faces) + non-degenerate faces + valid indices
  + **vertex-to-vertex** symmetric Hausdorff ≤ 5% diag + FinalSSIM ≥ 0.9.
- **Hausdorff is vertex-to-vertex** (official judge reply: "a and b vary across vertices…
  we do not iterate over interior or surface points"). So it is very loose — a few-hundred
  vertices already 5%-cover a unit-sphere mesh. It only ever fails at EXTREME over-
  compression. At our operating points it never binds. (Early <20% runs that said
  "Wrong Answer: too much geometric deviation" were exactly this — too few vertices.)
- FinalSSIM = mean over 6 axial views of 0.5·SSIM(normal map) + 0.5·SSIM(depth map).
  - Depth map: foreground z≈1.5–3.5, background = 255 → depth SSIM is dominated by the
    SILHOUETTE match; interior depth variance is tiny (c2 dominates → ≈1). QEM keeps the
    outline, so depth is ≈ free at our compression. NOT the wall.
  - Normal map (flat per-face normals): THE wall. Loses local normal variance as faces drop.

## Per-case walls (judge-confirmed)
| case | V ≤ | best keep | compression | wall | notes |
|---|---|---|---|---|---|
| 2 | 5,000 | 0.07 | 93% | SSIM (~geom) | near max; 94% untested |
| 3 | 25,000 | 0.36 | **64%** | SSIM, **INTRINSIC** | fails 66%; 9 methods pinned (see below) |
| 4 | 40,000 | 0.18 | 82% | SSIM | 83% AND 84% FAILED → hard wall exactly 82% |
| 5 | 50,000 | 0.21 | 79% | SSIM | 80% FAILED |
| 6 | 400,000 | 0.03 | 97% | SSIM | 98% untested |
| 7 | 1,100,000 | 0.04 | 96% | SSIM | 97% FAILED |

Current best = **85.17** = (93+64+82+79+97+96)/6.  (submissions/v21-case5-79)

## case 3 — methods that ALL fail at 66% (pin at 64%)
free-QEM · area-weighted QEM · GH-normal attribute quadric · silhouette edge-lock ·
anti-sliver gate · Delaunay edge-flips · correct nonlinear flat-shaded normal cost
(approach-c) · subset placement · **image-driven screen importance (λ=12)**.
Degeneracy ruled out (free-QEM faces healthy, min area ~1e-5 even at 96%).
=> case 3's FinalSSIM at a given compression is ~method-invariant. It is uniformly
detail-dense: there is no low-importance region to sacrifice. It fundamentally needs
~36% of its vertices. **Do not grind case 3 further.**

## Failure-mode decoder
- "too much geometric deviation" (only seen <20%): vertex-Hausdorff (too few verts). Avoid by
  never going so aggressive that V' can't 5%-cover the original (≈ keep ≥ a few hundred verts).
- A case red at our walls with no message: FinalSSIM < 0.9 (scores 0, not a hard-WA).
- Manifold/degenerate WA: never observed — the link-condition + area/flip gates hold.

## Where score can still come from
- Cheap, risky nudges: case 2 → 94%, case 6 → 98% (each +0.17 if they hold).
- Image-driven on case 4/5: untested — those meshes MAY have flat regions case 3 lacks.
- 90 average needs the medium cases (3,4) to break, which looks intrinsic for edge-collapse.
  Practical ceiling of this approach is ~85–86 unless a fundamentally different mesh is built.
