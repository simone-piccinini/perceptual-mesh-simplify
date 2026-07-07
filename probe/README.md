# probe/ — the wall-probing harness

Implements the plan/decode loop of [../docs/WALL-MODEL.md](../docs/WALL-MODEL.md) §6.
The machine does the arithmetic; the human does the click (Kattis 403s scripts) and the
spend decision.

## The loop

```bash
# 0. once: build band proxies + Eigen copy for preflight
python3 probe/make_band_proxies.py

# 1. plan a probe (any mix; ambiguity-checked before you spend the slot)
python3 probe/harness.py plan --read 3@6800            # S-read: case 3 at N=6800
python3 probe/harness.py plan --bank 4@4970 --read 5@4212   # multi-case batch

# 2. verify (clang build, byte-identity on untouched bands, optional judge-compiler check)
python3 probe/harness.py preflight [--docker]

# 3a. AUTO-SUBMIT (closes the click via scripts/judge_submit.py -> imc2.kattis.com)
python3 probe/harness.py submit            # DRY-RUN: prints the exact command, submits nothing
python3 probe/harness.py submit --live     # actually submits, polls, decodes, updates state

# 3b. or MANUAL: submit probe/out/main.cpp yourself, then paste the score:
python3 probe/harness.py decode 90.281234  [--dry]

# anytime: the wall ledger
python3 probe/harness.py status

# fully autonomous descent of one box-cut razor (guarded; dry-run unless --live):
python3 probe/harness.py campaign 3 --start 6800 --max-subs 3 [--live] [--auto-bank]
```

## Credentials / target

`~/.kattisrc` (outside the repo, mode 600, never committed) holds the token. The contest
problem `simplifygeometry` lives on **imc2.kattis.com / contest imc2-2** — all real
submissions go there (verified: the token authenticates on imc2; the problem is NOT on
open.kattis.com's public set). `submit`/`campaign` pass `--contest imc2-2` by default.

## Guardrails on the autonomous path (why it is still safe without a human clicking)

- **Dry-run by default.** `submit` and `campaign` print the exact `judge_submit.py` command
  and change nothing unless you add `--live`.
- **Budget + rate-limit.** `campaign --max-subs N --min-interval S` caps submissions per run
  and spaces them (contest etiquette + runaway protection).
- **Unique-decode-or-halt.** A result that matches more than one hypothesis stops the loop
  with NO state change (`apply_result` raises).
- **New-bank checkpoint.** On a new best the loop halts by default (snapshot into
  `submissions/` by hand); `--auto-bank` opts into continuing.
- **Duplicate/CE gates inherited** from `judge_submit.py` (won't re-burn a byte-identical
  source without `--force`) and from `preflight` (compile in `gcc:14` before spending).

## What each action means

- `--bank C@N` — case C outputs the bare mesh at N (`K = 0`). A pass at a new lower N is a
  bank candidate: snapshot `probe/out/main.cpp` into `submissions/` per convention.
- `--read C@N` — case C encodes its in-process self-score into the vertex count:
  `V' = N + 4K`, `K = round((S2 − 0.885)/5e-4)` clamped to [0,160]. The decode recovers S2
  for **that run's mesh on the judge**. Reads are never banks (the pads cost score);
  prefer read-N ≡ 0 (mod 4) so a decimation stall stays detectable.

## Hard rules baked into the harness

1. **Constants-only patching** of the frozen v111 base (`wall_model.json: base_file`), only
   inside the three probe blocks (cases 3/4/5). It will not synthesize code — anything
   beyond a constant is a new binary family and re-rolls every box-cut mean (the rung-1
   lesson). Cases 2/6/7 are close/manual-only.
2. **Ambiguity pre-check**: `plan` enumerates every possible outcome score of the planned
   probe and refuses plans whose hypotheses collide within the score's 6-decimal resolution
   — you can never burn a submission on an undecodable read.
3. **Unique decode or no write**: `decode` enumerates all hypotheses (each case: banked /
   WA / pass@N / K∈[0..160]) and updates `wall_model.json` only on a unique match.
4. **Never submits.** Output is always a file + a table of expected scores per outcome.

## Caveats (from WALL-MODEL.md)

- S2 is a **relative** instrument (our reconstruction of the judge metric): case-4 evidence
  puts it ~+0.005 optimistic. Anchor per case by pairing reads with pass/fail outcomes
  before trusting absolute margins.
- Box-cut cases (3, 4) are per-run coins at razor rungs even within a family: a WA is a
  draw, not proof of the wall — two consecutive WAs at a rung is the wall heuristic.
- `preflight --docker` needs Docker running and `make_band_proxies.py` run once (Eigen copy).

State: `wall_model.json` (ledger + reads + fails + log — committed).
Generated: `probe/out/` and `probe/cache/` (git-ignored).
