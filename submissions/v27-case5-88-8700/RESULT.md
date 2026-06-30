# v27 — case5 88% — JUDGE 87.00428, 7/7  ★ NEW BEST (crossed 87)

Config: case2 94 | case3 65 (PivA) | case4 82 | case5 **88** (PivA) | case6 97 | case7 96 = 87.00.
case5 Pivot-A streak: **79→88 (10 walls)**. Free-QEM capped case5 at 79%; metric-in-the-loop +9%.

## Confirmed caps (this run)
- case3 65%: WA'd at 66% with BOTH res160 AND res320 -> not render-limited; detail-uniform mesh,
  little screen-space asymmetry for steering to exploit. Hard cap (added per-case res_for infra,
  now a no-op returning 160).
- case4 82%, case6 97%, case7 96%: free-QEM caps (case7 also WA'd with Pivot-A, too dense).

## Next
- case5 89% (still climbing; caps score near 88 even at 100%).
- For >88 need a new angle: case3 DEPTH-channel steering (currently only normal map steered),
  or large-front with high-res render (timing-bound).
