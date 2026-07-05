# Documentation

Everything written about the project: the problem, the current strategy, the
theory it rests on, and the record of what we tried that failed.

> **TL;DR of the project.** Simplify a closed watertight mesh to as few vertices
> as possible while the judge's 6-view perceptual score stays `FinalSSIM ≥ 0.9`
> and the mesh stays a valid 2-manifold within 5% Hausdorff. Score per case =
> compression `100·(1 − V'/V)`, averaged over the 6 hidden cases.
> **Current best on the judge: 88.67, 7/7 valid** (submission v38).

## Read in this order

If you are new to the project, read these three top-level docs first — they are
the orientation layer:

1. **[problem-statement-summary.md](problem-statement-summary.md)** — the IMC
   Problem B statement, distilled. *What the judge measures and what counts.*
2. **[judge-map.md](judge-map.md)** — the living, authoritative model of the
   judge's behavior: per-case walls, which constraint binds, and the failure-mode
   decoder. *Updated every submission — the single source of truth for "where are
   we and why."*
3. **[architecture-roadmap.md](architecture-roadmap.md)** — the strategy: the
   current pipeline, its structural limits, the ranked pivots, and the
   **never-do list** (dead ends not to revisit).

Then dive into `theory/` for the derivations, or `postmortems/` for the full
story of how we got here.

## Folder map

| Folder | What lives there |
|---|---|
| *(top level)* | The three read-first orientation docs above, plus this index. |
| [`theory/`](theory/) | Durable derivations we authored — the algorithm and the metric. |
| [`postmortems/`](postmortems/) | What we tried, why it failed, and the lessons — chronological. |
| [`Future/`](Future/) | Forward-looking ideas not yet tried — candidates to lower `V'_min`. |
| [`references/`](references/) | External papers + bibliography ([index](references/README.md)). |
| `imgs/` | Figures referenced by the docs (e.g. the base-algorithm pseudocode). |

### theory/ — the foundations

- [perception-aware-solver.md](theory/perception-aware-solver.md) — **the current
  solver explained end to end**: every method beyond the QEM core (per-case
  dispatch, the in-loop rasterizer, Pivot-A steering, visibility culling, the
  inverse-rendering optimizer, and the validity invariants). Start here for the
  live `solver/main.cpp`.
- [ALGORITHM.MD](theory/ALGORITHM.MD) — the base QEM edge-collapse algorithm
  adapted to this problem (lazy deletion, version stamps, the manifold-safety gate).
- [qem-pseudocode.md](theory/qem-pseudocode.md) — the manifold-safe QEM engine in pseudocode.
- [wang-ssim.md](theory/wang-ssim.md) — Wang-2004 SSIM applied to our wall: **why
  the variance/contrast term, not the mean, is what caps compression.** The key
  theoretical result of the project.
- [paper-notes.md](theory/paper-notes.md) — working notes on the literature
  (Lindstrom-Turk, VSA, probabilistic quadrics, …) with actionable takeaways.

### postmortems/ — what we tried and why it failed

Chronological. Each is a debugged dead end or a go/no-go decision — the reasoning
behind the never-do list. Read these before reviving any "clever" idea.

- [quality-driven-termination.md](postmortems/quality-driven-termination.md) — the
  cost-budget stopping rule (submission v2) and the sample-case fix.
- [qem-cost-is-not-hausdorff.md](postmortems/qem-cost-is-not-hausdorff.md) — why the
  cost budget over-compressed: QEM cost bounds *average* plane distance, not the
  *worst-case* surface Hausdorff the judge measures.
- [reset-to-v1.md](postmortems/reset-to-v1.md) — the strategic revert to plain
  keep-ratio QEM after the cost-budget regression.
- [meshopt-step1-gate.md](postmortems/meshopt-step1-gate.md) — why meshoptimizer
  can't be used directly: it breaks watertightness on organic meshes.
- [hybrid-step2.md](postmortems/hybrid-step2.md) — meshopt's ideas on our
  manifold-safe collapse loop; the adaptive Hausdorff guard's judge-side failure.
- [adaptive-hausdorff-plan.md](postmortems/adaptive-hausdorff-plan.md) — the
  provably-Hausdorff-bounded adaptive plan (subset placement + bounding-sphere guard).
- [remesh-go-no-go.md](postmortems/remesh-go-no-go.md) — the decision memo on
  whether a VSA/remesh rebuild can beat the case-3/case-4 walls. **Concludes the
  walls are information-theoretic and ~88.5–89 is the realistic ceiling.**

## Where the rest of the project lives

| Area | Location | What |
|---|---|---|
| The solver | [../solver/main.cpp](../solver/main.cpp) | the single C++ file uploaded to the judge |
| The oracle | [../src/imc_eval/README.md](../src/imc_eval/README.md) | local reimplementation of the judge, file by file |
| Submissions log | [../submissions/README.md](../submissions/README.md) | versioned solver snapshots + judge results |
| Calibration | [../calibration/README.md](../calibration/README.md) | pinning the oracle's ambiguous params against real verdicts |

## Conventions

- **Theory we write** → `docs/theory/`, as Markdown. Keep it MathJax-friendly
  (display math on its own `$$` lines, no double underscores) so it renders both
  on GitHub and in a notes vault.
- **Post-mortems & decision memos** (what we tried, why it failed/was rejected) →
  `docs/postmortems/`. One file per investigation; keep the judge verdict and the
  takeaway at the top.
- **External sources** (papers, specs) → `docs/references/`: drop the PDF in and
  add an entry to [references/README.md](references/README.md) saying what it is
  and where in our code/theory we rely on it.
- **The living state** (per-case walls, current operating point) → keep
  [judge-map.md](judge-map.md) current; it is updated every submission.
- **Per-submission write-ups** (what scored, what failed, why) → the relevant
  `submissions/vN-.../RESULT.md`, not here.
