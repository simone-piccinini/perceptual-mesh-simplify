# Case 3 is (near-)intrinsic for edge-collapse — the structure-deficit diagnosis

> **VERDICT (Phase 0, local, 0 submissions).** The case-3 normal-map deficit is
> **100% the SSIM structure term**, it is **uncorrelated with where our pipeline puts
> faces** (`corr(deficit, face-density) = +0.01`), and it is **determined by the
> intrinsic local surface structure** (`corr(deficit, original normal-richness) = −0.50`,
> worst in the gentle mid-band). That is the signature of an **information-limited
> wall**, not an allocation error. Reallocation-class mechanisms (S1 ordering, S3
> weakest-view, S5 variance-density) cannot move it — and the one lever they'd use is
> **already deployed** (`sdef` steering). Connectivity/remesh (S7) needs creases the
> organic mid-band does not have. **Recommendation: bank 90.285538.** This closes the
> structural roadmap's Tier 1–3 for case 3 *before* building the dirty-region kernel or
> any mechanism. Reproduce with [`scripts/phase0/`](../../scripts/phase0/RUNBOOK.md).

## What was measured

Case 3's wall is the entire ~1.18-point gap to the leaders. The question Phase 0
answers, for free: is the deficit **spatially exploitable** (some regions much worse,
or starved of faces → a mechanism can reallocate/re-register) or **intrinsic** (the
organic surface simply carries more normal structure than ~7k faces can register)?

Method (all local, no judge):

1. Built a faithful organic case-3 proxy: armadillo decimated to **23,203 v** (matching
   case 3's real V=23,201), via a QEM library.
2. Ran the **real pipeline** (Pivot-A + VSA-lite + refine) to its **6,940-v wall**.
3. Rendered original vs. wall at judge resolution and decomposed the flat-normal SSIM
   into `l · c · s` (luminance · contrast · structure), per channel, foreground-only.
4. Mapped and quantified *where* the deficit lives.

**Fidelity check:** the solver's own 1024 self-score was **normal-SSIM 0.809**, matching
the real case 3's 0.812. The proxy reproduces the exact binding quantity, so the
diagnosis transfers in structure (not necessarily absolute value).

## The three results

**(1) The deficit is entirely the structure term.**

| l (luminance) | c (contrast) | structure |
|---|---|---|
| **1.000** | **0.998** | **≈0.81 (judge res)** |

Luminance and contrast are perfect. The facets paint normals of the right *magnitude*
in the wrong *pattern* — a registration failure, definitively. (Confirms the
`ATTEMPT_LOG` `l/c/s` decomposition and `wang-ssim.md`.)

**(2) The deficit is broad and view-uniform.** Gini **0.237** over 149,968 foreground
windows; all six axial views equally bad (1−cs ∈ [0.115, 0.135]). There is **no weak
view** to protect (kills S3) and no hotspot holding the loss.

**(3) The deficit is uncorrelated with our allocation and set by intrinsic structure —
the crux.**

- `corr(deficit, wall face/edge density) = +0.01` — **zero**. High-deficit windows do
  **not** have fewer faces. The loss is not "starved regions"; our placement is not
  systematically mis-aligned with it.
- `corr(deficit, original normal-richness σx) = −0.50`. The loss is **worst where the
  surface is gently curved** and **lowest on the sharp features**. The worst-10% windows
  sit at 0.76× the mean richness and 0.98× the mean face density.

This is exactly **Wang-2004 contrast-masking** (`wang-ssim.md`, exploit #2): sharp
features self-mask and are cheap; the penalty concentrates in the **intermediate-
curvature mid-band** — gentle undulation that collapse flattens into decorrelated
facets. The map shows it: broad mid-tone loss across the whole body, dark on the
sharpest ridges.

## Why this is a stop, not a lever

The instinct "mildly concentrated ⇒ small reallocation headroom" is **wrong** and worth
stating plainly: SSIM is the *mean* over windows, and pure redistribution of deficit
**conserves the mean** — concentration (Gini) alone recovers nothing. What would recover
score is placing faces where their *marginal* value is highest. The two correlations
close that door:

- deficit ⊥ face-density ⟹ the bad regions are **not under-allocated**; adding faces
  there means taking them from equally-deficient regions.
- deficit ∝ −richness ⟹ the loss is a property of **what the surface is**, not of where
  we put vertices — and the pipeline **already steers toward it** (`sdef_for` is on for
  case 3), yet the −0.50 correlation persists.

So the residual is the **intrinsic floor**: mid-band gentle undulation that ~7k faces
cannot register, roughly independent of allocation. Reallocation-class mechanisms have
nothing to fix. And connectivity/remesh (S7), which needs anisotropy/creases to align
new edges to, has no purchase on isotropic organic undulation (matching
`remesh-go-no-go.md`: "case 3 is uniform detail; VSA degenerates").

## The magnitude, honestly

To reach 91.0 needs **+0.069 normal-SSIM** at fixed N (≈ 989 fewer vertices at the
~3.5×10⁻⁵ Final/vertex wall slope, depth held). No mechanism class this diagnostic can
see delivers that: the strongest structural win in project history (VSA-lite) was
~+0.013 normal-SSIM, and it required going from a *position* proxy to a *normal* proxy —
a one-time step already taken. There is no visible source of a further ~0.07.

## Confidence and caveats

- **One proxy, not the hidden mesh.** But it reproduced the binding number (0.809 ≈
  0.812), and the finding is **triply consistent**: this diagnostic, Wang-2004 masking,
  and the independent `remesh-go-no-go` conclusion. Moderate-high confidence.
- Rendered at 512 (numba-less pure-Python 1024² is too slow); this inflates absolute `s`
  but the **correlations and view-uniformity — the decision variables — are
  resolution-robust**.
- The leaders *do* beat us, so headroom exists on the real mesh — but this says it is
  **not edge-collapse-reallocation headroom**. It would require a different construction
  class, for which neither this diagnostic nor the go/no-go offers a concrete lever.

## Decision

**Bank 90.285538.** Phase 0 did its job: it ruled out the multi-day S1/S6/S7 builds with
zero submissions. The only remaining thread is nudging the existing `sdef`/`lambda`
mid-band steering slightly harder — a one-constant change worth, at the theoretical
ceiling, a rounding-error gain with uncertain judge transfer. Not worth a submission
campaign.

*Reproduce / extend: [`scripts/phase0/RUNBOOK.md`](../../scripts/phase0/RUNBOOK.md).*
