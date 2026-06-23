# Documentation

Where everything written about the project lives.

| Area | Location | What |
|---|---|---|
| Problem | [problem-statement-summary.md](problem-statement-summary.md) | the IMC Problem B statement, distilled |
| Theory (ours) | [theory/](theory/) | derivations and design we authored |
| References | [references/](references/) | external papers + bibliography |
| Code guide | [../src/imc_eval/README.md](../src/imc_eval/README.md) | the oracle package, file by file |
| Submissions log | [../submissions/](../submissions/) | versioned solver snapshots + judge results |

## theory/

- [qem-pseudocode.md](theory/qem-pseudocode.md) — the manifold-safe QEM engine in pseudocode
- [quality-driven-termination.md](theory/quality-driven-termination.md) — the cost-budget stopping rule (submission v2)
- [qem-cost-is-not-hausdorff.md](theory/qem-cost-is-not-hausdorff.md) — why that cost budget over-compressed

## Conventions

- **Theory we write** → `docs/theory/`, as Markdown. Keep it MathJax-friendly
  (display math on its own `$$` lines, no double underscores) so it renders both
  on GitHub and in a notes vault.
- **External sources** (papers, specs) → `docs/references/`: drop the PDF in and
  add an entry to [references/README.md](references/README.md) saying what it is
  and where in our code/theory we rely on it.
- **Per-submission write-ups** (what scored, what failed, why) → the relevant
  `submissions/vN-.../RESULT.md`, not here.
