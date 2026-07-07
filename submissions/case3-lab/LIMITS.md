# case-3 LIMITS — what is tested, what is NOT (the honest map)

Purpose: answer "do we understand case-3's limits 100%?" — with provenance per line.
[JUDGE] = confirmed on the real judge. [LOCAL] = screened on a proxy only (does NOT transfer, §9.1).
[INFERRED] = arithmetic from scores. [UNTESTED] = never probed. Truthful; update every probe.

## 1. The compression wall (lowest N that still passes SSIM>=0.9)
case-3 input V = 23,201 [JUDGE-measured]. Score = 100*(1 - N/23201). The wall is a box-cut COIN
(per-run nondeterministic, sigma~0.001-0.002), so it is a distribution P(pass|N), not a sharp N.

| N | compression | status | provenance |
|---|---|---|---|
| 6954 | 70.03% | PASS | keep_for(0.2997) landing point |
| 6941 | 70.08% | PASS x2 (banked v111) | [JUDGE] friend's bank |
| 6940 | 70.09% | PASS, self-score S2=0.9135 | [JUDGE] friend's S-read 19898572 |
| 6900..6801 | 70.3-70.7% | **UNTESTED** | -- |
| 6800 | 70.69% | **IN FLIGHT** (bank-attempt 2026-07-07) | -- |
| 6799..6701 | -- | **UNTESTED** | -- |
| 6700 | 71.12% | WA (1 run; case-4 also coin-lost) | [JUDGE] 2026-07-07 read |
| <6700 | -- | **UNTESTED** | -- |

**Verdict: the wall is NOT pinned.** 6941 was banked conservatively (one rung into the coin);
(6700, 6941] was never probed. Slope 3.5e-5/vert + S2=0.9135@6940 puts the true 0.900 crossing at
~6700 and the reliable floor at ~6800 (S true ~0.904, ~2.7 sigma) => ~+0.10 of un-harvested limit.
The @6800 probe (in flight) tests this. To pin the coin fully: 2-3 S-reads at 6800/6850/6900 map S(N).

## 2. The mechanism limit (can a better simplifier LOWER the wall?)
The wall is pipeline-relative (WALL-MODEL §1). Leaders sit ~85% on case-3 (INFERRED from the 1.18-pt
gap) => a better simplifier renders a passing normal map at ~half the vertices. Our pipeline is at a
mature local optimum:
| lever | result | provenance |
|---|---|---|
| nmetric=3 (true SSIM-loss placement) | -0.010 | [LOCAL] not judge-tested |
| nmetric=4 (tempered) | -0.0013 | [LOCAL] not judge-tested |
| SIL (silhouette/depth) on c3 | -0.0012 (depth +0.0005, normal -0.003) | [LOCAL] not judge-tested |
| R1 interleave / 768 / lambda-sweep | judge-NEGATIVE | [JUDGE] closed |
**Verdict: cheap mechanisms screen local-negative and are NOT judge-tested.** The transfer wall
(§9.1: proxies mislead; we lack case-3's real mesh locally) means local screens are only weak
evidence. The ONLY door with real headroom is a globally-better optimizer (THEORY Road B item 2,
differentiable co-optimization) — heavy, transfer-risk, UNBUILT. This limit is NOT established.

## 3. Metric limits that bind case-3 (from JUDGE-ENVELOPE — all [JUDGE])
- FinalSSIM = 0.5*normal + 0.5*depth >= 0.9. case-3 self-score split: normal~0.805, depth~0.984.
- The binding term is the normal-map STRUCTURE (sigma_xy correlation), not luminance/contrast/depth.
- depth is ~saturated (0.984; SIL reaches only +0.0005) -> depth is NOT a lever for case-3.
- Hausdorff v2v <=5% diag: loose, NEVER binds at case-3's N. Faces geometrically unconstrained.
- CPU <=21s: case-3 refine converges ~13-14s (float32) -> case-3 is a converged/box-cut hybrid;
  a code change re-rolls the box-cut mean of OTHER cases (WALL-MODEL §3).
- Topology: genus-0 -> surgery has zero prize. Disconnected/nested output legal (used by the S-read).

## Bottom line (truthful)
- The compression LIMIT of the CURRENT pipeline is NOT pinned (~+0.10 likely un-harvested below 6941).
  Automatable to pin (Level A/B ladder) — in progress.
- The MECHANISM limit (can we lower the wall) is NOT established: cheap tweaks local-negative and
  un-transferred; the real lever (co-optimization) is unbuilt. This is where the leader gap lives.
