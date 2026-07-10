# v112 — REMESH-SPEED: flip remesher + refine speed pass → c3 @6900

**Verdict: ACCEPTED 7/7, SCORE 90.314273 [JUDGE 20018842, 2026-07-10] — NEW BANK (+0.028735)**

sha256 d1d7e156206f · 115.2 KiB · banner REMESH-SPEED 2026-07-10

## What changed vs v111 bank (90.285538)

1. **REMESH-FAST flip remesher** (from the 2aeb49f line): incremental per-flip box-SSIM delta
   (`flip_delta_local`, validated ratio ≈1.0 vs full render), cheap rendered-normal-error edge rank,
   2-ring-independent flips (additive deltas, no verify render). Runs on the FINAL c3 mesh at 1024,
   box `r_elapsed()+1.1s`. c3 band only (`G_REMESH`).
2. **Refine speed pass** (~−23% c3 CPU, output byte-identical on c3/c4 proxies):
   - original-image box-stats (`mx`,`xx`) cached per (view,channel), rebuilt on res change;
   - all fills/normalizations in `refine_score_grad` crop-restricted (exact: r_boxsum reads rows
     `[cy0−R, cy1+R]` only; grad products are ±0 outside the crop);
   - **both gated to V ≤ 100000** — c6 (377k) / c7 (1M) execute the pre-speedup code verbatim,
     trajectories bit-identical to the bank (JUDGE-CONFIRMED: only c3 payout moved).
3. **c3 target 6900** (was 6940).

## Decode

- Score delta ×6 = +0.172410 = exactly c3 6940→6900 (70.088→70.260). All other cases identical.
- **19936152's c3 'x' was a TLE** (21.4s → 19.3s here, same mesh byte-identical locally).
- **The flips BREAK the c3 SSIM wall**: bare 6900 was a deterministic WA (19935666); 6900+flips
  passes. First judge-validated topological gain.

## CASETIME (margins to the ~21s CPU ceiling)

c1 1.9 · c2 6.0 · **c3 19.3 (1.7)** · c4 15.4 · **c5 19.4 (1.6)** · c6 17.5 · **c7 19.9 (1.1)** — 3 cases TLE-tight.

## Next

Remesher headroom: box is only 1.1s and rounds=8/K=1000 self-terminate; c3 margin 1.7s. Probe deeper
N (6880/6860) and/or bigger remesh box — deterministic c3 → clean single-submission reads.
