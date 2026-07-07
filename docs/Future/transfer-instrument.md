# The transfer instrument — cross-proxy sign-consistency

**Status: FIRST VALIDATION PASSED (2026-07-06).** A local A/B signal that predicts the *sign*
of a mechanism's judge transfer, validated against two known-outcome mechanisms. This is the
prerequisite that unblocks Road B (and vets any future position/appearance mechanism before
spending a judge submission). Research toggle `G_R1` added (judge-inert unset; v109
byte-identical — verified cow/bunny/fandisk/armadillo).

## The problem it solves

Local proxy A/B over-rewards position-space optimization: mechanisms gain locally and fail on
the judge (R1, 768-native, cheap-flip — transfer ratio ≈ 0 to negative; THEORY.md §9.1). Road B
is un-buildable without a local signal that predicts transfer. The catch in the *old* method:
R1 was screened on **two armadillo-derived proxies** (25k/35k armadillo decimations + armadillo
itself) — an **armadillo monoculture**. Both agreed "+0.002", so R1 looked safe, then WA'd 3/3
banked razors. Same-family proxies don't test transfer; they test reproducibility on one shape.

## The instrument

Run a mechanism's A/B across a **structurally diverse** proxy panel and read the **sign
pattern**, not the mean:

- **sign-consistent (all ≥ 0, some > 0)** → the gain is a *systematic* effect → predict TRANSFER.
- **sign-flip across the panel** → the gain is *proxy-specific structure* → predict NO transfer.

Magnitude is not trusted (it's what over-rewards); only the sign pattern is.

## Validation against ground truth (the key result)

Panel: bunny-subdiv & cow-subdiv (organic, case-3 band) + fandisk-subdiv (CAD). Each at a keep
with real deficit. Δ = final-SSIM(mechanism) − final-SSIM(control), local oracle:

| mechanism | **judge ground truth** | bunny | cow | fandisk | panel sign | instrument says | correct |
|---|---|---|---|---|---|---|---|
| **R1** (interleave) | **NEGATIVE** (WA 3/3) | +0.00285 | **−0.00161** | ~0 | **SIGN-FLIP** | reject | ✓ |
| **SIL** (coverage) | **POSITIVE** (~0.3×) | +0.00060 | +0.00201 | ~0 | **consistent +** | accept | ✓ |

The instrument discriminates correctly on **both** a true-negative and a true-positive. R1's
fatal tell is the **cow sign-flip** — exactly the signal the armadillo monoculture could not
show. (fandisk saturates near 1.0 at these keeps → uninformative; the discriminating pair is
bunny-vs-cow, both organic but different shape.)

## The decision rule (deployable now)

> Before spending a judge submission on any position/appearance mechanism, A/B it across the
> diverse panel. **Require sign-consistency (no proxy negative beyond ±1e-5).** A single
> sign-flip predicts non-transfer — do not submit. R1 fails (cow < 0); SIL passes.

This would have blocked R1 before its three wasted submissions.

## Honest caveats (this is a first validation, not a proof)

- **N = 2 ground-truth mechanisms.** Two points (one −, one +). Strengthen by adding the other
  known outcomes: 768-native (−), Pivot-A ordering (+, strong), D3 depth (null), cheap-flip D5
  (−). The instrument must reproduce each. Until then it is *promising*, not established.
- **Weak panel.** Real discrimination came from bunny-vs-cow (both organic). fandisk saturates;
  there is no CAD/rough-scan signal at these keeps, and no genuine *raw-scan* surrogate (the
  true judge meshes are scans; all proxies are clean/decimated). Add: a rough/re-meshed mesh, a
  noised variant tuned to match scan statistics, and per-case-matched keeps.
- **Predicts sign, not magnitude.** It tells you *whether* to submit, not how much you'll gain.
  Good enough to gate submissions; not enough to rank rungs.
- **Panel size vs CPU.** Each mechanism × panel × keep is ~N solver runs; fine for gating,
  budget it if the panel grows.

## Next steps (to make Road B actually buildable)

1. **Backfill the ground-truth table** (768-native, Pivot-A, D3, D5) — confirm the instrument
   reproduces all known signs. This is the make-or-break; do it before trusting the rule.
2. **Widen the panel** with a rough-surface / scan-like mesh so the sign test has real dynamic
   range beyond bunny-vs-cow.
3. **Then, and only then**, iterate a joint/appearance optimizer (Road B) accepting *only*
   sign-consistent gains — the first time that class of mechanism can be built without a judge
   lottery.

*Evidence trail: D4 (shelved), D5 (shelved), D1 (inert), Road B (measurement-blocked →
this instrument is the unblock attempt). See roadb-assessment.md.*
