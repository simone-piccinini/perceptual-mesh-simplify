# IMC 2026 — Problem B
## Perception-Aware Simplification of Million-Vertex 3D Meshes for Mobile Platforms

> One-line summary: given a high-poly **closed watertight triangle mesh**, output a mesh with **as few vertices as possible** that still looks visually identical from 6 fixed cameras (multi-view **normal + depth SSIM ≥ 0.9**) and stays geometrically/topologically valid.

---

## 1. Goal & scoring at a glance

| Aspect | Value |
|---|---|
| **Objective** | Minimize the simplified vertex count `V'` (≡ maximize compression rate) |
| **Hard validity gate** | `FinalSSIM ≥ 0.9` (else the test case scores **0**) |
| **Per-case score** | `compression = 100·(1 − V'/V)` |
| **Final score** | Arithmetic mean of per-case scores over all test cases |
| **Other hard constraints** | Manifold + watertight, non-degenerate faces, valid indices, symmetric Hausdorff ≤ 5% of bbox diagonal |

The title says "lossless," but the task is really **perception-preserving lossy** simplification: you may change geometry freely as long as the perceptual score and the constraints hold.

---

## 2. The evaluator — "Standardized Virtual Photography"

The judge renders both the original `M` and your `M'` from **6 fixed cameras**, builds 2 feature images per view, and compares them with SSIM.

### Camera setup
- Input mesh is **pre-normalized**: centered at the origin, lies inside the unit sphere (`‖v‖ ≤ 1`).
- 6 viewpoints at fixed distance **D = 2.5**, one per signed axis:
  `(±D,0,0), (0,±D,0), (0,0,±D)`, each looking at the origin.
- Camera looks down its **−Z axis** (OpenGL convention). Rendered directly at distance `D`, no extra scaling/recentering → the frame is identical every time.

### Perspective projection
For a camera-space vertex `(x, y, z)`:
```
u = f_x · (x/z) + c_u
v = f_y · (y/z) + c_v
```
- Focal length `f_x = f_y = 800.0` px
- Principal point `(c_u, c_v) = (512, 512)`
- **Resolution: 1024 × 1024** per image

### Two feature maps per view

**(a) Normal map — light/shadow undulation**
- **Flat shading**: every pixel of a triangle gets that face's single unit normal (no per-vertex normals, no interpolation).
- Encode to RGB: `I_N(P) = (n_p + [1,1,1]ᵀ) × 127.5`, mapping each component from `[-1,1]` → `[0,255]`.
- **Background** (no triangle): normal `(0,0,0)` → neutral gray `(127.5, 127.5, 127.5)`.

**(b) Depth map — contour / occlusion**
- Stores camera-axis depth `z`, **perspective-correct** interpolated across the triangle.
- The screen-linear quantity is `1/z`, so:
  ```
  z_P = 1 / ( w0/z0 + w1/z1 + w2/z2 )
  ```
  where `w0,w1,w2` are barycentric weights (`w0+w1+w2 = 1`).
- **Background** depth `z_b = 255` (far plane).

Each pixel is sampled **once at its center `(u+0.5, v+0.5)`**, covered by the nearest triangle whose projection contains that point (standard z-buffer).

---

## 3. Scoring formula

### SSIM (standard)
- `11 × 11` sliding window, constants `k1 = 0.01`, `k2 = 0.03`, `L = 255`.
- `c1 = (k1·L)²`, `c2 = (k2·L)²`.
- `SSIM(X,Y) = [(2μ_Xμ_Y + c1)(2σ_XY + c2)] / [(μ_X²+μ_Y²+c1)(σ_X²+σ_Y²+c2)]`, output in `[0,1]`.
- For the **RGB normal map**, SSIM is computed per channel and averaged.

### Foreground-only averaging (important nuance)
A window contributes to the mean **iff its center pixel is non-background in the original OR the simplified rendering**. Windows that are background in **both** are excluded. → empty space around the object doesn't inflate the score; only the silhouette + surface matters.

### FinalSSIM
```
FinalSSIM = average over 6 views of [ ω_N · SSIM(normal) + ω_D · SSIM(depth) ]
ω_N = ω_D = 0.5
```
Valid submission requires **FinalSSIM ≥ 0.9**.

---

## 4. Constraints

### Mesh validity (topology)
- `1 ≤ V' ≤ V` (`V'=0` or `V'>V` ⇒ rejected).
- **Manifold**: every edge shared by exactly 2 triangles; closed, watertight 2-manifold.
- **Non-degenerate**: all faces have strictly positive area.
- **Valid indices**: face indices within the vertex array range.

### Geometric deviation (symmetric Hausdorff)
```
d_H(M, M') = max( d→(M,M'), d→(M',M) ) ≤ 5% × Diagonal
d→(A,B) = max_{a∈A} min_{b∈B} ‖a − b‖
Diagonal = sqrt(Lx² + Ly² + Lz²)   (original AABB edge lengths)
```
Normalizes tolerance to **5% of mesh size**, independent of scale. Direction 1 keeps every original vertex covered; direction 2 forbids simplified vertices from drifting off the original surface.

---

## 5. Input / Output (modified OBJ over stdin/stdout)

**Input**
- Line 1: integers `V F` (`1 ≤ V ≤ 1.1·10⁶`, `1 ≤ F ≤ 2.1·10⁶`).
- `V` lines: `v x y z` — `−1 ≤ x,y,z ≤ 1`, inside unit sphere, ≤ 15 decimals; bbox centered at origin.
- `F` lines: `f v1 v2 v3` — **1-indexed** triangle.
- Guaranteed: closed watertight connected 2-manifold, non-degenerate faces, no duplicate vertices/faces.

**Output**
- Same format. Must be **manifold**, **no zero-area faces**, total ≤ **100 MiB** (limit your printed decimals on large meshes).

**Provided tooling**
- `baseline.cpp` / `baseline.py` for fast I/O (modifiable / optional).
- **Eigen 5.0.0** available for C++ (`#include "Eigen/Dense"`); no need to submit Eigen files.

---

## 6. Test cases (per-case size bounds)

| Case | `V ≤` | `F ≤` |
|---|---:|---:|
| 1 (sample) | 10 | 15 |
| 2 | 5,000 | 10,000 |
| 3 | 25,000 | 50,000 |
| 4 | 40,000 | 80,000 |
| 5 | 50,000 | 100,000 |
| 6 | 400,000 | 800,000 |
| 7 | 1,100,000 | 2,100,000 |

The sample earns no points; cases 2–7 score. Note the spread: most cases are small-to-mid, with case 7 being the only true million-vertex stress test.

### Sample walkthrough
A unit cube (8 corners) plus one **redundant coplanar vertex** (`v 0.5 0.49 0.49`) splitting the right face into extra triangles. Removing it → 8 vertices / 12 faces, identical normals & depth ⇒ `FinalSSIM = 1`, compression `= 100·(1 − 8/9) ≈ 11.11`.

---

## 7. Analysis & strategy notes

**What the metric rewards**
- The score is **perceptual, not geometric deviation**. Large **coplanar / low-curvature regions** can be decimated almost for free: flat shading means identical face normals, and depth varies smoothly → SSIM barely moves.
- **Silhouette / contour edges** (depth map) and **normal-discontinuity edges / sharp creases** (normal map) are the expensive places — collapsing them changes pixels and tanks SSIM.
- Only **6 axis-aligned views** are scored. Detail invisible from all six axes is cheap to remove — but the **Hausdorff ≤ 5% diagonal** constraint still forces global fidelity, so you can't hollow out hidden cavities arbitrarily.

**Which constraint binds**
- `FinalSSIM ≥ 0.9` is almost certainly the **binding** constraint; Hausdorff (5% of diagonal) is comparatively loose. But manifold-preservation is a hard structural gate you cannot violate even once.

**Likely approach**
1. **QEM edge-collapse decimation** (Garland–Heckbert quadric error metric) as the core engine — fast, quality-aware, scales to millions of faces.
2. Restrict to **manifold-preserving collapses** (check link/2-manifold conditions; reject collapses that create non-manifold edges, flips, or degenerate faces).
3. Weight the quadric / collapse cost to **protect normal-discontinuity and silhouette-relevant edges** (curvature- or normal-aware error), so flat regions go first.
4. **Reimplement the evaluator locally** (6-view normal+depth rasterizer + the exact SSIM with foreground masking) as an oracle, then **binary-search the decimation target** to find the minimum `V'` keeping `FinalSSIM ≥ 0.9` with a safety margin.
5. Verify Hausdorff and manifoldness before emitting; trim printed decimals to respect the 100 MiB cap on the big cases.

**Gotchas to match the judge exactly**
- OpenGL **−Z** camera convention; `f = 800`, `1024²`, principal point `(512,512)`.
- **Perspective-correct** depth via `1/z` interpolation (not linear `z`).
- Pixel sampled at **center `+0.5`**; background normal = gray `127.5`, background depth = `255`.
- Foreground SSIM masking rule (window counted if non-background in original **or** simplified).
- Normal-map SSIM averaged over the **3 channels**; final = mean over 6 views of the `0.5/0.5` normal/depth blend.
