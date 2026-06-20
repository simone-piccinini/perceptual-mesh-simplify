# `imc_eval` — file guide

The offline reimplementation of the judge, one responsibility per file.

| File | What it does |
|---|---|
| `geometry.py` | The judge's fixed setup: the pinned camera constants (1024×1024, focal 800, D = 2.5, six axial views) and basic mesh geometry (face normals, bbox diagonal). |
| `render.py` | Turns a 3D mesh (vertices + triangles) into flat 2D images — a normal map and a depth map — exactly like photographing it from each camera. |
| `ssim.py` | Grades how different two images are *the way human eyes do* (structural similarity, foreground only). |
| `hausdorff.py` | Measures how far apart two meshes are in 3D space (the geometric-deviation check). |
| `validity.py` | All the pass/fail structural checks: vertex count, valid indices, no degenerate faces, closed 2-manifold. |
| `score.py` | The orchestrator: runs render → SSIM → Hausdorff → validity and reports FinalSSIM, compression, and pass/fail. |
| `obj_io.py` | Reads and writes the mesh files (the modified-OBJ input/output format). |
| `cli.py` | Command-line front end (`imc-score`) so we can test a mesh from the terminal. |
