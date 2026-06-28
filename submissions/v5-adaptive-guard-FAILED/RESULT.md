# Submission v5 — adaptive mode + Hausdorff guard — FAILED (regression)

Error-bounded adaptive decimation (STEP-2 hybrid engine) run with
`kOpTargetError = 0.02`, `kOpNormalWeight = 1.0`, Hausdorff guard 4.5%.

## Judge result
- **2 / 7 — score 15.922401** (down from 64).
- SAMPLE ✅, secret case 1 ✅; **secret cases 2-6 → Wrong Answer** (cases 3-7 overall).
- "Wrong Answer", no further detail from the judge.

## Why it failed
Same failure family as v2 (cost-budget). The adaptive mode pushes specific meshes to
very high compression (88-99% on the local bench). The Hausdorff guard (`dev[]`) only
bounds **direction-1** of the symmetric Hausdorff (every original vertex stays near
the simplified surface). It does NOT bound **direction-2**: the free QEM optimal target
`x_bar` can drift OFF the original surface, and over many collapses that drift exceeds
5% of the diagonal on the judge's hidden geometries → geometric-deviation Wrong Answer.

The 4 local proxy meshes (bunny/cow/fandisk/armadillo) measured symmetric Hausdorff
< 5%, so the local bench did NOT expose the failure. **Local numbers lied again** — the
documented trap (see docs/qem-cost-is-not-hausdorff.md).

## Lesson
A valid 64% beats an invalid anything. Adaptive over-compression is unsafe without a
TRUE two-directional point-to-surface guard (needs a spatial structure at 1.1M scale).
Reverted the live solver to keep mode 0.36 (v4). Adaptive parked until the
direction-2 guard is built and verified.

## Operating point in this snapshot (as submitted)
`kOpTargetError = 0.02`, `kOpNormalWeight = 1.0`, guard devfrac auto = 0.045.
