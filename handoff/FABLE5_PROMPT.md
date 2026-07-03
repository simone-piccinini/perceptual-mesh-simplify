# Orchestration brief for Fable 5 — mesh-simplification solver, 89.49 → 92+

You are being brought in as a **second, independent researcher/strategist** on this problem, not as
an executor of a fixed checklist. A prior session (me, Sonnet 5) read the full codebase, the entire
judge-metric source, the complete experiment history (45 submissions), and did three rounds of
external literature research to write this brief. Everything below is **my best current analysis**,
not settled fact. Where I say "I think," form your own view — read the same primary sources yourself
(paths given below, all local, all readable), and if you disagree with a priority ranking, a risk
assessment, or the whole framing, say so and act on your own judgment instead. **You may well find
something better than everything in this document — that is the point of bringing you in.** The one
thing I'd ask you not to relitigate without new evidence is the ground-truth discipline in §1, because
it's the methodology that produced every real gain in this project's history.

## 0. Mission

Current solver (`solver/main.cpp`, 759 lines) scores **89.49/100, 7/7 passing** on the live Kattis
judge (`https://imc2.kattis.com/contests/imc2-2/problems/simplifygeometry`). Target: **≥92**. That
needs **+15.1 in the six-case sum** (92×6=552 vs current ≈536.9) — a big ask; be honest with yourself
and the user about whether each experiment plausibly contributes to that, not just "would it help a
little." Per-case breakdown and full method inventory are in §3.

**Deadline — confirmed live during this research, worth knowing up front:** this is the real, public,
currently-running **"IMC Challenge sponsored by Huawei"** on Kattis (this exact problem is Problem B of
the 2025/26 edition — overview: `huawei.com/minisite/imc-challenge/en/`, contest:
`imc25.kattis.com`). Problem released June 18 2026, **code-submission deadline July 18 2026**. Today
is **July 2, 2026 — 16 days left.** This should shape prioritization: bank the fast, cheap,
high-confidence gains (Tiers 0–1 in §7) early and for certain; run the bigger, slower bets (Tier 3) in
parallel if there's bandwidth, but don't let an unfinished risky rewrite be the only thing in flight a
few days out from the deadline. Best-counts protects every point already banked regardless of what
happens after.

## 1. Ground truth discipline — read this before doing anything else

**The judge is the only oracle. Local tests are hints, not verdicts.** This project's history (§5) is
full of techniques that "obviously" should or shouldn't work by local reasoning, and were wrong in
both directions. Operating rules, all judge-confirmed by this project's own experience:

- **Best-counts**: the judge keeps your best-ever total; a failed/regressed submission costs nothing.
  This means the correct bias is to **submit more, not less** — bisection sweeps, isolated probes, and
  long-shot bets are all free rolls. Don't sit on a candidate because you're not sure.
- **Isolate every experiment to one case.** Keep all other cases byte-identical to the current-best
  config so a WA cleanly attributes to the one thing you changed. This project got burned early by
  changing several cases in one submission and not knowing which one broke (see the case4/case5/case3
  triple-push in §5).
- **You (or the implementer) cannot submit to the judge yourselves** — there is no submission API/CLI
  wired into this repo (checked: no `kattisrc`, no submit script). The user submits `solver/main.cpp`
  to the Kattis web UI manually and reports back the result. Prepare each candidate so that report-back
  is easy: what changed, which case(s) it targets, what you expect, and **what exact verdict text to
  look for** (see §4.5 — this might matter more than the team previously assumed).
- **The retry protocol**, per the user's explicit instruction: if a submission comes back negative
  (WA or a regression), do not treat the underlying idea as dead after one try. Before writing it off,
  run **up to ~3 more variations that debug or adjust in the direction of that same idea** — narrow the
  isolation further, sweep the one suspect parameter, verify (locally, via the oracle) that the
  mechanism you added actually fired and did what you think, check it wasn't confounded with a
  simultaneous compression push. Only after several honestly-debugged attempts treat that *class* of
  method as exhausted **for the case you tested it on** — and even then, stay ready to revisit if a new
  capability changes the playing field. This project's biggest win (VSA-lite, +5 points on case3) came
  from reopening a question ("is case3 a normal-map allocation problem?") that an earlier, differently-
  implemented test (Pivot-A alone) had appeared to close. See §5.2 — take it seriously.
- **Local proxy fidelity is per-case, not uniform** (measured against real judge-confirmed pass/fail
  points, see `handoff/SOLVER_STATE.md`):
  - **case3**: proxy tracks the judge closely ("faithful") — trust relative *and* roughly-absolute
    comparisons.
  - **case4, case5**: proxies are **pessimistic** (read lower than the judge) and **unreliable in
    absolute terms** — a mesh can read < 0.90 locally and still pass. Trust only **relative**
    comparisons made at matched settings on the same proxy (e.g. "does method A read higher than
    method B at the same keep fraction on the same proxy mesh"), never the absolute number.
  - **case2, case6, case7**: no committed local proxy mesh at all. Bisect blind, on the judge, in small
    steps — this has worked repeatedly (see §5.1).
- **Update the paper trail as you go**: `handoff/SOLVER_STATE.md` (per-case dashboard),
  `handoff/ATTEMPT_LOG.md` (factual technique→result log), and a new `submissions/vNN-.../` snapshot
  (`main.cpp` + `RESULT.md`) on every judge submission. This discipline is why this brief could be
  written precisely — keep it going.

## 2. Where everything is

- **Current solver (read fully, it's short):** `solver/main.cpp` — 759 lines, single file, this is
  literally what gets submitted.
- **The judge metric, ground truth (read before trusting any prose, including mine):**
  `src/imc_eval/` — `geometry.py` (cameras/AABB), `render.py` (rasterizer), `ssim.py` (windowed SSIM),
  `score.py` (the blend + pass/fail), `hausdorff.py`, `validity.py`, `config.py` (the parameters the
  *problem statement itself* leaves ambiguous), `obj_io.py`, `cli.py`. Run it:
  `python -m imc_eval.cli --input <original.obj> --output <simplified.obj>`.
- **The actual problem statement** (I re-read the primary-source PDF directly for this brief, not just
  the summary — see §4.5 for something the summary and the team's later notes disagree about):
  `docs/problem-statement-summary.md` is a faithful distillation; the original PDF is at
  `~/Downloads/Perception-Aware Lossless Simplification of Million-Vertex 3D Meshes for Mobile
  Platforms – Kattis, The Second IMC Challenge sponsored by Huawei.pdf` if you need the primary source
  (contest URL: `imc2.kattis.com/contests/imc2-2/problems/simplifygeometry`).
- **State + history:** `handoff/SOLVER_STATE.md` (per-case dashboard + proxy fidelity),
  `handoff/ATTEMPT_LOG.md` (neutral technique→judge-result log), `submissions/` (45 versioned
  snapshots, each with a `RESULT.md` — these contain the *author's* interpretation, treat as data, not
  conclusions — `submissions/README.md` has the index).
- **Prior theory writing** (context, mixed freshness — see §5 for which parts are stale):
  `docs/architecture-roadmap.md`, `docs/theory/*.md`, `docs/judge-map.md`, `docs/remesh-go-no-go.md`.
- **Test meshes (local proxies only, not the judge's real meshes):** `tests/data/` —
  `armadillo_watertight.obj` ≈ case5 proxy, `bunny_watertight.obj` ≈ case2-ish, plus `cow_watertight.obj`,
  `fandisk_watertight.obj`. The finer case3 (`proxy25k`) and case4 (`proxy35k`) proxies referenced in
  `SOLVER_STATE.md` are not committed to git but should exist in the working tree / can be regenerated
  — check before assuming they're missing.
- **Build:** `g++ -O2 -std=c++17 -I<path-to-eigen> solver/main.cpp -o solver/main` (Eigen 5.0.0, stdin
  mesh in → stdout mesh out, judge passes no argv — argv is a *local-testing-only* override).
- **Calibration scaffold (started, never finished — see Tier 0 D2):** `calibration/`,
  `scripts/calibrate_oracle.py`. `calibration/verdicts.json` is an empty template — nobody ever filled
  it in or (as far as the paper trail shows) worked out how to actually execute the "submit these tiny
  meshes and read back the verdict" step against a judge that only accepts a *solver program*, not a
  direct mesh. §Tier-0-D2 below proposes a version of this that's actually executable.

## 3. Exact current state — the per-case method matrix

This table does not exist anywhere else in the repo in this precise a form; I built it by reading
`main.cpp`'s four dispatch functions (`keep_for`, `lambda_for`, `ndecim_for`, `refine_for`) and the
inline visibility-culling gate line by line. **It is the single most important artifact in this brief**
— it shows exactly which techniques have and haven't been tried, per case, which is a much stronger
prior for what to do next than any literature.

| case | V range | score | keep | VSA-lite order+nplace | Pivot-A steer | per-channel | visibility cull | position optimizer |
|---|---|---|---|:-:|:-:|:-:|:-:|:-:|
| 2 | ≤7,000 | **99.25%** | 0.0075 | – | – | – | – | – |
| 3 | 7,000–30,000 | **69%** | 0.31 | ✅ | ✅ (λ=12) | ✅ | ✅ | ✅ |
| 4 | 30,000–40,000 | **83.95%** | 0.1605 | ❌ | ❌ | ❌ | ❌ | ✅ |
| 5 | 40,000–100,000 | **90.75%** | 0.0925 | ✅ | ✅ (λ=12) | ✅ | ❌ | ❌ |
| 6 | 100,000–400,000 | **97%** | 0.03 | – | – | – | – | – |
| 7 | >400,000 | **96.95%** | 0.0305 | – | – | – | – | – |

(– = never applied, gated out by design, mainly for TLE-risk / presumed-low-yield reasons on the huge
meshes; ❌ = applicable range but **not currently enabled**, i.e. a real gap; ✅ = active in the
current best submission.)

**The single biggest takeaway from this table: case4 — the second-worst-scoring case — is running
almost none of the machinery that took case3 from 64%→69% and case5 from 79%→90.75%.** It only has the
position optimizer. Read that as a strong prior, not a certainty (case4 is architecturally different —
more mechanical/CAD-like per `docs/architecture-roadmap.md` — so the same techniques might transfer
worse), but it is the most under-explored cell in this table by a wide margin. See Tier 1 T1.

Second takeaway: **case5 has never had visibility culling**, despite being an armadillo-like organic
mesh (limbs, ears, torso) that plausibly self-occludes as much as or more than case3, where visibility
culling was a clean +1 point for near-zero cost. See Tier 1 T2.

## 4. The metric, precisely — facts I derived or confirmed, not guesses

### 4.1 depthSSIM is saturated; normalSSIM is the only thing that moves
Confirmed repeatedly in this project's own local measurements: depthSSIM sits ≈0.98–0.99 almost
regardless of compression level on the organic cases; normalSSIM (≈0.72–0.82 near the walls) is what's
actually being fought over. A "jointly optimize both" attempt (add depth to the optimizer's accept
criterion) **WA'd case4** — the 50/50 blend let the optimizer trade a small normal loss for a small
depth gain that looked net-positive on the pessimistic proxy but wasn't on the judge. Do not repeat
that exact experiment; a *sequential* (not joint) attempt is a different, lower-priority idea (Tier 5).

### 4.2 The closed-form loss for a flat interior window (verified against `src/imc_eval/ssim.py`)
For a window that sits entirely inside one original face (constant encoded channel value `a`) and one
simplified face (constant value `b`), every variance/covariance term in the SSIM formula is exactly
zero, so the whole window's SSIM collapses to the luminance term alone:

```
SSIM_window = (2ab + C1) / (a² + b² + C1)          C1 = 6.5025
```

I derived this from the formula in `ssim.py`/the problem PDF and it is exact for any window that
doesn't straddle a face boundary (the large majority of windows on a compressed organic mesh — window
boundaries are a 1-D contour, interiors are 2-D area). This is **not** what the current VSA-lite
collapse-ordering cost (`incident_ndist` in `main.cpp`) actually computes — it uses a generic
area-weighted `(1 − cos θ)` between old and new face normals, which is a reasonable angular heuristic
but is provably not the metric's real shape (the real loss is per-channel, saturating near `a≈b`, and
asymmetric across the `[0,255]` encoding because of the `+C1` term). See Tier 2 M1 for the concrete
proposed replacement.

### 4.3 What's confirmed-fixed by the problem statement vs. genuinely ambiguous
I re-read the primary-source PDF (not just the in-repo summary) specifically to pin this down:
- **`ω_N = ω_D = 0.5` is stated as a fixed constant in the PDF**, not symbolic/tunable. The oracle's
  `config.py` docstring calls this "HIGH impact, had to be guessed" — that's **overcautious**; it isn't
  actually ambiguous. Don't spend effort recalibrating the blend weight.
- **The `11×11` window's internal weighting (box/uniform vs. Gaussian) is genuinely left unspecified**
  by the PDF — it just says "11×11 local sliding window." The oracle defaults to box (uniform_filter);
  Wang et al. 2004's canonical SSIM uses Gaussian (σ=1.5). `config.py` estimates this is worth "~0.002
  at the gate." Given how many of this project's operating points sit within 0.002–0.005 of their wall
  (case4, case5 both explicitly described as "razor-edge" in `handoff/ATTEMPT_LOG.md`), this is small
  but plausibly decision-relevant. See Tier 0 D2 for a concrete, executable way to test it against the
  real judge (the existing `calibration/` scaffold was started but never finished/executed).

### 4.4 Depth encoding and normal-space are still real ambiguities
`src/imc_eval/README.md`'s "Known calibration gaps" section (not previously surfaced in the theory
docs) flags two more oracle guesses worth knowing about: raw camera-space depth storage (vs. some other
normalization) and world-space vs. view-space face normals. Lower priority than 4.3 (no specific
impact estimate exists), but worth keeping in mind if a future local-vs-judge discrepancy shows up that
nothing else explains.

### 4.5 A real discrepancy worth resolving on the next submission, for free
The problem PDF states, verbatim, directly under "Constraints" (manifold / non-degenerate / vertex
count / Hausdorff): *"If they do not [satisfy the constraints], you will get Wrong Answer **and be
informed of which one you violated**."* But `docs/theory/paper-notes.md` (written later in the
project) asserts as "CRITICAL... confirmed by user" that *"the judge only says Wrong Answer — no
reason."* These two claims are in tension, and I think I can partially resolve it by re-reading the PDF
structure: the "you'll be told which constraint" sentence sits under the **Mesh Validity / Geometric
Deviation constraints** section specifically; the `FinalSSIM < 0.9` case is described separately, later,
under "Validity Threshold," purely as *"submissions below the threshold get 0 points"* — never called
"Wrong Answer" in that section. That reads to me like two different verdict mechanisms: a **hard
constraint violation** (manifold/Hausdorff/vertex-count) → WA with a specific checker message; **SSIM
below 0.90** → a validly-structured submission that simply scores 0, possibly shown differently in
Kattis's UI (e.g. as Accepted-with-zero rather than WA). This would also explain why *early* submissions
in this project's history did see specific messages (`docs/theory/qem-cost-is-not-hausdorff.md` quotes
an actual verdict: *"Wrong Answer: too much geometric deviation"*) while later, more targeted
attempts near the SSIM wall reportedly saw only bare "Wrong Answer." **Action: on the very next
submission (whatever it's testing), look carefully at the exact verdict text/UI state Kattis shows, per
case if visible, and record it precisely in the RESULT.md.** If a future WA on case4/case5 ever again
shows a specific "geometric deviation" or "manifold" message, that's a different, fixable class of bug,
not an SSIM-wall problem — worth knowing immediately rather than assuming it's the SSIM wall (as the
team's operating assumption currently would).

## 5. What's already closed out, and — more important — what only *looks* closed

### 5.1 Genuinely exhausted (don't redo these exact things)
- 9+ position-quadric cost reweightings (area-weighted QEM, GH-normal attribute quadric, silhouette
  edge-lock, anti-sliver, Delaunay flips, subset placement, image-driven screen-importance) — all
  pinned the same wall pre-VSA-lite. The theoretical reason (`docs/theory/wang-ssim.md`) is solid: QEM
  position-cost reweighting only ever changes *where the mean sits*, never the *local variance*, and
  the variance/contrast term is what SSIM actually penalizes in detailed regions.
- Naively squaring the normal-distortion cost (`area·(1−cosθ)²`) or dropping area weighting — both
  tested worse locally than the current `area·(1−cosθ)` (this is why Tier 2 M1's closed-form proposal
  should be treated as *a different function family*, not "we already tried squaring it," and validated
  carefully rather than assumed to win).
- Position-optimizer convergence on case3: 30s and 90s of wall-clock gradient ascent give the same
  result (+0.0005) — genuinely plateaued *for that optimizer*. (Caveat in 5.2/Tier 3 B1: this may be a
  property of *unpreconditioned* gradient ascent specifically, not a true ceiling.)
- Edge-flip topology moves scored by real SSIM: +0.0005, negligible.
- meshoptimizer (zeux/meshoptimizer) attribute/normal-preserving mode and non-greedy vertex clustering
  both scored dramatically *worse* than plain QEM on real rendered normal-SSIM, pre-VSA-lite. Read this
  as "explicitly preserving normals as an attribute, independent of triangle-quality discipline, tends
  to backfire" (slivers → volatile face normals), not as "no alternative backbone can ever help" — see
  Tier 3 B2 for why a *manifold-safe-collapse-disciplined* variational method is a different bet.

### 5.2 Looked closed, was reopened — treat every "wall" as a data point, not a limit
This is the most important pattern in the project's history and it happened **twice**:
1. **case2** was labelled "geometry-capped ~92–94%" and then climbed, via pure keep-fraction
   bisection with zero algorithm changes, all the way to **99.25%** (93→94→…→99.25, almost every step
   passed). `docs/judge-map.md`'s own retrospective calls this "the two big lessons of the project":
   *"never trust an assumed cap."*
2. **case3** was declared, in `docs/remesh-go-no-go.md` (dated, with a full "empirical kill-shot"
   section testing 4 genuinely different simplifiers against QEM), to be **information-theoretically
   capped at 65%**, with the explicit conclusion *"90 is unreachable... the realistic ceiling of ANY
   rebuild is ~88.5-89."* That conclusion was reached by testing screen-space contrast-deficit steering
   (Pivot-A) on top of **position-ordered** QEM. It did not test changing the ordering criterion itself.
   One session later, **VSA-lite** (order by normal distortion instead of position error, keeping
   everything else identical) took case3 from 67%→69% and the *whole solver* past the "90 unreachable"
   document's own baseline. The lesson isn't "VSA-lite was right and the old analysis was wrong" — the
   lesson is that **"we tried steering/reweighting and it didn't help" is not the same claim as "we
   tried changing what's greedily minimized and it didn't help,"** and this project had, at the time,
   only tested the former.

**Apply this skepticism forward, specifically to:** case4 (only ever tested Pivot-A/VSA at a
*simultaneous compression push*, never isolated at its own confirmed operating point — Tier 1 T1); the
"case6/case7 too big for VSA, TLE risk" assumption (asserted, never actually timed — Tier 4 I1); and
the position-optimizer's "converged" plateau (true for *raw* gradient ascent specifically — Tier 3 B1).

## 6. Research directions worth understanding

*(Citations/mechanism details in this section were gathered by three parallel literature-research
passes done for this brief — VSA/variational remeshing, inverse-rendering geometry optimization, and a
broad perceptual/appearance-driven-simplification sweep plus a check for any public trace of this exact
contest. Treat page/mechanism details as a starting pointer, not a substitute for reading the actual
papers if you decide to build on one.)*

**Cohen-Steiner/Alliez/Desbrun, "Variational Shape Approximation" (SIGGRAPH 2004).** Source of the L2,1
normal-distortion metric VSA-lite already borrows. I had this checked directly against the original
paper text and CGAL's mature (20-year-later) implementation specifically to answer whether a
manifold-safe hybrid (VSA's partition as a *protection signal* for ordinary edge-collapse, boundaries
frozen, no retriangulation) is a known, workable pattern. Findings, which matter for how much you should
expect from Tier 3 B2:
- **The paper's own extraction step (anchors → chord-subdivision → a Dijkstra-flooded "discrete CDT" →
  polygon merging) is a genuinely separate remeshing stage, and the authors admit it patches around
  topological artifacts (extra "pyramid" vertices on fin-like features) specifically to avoid
  non-manifold output** — manifoldness is something they fight for, not something the algorithm
  guarantees by construction.
- **CGAL's own VSA implementation still cannot promise manifold output.** Its docs state the output is
  effectively a triangle soup requiring a separate `orient_polygon_soup()` repair pass, and "Guarantee
  manifold output" is an **open, unresolved TODO** on CGAL's issue tracker (#2368) — strong, current,
  independent confirmation that boundary retriangulation is exactly the risk `docs/remesh-go-no-go.md`
  already flagged, unsolved even by the most mature open-source implementation of this algorithm.
- **No published work combines VSA's partition purely as a collapse-order/protection signal while
  freezing region boundaries** — the Tier 3 B2 hybrid is genuinely unmapped territory, not a known-good
  or known-bad pattern.
- **Important honest caveat for B2's expected value: VSA's actual mesh-count reduction comes specifically
  from the boundary retriangulation / polygon-merging step, not the clustering alone.** A hybrid that
  freezes boundaries and only collapses within each proxy's interior is manifold-safe by construction
  (it's just constrained ordinary VSA-lite collapse) but should be expected to capture a **smaller** gain
  than a full VSA rebuild — it prunes interior fan complexity per region, not whole regions down to a
  handful of boundary polygons. A safer, smaller bet than "true VSA," not a substitute for it.
- **No published evaluation of VSA under any image-space/SSIM-style metric exists either** — this
  project's own result (normal-distortion *ordering* beating position-error ordering under this exact
  rendered-SSIM judge) is, as far as this search found, novel; nobody has confirmed or contradicted it
  externally.

**Nicolet, Jacobson, Jakob, "Large Steps in Inverse Rendering of Geometry" (SIGGRAPH Asia 2021)** —
paper: `bnicolet.com/publications/Nicolet2021Large.pdf`, code: `github.com/rgl-epfl/large-steps-pytorch`,
sparse-Cholesky solver: `github.com/rgl-epfl/cholespy`. I had this checked directly against the paper
for this brief, and it confirms exactly the failure mode we suspect, not just by analogy: their Fig.
1/3/6/7 show plain unpreconditioned gradient descent on rendering-derived vertex gradients producing
"tangled"/"blurry" results that **stagnate in a λ-dependent stalemate** at a fixed step budget, while
their preconditioned version keeps converging — and their theoretical framing is precisely our
hypothesis, that sparse/local gradients (a silhouette or normal-map mismatch) need ~O(√n) iterations of
plain descent just to *diffuse* across the mesh, which looks exactly like "converged" if you stop
earlier. The **simplified, directly bolt-on-able form** of their method (their eq. 14 — skip the full
Adam-reparameterization machinery entirely): build `M = I + λL` once, where `L` is the **combinatorial**
graph Laplacian (`L_ii=deg(i)`, `L_ij=-1` per edge — they found cotangent gives no meaningful difference,
and combinatorial's sparsity is purely topological) over the current mesh's surviving vertices; factor it
once with a sparse Cholesky (Eigen `SimplicialLDLT` is fine at our vertex counts); each iteration, solve
`M·g_precond = g_raw` against the **already-computed exact analytic gradient** instead of using it
directly, then ascend on `g_precond` with the existing monotonic-accept / step-halving / wall-clock-box
scaffolding completely unchanged. λ≈19–32 in their experiments (retune against our objective). This is a
small, contained, CPU/Eigen-only change to `refine_positions()` — see Tier 3 B1, now upgraded in
confidence given this is a confirmed, not speculative, mechanism.

**A dedicated 2018–2026 literature sweep for anything beating the above, done for this brief:**
confirmed **Hasselgren et al., "Appearance-Driven Automatic 3D Model Simplification" (NVIDIA, CVPR
Workshops 2021, `arxiv.org/abs/2104.03989`)** is the closest published match to this problem shape —
joint vertex-position + material optimization against an image-space loss via differentiable rendering
(nvdiffrast), across many viewpoints. Honest conclusion: **this project's Pivot-A + inverse-rendering
position optimizer, together, are already a hand-rolled, analytically-differentiated version of that
technique**, adapted to a fixed 6-camera judge instead of nvdiffrast's randomized-viewpoint
generalization goal (which we don't need — we know our exact 6 views in advance). A 2026 paper,
**FA-QEM** (`arxiv.org/abs/2605.14029`), folds a normal-consistency term into one fused quadric rather
than a separate ordering pass — close enough to Garland-Heckbert's own attribute-quadric extension
(already tried, degenerates on flat faces) that it's likely marginal over VSA-lite, not worth
reimplementing. A dedicated search for learned/neural collapse-cost functions (GNN-guided decimation,
"neural LOD," 2023–2026) found nothing with portable, small-enough-to-hardcode weights aimed at
rendered-perceptual similarity — what exists targets FEM-simulation-accuracy coarsening or full neural
mesh generation, wrong problem class. **Net: no external idea beats what's already in the backlog below
— treat it as genuinely the frontier, not as "obvious things nobody's tried yet."**

**Perceptual/appearance-driven simplification, broader sweep.** The project's own notes already cover
Lindstrom-Turk image-driven simplification (too expensive per-candidate at our scale, but its
memoryless/near-equilateral placement trick is cheap and unused), Cohen/Olano/Manocha appearance-
preserving simplification (assumes texture/normal maps we don't ship — not directly usable), Trettner-
Kobbelt probabilistic quadrics (tested, worse than free-QEM on clean meshes — the σ-regularization pulls
vertices off-surface), and mesh saliency (Lee/Varshney/Jacobs 2005) and view-dependent/silhouette work
(Luebke-Erikson normal cones) as candidates for a silhouette-contour-specific protection term, distinct
from VSA-lite's interior-normal-distortion focus (Tier 2 M3) — gated on whether §Tier-0-D3's diagnostic
actually shows a silhouette-attributable deficit on case4/case5 (case3's deficit is already known to be
interior-concentrated, so this specific mechanism is likely low-yield *there*).

**On the contest itself — correction to my own initial assumption, checked directly for this brief:**
this is **not** a private/unindexed judge. It's the real, public, currently-running "IMC Challenge
sponsored by Huawei" (overview: `huawei.com/minisite/imc-challenge/en/`; Kattis:
`imc25.kattis.com`). Confirmed: problem released June 18 2026, **code-submission deadline July 18
2026** (see §0 — 16 days out from today). No writeups/leaderboard/prior solutions are indexed yet,
expected mid-contest (submissions are embargoed). Worth knowing: **the top-40 teams have an
article/writeup requirement**, so competitor technique writeups will likely become public *after* the
deadline — a genuine future idea source, just not available now. (Also ruled out a false lead: "Image
Matching Challenge" on Kaggle is a completely unrelated 2D computer-vision competition that surfaces on
a naive "IMC" search — ignore hits from that.)

## 7. Prioritized experiment backlog

Ranked by my best guess at (expected gain × probability × low cost), tiered so you can parallelize
within a tier. **Numbers in "expected gain" are honest guesses, not measurements — say so if you use
them, and update them the moment real data (local or judge) exists.**

### Tier 0 — free diagnostics, zero solver risk, do these regardless of what else you pick up
**D1. Re-verify judge verdict granularity (§4.5).** Cost: nothing, just read carefully. On the very
next submission, record the *exact* verdict text/state per case if Kattis shows one. If a specific
constraint-violation message ever appears again on case4/case5, that changes the diagnosis completely
(bug, not SSIM wall).

**D2. Case3-anchored SSIM-window calibration (box vs. Gaussian, §4.3).** Hypothesis: one of the two
window types is a measurably better model of the real judge. Method: using case3's proxy (the one
confirmed "faithful"), find or construct a keep fraction where `OracleConfig(ssim_window="box")` and
`OracleConfig(ssim_window="gaussian")` disagree on pass/fail (should exist somewhere near case3's
current 69%/70% boundary, given `config.py`'s own "~0.002 at the gate" estimate and how tight that
margin is). Submit that one operating point for case3 (isolated, other cases untouched); the verdict
tells you which window model to trust everywhere else. This sidesteps the "judge only accepts a solver,
not a direct mesh" problem that likely stalled the original `calibration/` scaffold (its `verdicts.json`
was never filled in) by making the *live case3 operating point itself* the discriminating probe, instead
of a synthetic calibration mesh nothing can actually feed to the judge directly.

**D3. Interior-vs-silhouette SSIM-deficit split for case4 and case5 (local-only, no submission).**
Case3's deficit is documented as interior-concentrated; case4/case5 have never been checked. Cheap
script using the existing oracle: mask out silhouette-boundary windows (adjacent to a background pixel
in the original render) vs. interior windows, compare their contribution to the normalSSIM deficit at
current operating points. Decides whether Tier 2 M3 (silhouette-contour protection) is worth building
at all for these two cases.

### Tier 1 — cheap, isolated, high-confidence coverage gaps (§3's table is the evidence)
**T1. Full modern arsenal on case4, isolated and bisected from the confirmed 83.95% floor.**
Hypothesis: case4 is the least-augmented organic case (§3) and its one "VSA push" data point conflated
a method change with a simultaneous compression push (84.25%, WA, per `handoff/ATTEMPT_LOG.md` — the
same submission also pushed case3 and case5 at once). Method: enable `ndecim_for`/`lambda_for`
(per-channel)/visibility-culling for case4's V-range (30000,40000], **first at exactly today's keep
0.1605** (isolation check: does a different collapse order at the same target vertex count still pass?
Not guaranteed a priori — a genuine judge question), then bisect keep downward in the small increments
(~0.25–0.5%) that worked repeatedly for case3/case4/case7 before. Validation: compare proxy35k's
*relative* normalSSIM (VSA-ordered vs QEM-ordered, same keep) before submitting anything — proxy35k is
pessimistic in absolute terms but relative comparisons at matched settings are the trusted signal here.
Expected gain: genuinely uncertain — could be 0 (case4's "mechanical/piecewise-planar" character per
`docs/architecture-roadmap.md` may just not respond the way organic case3/case5 did) to several points.
Risk: case4 is documented "razor-edge" — any change can flip it: this is exactly why isolating the
compression-level variable from the method variable matters. Retry protocol (§1) fully applies.

**T2. Visibility culling on case5.** Hypothesis: armadillo-like meshes plausibly self-occlude
(limbs/torso/ears) at least as much as case3, where this was a clean, cheap +1 point. Never tried on
case5. Method: extend the existing `compute_visibility()` gate to case5's V-range; test isolated at
current keep 0.0925 first, then bisect down with VSA+nplace+visibility together. Low engineering cost
(the mechanism already exists and is generic). Expected gain: +0.25 to +1.5 points, speculative.

**T3. Isolated position-optimizer test on case5 at its confirmed (non-pushed) keep.** The one existing
data point (optimizer + case5 at a simultaneous 91% push) WA'd and was attributed to "the optimizer
overfits the pessimistic proxy's normal field" — but that also conflated a push with the method change.
Test the optimizer alone at 90.75% first; if the proxy shows a genuine (not noise-level) gain and it's
judge-confirmed safe, only then bisect keep with both together. Temper expectations: there's a specific
documented overfitting concern here, unlike T1/T2 which are cleaner gaps.

**T4. Continuous opportunistic bisection, case2/case6/case7, running throughout everything else.**
Zero algorithm risk (pure keep-fraction search on unmodified free-QEM), essentially free given
best-counts. Low individual expected value per step (these are likely close to a real ceiling — dense
mesh normal-map fidelity or geometric floor) but §5.1's "never trust an assumed cap" lesson argues for
not stopping just because recent steps returned less.

### Tier 2 — medium-effort refinements of the one mechanism that's actually proven out
**M1. Replace `incident_ndist`'s `area·(1−cosθ)` with the closed-form per-channel SSIM-consistent loss
(§4.2).** Concretely, per affected face and per channel `c ∈ {x,y,z}`: `a_c = (n_old[c]+1)·127.5`,
`b_c = (n_new[c]+1)·127.5`, `loss_c = 1 − (2·a_c·b_c + 6.5025)/(a_c² + b_c² + 6.5025)`; replace the
single `oneminus` term with `Σ_c loss_c`, keep the existing `0.5·area_new` weighting. Same O(valence)
per-candidate-edge cost as today — a drop-in swap, not a new mechanism. This also automatically
sharpens `nplace`'s candidate-position selection (same function, reused). Validate locally on case3
first (faithful proxy: compare normalSSIM at matched keep, old vs. new cost formula) before touching
case4/case5's less-trustworthy proxies. Caution: a *nearby* variant (squaring the plain cosine term)
already tested worse locally — this is a different function family (channel-wise, saturating,
`C1`-consistent) but treat that history as a reason to validate carefully, not as "already tried."
Expected gain: modest but broad (touches every case using VSA-lite) if it holds up — a fraction of a
point per case, possibly more given how close several cases sit to their walls.

**M2. Projected/view-aware area weighting for the VSA-lite cost.** `docs/architecture-roadmap.md`'s
own unaddressed critique #1: weighting by 3D world-space face area (as `incident_ndist` does today)
mismatches screen-space importance, and camera distance varies enough across a unit-sphere mesh at
D=2.5 (~1.5–3.5 effective distance) that projected area can differ several-fold between near- and
far-side geometry. Precompute a per-face `Σ_views area_world·max(0,cosθ_view)/d²` scalar once before
decimation, refresh lazily only for faces touched by a collapse (same amortized cost pattern as the
existing incremental heap updates). Note this is a different mechanism than "area-weighted QEM
position cost" (tested, hurt cases 4/6, in §5.1's dead list) — that reweighted *position* error;
this reweights the *already-winning normal-distortion* ordering. Medium engineering effort; pair with
M1, test on case3/case5 first.

**M3. Silhouette-contour collapse protection — build only if Tier-0 D3 shows it matters for case4/
case5.** Method, refined via literature research (§6): since there are only 6
fixed, known, axis-aligned camera directions — not the general arbitrary-viewpoint case Luebke-
Erikson's normal-cone method targets — a cheap, exact, camera-count-bounded test suffices: precompute,
once per face before decimation, whether that face's normal sits within a small angular tolerance of
perpendicular to any of the 6 fixed view axes (a proxy for "near a silhouette fold from at least one
camera that will ever render it"), and inflate collapse cost there; no general normal-cone bookkeeping
needed. Separately from VSA-lite's interior-normal-distortion term and Pivot-A's contrast-deficit term.
Do not build this speculatively —
case3's own deficit is documented interior-concentrated, so this mechanism plausibly has near-zero
yield *there*; it's only worth the engineering cost if D3's diagnostic shows real boundary-window
contribution on case4/case5 specifically.

### Tier 3 — big swings (at least one is requested; here are two, different risk profiles)
**B1. Laplacian/Sobolev-preconditioned position optimizer (§6, Nicolet et al. 2021).** Hypothesis:
case3's optimizer "convergence" (30s == 90s) is an artifact of unpreconditioned per-vertex gradient
ascent on a rough objective landscape, not the true optimum — meaning there's real, currently-unclaimed
SSIM on the table from the *same* decimated vertex set. Method: build a sparse Laplacian-based
`(I + λL)` matrix over the current mesh's surviving vertices, factorize once (Cholesky, Eigen has this
built in), and reparameterize the gradient-ascent step through it every iteration instead of using the
raw analytic gradient directly. All CPU, all Eigen, no new dependency. Validation: locally on case3
first — does the reparameterized optimizer reach a measurably higher normalSSIM than the current one at
the same or less wall-clock budget? If yes, this is a clean win to bisect on the judge; if it converges
to the *same* place, that's real evidence the plateau is genuine, which is itself valuable information
(closes an open question cleanly either way). Risk: medium engineering effort, real but bounded (it's
strictly an alternative to the existing optimizer step, easy to A/B and to revert if it doesn't help or
misbehaves near the Hausdorff cap). This mechanism, its documented failure mode, and a CPU/Eigen-only
bolt-on path (§6) are now confirmed directly against the paper, not speculative extrapolation — of the
two Tier 3 bets, this is the one I'd start first.

**B2. Scoped "VSA-medium" — proxy-partition-protected greedy collapse.** The bigger structural bet:
run VSA's Lloyd-relaxation face-partitioning (by normal proxy) to convergence, then use the converged
partition purely as a **protection signal** for the existing, already-safe link-condition-gated
edge-collapse — heavily penalize or forbid collapses that would cross a proxy-region boundary — without
ever doing free-form boundary retriangulation. This inherits the manifold guarantee for free (the
actual collapse mechanics are unchanged) instead of rebuilding it, which is where this project's own
prior analysis says VSA implementations usually break (`docs/remesh-go-no-go.md`). This is more global
than VSA-lite (which has no explicit stable-partition notion, just a per-collapse local proxy for one)
and a meaningfully bigger engineering lift (Lloyd relaxation to convergence, on top of the existing
pipeline). Scope it to case3 only first (highest remaining upside, faithful proxy to validate against)
with a hard, cheap fallback (today's VSA-lite config) if it doesn't clear the bar. Checked directly against the VSA
literature and CGAL's implementation for this brief (§6): the "partition-as-protection-signal, not
retriangulation" pattern is genuinely novel — nobody has published it — and CGAL's own 20-years-later
implementation still can't guarantee manifold output from the full retriangulation approach, which is
corroborating evidence for staying with collapse-only. But also temper expectations: VSA's real
compression payoff comes from the retriangulation step specifically, so this scoped hybrid should be
expected to give a **smaller** gain than "true VSA" would — a safer, cheaper, lower-ceiling bet, worth a
scoped shot on case3 precisely because it's unexplored, not because it's likely to be the 92-point
unlock by itself.

### Tier 4 — infrastructure (unlocks other experiments, not a direct lever by itself)
**I1. Multithread the 6-axial-view render/SSIM/gradient pipeline.** The 6 views are embarrassingly
parallel and are used in three hot paths: Pivot-A's per-pass importance render, visibility computation,
and the optimizer's per-iteration render+gradient. Case3/case5 currently run at ~16–17s of the ~20s
safe budget (empirically-derived — the ~21s limit isn't stated in the problem PDF itself, and core
count isn't stated either). **Don't hardcode a core-count assumption; call
`std::thread::hardware_concurrency()` at runtime and degrade gracefully to 1 thread if that's what's
available** — safe under any actual judge configuration. Payoff is indirect: could let the position
optimizer run long enough to converge at judge-exact 1024 resolution instead of 512 (the earlier
"1024 is worse" finding was explicitly attributed to under-convergence in the time budget, not to 1024
being fundamentally wrong — worth re-testing once there's real budget headroom), and could make
extending VSA-lite/Pivot-A to case4/case6/case7 safe against the (currently just assumed, never
measured) TLE risk on huge meshes.

### Tier 5 — exploratory, time-permitting
**X1. Sequential (not joint) depth-then-normal optimizer pass**, to try to capture any remaining depth
slack (0.985→~0.99?) without repeating §4.1's joint-objective trading failure. Small absolute ceiling,
low priority.

**X2. Beam-search/lookahead greedy collapse** (short lookahead instead of pure greedy-cheapest,
still within the same manifold-safe framework). Real engineering cost, real TLE risk on already-tight
case3/case5 budgets, uncertain payoff over VSA-lite's already-strong ordering. Only worth it if Tier 4
I1 frees up real budget first.

## 8. Where I want your independent judgment specifically

- **Is the Tier 3 B2 hybrid (VSA partition as a protection signal, not a retriangulation) actually a
  good idea, or am I underestimating why nobody in this project's history tried exactly that?** I built
  the argument for it myself from first principles plus secondhand paper knowledge; I'd trust a fresh
  read of the VSA literature (and maybe its practical descendants in remeshing tools) over my own
  reasoning here.
- **Is 92 actually reachable by continuing to refine this backbone (manifold-safe greedy collapse +
  smarter cost functions), or does it structurally require something this whole family of methods can't
  give?** I lean toward "keep pushing this backbone, it has repeatedly out-performed alternatives
  tested so far" (§5.1), but I've been wrong about ceilings before in exactly this project (§5.2), and
  so has everyone before me on this.
- **Is there a mechanism specific to this *exact* metric (flat-per-face normals, exactly 6 fixed axial
  views, foreground-union windowing, the specific `C1`/`C2` constants) that neither I nor the prior
  sessions have spotted?** The closed-form derivation in §4.2 came from just sitting with the formula
  and the encoding for a while — there may be more like it (e.g. something exploitable about the
  foreground-union rule specifically, or about the fact that all 6 cameras are axis-aligned and the mesh
  is unit-sphere-normalized). If you see one, that's exactly the kind of thing worth chasing over
  anything in the backlog above.

Good luck. Submit early, submit often, trust the judge over both of us.
