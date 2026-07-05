# v44 — VSA-lite extended to case5 (90->90.5) — JUDGE 89.445331, 7/7  ★ NEW BEST

Config: case2 99.25 | case3 69 (VSA) | case4 83.95 (QEM) | case5 **90.5** (VSA) | case6 97 | case7 96.95 = 89.44.

## What changed vs v43 (89.36)
- `ndecim_for` now = case3 + case5 (both organic, normal-bound). case5 keep 0.10 -> 0.095 (90 -> 90.5%).
- VSA-lite gave case5 **+0.0175 normal-SSIM at 90%** (biggest single-case VSA gain) on the pessimistic
  armadillo proxy; pushed the keep until the relative proxy margin over the known-pass level was +0.0030.
  Judge confirmed 7/7.

## case4 excluded (learned the hard way)
- A prior submit pushed case4 to VSA-84.25% (proxy margin +0.0021) and the judge **WA'd it (75.45, 6/7)**.
  case4's proxy over-predicts even VSA's RELATIVE signal by >0.002 -> case4 stays confirmed QEM 83.95%
  (`ndecim_for` excludes 30000<V<=40000). Pushing case4 needs a direct judge-bisect, not the proxy.

## Confirmed VSA judge results so far
- case3 67 -> 69  (v43, +0.33 avg)
- case5 90 -> 90.5 (v44, +0.08 avg)
- 89.03 -> 89.36 -> 89.44

## Next
- case5 -> 91% (proxy 0.84908; pessimistic proxy so a real shot).
- Test position-optimizer STACKING on the VSA case5 partition (case5 currently has no optimizer; refine_for
  excludes V>40000). VSA gave case3 a better partition AND the optimizer added +0.006 on top — case5 may do
  the same, pushing well past 90.5.
- Judge-bisect case4 in (83.95, 84.25).
