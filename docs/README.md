# Documentation

Everything written about the project: the judge, the solver, the theory it rests on, and
the record of what was tried and failed.

> **The project in one paragraph.** Simplify a closed watertight mesh to as few vertices
> as possible while the judge's six-view perceptual score stays `FinalSSIM ≥ 0.90` and the
> mesh stays a valid 2-manifold within 5% Hausdorff. Score per case = compression
> `100·(1 − V'/V)`, averaged over six hidden cases. **Final standing: 90.285538, all seven
> cases passing** (v111). See the [top-level README](../README.md) for the overview.

Two documents are in Italian (`PROBLEM-AND-JUDGE.md`, `THEORY.md`); everything else is in
English.

## Read in this order

1. **[PROBLEM-AND-JUDGE.md](PROBLEM-AND-JUDGE.md)** 🇮🇹 — the authoritative model of the
   judge: the rules, the exact render pipeline, and the behaviours established
   experimentally over 100+ submissions. *If any other doc contradicts this one, this one
   wins.*
2. **[theory/solver-anatomy.md](theory/solver-anatomy.md)** — the solver explained from
   textbook QEM upward, layer by layer, ending at 90.29. *Start here for the code.*
3. **[Future/STRUCTURAL-ROADMAP.md](Future/STRUCTURAL-ROADMAP.md)** — where the project
   stands, what the remaining deficit costs in vertices, and the ranked open ideas.

## The judge

| Doc | What it covers |
|---|---|
| [PROBLEM-AND-JUDGE.md](PROBLEM-AND-JUDGE.md) 🇮🇹 | The rules and the render pipeline, verified fact by fact. |
| [JUDGE-ENVELOPE.md](JUDGE-ENVELOPE.md) | The operational contract — what is possible and how we know. Every claim tagged with provenance. |
| [WALL-MODEL.md](WALL-MODEL.md) | The per-case walls: how they are found, measured and harvested; the judge as a noisy oracle. |

## The solver

| Doc | What it covers |
|---|---|
| [theory/solver-anatomy.md](theory/solver-anatomy.md) | Narrative walkthrough: each layer as an idea first, then the functions implementing it. |
| [SOLVER-FUNCTION-REFERENCE.md](SOLVER-FUNCTION-REFERENCE.md) | Every function — signature, purpose, algorithm. |
| [SOLVER-INTERNALS.md](SOLVER-INTERNALS.md) | Line-level reference and the per-case operating-point table. |
| [theory/perception-aware-solver.md](theory/perception-aware-solver.md) | The earlier, narrower map of the machinery beyond the QEM core. |
| [V2-CONSTRUCTION.md](V2-CONSTRUCTION.md) | `main_v2.cpp` — a from-scratch construction/carve solver kept as a parallel line. |

## Theory

| Doc | What it covers |
|---|---|
| [THEORY.md](THEORY.md) 🇮🇹 | The consolidated mathematics of the metric and what was proved about it. |
| [theory/paper-notes.md](theory/paper-notes.md) | Working notes on the literature (Lindstrom–Turk, VSA, probabilistic quadrics) with actionable takeaways. |
| [references/README.md](references/README.md) | Bibliography and vendored papers. |

## Postmortems — what failed and why

Chronological. Each is a debugged dead end or a go/no-go decision. **Read these before
reviving any idea** — several of them killed multi-day plans before they were built.

| Doc | Verdict |
|---|---|
| [quality-driven-termination.md](postmortems/quality-driven-termination.md) | The cost-budget stopping rule and the sample-case fix. |
| [qem-cost-is-not-hausdorff.md](postmortems/qem-cost-is-not-hausdorff.md) | Why the cost budget over-compressed: QEM cost bounds *average* plane distance, not worst-case surface Hausdorff. |
| [reset-to-v1.md](postmortems/reset-to-v1.md) | The strategic revert to plain keep-ratio QEM after the cost-budget regression. |
| [meshopt-step1-gate.md](postmortems/meshopt-step1-gate.md) | meshoptimizer can't be used directly — it breaks watertightness on organic meshes. |
| [hybrid-step2.md](postmortems/hybrid-step2.md) | meshopt's ideas on our collapse loop; the adaptive Hausdorff guard's judge-side failure (2/7). |
| [adaptive-hausdorff-plan.md](postmortems/adaptive-hausdorff-plan.md) | The provably-bounded adaptive plan: subset placement + bounding-sphere guard. |
| [remesh-go-no-go.md](postmortems/remesh-go-no-go.md) | Can a VSA/remesh rebuild beat the case-3/4 walls? Concludes the walls are information-theoretic. |
| [d3-depth-optimizer-null-result.md](postmortems/d3-depth-optimizer-null-result.md) | Depth in the optimizer — a null result, on the wrong base. |
| [d4-compile-oom.md](postmortems/d4-compile-oom.md) | `cc1plus` killed on the judge — probabilistic quadrics never compiled. |
| [compile-headroom.md](postmortems/compile-headroom.md) | The solver was sitting at the judge's compiler ceiling. |
| [case3-intrinsic-wall.md](postmortems/case3-intrinsic-wall.md) | **The central diagnosis.** Case 3's deficit is 100% the SSIM structure term, spatially broad, and uncorrelated with face allocation — an information-limited wall, not an allocation error. |

## Future — open ideas

| Doc | Status |
|---|---|
| [Future/STRUCTURAL-ROADMAP.md](Future/STRUCTURAL-ROADMAP.md) | **The live plan.** What ">91" costs in vertices, the measurement prerequisite, and the ranked ideas. |
| [Future/structural-ideas.md](Future/structural-ideas.md) | The older idea list plus the graveyard of dead mechanisms. |
| [Future/transfer-instrument.md](Future/transfer-instrument.md) | Predicting judge behaviour from local measurements — **falsified**, three times. |
| [Future/roadb-assessment.md](Future/roadb-assessment.md) | The appearance-driven joint optimizer: real, but gated on the measurement problem. |
| [Future/c4-harvest-ladder.md](Future/c4-harvest-ladder.md) | Case-4 razor re-harvest — closed, banked at N=4970. |
| [Future/d5-flip-optimizer.md](Future/d5-flip-optimizer.md) | Render-gated edge flips — shelved on the cheap proxy; revisited in `experiments/kern-registration-descent/`. |

## Where the rest of the project lives

| Area | Location | What |
|---|---|---|
| The solver | [../solver/main.cpp](../solver/main.cpp) | the single C++ file uploaded to the judge |
| The oracle | [../src/imc_eval/README.md](../src/imc_eval/README.md) | offline reimplementation of the judge, file by file |
| The harness | [../probe/README.md](../probe/README.md) | wall-probing: plan, preflight, submit, decode |
| Submissions | [../submissions/README.md](../submissions/README.md) | 100 versioned solver snapshots + judge results |
| Experiments | [../experiments/](../experiments/) | self-contained investigations with their own notes |
| Session log | [../handoff/ATTEMPT_LOG.md](../handoff/ATTEMPT_LOG.md) | chronological record of what was tried each session |

## Conventions

- **Theory we write** → `theory/`, as Markdown. Keep it MathJax-friendly (display math on
  its own `$$` lines, no double underscores) so it renders on GitHub and in a notes vault.
- **Postmortems and decision memos** → `postmortems/`. One file per investigation, with the
  judge verdict and the takeaway at the top.
- **Forward-looking ideas** → `Future/`. Mark the status (`LIVE` / `CLOSED` / `SHELVED` /
  `FALSIFIED`) in the first two lines, so a reader knows before investing.
- **External sources** → `references/`: drop the PDF in `research/` and add an entry to
  [references/README.md](references/README.md).
- **Per-submission write-ups** → the relevant `submissions/vN-.../RESULT.md`, not here.
- **Figures** → `imgs/`. Charts are authored as SVG (the editable source) and committed
  alongside a 2× PNG export, which is what the READMEs embed, using plain markdown
  `![...](path)` syntax. Both details are deliberate: several renderers refuse inline SVG,
  and `<picture>`/`srcset` breaks in editor previews that rewrite `src` but not `srcset`.
  Figures therefore use one light-surface PNG, which stays legible on a dark page too.
