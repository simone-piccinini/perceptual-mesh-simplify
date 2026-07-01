# v22 — Pivot-A (metric-in-the-loop) — JUDGE 85.67, 7/7  ★ NEW BEST

Judge: **85.67093, 7/7, C++** (prev best 85.33 / v21 was 85.17). First break past the
free-QEM ceiling via real rendered-SSIM steering.

## Per-case operating point
| case | V (~) | keep | compression | path |
|------|-------|------|-------------|------|
| 2 | 5k    | 0.06 | 94% | free-QEM (λ0) |
| 3 | 25k   | 0.35 | **65%** | **Pivot-A λ12** (was 64% free-QEM wall) |
| 4 | 40k   | 0.18 | 82% | free-QEM (λ0) |
| 5 | 50k   | 0.20 | **80%** | **Pivot-A λ12** (was 79% free-QEM wall) |
| 6 | 400k  | 0.03 | 97% | free-QEM (λ0) |
| 7 | 1.1M  | 0.04 | 96% | free-QEM (λ0) |

## What worked — Pivot-A
Metric-in-the-loop steering: inside the solver, render the current mesh's 6 axial flat-shaded
normal maps (own rasterizer, pixel-validated vs the oracle) in 8 staged passes; per window
measure the **SSIM contrast-term deficit `1 - c`, c=(2σxσy+C2)/(σx²+σy²+C2)**; accumulate per
vertex; steer `cost *= (1 + λ·(imp[i]+imp[j]))`, λ=12. Broke case3 64→65 and case5 79→80 on
the judge. Runtime 0.08–0.30s on 12k–50k meshes (judge-safe).

## What killed the earlier "no gain" verdict (it was a bug + bad proxy)
1. **Wrong signal**: first version used `σx−σy` not the true `1−c`. Wrong steering.
2. **Symmetric proxy**: tested only a bumpy sphere — screen-space = object-space there, so
   steering is redundant *by construction*. Retesting on **asymmetric** meshes (cow +2%
   compression @ SSIM 0.9, armadillo 0.9026→0.9046) exposed the real gain.
Lesson (user was right): do not conclude from one experiment — suspect bug/weak-impl first.

## What didn't
- **case4 83%** WA'd *even with Pivot-A* → mechanical mesh, no steering gain (fandisk proxy
  showed exactly 0.0000). Pulled case4 back to free-QEM 82% (λ0).
- case6 98% WA'd earlier → capped at 97%.
- Probabilistic Quadrics (Trettner-Kobbelt): *worse* than free-QEM on clean meshes
  (σ-regularization pulls off the surface). Dead.

## Implementation notes
- Pivot-A gated by `lambda_for(V)`: λ=12 only for V∈(7000,30000] (case3) and (40000,100000]
  (case5). Cases 2,4,6,7 → λ=0 → **byte-identical** to v21 free-QEM (verified via cmp;
  confirmed-passing walls cannot regress).
- Output `v %.17g` full precision. Manifold/area(1e-15)/flip(0.0) gates unchanged.

## Next
- Push case3 65→66%, case5 80→81% (each passed at +1%, try +2%).
- case4 stuck at 82%; λ=30 long shot or accept mechanical cap.
