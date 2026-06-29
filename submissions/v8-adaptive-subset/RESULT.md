# Submission v8 — provably geometry-safe adaptive + per-case dispatch

## Judge result
**ACCEPTED, 7/7, score 74.334918** (sub 19857??? — up from 64). Best so far.

## What it does
Per-case dispatch by vertex count:
- **V > 100k (cases 6,7)** → ADAPTIVE, SUBSET placement (collapse to cheaper original
  endpoint → every survivor on the original surface). Two-sided Hausdorff guard,
  **no grid**: dir-1 = per-cluster bounding sphere; dir-2 = modified-face longest-edge
  ≤ margin. Both ≤ margin ⇒ symmetric Hausdorff ≤ margin (0.045 ⇒ <4.5% < 5%),
  PROVABLY. margin 0.045, floor 0.05 (≤95%).
- **V ≤ 100k (cases 2,3,4,5)** → KEEP 0.36 free-QEM (the proven 64).

So score = (64·4 + ~95·2)/6 ≈ 74.3. Cannot drop below 64 (dispatch keeps the proven path).

## What worked / what didn't
- **Worked:** large/dense meshes compress to ~95% with provably-bounded Hausdorff, 7/7.
- **Didn't:** *pure* adaptive (subset) on the MEDIUM meshes (25k–50k) WAs them. Geometry
  is provably ≤ margin there too, so by elimination the medium wall is **SSIM** — likely
  the subset placement's poor face-normal quality at high compression, not the
  compression level itself.

## Key learning
- The judge reports only "Wrong Answer" — **no reason.** So every earlier "failure =
  Hausdorff" note was a guess. Making geometry *provably* safe turns the binary verdict
  into a diagnosis: medium WA ⇒ SSIM.
- Subset placement = the trick that makes Hausdorff provably bounded without a grid (and
  killed the v5/earlier dir-2 hole that scored 31.66).

## Next
- Push large floor lower (dense meshes hold SSIM far past 95%).
- Lift medium past 64%: free-QEM (better normals than subset) at lower keep, and/or
  Probabilistic-Quadrics placement to hold normal-map SSIM at higher compression.
