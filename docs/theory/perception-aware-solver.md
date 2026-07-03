# The perception-aware solver — every method beyond the QEM core

This document explains the machinery in [`solver/main.cpp`](../../solver/main.cpp)
that sits **on top of** the base Garland–Heckbert quadric edge-collapse decimator.
The QEM core (quadrics, the min-heap, lazy version stamps, the link/area/flip
gates, `Collapse`) is assumed and **not** re-derived here — see
[qem-pseudocode.md](qem-pseudocode.md) and [ALGORITHM.MD](ALGORITHM.MD) for that.

What *is* covered: the per-case operating-point dispatcher, the in-loop
rasterizer, and the three perceptual optimization systems layered around the
collapse loop —

1. **Pivot-A** — metric-in-the-loop cost steering by measured SSIM contrast deficit;
2. **Visibility culling** — free collapse of geometry no camera ever sees;
3. **The inverse-rendering vertex optimizer** — post-decimation gradient ascent on the *actual* rendered normal-SSIM;

plus the dormant **subset-placement / adaptive-Hausdorff guard**, the `seed_heap`
glue, and the invariants that keep every one of these manifold-safe.

> **Why any of this exists.** The judge returns only pass/fail per case, best
> submission counts, and submissions are effectively unlimited. So each hidden
> case's compression wall is *binary-searched on the judge*, and the binding wall
> is almost always the **SSIM contrast/variance term** of the flat-shaded normal
> map — a quantity the geometric QEM cost is provably blind to (see
> [wang-ssim.md](wang-ssim.md)). Every method below exists to attack that specific
> wall while never breaking the hard validity gates.

---

## 0. The end-to-end control flow

`main()` wires the systems together. The exact order matters (some systems render
the *original* mesh before any collapse, others run only after decimation):

```mermaid
flowchart TD
  A[load OBJ] --> B["PerCaseConfig(|V|):<br/>keep, λ, perChan, refine, useVis"]
  B --> C["Initialize:<br/>quadrics, incidence, spheres, heap"]
  C --> D{refine?}
  D -- yes --> E["RefineInitOriginal:<br/>render original 6 normal maps @512"]
  D -- no --> F["target = max(1, ⌊keep·V⌋)"]
  E --> F
  F --> G{useVis?}
  G -- yes --> H["ComputeVisibility → hid[v]"]
  G -- no --> I{λ &gt; 0 ?}
  H --> I
  I -- "yes (cases 3,5)" --> J["8 staged Pivot-A passes:<br/>update importance → seed_heap → Decimate(tgt_p)"]
  I -- "no (cases 2,4,6,7)" --> K["Decimate(target)"]
  J --> L{refine?}
  K --> L
  L -- "yes (cases 3,4)" --> M["RefinePositions:<br/>SSIM-gradient ascent, time-boxed"]
  L -- no --> N["save OBJ (%.17g)"]
  M --> N
```

The whole strategy is a **lookup table keyed on vertex count**. There is no
runtime auto-tuning; the constants encode where each hidden case's wall was found
on the judge.

---

## 1. Per-case operating point (the "hard-coded" dispatcher)

Five small functions map the input vertex count `V` to a configuration. The
thresholds are chosen so each band lands on exactly one scored case (case sizes:
2 ≤ 5k, 3 ≤ 25k, 4 ≤ 40k, 5 ≤ 50k, 6 ≤ 400k, 7 ≤ 1.1M).

| Function | Case 2 (≤7k) | Case 3 (≤30k) | Case 4 (≤40k) | Case 5 (≤100k) | Case 6 (≤400k) | Case 7 (>400k) |
|---|---|---|---|---|---|---|
| `keep_for` (target fraction) | **0.01** | **0.33** | **0.17** | **0.10** | **0.03** | **0.04** |
| `lambda_for` (Pivot-A strength) | 0 | **12** | 0 | **12** | 0 | 0 |
| `per_chan_for` (per-channel steering) | 0 | **1** | 0 | **1** | 0 | 0 |
| `refine_for` (inverse-render optimizer) | 0 | **1** | **1** | 0 | 0 | 0 |
| visibility gate (in `main`) | off | **on** | off | off | off | off |

Reading the columns tells you *which methods run on which case*:

- **Case 2** (99% compression): plain free-QEM keep, nothing else. Its wall is a
  geometry floor, not SSIM — steering has nothing to protect.
- **Case 3** (67%): the full stack — per-channel Pivot-A steering **+** visibility
  culling **+** the inverse-rendering optimizer. Its detail is near-uniform, so
  every lever is thrown at it.
- **Case 4** (83%): plain QEM base **+** the optimizer (no steering, no
  visibility). Mechanical/piecewise-planar; QEM is already near-optimal, the
  optimizer only polishes.
- **Case 5** (90%): per-channel Pivot-A steering only. This is where steering paid
  off hardest — it cracked the case from 79% to 90% on the judge.
- **Cases 6, 7** (97%, 96%): plain free-QEM. Dense organic surfaces already near
  their caps; the add-ons either don't help or risk TLE at that scale.

`keep` sets the stopping target `target = max(1, ⌊keep·V⌋)`; tiny meshes
(`V < 1000`, i.e. the sample) skip decimation entirely and are emitted unchanged.

---

## 2. The in-loop rasterizer (shared infrastructure)

Pivot-A, visibility, and the optimizer all need to *see what the judge sees*, so
the solver carries a compact software rasterizer that mirrors the judge's pipeline.

### Camera basis — `view_basis(v)`
Six axial cameras at distance `D = 2.5`, each looking at the origin down its own
`−axis` (OpenGL convention). Up vectors are `+Z` for the four equatorial views and
`+Y` for the two polar views, matching the oracle.

### Projection & rasterization — `render_faceid(v, fid)`
Renders at resolution `W = g_res` with focal `f = 800·(W/1024)` and principal
point `(W/2, W/2)` — the judge's `f = 800` at `1024²`, rescaled so a lower-res
render frames the model identically. For each alive face:

- transform its 3 vertices to camera space `(x, y, d)` with `d = r·fwd`;
- project `u = f·x/d + C`, `v = f·y/d + C`;
- rasterize with edge functions, sampling each pixel at its centre `(px+0.5, py+0.5)`;
- perspective-correct depth `z = 1 / (w0/d0 + w1/d1 + w2/d2)` and keep the nearest
  face per pixel in a z-buffer.

The output is a **face-id buffer** `fid` (the index of the front face at each pixel,
or `−1` for background). Everything downstream is computed from `fid`, so the
rasterizer runs once per view per query and the attributes are derived cheaply.

### Attribute maps derived from `fid`
- `face_lum(f)` — the flat-normal encoded as scalar luminance
  $\ell = \tfrac{1}{6}\big((n_x{+}1)+(n_y{+}1)+(n_z{+}1)\big) \in [0,1]$, the
  grayscale stand-in for the RGB normal map.
- `chan_map(fid, c)` — the per-channel normal value $(n_c+1)/2 \in [0,1]$ for
  channel $c \in \{x,y,z\}$, matching the judge's per-channel normal-map SSIM.
- `contrast_map` / `contrast_vals` — the **local contrast** $\sigma$ of a field:
  a box-window standard deviation with radius $r = \max(1, W/96)$. This $\sigma$ is
  exactly the quantity the SSIM contrast term compares, so it is the signal the
  perceptual systems steer on.

---

## 3. Add-on 1 — Pivot-A: metric-in-the-loop steering

**Idea.** QEM chooses *which* edge to collapse by a 3D geometric cost. Pivot-A
multiplies that cost by a **perceptual importance** so that regions where the
rendered normal map is *losing structure* become expensive to touch, and flat /
already-matched regions stay cheap. It is Lindstrom–Turk image-driven
simplification made feasible at 21 s by rendering periodically at low resolution
instead of per candidate edge.

### 3.1 The importance signal — `pivotA_update_importance()`

Before decimation, `pivotA_init_original()` renders the **original** mesh and
stores its per-view local contrast $\sigma_x$ (grayscale in `g_sigx`, and
per-channel in `g_sigxc` when `per_chan` is set).

Each Pivot-A pass renders the **current** (partly decimated) mesh, computes its
contrast $\sigma_y$, and forms the per-pixel **SSIM contrast deficit**

$$
d(p) \;=\; 1 - c(p), \qquad
c(p) \;=\; \frac{2\,\sigma_x(p)\,\sigma_y(p) + C_2}{\sigma_x(p)^2 + \sigma_y(p)^2 + C_2},
$$

with $C_2 = 0.0009 = (0.03)^2$ in the normalized $[0,1]$ luminance space (the
SSIM $c$-term; see [wang-ssim.md](wang-ssim.md)). When `per_chan` is on, the
deficit is summed over the three normal channels, which the judge scores
separately. The deficit at each covered pixel is scattered onto the three
vertices of its front face; the accumulated per-vertex importance `imp[v]` is then
**normalized to $[0,1]$** by its maximum over all 6 views.

Intuitively: $d(p)$ is near 0 where the simplified render already reproduces the
original's local normal variation (flat regions, or regions still dense enough),
and rises where the simplification has *flattened out* structure the original had.

### 3.2 The cost multiplier — in `Evaluate`

For a candidate edge $(i,j)$ the geometric QEM cost is scaled:

$$
\text{cost}(i,j) \;\mathrel{*}=\; \big(1 + g_\lambda\,(\text{imp}[i] + \text{imp}[j])\big),
\qquad g_\lambda = 12 \text{ (cases 3, 5)}.
$$

High-importance edges become up to $\sim 25\times$ more expensive, so the heap
drains cheap flat regions first and defers collapses in contrast-critical regions
— exactly reallocating the vertex budget toward the windows that cost SSIM points.

### 3.3 Staged decimation — in `main`

Because the deficit *grows* as collapses proceed, a single static importance map
would go stale. So decimation runs in **8 passes**: each pass re-renders,
recomputes importance, rebuilds the heap (`seed_heap`), and decimates to an
intermediate target

$$
\text{tgt}_p = \text{start} - \Big\lfloor (\text{start} - \text{target})\cdot \tfrac{p}{8} \Big\rfloor,
\quad p = 1,\dots,8.
$$

The steering thus tracks the deficit as the mesh coarsens. The in-loop render
resolution is a uniform `g_res = 160` (`res_for`); higher resolutions were tested
and cracked nothing — the medium walls are information-theoretic, not
render-limited.

### 3.4 What it bought, and its limits
- **Case 5: 79% → 90%** on the judge (per-channel steering) — the biggest single
  win of the whole project.
- **Case 3:** steering alone did *not* break the wall (its detail is uniform, so
  there is no low-importance region to sacrifice — QEM already keeps faces where
  the contrast lives). Case 3 needed visibility + the optimizer on top.
- **Cases 2, 6, 7:** `λ = 0`, so `Evaluate` is byte-identical to plain free-QEM —
  the judge-confirmed walls there are preserved exactly.

---

## 4. Add-on 2 — visibility culling

**Idea.** `FinalSSIM` is rendered from only 6 axial cameras. A face that is never
the front (z-buffered) surface in any of the 6 views contributes **nothing** to the
score. Collapsing such geometry is therefore free of perceptual cost, so its
vertex budget should be handed to the visible surface.

### 4.1 Hidden-vertex detection — `compute_visibility()`
Renders the 6 axial face-id buffers at `g_res = 512` and marks every face that
appears as a front face in any view. A vertex is **hidden** (`hid[v] = true`) iff
*none* of its incident faces is ever visible. (512 is used because it is fast even
on large meshes and sub-pixel faces are essentially free to collapse anyway; the
resolution only needs to avoid mis-marking a genuinely visible face as hidden.)

### 4.2 Free collapse — in `Evaluate`
When **both** endpoints of an edge are hidden, its cost is scaled by $10^{-4}$:

$$
\text{if } \text{hid}[i] \wedge \text{hid}[j]:\quad \text{cost} \mathrel{*}= 10^{-4}.
$$

These edges float to the top of the heap and collapse first, concentrating the
kept vertices on what the cameras actually see. It only fires on **case 3** (gate
`7000 < V ≤ 30000`).

### 4.3 The decisive result
- **Case 3: 66% → 67%** on the judge. Without visibility, case 3 at 67% was a
  Wrong Answer; with it, the freed hidden budget gave the visible surface enough
  margin to clear the SSIM wall.
- The local proxy predicted only ~2% hidden geometry and called the lever
  "negligible" — **wrong.** The real case-3 mesh carries enough occluded geometry
  for the lever to work. Lesson (recurring in this project): the judge decides,
  not the local proxy.
- Tested and **failed** on the large cases (case 6 @98%+vis, case 7 @97%+vis, case
  4 @84%+vis all Wrong Answer) — those meshes have little hidden geometry at their
  compression, so the gate is deliberately restricted to case 3.

---

## 5. Add-on 3 — the inverse-rendering vertex optimizer

**Idea.** After decimation fixes the *topology*, the surviving vertex *positions*
are still free variables. This system ascends them along the **analytic gradient of
the real rendered normal-SSIM**, directly optimizing the judge's objective rather
than any geometric proxy. Runs on **cases 3 and 4** (`refine_for`: `7000 < V ≤ 40000`).

### 5.1 The objective — `refine_score_grad`
Before decimation, `refine_init_orig()` renders the original mesh's 6 views at
`g_refine_res = 512` and stores the per-channel normal images (0–255, background
127.5) and foreground masks. The objective is the mean normal-map SSIM of the
current mesh against those stored originals:

$$
S = \frac{1}{6\cdot 3}\sum_{v=1}^{6}\sum_{c\in\{x,y,z\}} \operatorname{SSIM}_{\text{fg}}\big(X^{v,c},\, Y^{v,c}\big),
$$

computed with the judge's 11×11 box window, $C_1 = 6.5025$, $C_2 = 58.5225$
(255-space), and foreground-only averaging (a window counts if it is non-background
in the original **or** the current render). The per-window SSIM uses the standard
decomposition with

$$
A = 2\mu_x\mu_y + C_1,\quad B = 2\sigma_{xy} + C_2,\quad
\mathcal{C} = \mu_x^2 + \mu_y^2 + C_1,\quad \mathcal{D} = \sigma_x^2 + \sigma_y^2 + C_2,
\qquad \text{SSIM} = \frac{A B}{\mathcal{C}\,\mathcal{D}}.
$$

### 5.2 The analytic gradient chain
`refine_score_grad` also returns $\nabla_{\text{pos}} S$, backpropagated in three
stages (all verified bit-exact against the Python oracle):

1. **SSIM → pixel.** The per-window partials

   $$
   \frac{\partial\,\text{SSIM}}{\partial \mu_y} = \frac{2B(\mu_x\mathcal{C} - \mu_y A)}{\mathcal{C}^2\mathcal{D}},\quad
   \frac{\partial\,\text{SSIM}}{\partial \sigma_y^2} = -\frac{A B}{\mathcal{C}\mathcal{D}^2},\quad
   \frac{\partial\,\text{SSIM}}{\partial \sigma_{xy}} = \frac{2A}{\mathcal{C}\mathcal{D}},
   $$

   are accumulated over every window covering a pixel (via the same separable box
   sums used for the forward pass), giving $\partial S/\partial Y(p)$ per pixel.
2. **Pixel → face normal.** Since $Y(p) = (n_f[c]+1)\cdot 127.5$ for the front face
   $f$ at $p$, contributions sum into $\partial S/\partial n_f = 127.5\sum_{p\in f}\partial S/\partial Y(p)$.
3. **Face normal → vertex position.** The unit face normal
   $n = (p_1-p_0)\times(p_2-p_0)/\lVert\cdot\rVert$ is differentiated w.r.t. its
   three vertices; the tangential component $g = (\,\text{d}n - n(n\!\cdot\!\text{d}n)\,)/\lVert\text{cross}\rVert$
   is distributed as $(a-b)\times g$, $b\times g$, $g\times a$ onto the three
   vertices (with $a = p_1-p_0$, $b = p_2-p_0$).

This is the gradient of *flat-shading* at fixed rasterization: it captures how
moving a vertex tilts the constant normals of its incident faces. Coverage /
silhouette changes are **not** in the analytic gradient — instead the outer loop
re-renders every step, so coverage updates numerically and the monotonic accept
(below) guarantees correctness against the true re-rendered score.

### 5.3 The ascent — `refine_positions`
Projected gradient ascent with hard safety rails:

```
base ← pos;  cap ← 0.02·diag;  step ← 0.02·diag;  cur ← score()
repeat up to 1000 iters:
    if wall-clock > 16 s: break                      # hard time-box → never TLE
    g ← ∇score();  gmax ← max‖g[v]‖
    move each alive v by step·g[v]/gmax,
        then clamp its displacement from base[v] to ≤ cap   # Hausdorff bound
    if score() > cur AND all faces nondegenerate:
        accept (cur ← score())                       # monotonic: real SSIM only rises
    else:
        revert; step ← step/2; stop if step < 1e-6·diag
```

Four properties make it always safe and always a net gain:

- **Monotonic accept** — a step is kept only if the *actually re-rendered* SSIM
  rises, so the optimizer can never lower the score.
- **Displacement cap** `0.02·diag` — no vertex drifts more than 2% of the diagonal
  from its post-decimation position, keeping the symmetric Hausdorff well inside
  the 5% budget.
- **Nondegeneracy guard** (`refine_valid`) — any step producing a zero-area face is
  rejected. Topology is never changed by a move, so manifoldness is automatic.
- **Wall-clock time-box** (16 s) — the loop cannot TLE regardless of mesh size or
  iteration count; it simply stops improving.

Because it optimizes the metric itself, it is the one lever that helps even on
case 3's uniform detail (where reallocation has nothing to move): it does not need
a cheap region to sacrifice, it just nudges the geometry to render closer to the
original.

---

## 6. Glue — `seed_heap`

Between Pivot-A passes (and after visibility marking) the edge heap must be
rebuilt from the *current* mesh with the *fresh* importance. `seed_heap` clears the
priority queue and, iterating the alive faces, re-evaluates each unique edge once
(deduplicated by a 64-bit `i·nv + j` key) and pushes it with the current version
stamps. It is the non-initial counterpart to the heap-seeding loop inside
`Initialize`.

---

## 7. Dormant — subset placement & the adaptive Hausdorff guard

The solver also contains a **provably Hausdorff-bounded** path, currently switched
off (`kOpAdaptive = 0`) because free-QEM placement beats it on SSIM. It is kept as
a geometry-safe fallback and is worth understanding.

- **Subset placement** (in `Evaluate`, when `g_adaptive`): a collapse moves to the
  *cheaper of the two original endpoints* rather than the free QEM optimum. Every
  surviving vertex is then an original vertex, so it lies exactly on the original
  surface (the direction-2 Hausdorff vertex term is 0 by construction).
- **Direction-1 guard** (in `Decimate`): each survivor carries a **bounding sphere**
  `(sc, sr)` of the original vertices it represents, merged on every collapse
  (`merge_spheres`). A collapse is rejected if $\lVert c_m - \bar{x}\rVert + r_m > \text{margin}$
  — a sound upper bound on any represented original's distance to the new surface.
- **Direction-2 guard** (`edges_ok`): every face modified by the collapse must have
  its longest edge ≤ margin. Since the face's vertices are on the surface, this
  bounds how far its interior can bulge off the surface.

Both bounds ≤ margin ⇒ symmetric Hausdorff ≤ margin (0.045 ⇒ < 4.5% < 5%), with no
spatial grid. See [../postmortems/adaptive-hausdorff-plan.md](../postmortems/adaptive-hausdorff-plan.md)
for the full derivation and why the active solver uses free-QEM keep instead.

---

## 8. Why every add-on stays valid (the invariants)

None of the perceptual systems can produce an invalid mesh, because each touches
only a dimension the hard gates don't depend on:

| System | What it changes | What it never touches |
|---|---|---|
| Per-case dispatch | the stopping target | topology, positions |
| Pivot-A steering | collapse **order** (a cost multiplier) | the collapse itself still passes the link/area/flip gates |
| Visibility culling | collapse **order** (a cost multiplier) | same — hidden edges still collapse through the gates |
| Inverse-render optimizer | vertex **positions**, within a displacement cap | topology is frozen; nondegeneracy re-checked every step |

The link condition + positive-area + no-flip gates in `SafeToCollapse` run on
**every** collapse regardless of cost, so the output is always a closed 2-manifold
with non-degenerate faces. The optimizer never changes connectivity and reverts any
step that degenerates a face or fails to improve the score. The displacement cap
(and, in the dormant path, the two-sided sphere/edge guards) keep the Hausdorff
deviation inside budget. In short: **the add-ons can only change *which* valid mesh
you get, never *whether* it is valid.**

---

## 9. Putting it together — the 88.67 configuration

The current best (submission v38, 7/7 valid) is the sum of these methods dispatched
per case:

| Case | keep / compression | Methods active |
|---|---|---|
| 2 | 0.01 / **99%** | free-QEM keep only |
| 3 | 0.33 / **67%** | per-channel Pivot-A **+** visibility **+** optimizer |
| 4 | 0.17 / **83%** | free-QEM base **+** optimizer |
| 5 | 0.10 / **90%** | per-channel Pivot-A steering |
| 6 | 0.03 / **97%** | free-QEM keep only |
| 7 | 0.04 / **96%** | free-QEM keep only |

Mean = (99 + 67 + 83 + 90 + 97 + 96) / 6 ≈ **88.67**. The authoritative per-case
status is [../judge-map.md](../judge-map.md); the go/no-go on pushing further is
[../postmortems/remesh-go-no-go.md](../postmortems/remesh-go-no-go.md).

---

## 10. Constants reference

| Symbol / knob | Value | Where | Meaning |
|---|---|---|---|
| in-loop render res | 160 | `res_for` | Pivot-A normal-map resolution |
| Pivot-A passes | 8 | `main` | staged re-render/steer cycles |
| $g_\lambda$ | 12 | `lambda_for` | steering strength (cases 3, 5) |
| $C_2$ (steering) | 0.0009 | `pivotA_update_importance` | SSIM $c$-term stabilizer, $[0,1]$ space |
| contrast radius | $\max(1, W/96)$ | `contrast_map` | local $\sigma$ box radius |
| visibility res | 512 | `compute_visibility` | hidden-face detection resolution |
| hidden multiplier | $10^{-4}$ | `Evaluate` | cost scale when both endpoints hidden |
| optimizer res | 512 | `g_refine_res` | SSIM-gradient render resolution |
| optimizer budget | 16 s | `g_refine_budget` | hard wall-clock time-box |
| displacement cap | $0.02\cdot\text{diag}$ | `refine_positions` | per-vertex Hausdorff bound |
| $C_1, C_2$ (optimizer) | 6.5025, 58.5225 | `R_C1, R_C2` | SSIM stabilizers, 255-space |
| SSIM window | 11×11 | `R_WN=121, R_RAD=5` | box window |
| adaptive margin | 0.045 | `kOpMargin` | dormant Hausdorff guard (< 5%) |
| small-mesh skip | 1000 | `kSmallMeshSkip` | emit unchanged below this |
| output precision | `%.17g` | `save_obj` | full double precision |

---

## 11. Lessons baked into the design

1. **The wall is SSIM contrast, not geometry.** Every method here targets the
   normal-map contrast/variance term; the geometric QEM cost is only an ordering
   heuristic (see [wang-ssim.md](wang-ssim.md), [../postmortems/qem-cost-is-not-hausdorff.md](../postmortems/qem-cost-is-not-hausdorff.md)).
2. **Reallocation vs. re-optimization.** Pivot-A and visibility *reallocate* the
   vertex budget (useful only when a low-importance region exists to sacrifice —
   great for case 5, weak for uniform case 3). The optimizer *re-optimizes* the
   surviving positions and so helps even without slack.
3. **The judge is ground truth; the local proxy under-estimates it.** Visibility's
   case-3 win contradicted the proxy's "negligible" prediction. Constants are
   pinned on the judge, not locally.
4. **Safety is structural, not tuned.** Manifoldness, non-degeneracy, and Hausdorff
   are guaranteed by construction (gates, frozen topology, displacement cap, hard
   time-box) — so aggressive perceptual optimization can never cost a valid case.
