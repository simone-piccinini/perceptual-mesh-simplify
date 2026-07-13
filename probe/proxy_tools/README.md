# Transferring proxy (R-ι) — subset-placement recipe + sign validation

STATE: 2026-07-13. c5 transferring proxy FOUND + R1-sign-validated. c3 open. See ROADS R-ι.

## The problem
Local A/B on the in-repo proxies does not transfer to the judge for position-space work (§9.1):
the proxies are **too smooth**. R-θ showed the only proxy that ever matched the judge's *sign* was
`ab_orig` (a rough native armadillo). Naively downloading Stanford + QEM-decimating does **not**
help — at equal count a QEM decimation of the *rough* canonical Armadillo is no rougher than our
smooth proxy, because QEM optimal-placement smooths away the sub-triangle scan detail that is the
transfer-relevant signal.

## The recipe (`make_transferring_proxy.py`)
1. Download the canonical rough Stanford Armadillo (172,974 v, real Paraform scan reconstruction):
   `https://graphics.stanford.edu/pub/3Dscanrep/armadillo/Armadillo.ply.gz`
2. QEM-decimate to the judge count for **connectivity** (`fast_simplification`).
3. **Snap** every surviving vertex to its nearest ORIGINAL vertex = subset placement → restores the
   scan noise QEM removed.

Result at c5 (49,987 v): mean|dihedral| **11.7°** vs the smooth in-repo proxy **10.2°** (+15%).

## The validation — the R1 sign test (the only real definition of "transferring")
Roughness alone can mislead (it's a geometric proxy for the judge's normal-map σxy). The real test:
run a mechanism whose **judge sign is known** and check the proxy reproduces it. R1 (mid-decimation
refine interleave) is judge-NEGATIVE on c5 (WA'd, sub 19897122). Re-exposed behind `G_R1` (local
only — R1 is judge-dead, never submitted), c5 self-score S2n (the binding normal term):

| proxy | R1 ΔS2n | sign | vs judge (NEG) |
|-------|---------|------|----------------|
| smooth in-repo (armadillo_watertight, 49990) | **+0.0019** | + | ✗ inverted |
| **rough subset (this recipe, 49988)** | **−0.0012 / −0.0015** (2 runs) | **−** | **✓ matches** |

The smooth proxy rewards what the judge punishes; the subset proxy reproduces the judge's sign.
This is a validated transferring proxy **for the R1 mechanism class on c5**.

## Caveats / open work
- **Mechanism-dependent transfer.** ROADS records `ab_orig` mis-predicted ANISOQ (proxy +8.7e-4,
  judge −4e-3). Validate EACH new mechanism's sign on this proxy before trusting an A/B; don't assume
  one proxy transfers for all mechanisms. Next: re-run the ANISOQ sign test on this proxy.
- **Holes.** The snap drops ~0.4% degenerate faces → tiny holes. They cancel in an A/B delta but a
  hole-free subset decimator (true endpoint-collapse, e.g. the solver's own subset mode) would
  isolate roughness from holes more rigorously.
- **c3 (the prize) still open.** c3 is not the armadillo; this recipe gave no roughness gain there.
  Need a native ~23k organic scan, or the raw range scans as an SSIM reference.

## Files
- `mesh_tool.py` — binary-PLY / solver-OBJ IO, dihedral roughness, format conversion.
- `make_transferring_proxy.py` — the recipe above.
