# IMC 2026 — Problem B: Mesh Simplification

Tooling for the contest *Perception-Aware Simplification of Million-Vertex 3D
Meshes*. The goal: simplify a mesh to the fewest vertices possible while the
judge's multi-view perceptual score stays `FinalSSIM >= 0.9` and the mesh stays
a valid closed 2-manifold within 5% Hausdorff of the original.

This repo currently contains the **local evaluator (oracle)** — a faithful,
offline reimplementation of the judge so we can score candidate simplifications
without spending submissions. The simplification algorithm itself comes next.

## Why an oracle first

The judge is fully specified and deterministic, so we can reproduce its number
locally and iterate against our own copy of the scorer. Every algorithm
decision depends on being able to measure the score ourselves.

## Layout

```
src/imc_eval/
  geometry.py   fixed camera constants, face normals, AABB diagonal, 6 views
  render.py     z-buffered rasteriser -> normal map + depth map (+coverage)
  ssim.py       11x11 box-window SSIM with foreground-only averaging
  validity.py   vertex count / indices / non-degenerate / closed-2-manifold
  hausdorff.py  symmetric Hausdorff (v1: vertex-based approximation)
  score.py      evaluate(Vo,Fo,Vs,Fs) -> Report (FinalSSIM, compression, pass)
  obj_io.py     read/write the modified-OBJ format
  cli.py        `imc-score` command
scripts/
  validate_oracle.py   self-check against identity + the sample case
tests/data/     sample.in, sample.out (the cube from the statement)
baseline/       provided I/O scaffold (baseline.cpp)
notes/          problem analysis
```

## Setup

```bash
cd imc-mesh-simplify
python3 -m venv .venv
source .venv/bin/activate
pip install -e .          # numpy + scipy (+ numba where wheels exist)
```

`numba` is optional — it JIT-accelerates the rasteriser. If it isn't installed
(e.g. no wheel for your Python yet) the renderer falls back to pure Python:
correct, just slower, which is fine for the small/medium cases.

## Use

Validate the oracle is wired correctly:

```bash
python scripts/validate_oracle.py
# expect: identity -> SSIM 1.0 / 0%, sample -> SSIM ~1.0 / 11.11% / PASS
```

Score a simplified mesh against the original:

```bash
imc-score --input mesh.in --output mesh.out
# or: python -m imc_eval.cli --input mesh.in --output mesh.out
```

## Known calibration gaps

The statement pins most of the pipeline (1024x1024, f=800, principal point
(512,512), D=2.5, flat per-face normals, `(n+1)*127.5` encoding, perspective-
correct `1/z` depth, pixel-centre `+0.5` sampling, SSIM k1=0.01/k2=0.03/L=255,
foreground masking). A few details are under-specified and are implemented to
the most literal reading; verify against the sample and, where needed, file a
platform Clarification:

1. **Depth-map scaling.** We store raw camera-space depth (object ~1.5–3.5)
   with background = 255, per the literal text. If the judge normalises depth
   into [0,255] differently, depth SSIM near the 0.9 boundary will drift.
2. **Normal space.** We use world-space face normals (view-independent), as the
   statement describes a single per-face normal. View-space is the alternative.
3. **Hausdorff.** v1 is vertex-to-vertex (KD-tree), not point-to-surface.
   Conservative and loose; upgrade to surface sampling if it ever binds.

These do not affect the *identity* and *sample* checks (both meshes are rendered
with the identical pipeline), so those validate the machinery, not the absolute
calibration of items 1–2.
