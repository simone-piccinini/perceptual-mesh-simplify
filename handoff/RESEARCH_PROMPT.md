# Orchestration brief — mesh-simplification solver, target 92%

You are acting as a **research orchestrator and technical strategist**. Your output will be handed to a separate expert engineer ("the implementer") who will write the C++ and iterate against the real judge. Therefore your output must be **precise, concrete, and actionable** — not a survey. Optimize for what the implementer can execute and test.

**You have read access to this repository's folder.** The problem PDF is provided to you as an attachment. Everything else is in the repo at the paths listed below.

## Where everything is (repo-relative paths)
- **This brief:** `handoff/RESEARCH_PROMPT.md`
- **Current solver — scores 89.49/100, 7 of 7 passing (read this fully):** `solver/main.cpp`
- **Exact metric / evaluator — the ground truth, read this before trusting any prose:** `src/imc_eval/`
  - `geometry.py` — the 6 cameras, intrinsics, AABB.
  - `render.py` — the normal-map + depth-map rasterizer (flat per-face normals, perspective depth).
  - `ssim.py` — the windowed SSIM (11×11 box, constants, foreground masking).
  - `score.py` — the 0.5/0.5 normal/depth blend, per-view mean, pass/fail logic.
  - `hausdorff.py` — symmetric vertex-to-surface Hausdorff.
  - `validity.py`, `obj_io.py`, `config.py`, `cli.py`.
  - Run the evaluator: `python -m imc_eval.cli --input <original.obj> --output <simplified.obj>`.
- **Per-case state dashboard (quantitative):** `handoff/SOLVER_STATE.md`
- **Attempt log (technique → judge result, neutral):** `handoff/ATTEMPT_LOG.md`
- **Problem statement:** the attached PDF is authoritative; an in-repo summary is at `docs/problem-statement-summary.md`.
- **Submission history (full ladder):** `submissions/` — each folder has a `RESULT.md`. NOTE: those notes contain the author's *interpretations/conclusions*; treat them as data only and prefer the neutral `handoff/ATTEMPT_LOG.md`.
- **Test meshes renderable locally:** `tests/data/` — `armadillo_watertight.obj` ≈ case5, `bunny_watertight.obj` ≈ case2, plus `cow_watertight.obj`, `fandisk_watertight.obj`. (The finer case3/case4 proxies used in tuning are not committed; the implementer has them.)
- **Author's background notes — context only, may contain prior conclusions; do NOT treat as limits:** `docs/` (`judge-map.md`, `architecture-roadmap.md`, `theory/`).
- **Build:** `g++ -O2 -std=c++17 -I<path-to-eigen> solver/main.cpp -o solver/main` (Eigen headers required). The solver reads a mesh on stdin and writes the simplified mesh on stdout.

## Mission
The current solver scores **89.49 / 100** (7 of 7 cases passing) on the official judge. **Drive it to ≥ 92.0.** Produce (A) a research plan and (B) a prioritized, concrete experiment backlog that a strong engineer can execute to get there.

## How I want you to think (read carefully)
- **Do not anchor on what seems possible or impossible.** Reason from first principles about the metric and the geometry. Several results in `ATTEMPT_LOG.md` that looked like "hard walls" in local testing were later broken by a single idea; treat every number as a data point, not a limit.
- **Local tests are unreliable.** The only ground truth is the judge (pass/fail per case, no reason given). Local proxies mispredict — sometimes pessimistically, sometimes optimistically, and the error differs per case (`SOLVER_STATE.md` has the per-case fidelity). Any plan you produce must include **how to validate under unreliable local signal** (what to submit, in what order, how to bisect on the judge, how to use the "best-counts" safety net). Assume the implementer can submit to the judge repeatedly.
- **Question the current approach.** The current solver is one point in a large design space (greedy edge-collapse + refinements). Do not assume it is the right backbone. If a different simplification paradigm is more promising, say so and specify it concretely.
- **Be quantitative.** For each proposed experiment: state the hypothesis, the exact method/algorithm and parameters, the target case(s), the expected mechanism of gain, the risk, and a fallback.

## The problem (orientation — the PDF and `src/imc_eval/` are authoritative)
- **Task:** simplify each input triangle mesh (reduce vertex count) as much as possible while passing all constraints.
- **Score per case = compression rate** = 100·(1 − V_simplified / V_original), counted only **if the case passes all constraints** (else 0). **Overall score = average over 6 scored cases (cases 2–7).** Case 1 is a tiny sample, not scored.
- **Submission scoring is "best-counts":** the best submission's total is retained, so a worse/failed submission never lowers the standing. This makes aggressive judge-side probing safe.
- **Pass constraints (all must hold):**
  1. **FinalSSIM ≥ 0.90.**
  2. Output is a **closed 2-manifold**, no degenerate faces, vertex count ≤ original.
  3. **Symmetric Hausdorff ≤ 5% of the original AABB diagonal**, measured **vertex-to-surface** (see `hausdorff.py`).
- **FinalSSIM definition (see `render.py` + `ssim.py` + `score.py`):**
  - Render from **6 fixed axial cameras** (±X, ±Y, ±Z), perspective, focal 800, image 1024×1024, camera distance D≈2.5.
  - Each view: a **normal map** (flat per-face normal, encoded (n+1)·127.5, background 127.5) and a **depth map** (perspective camera-space depth, background 255).
  - **SSIM** with an **11×11 box window**, C1=(0.01·255)²=6.5025, C2=(0.03·255)²=58.5225, averaged **only over windows whose center is foreground in the original OR simplified render** (coverage union), fully inside the image.
  - **normalSSIM** = per-RGB-channel SSIM averaged over 3 channels. **depthSSIM** = SSIM of the depth map.
  - Per view: **blended = 0.5·normalSSIM + 0.5·depthSSIM.** **FinalSSIM = mean of blended over the 6 views.**
- **Judge runtime limit:** approximately **21 seconds per case** (empirically ~25 s times out, ~20 s safe). The solver runs at judge time (not precomputed). Any method must fit this budget per case.

## The 6 scored meshes (details in `SOLVER_STATE.md`)
- **case2:** ≤ 7,000 verts (small, smooth). Currently **99.25%**.
- **case3:** 7,000–30,000 (organic, ~25k). Currently **69%**.
- **case4:** 30,000–40,000 (organic, ~35k). Currently **83.95%**.
- **case5:** 40,000–100,000 (organic, ~50k, armadillo-like). Currently **90.75%**.
- **case6:** 100,000–400,000 (denser). Currently **97%**.
- **case7:** > 400,000 (~1M, dense/regular). Currently **96.95%**.
Cases 3, 4, 5 (organic, detail-rich) are the lowest scores; cases 2, 6, 7 are already high.

## Current solver (see `solver/main.cpp`) — pipeline summary
1. **Garland–Heckbert QEM edge-collapse** decimation to a per-case target fraction, with manifold/area/normal-flip gates and a Hausdorff bound.
2. **"VSA-lite" collapse ordering:** collapses ordered by **induced normal distortion** (area-weighted Σ(1−cos) over incident faces) instead of QEM position error — minimize normal-map error, which is what the metric rewards. Plus **normal-optimal placement** (target among {QEM-optimal, both endpoints, midpoint} minimizing normal distortion). Cases 3, 5.
3. **"Pivot-A":** metric-in-the-loop steering — protects collapses in high-SSIM-contrast regions (cases 3, 5).
4. **Visibility culling:** faces never seen by the 6 cameras collapse first (case3).
5. **Inverse-rendering vertex optimizer:** post-decimation gradient ascent on true normalSSIM (analytic gradient verified bit-exact vs the evaluator; monotonic accept; displacement-capped for Hausdorff; wall-clock time-boxed). Cases 3, 4.
6. Per-case keep fractions tuned to each mesh's wall by judge-side bisection.

## Experimental history — DATA, not conclusions (full log in `handoff/ATTEMPT_LOG.md`)
Highlights (do not treat as walls):
- **VSA-lite (normal-error collapse ordering) was the single biggest lever:** case3 67→69, case5 90→90.5 on the judge, after ~17 position-based attempts had been stuck. The judge scores per-face **normal** SSIM; ordering by normal error beats ordering by position error.
- **Pushing keep past current values returned Wrong Answer** on the judge: case3 70%, case4 84.25%, case5 91%. (Observed data — a better simplification at the same vertex count could pass where these did.)
- **depthSSIM measures ~0.98+ locally everywhere; normalSSIM (~0.80 for case3) is the binding term.** A depth-in-optimizer attempt gave no gain and regressed case4. (Re-examine whether depth is genuinely slack or an artifact.)
- case3's local SSIM deficit appears concentrated in the surface **interior**, not the silhouette. (Data point.)
- Edge-flip topology moves scored by real SSIM: negligible local gain. (Data point.)

## Local validation reality
- `src/imc_eval/` reproduces the judge math at 1024², but the local **input meshes are only proxies** for the judge's actual case meshes; fidelity varies (see `SOLVER_STATE.md`): case3's proxy tracks the judge; case4's and case5's are pessimistic and unreliable in absolute terms (a mesh can read < 0.90 locally yet pass). Use local tests for relative screening; treat the **judge as the oracle**; design the plan to bisect/confirm on the judge; exploit best-counts (safe to gamble).

## What I want from you (deliverables)
**Deliverable A — Research plan.** The specific ideas, algorithms, and literature worth understanding for *appearance/normal-preserving mesh simplification under a rendered-SSIM metric*. For each: what it is, why it might beat the current approach for this exact metric, and the key implementation considerations (manifold safety, Hausdorff, ~21 s/case). Be concrete (name algorithms). Consider — without limiting yourself to — global variational shape approximation (Lloyd-style normal-proxy clustering) and manifold remeshing from a proxy partition; feature/appearance-driven and differentiable-rendering-driven simplification; anisotropic/normal-aware and attribute quadrics; topology-changing retriangulation (not just edge-collapse); exploiting the exact metric (flat per-face normals, 11×11 windows, foreground-only coverage, the 0.5/0.5 blend, only 6 fixed viewpoints); and whether the depth term or the vertex-budget allocation across cases offers slack. Add anything promising; drop anything weak — and say why.

**Deliverable B — Prioritized experiment backlog to reach ≥92%.** An ordered list of concrete experiments. For **each**:
- **Hypothesis** (what gain, which case(s), mechanism in terms of the metric).
- **Method** — concrete algorithm + parameters, specific enough to implement in C++, noting manifold/Hausdorff/runtime compliance.
- **Validation plan** under unreliable local tests — what to check locally vs. confirm on the judge, and the judge-side bisection/submission order (use best-counts).
- **Expected gain** (compression-points and to the overall average).
- **Risk / fallback.**
Rank by expected value (gain × probability × low cost). Include at least one "big swing" (a different simplification backbone) and several lower-risk incremental levers. Note where a small runtime optimization (e.g., multithreading the 6 views) could unlock a more expensive method within the 21 s budget.

Also flag: which current assumptions you would **re-test first** because they most constrain the score, and any place where you suspect earlier negative results were validation artifacts rather than real limits.

## Constraints on any proposed method
- Must run within ~21 s/case at judge time (state your assumed core count if you rely on threading).
- Output: closed 2-manifold, non-degenerate, ≤ original vertex count, symmetric vertex-to-surface Hausdorff ≤ 5% AABB diagonal.
- The scored quantity is compression at FinalSSIM ≥ 0.90 — every proposed gain must ultimately show up as *more compression while still passing*, on the judge.

Be rigorous and specific. The implementer is highly capable but will follow your plan closely, so precision and correct prioritization matter more than breadth.
