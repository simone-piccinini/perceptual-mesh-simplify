# Road B (joint / appearance-driven optimizer) — assessment 2026-07-06

**Bottom line: the door is real but gated by an UNSOLVED measurement problem, not an
engineering one. The classic joint optimizer is already judge-proven negative; the
prerequisite that would make it buildable — a transfer-faithful local signal — does not
exist and the obvious model for one was falsified below. Recommend NOT starting a
speculative optimizer build; it repeats R1.**

## The opportunity (why Road B is tempting)

The remaining solver walls are the converged LOCAL OPTIMUM of the decimate-then-refine
family. Structurally different meshes at the same vertex count spread **±0.013 SSIM**
(measured) — i.e. better optima exist at every banked count, and JUDGE-ENVELOPE §6 calls a
globally better optimizer "the only door left to 91+."

## Wall 1 — the classic joint optimizer is already judge-negative (THEORY.md §9.1)

R1 (interleaved decimate↔refine, so ordering/placement act on SSIM-optimized geometry) gained
**+0.0015–0.002 on both local proxies** and **failed its banked razor on the judge in three of
three live families** (cases 3 & 5). This established a theory-level fact:

> The armadillo-derived proxies **systematically over-reward position-space optimization.**
> Measured transfer ratio ≈ **0 to negative** across three position-space mechanisms
> (R1, 768-native, cheap-flip D5). Only **throughput** (same trajectory, more iterations)
> transfers; **new basins / trajectories do not.**

Road B's textbook forms are exactly this non-transferring class:
- *decimate→refine→re-decimate→refine* — re-decimating the refined mesh = R1. Closed.
- *nvdiffmodeling co-optimization of positions during reduction* — even more position-space
  micro-optimization. Predicted-dead by the same result.
- *basin-diversity harvesting (N seeded orders, keep best by self-score)* — selection is on
  the **local self-score**, the very metric that over-rewards → picks proxy-specific structure.

## Wall 2 — the optimizer is basin-limited, not throughput-limited

The one transferable optimizer class is throughput (converge the *same* trajectory faster →
more of it in the box). But D1's cap A/B (2026-07-06) showed the position ascent **plateaus at
0.36–0.84% Hausdorff, far inside its 2% cap**, and even a 25× cap widening moved SSIM by 5e-6.
The optimizer is *already converged* in its basin — more throughput reaches the same local
optimum, it does not escape it. So the transferable lever (throughput) cannot open this door,
and the door-opening lever (a new basin) does not transfer. That scissor is the whole problem.

## Wall 3 — the enabling prerequisite (a transfer-faithful proxy) has no known form

Everything above means Road B is un-validatable locally: any basin-changing optimizer looks
good on the proxy and (per three judge reads) fails on the true meshes. The only way to build
Road B responsibly is a **local instrument whose A/B sign predicts the judge** — then iterate a
joint optimizer against it instead of burning ~1 submission/mechanism at ≈2/3-per-case odds.

**PoC (falsified) — "the proxy over-rewards because it's smoother than raw scans, so add
scan-like noise":** perturbed bunny_c3 vertices along their normals by 0.4% diag and measured
the refine gain (on−off) vs the clean proxy:

| proxy | refine OFF | refine ON | gain |
|---|---|---|---|
| clean bunny_c3 @keep .05 | 0.796045 | 0.800725 | **+0.004680** |
| noised bunny_c3 @keep .05 | 0.517023 | 0.525754 | **+0.008730** |

Noise **increased** the gain (lower baseline → more recoverable deficit), the *opposite* of
what a transfer instrument needs. Surface smoothness is not the isolable carrier of the
over-reward; the naive instrument is wrong. A real instrument would have to be **validated
against the known judge ground truth** (predict R1 negative AND SIL ≈ +0.3×) — a multi-step
research harness with no guaranteed solution, not a quick build.

## The only Road-B-adjacent thing that transferred

**SIL / coverage (THEORY.md §9.2), transfer ratio ≈ 0.3** — because it corrects a *systematic
geometric bias* (the silhouette chord under/over-shoot has a definite per-vertex sign), not
proxy-specific micro-structure. Its own §9.2 note: any *intensification* (more rounds, scaled
steps) "re-enters the proxy-specific position-space regime and inverts, exactly like R1."
Lesson: the transferable moves are **systematic-bias corrections**, not basin exploration.

## Recommendation

1. **Do not build the classic joint/appearance optimizer.** It is R1; the judge has spoken
   three times. Building it repeats a closed experiment and burns submissions on a lottery.
2. If Road B is pursued at all, the *only* honest first deliverable is the **transfer
   instrument**, validated against the R1/SIL ground truth — a research bet, not an
   optimizer. The naive (noise) model is falsified; there is no obvious next model.
3. Higher-ROI alternatives given the session's evidence: **systematic-bias correctors** in the
   SIL family (e.g. D6 silhouette-coverage), or **razor re-harvest** (reliable hundredths,
   bank-protected). These are the levers whose local sign has actually matched the judge.

*Session evidence trail: D4 (marginal EV, shelved), D5 (cheap driver anti-correlated,
shelved), D1 (cap non-binding, inert), Road B (measurement-blocked, this doc).*
