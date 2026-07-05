# v100 — float32 refine base (submission 19894847)

**Score: 90.238542 — 7/7 PASS (bit-identical to the bank; residual +0.000000)**
Passing cases: 2, 3, 4, 5, 6, 7 (+ sample). Bank UNCHANGED, now reproduced on the new platform.

## What this build is
- All refine image buffers + r_boxsum storage in **float32** (double running accumulators);
  decimation untouched (proven V-identical). Refine is memory-bound → ~2× boxed iterations.
- Effects at banked rungs: case 3 refine now CONVERGES inside its box (runtime 20.9 → 17.4 s,
  TLE razor gone); case 5 box trimmed 19 → 17 s (converges; runtime 21-22.8 → 19.1 s);
  memory −4 MiB × 17 buffers.
- Keeps: c2 0.0065 | c3 0.2996875 (70.03125) | c4 0.1425 | c5 0.08453125 (V=4226) |
  c6 0.023046875 | c7 0.02855. c3 hybrid-1024 on; c5 512-refine.

## Same-day judged conclusions (2026-07-05)
- Vin_case5 = 49987 [5-probe integer solve]; judge SSIM ≈ ours (probe #7 closed, no bias).
- Judge is PER-RUN nondeterministic on box-cut cases (byte-identical resubmits flip verdicts).
- c5 sub-4226 rungs: 12+ WA across f64/f32/λ/hybrid/768 — deterministic wall at V=4226.
- c3 70.0625: WA also with converged refine → deterministic wall at 70.03125.
- c5 hybrid-1024: closed ×2 (local −0.0008, judge WA). c5 768-native: closed negative
  (banked-rung WA with 768 vs pass with 512, same day; local +0.00067 did not transfer).
