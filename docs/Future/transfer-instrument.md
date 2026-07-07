# The transfer instrument — cross-proxy sign-consistency

**Status: FALSIFIED AT BACKFILL (2026-07-06).** The instrument passed its first N=2
validation (R1 ✓, SILv2 ✓) but **failed the ground-truth backfill**: it misreads Pivot-A
(the solver's strongest judge-positive mechanism) as reject, its SILv2 verdict flips with
panel keep choice, and it cannot distinguish SILv2 (judge-positive) from SILv3
(judge-negative). See "Backfill results" below for the data and the two root causes
(per-case mesh-dependence + local noise floor). The first validation was panel luck.
The process worked as designed — the tool was killed by ground truth *before* it gated any
decision, at a cost of ~25 local runs and zero judge submissions. Research toggles `G_R1`,
`G_SILV3` added (judge-inert unset; v109 byte-identical — verified
cow/bunny/fandisk/armadillo).

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

## Backfill results (2026-07-06) — the falsification

Panel: bunny_c3 & cow_c3 @keep .08, fandisk-sub @keep .02 (probed for real deficit, 0.9933).
Pivot-A ablated via `G_NOLAMBDA` (gain = ctrl − ablated); 768-native via argv res override;
SILv3 reconstructed per THEORY §9.2 (`G_SILV3`: radius 14, vote-magnitude-scaled steps,
double round).

| mechanism | judge truth | bunny | cow | fandisk | panel verdict | correct? |
|---|---|---|---|---|---|---|
| R1 (from first val.) | NEGATIVE | +0.00285 | −0.00161 | ~0 | SIGN-FLIP → reject | ✓ |
| 768-native | NEGATIVE | +0.00025 | −0.00007 | −0.00006 | SIGN-FLIP → reject | (✓)* |
| **Pivot-A** | **POSITIVE (strong)** | +0.00358 | **−0.00158** | +0.00012 | SIGN-FLIP → reject | **✗** |
| SILv2 | POSITIVE (~0.3×) | +0.00060 | +0.00201 | −0.00005 | SIGN-FLIP → reject | **✗**† |
| SILv3 | NEGATIVE | +0.00104 | +0.00175 | −0.00005 | SIGN-FLIP → reject | (✓)* |

\* correct verdict but unreadable data — see noise floor. † SILv2 read CONSISTENT(+) on the
first panel (fandisk @keep .15, saturated) and SIGN-FLIP on this one (@keep .02): the verdict
is an artifact of panel/keep choice. v2-vs-v3 are indistinguishable (identical fandisk deltas;
bunny/cow differences within noise) — the instrument cannot see the one distinction that
mattered most.

**Root cause 1 — the bar is conceptually wrong.** Judge ground truths are **per-case**, and the
solver deploys mechanisms **per-case-gated** (Pivot-A on cases 3/5 only, SIL on case 5 only).
A judge-positive mechanism is *allowed* to hurt unrelated shapes — Pivot-A genuinely hurts
cow-subdiv (−0.0016, 10× the noise floor) while being the strongest judged win on the real
case-3/5 meshes. Sign-consistency across arbitrary diverse shapes tests generality, not
transfer-to-the-one-hidden-mesh. Diversity was the fix for the armadillo monoculture, but it
overshoots.

**Root cause 2 — the local noise floor swallows the small reads.** Near-null perturbations
(keep ± 1 vertex) move final SSIM by **|Δ| ≈ 1–3 × 10⁻⁴** on these proxies. 768-native's
reads (±0.7–2.5 × 10⁻⁴) and every fandisk delta are at/below the floor — those verdicts are
noise, and any instrument reading gains < ~5 × 10⁻⁴ per mesh is reading static. (This floor
number is independently useful: it is the minimum effect size any future local screen can
claim on these proxies.)

## Where this leaves the transfer problem (honest)

Open. Three formulations tried, three falsified: smooth-proxy noise model (roadb-assessment),
armadillo monoculture (R1's original screen), cross-proxy sign-consistency (this doc). What
survives from the wreckage:

- **The validation-first process works.** Each formulation died against ground truth in hours
  of local compute, zero judge submissions. Any future instrument candidate must pass the full
  5-mechanism table (R1−, 768−, Pivot-A+, SILv2+, SILv3−) before gating anything.
- **The noise floor (~1–3e-4) is now measured** — a prerequisite fact no prior screen had.
- The remaining honest instrument idea is **per-case-matched proxies + effects ≫ floor**
  (predict transfer only for the case a mechanism targets, only when the local gain clears
  ~5e-4 on that case's proxy) — R1 (+0.0015–0.002 on case-matched proxies) would still have
  passed that bar and failed the judge, so even this needs something more (e.g. a judge-side
  S-read instrument per THEORY §9.2's SIL conclusion). Road B stays measurement-blocked.

*Evidence trail: D4 (shelved), D5 (shelved), D1 (inert), Road B (measurement-blocked),
naive noise instrument (falsified), cross-proxy sign-consistency (falsified at backfill).
See roadb-assessment.md.*
