# v29 — per-channel steering, case5 90% — JUDGE 87.33770, 7/7  ★ NEW BEST

Config: case2 94 | case3 65 | case4 82 | case5 **90** (PivA per-channel) | case6 97 | case7 96 = 87.34.

## Breakthrough: per-channel normal steering
Pivot-A steered by GRAYSCALE normal luma. The judge scores nx/ny/nz SEPARATELY. Switching the
contrast-deficit signal to per-channel (sum of 1-c over the 3 normal components) is a sharper,
judge-aligned signal: +0.0030 over grayscale on the cow proxy, and on the judge it **broke
case5's 90% wall** that grayscale could not pass at res160 OR res320.
case5 Pivot-A streak now **79->90 (free-QEM was 79%)**.

## Next
- case5 91% (per-channel may have more headroom).
- case3 66% + case4 83% with per-channel (grayscale capped them; sharper signal may break them,
  esp. if their normal variation is anisotropic).
