# Oracle calibration

The oracle (`src/imc_eval/`) is a home-made replica of the secret judge. A few
details the problem statement leaves ambiguous had to be **guessed** (see
`src/imc_eval/config.py`): the SSIM blend weights `lambda_normal`/`lambda_depth`
(default 0.5/0.5) and the SSIM window (`box` vs `gaussian`). They can only be pinned
by comparing the oracle against the real judge.

## Workflow

1. **Prepare discriminating cases** (deterministic, builds the solver):
   ```
   python scripts/calibrate_oracle.py generate
   ```
   Writes near-gate, λ-discriminating outputs to `cases/`, their default-vs-grid
   predictions to `cases.json`, and an empty `verdicts.json` template.

2. **Get real verdicts.** Submit / score those cases on the judge and fill
   `verdicts.json` (`"judge": "ACCEPTED" | "WRONG_ANSWER"`, plus `constraint`/`score`
   if known). No network automation — you enter the verdicts by hand.

3. **Fit the parameters:**
   ```
   python scripts/calibrate_oracle.py calibrate
   ```
   Grid-searches `(lambda, window)` for the best match, reports how much it cuts the
   disagreement, and writes `oracle_config.json`. Load it with
   `OracleConfig.load("calibration/oracle_config.json")` and pass to `evaluate(...)`.

4. **Track reliability over time:**
   ```
   python scripts/compare_judge_vs_oracle.py
   ```
   Tables oracle-prediction vs judge-verdict, appends to `judge_history.jsonl`.

## Files

- `cases.json`, `cases/*.obj` — generated calibration cases (real solver outputs).
- `verdicts.json` — **you fill this** with the judge's real verdicts.
- `oracle_config.json` — the tuned parameters (created by `calibrate`).
- `judge_history.jsonl` — append-only log of oracle-vs-judge agreement.

## Honest caveat

The judge scores its 7 **hidden** cases; these calibration meshes are chosen by you.
A good fit here is the best available signal but does NOT guarantee a perfect fit on
the hidden cases. More (and more discriminating) points = more trust. The contest has
no penalty for wrong/multiple submissions and only the best counts, so calibration is
not limited to a few points — only a possible undocumented cooldown to wait out.
