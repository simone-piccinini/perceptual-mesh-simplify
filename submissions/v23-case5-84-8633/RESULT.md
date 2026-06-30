# v23 — case5 Pivot-A streak — JUDGE 86.33777, 7/7  ★ NEW BEST

Judge: **86.33777, 7/7, C++** (prev 85.67 v22). Driven entirely by case5 Pivot-A.

## Per-case
| case | keep | compression | path | note |
|------|------|-------------|------|------|
| 2 | 0.06 | 94% | free-QEM | |
| 3 | 0.35 | 65% | Pivot-A λ12 | wall (66% WA'd) |
| 4 | 0.18 | 82% | free-QEM | Pivot-A no gain (mechanical) |
| 5 | 0.16 | **84%** | Pivot-A λ12 | **6 walls broken: 79→80→81→82→83→84** |
| 6 | 0.03 | 97% | free-QEM | |
| 7 | 0.04 | 96% | free-QEM | |

## Climb this run (all judge-confirmed)
85.33 → (case2 already 94) → Pivot-A integrated → case3 64→65, case5 79→80 = 85.67
→ case5 81 = 85.83 → case5 82 = 86.0 → case5 83 = 86.17 → case5 84 = **86.33**.

case5's mesh is exceptionally Pivot-A-friendly (highly asymmetric → big screen-space/object-space
gap → steering reallocates a lot). Free-QEM capped it at 79%; metric-in-the-loop took it to 84%.

## What didn't (this run)
- **case7 97% Pivot-A WA'd** (large front). Ran fine (5.3s, valid) but failed the SSIM gate.
  Diagnosis: large meshes are too DENSE — at 97% case7 still has ~30k verts, and the in-loop
  render at 160² cannot resolve that detail, so the contrast-deficit signal is too coarse to
  steer usefully. Large front likely needs much higher render res (→ timing-bound). Parked.
- case3 66% WA'd at λ12 → 65% is the λ12 wall. Stronger λ untested.
- case4 83% WA'd (free-QEM and Pivot-A both) → mechanical, no steering gain. 82% cap.

## Next levers
1. case5 → 85% (streak continues; reliable +0.17/step until it caps).
2. case3 retry 66% with stronger steering (λ=24, more passes, higher res).
3. Large front (6,7) only viable with higher-res in-loop render — timing experiment needed.
