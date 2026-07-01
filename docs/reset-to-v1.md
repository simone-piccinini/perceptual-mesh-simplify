# Strategic reset to v1 (keep-ratio) + three targeted interventions

## Why we reset

| Submission | Approach | Judge result |
|---|---|---|
| **v1** `simplifygeometry.cpp` | keep 50%, no SSIM/Hausdorff logic | **6/7, ~50** |
| evolved | cost-budget + deviation guard + normal term | **2/7, ~16 (REGRESSION)** |

The evolved versions pushed ~99% compression on local proxies but on the judge:
- cases 3-6 → *"too much geometric deviation"* (blew the 5% Hausdorff on detailed meshes),
- case 7 (1.1M) → **Time Limit Exceeded** (extra per-collapse work didn't scale).

**The binding constraint is Hausdorff, not SSIM.** The QEM collapse cost is an
L2 *average* of distances to the original face *planes* — not the L∞ *max*
point-to-surface distance. A budget tuned to hit 99% therefore silently exceeds
the 5% Hausdorff on curved/detailed geometry. A **valid 50% scores 50; an invalid
99% scores 0**. Five invalid cases dragged the evolved score to 16.

So we reverted to v1 and hardened it with three *minimal* interventions — no
perceptual intelligence, no deviation guard, no normal term (those caused the
regression). The regression source is archived at
`submissions/v3-evolved-regression/`.

## The three interventions (only changes vs pure v1)

### Int. 1 — small-mesh skip (unblocks the sample → 7/7)
The 9-vertex sample is a cube + 1 redundant vertex; `keep*9 = 4` vertices cannot
close a cube → invalid. Rule: **`V < 1000` → skip decimation, emit the input
unchanged** (always valid: manifold, Hausdorff 0, SSIM 1). The smallest *scored*
case has 25,000 vertices, so this only ever fires on the sample (worth 0 points)
— it buys validity, never costs compression.

### Int. 2 — scale (the important one: case 7 within time/memory)
Replaced the per-vertex `unordered_set<int>` incidence sets with **compact
`vector<int>`** (contiguous, no hashing, far less memory; erase = O(degree)
swap-remove), and replaced the per-call `unordered_set` dedup in `Neighbors` /
`SafeToCollapse` with **reusable generation-stamped marker arrays**. The
decimation *logic is unchanged* → **identical V and F output**, only faster and
lighter.

### Int. 3 — clean `keep` parameter
`keep = argv[1]`, default `0.5` (the v1 setting). No auto-tuning. Documented:
lower `keep` → more compression → more score, but risks the hard constraints.
**The operating point is found by submitting to the judge**, not from local
proxies.

## Proof — numbers

**Restore:** `simplifygeometry.cpp` is byte-identical to the archived v1
(17,482 bytes). Compiles clean (`g++ -O2 -std=c++17`). keep 0.5 halves: sphere
2562→1281, armadillo 49990→24995.

**Int. 2 — identical output** (V F), opt vs unopt:

| mesh | keep 0.5 | keep 0.3 | keep 0.1 |
|---|---|---|---|
| armadillo | 24995/49986 = | 14997/29990 = | 4999/9994 = |
| fandisk | 3237/6470 = | 1942/3880 = | 647/1290 = |
| torus 1.05M | 524288/1048576 = | — | — |

**Int. 2 — scale (1,048,576-vertex torus):**

| version | keep | time | RSS |
|---|---|---|---|
| unopt (unordered_set) | 0.5 | 3.25 s | 911 MB |
| **opt (vector)** | 0.5 | **2.23 s** | **638 MB** |
| unopt | 0.1 | 6.09 s | 920 MB |
| **opt** | 0.1 | **4.14 s** | **647 MB** |

→ ~1.45× faster, −273 MB, same output. The judge ran v1-unopt at **8.58 s** on
case 7 (1.1M, harder than this clean torus); optimized ≈ **6 s**, ~670 MB —
both well under **21 s / 2048 MB**, with headroom for lower `keep`.

**Int. 1 — sample valid:** `solver/main 0.5 < sample.in` → 9 verts unchanged,
manifold/area/indices/Euler all OK, Hausdorff 0.

**Structural certification** (suite invariants INV1–6 + exact symmetric
Hausdorff, as % of the 5% AABB-diagonal budget):

| mesh | keep | V→V' | manif/area/idx/euler | Hausdorff |
|---|---|---|---|---|
| sample | 0.5 | 9→9 | OK | 0.0% budget |
| bunny | 0.5 | 3485→1742 | OK | 5.1% |
| cow | 0.5 | 2903→1451 | OK | 12.2% |
| fandisk | 0.5 | 6475→3237 | OK | 0.0% |
| armadillo | 0.5 | 49990→24995 | OK | — |
| torus 1.05M | 0.5 | →524288 | OK | — |

All structurally sound. L2 `check_structural_validity` → **PASS**. (Hausdorff
proxy numbers are *informative only* — the judge's hidden meshes are harder; this
is the whole lesson.)

## Next step — yours
Submit with decreasing `keep` (0.45, 0.40, 0.35, …) and take the lowest value
still valid on all 6–7 cases. Each step that stays valid adds ~5 to the score;
the first that goes invalid (Hausdorff/SSIM/time) tells you the floor. The judge
is the only ground truth.
