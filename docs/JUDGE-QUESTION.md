# Judge clarification question — ready to send (ARCHITECT-REVIEW §6)

*This is a HUMAN action: post it to the contest organizers (same channel that answered the
2026-06-18 Hausdorff clarification). It is free and could reopen the case-3 structure front.
Rules it obeys: (a) does not ask for the solution; (b) the answer materially changes strategy;
(c) genuinely open — our self-score calibration §7.1 pins normal-space / depth / the box window
only for the IDENTITY mesh, not for the background-in-window treatment that a simplified mesh with
different silhouettes stresses.*

## PRIMARY (metric definition — high leverage, still open)

> For the SSIM computation: an 11×11 window is counted when its centre pixel is foreground in the
> original OR the simplified render (the union). **Within such a counted window, are the SSIM
> statistics (means μ, variances σ², covariance σ_xy) computed over ALL 121 pixels (including
> background pixels at their constant value), or only over the FOREGROUND pixels present in the
> window?**

**Why it matters.** The binding term for us is σ_xy on the normal map, and ~90% of our measured
deficit is in windows straddling the silhouette. If the judge INCLUDES background pixels (our
current assumption), boundary windows are dominated by the constant background → the structure
deficit is computed very differently than if the judge MASKS background. The two answers imply
OPPOSITE steering strategies on boundary windows. Our calibration only touched this tangentially
(one mesh, near the wall where silhouettes match), so it is NOT pinned like normal-space/depth are.

## RUNNER-UP (compression valve — send instead if you prefer)

> Given the validity rule 1 ≤ V′ ≤ V, may an output contain ISOLATED vertices (referenced by no
> face) and still be accepted?

**Why it matters.** If a better mechanism pushes case-3 toward 76%+, the FORWARD direction of the
vertex-to-vertex Hausdorff (every ORIGINAL vertex needs a nearby output vertex) can start to bind.
Isolated vertices scattered on the uncovered original clusters satisfy it at ZERO SSIM cost (an
isolated vertex renders nothing) — an escape valve that unlocks aggressive compression exactly in
the winning scenario. Currently marked OPEN/IDLE; becomes live the moment case-3 moves.

*Send ONE. The primary has more immediate leverage on the front that binds today (case-3 structure).*
