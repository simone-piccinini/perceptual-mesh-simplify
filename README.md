# IMC 2026 — Problem B: Mesh Simplification

> **New here? Read in this order:** [`STATUS.md`](STATUS.md) (where we are now) →
> [`CLAUDE.md`](CLAUDE.md) (how to work without hallucinating) →
> [`docs/JUDGE-ENVELOPE.md`](docs/JUDGE-ENVELOPE.md) (measured judge facts) →
> [`docs/ROADS.md`](docs/ROADS.md) (what to try) → [`docs/THEORY.md`](docs/THEORY.md) /
> [`docs/WALL-MODEL.md`](docs/WALL-MODEL.md) (the math). **The authoritative score is on Kattis,
> never a local file** (`submissions.jsonl` is a partial ledger — it misses web-UI submits).

Tooling for the contest *Perception-Aware Simplification of Million-Vertex 3D
Meshes*. The goal: simplify a mesh to the fewest vertices possible while the
judge's multi-view perceptual score stays `FinalSSIM >= 0.9` and the mesh stays
a valid closed 2-manifold within 5% Hausdorff of the original.

The repo has two halves. The **C++ solver** in `solver/` is the single file that
is actually uploaded to the judge. The **local evaluator (oracle)** in
`src/imc_eval/` is a faithful, offline reimplementation of the judge's metric,
used to check validity and score candidates without spending submissions. Both are
mature: `solver/main.cpp` is the banked decimation solver (all 7 cases green, bank
on Kattis — see `STATUS.md`), and `solver/main_v2.cpp` is an independent
construction/carve solver (~90.24). Per-case state lives in `STATUS.md`; the
current bank number lives in `STATUS.md` and on Kattis, nowhere else.

> ⚠ **Read the oracle correctly.** The metric MATH is judge-exact (validated,
> ENVELOPE §7.1: no bias). But the judge INPUT meshes are hidden — our local
> *proxies* (armadillo-derived) are NOT the judge's meshes, and they are measurably
> **too smooth**, so position-space A/B gains transfer to the judge at ratio ≈ 0
> (ENVELOPE §9.1). Local numbers decide **validity and vertex counts**, never
> judge pass/fail. This is the single most expensive lesson in the project.

## Why an oracle first

The judge's metric is fully specified and deterministic, so we can reproduce its
math locally and iterate against our own copy of the scorer. Every algorithm
decision that concerns *validity* (manifold, indices, Hausdorff, vertex count)
depends on being able to measure it ourselves. What the oracle CANNOT do is
predict the judge's pass/fail on the hidden inputs (see the warning above).

## Layout

```
solver/           C++ — the submission (the single file uploaded to the judge)
  main.cpp        banked decimation solver (VSA-lite ordering + QEM + s-def steering + refine)
  main_v2.cpp     independent construction/carve solver (see docs/V2-CONSTRUCTION.md)
                  Eigen is provided by the judge; vendor it locally for dev builds
src/imc_eval/     Python — the oracle (metric truth + validation), local only
  geometry.py   fixed camera constants, face normals, AABB diagonal, 6 views
  render.py     z-buffered rasteriser -> normal map + depth map (+coverage)
  ssim.py       11x11 BOX-window SSIM with foreground-union averaging
  validity.py   vertex count / indices / non-degenerate / closed-2-manifold
  hausdorff.py  symmetric Hausdorff — computes point-to-SURFACE (deliberately
                STRICTER than the judge's vertex-to-vertex; see "Judge calibration")
  score.py      evaluate(Vo,Fo,Vs,Fs) -> Report (FinalSSIM, compression, pass)
  obj_io.py     read/write the modified-OBJ format
  cli.py        `imc-score` command
scripts/          Python — dev harness (judge_submit.py, validate_oracle.py, judge_audit.py, ...)
probe/            the plan->preflight->submit->decode wall-probing harness (harness.py)
tests/data/       sample.in/out + proxy meshes (armadillo/bunny/cow/fandisk)
docs/             JUDGE-ENVELOPE (facts) · THEORY (math) · WALL-MODEL (walls/S-read) ·
                  ROADS (what to try) · SOLVER-INTERNALS / V2-CONSTRUCTION (code maps) ·
                  postmortems/ (what failed & why). See docs/README.md for the index.
handoff/          ATTEMPT_LOG.md (human narrative) · submissions.jsonl (partial ledger)
submissions/      current/ (<=5 live snapshots); archive/ for the rest
```

## Setup

One command builds and verifies everything (Python oracle + C++ solver + Eigen):

```bash
./scripts/setup.sh
```

It creates `.venv` (numpy/scipy, plus numba where wheels exist), installs/locates
Eigen and symlinks it next to `solver/main.cpp`, compiles the solver, and runs the
oracle self-check. Supports macOS (Homebrew) and Linux (`libeigen3-dev`).

<details><summary>Or set it up manually</summary>

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .                                     # numpy + scipy (+ numba where wheels exist)
brew install eigen                                   # macOS; Linux: apt-get install libeigen3-dev
ln -sfn "$(brew --prefix eigen)/include/eigen3/Eigen" solver/Eigen
g++ -O2 -std=c++17 solver/main.cpp -o solver/main
```
</details>

`numba` is optional — it JIT-accelerates the rasteriser. If it isn't installed
the renderer falls back to pure Python: correct, just slower.

## Use

Validate the oracle is wired correctly:

```bash
python scripts/validate_oracle.py
# expect: identity -> SSIM 1.0 / 0%, sample -> SSIM ~1.0 / 11.11% / PASS
```

Score a simplified mesh against the original (validity + FinalSSIM math, NOT a judge pass/fail oracle):

```bash
imc-score --input mesh.in --output mesh.out
```

## Judge calibration — SETTLED (do not re-open these; they cost submissions to close)

The statement pins the pipeline (1024×1024, f=800, principal point (512,512), D=2.5,
flat per-face normals, `(n+1)·127.5` encoding, perspective-correct `1/z` depth,
pixel-centre `+0.5` sampling, SSIM k1=0.01/k2=0.03/L=255, foreground masking). The
few under-specified details are now **measured**, not assumed — full record in
[`docs/JUDGE-ENVELOPE.md`](docs/JUDGE-ENVELOPE.md):

1. **Metric calibration: NO bias** `[JUDGE §7.1]`. The judge PASSED the exact
   simplified mesh our in-process scorer self-scored at S=0.910, proving oracle
   FinalSSIM ≈ judge FinalSSIM on the same mesh. So normal-space (world), depth
   scaling, and the SSIM window are all effectively pinned — the earlier
   "under-specified, file a Clarification" notes are **resolved**.
2. **SSIM window is a BOX (uniform), not Gaussian** `[INFERRED, decisive]`. A
   Gaussian window would misread the operating point by ~0.047. The oracle uses the
   box window; anything Gaussian lies.
3. **Hausdorff is VERTEX-TO-VERTEX, ≤5% of the AABB diagonal** `[OFFICIAL
   clarification 2026-06-18]`: *"a and b vary across vertices ... we do not iterate
   over interior or surface points."* Faces (the surface) carry NO geometric
   constraint. ⚠ Our `hausdorff.py` computes point-to-**surface**, which is
   deliberately **STRICTER** than the judge — a conservative safety margin, NOT a
   match. In practice v2v Hausdorff is loose and never binds at our operating
   points. Do not spend effort treating it as active. (The forward direction —
   every original vertex needing a nearby output vertex — could start to bind only
   if a future mechanism pushes case-3 much further; see ARCHITECT-REVIEW §6
   runner-up.)

**Bottom line:** the metric is trusted; the *proxy meshes* are not. See the oracle
warning at the top and `docs/JUDGE-ENVELOPE.md §7.2` for what local tests are worth.
