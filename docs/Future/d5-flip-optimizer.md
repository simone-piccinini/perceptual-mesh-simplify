# D5 — connectivity in the optimizer loop (render-gated edge flips)

**Status: SCAFFOLD LANDED, cheap-proxy driver CLOSED (2026-07-06). Env-gated `G_FLIPOPT`,
judge-default OFF (v109 byte-identical). Finding 1 below closed the cheap `flip_tricost`
driver with data; the viable path (flips selected by localized real-SSIM) is scoped but
unbuilt — see "The redirect".**

## The idea in one sentence

The inverse-rendering optimizer (lever 4) freezes the triangulation and only moves
vertices; **D5 lets it also change *which* triangles exist** — manifold-safe edge flips,
accepted only when they raise the *real* rendered normal-map SSIM — so geometry **and**
topology co-adapt to the target normal field.

## Why this is worth doing

- **It is the one lever the graveyard never contained.** Every killed idea was a *cost
  reweighting* or a *vertex-normal preserver* (see [structural-ideas.md](structural-ideas.md)
  §graveyard). A flip changes the *face pattern* at **zero vertex cost** and zero Hausdorff
  cost (vertices don't move) — a genuinely new degree of freedom, and exactly the "better
  placement geometry / connectivity change" the graveyard analysis flagged as open space.
- **It attacks the binding wall directly.** The wall everywhere is the normal-map SSIM
  *structure* term. A flip re-paints the facet normals a window sees; on a flat/coplanar
  patch mis-triangulated into slivers, one flip can fix the local normal pattern that a
  vertex move cannot reach (moves are stuck in the given triangulation's basin).
- **The primitive already exists and is proven.** `flip_pass()` (solver/main.cpp:589) is a
  manifold-safe flip (link/duplicate-edge guard via `EdgeExists`, orientation guard, vfaces
  maintenance). Its own comment records the key prior: *"Session-1 measured flips-by-real-SSIM
  at +0.0005 local and never judged it; this is the cheap-objective form."* D5 supplies the
  missing piece — the real-SSIM driver, interleaved into the optimizer.

## Algorithm

Interleave, inside `refine_positions()` after the first position-convergence:

```
repeat up to R rounds (while CPU budget remains):
    snapshot topology (faces, face_alive, vfaces) and current score `cur`
    run ONE proxy-improving flip sweep:
        for each interior manifold edge (exactly 2 alive faces):
            form quad (a,b | c,d); skip if EdgeExists(c,d) (would go non-manifold)
            proxy gain = flip_tricost(old pair) - flip_tricost(new pair)   # area*(1 - n_face . n_ref)
            commit the flip iff proxy gain > 0 AND orientation guard holds
    sn = refine_score_grad(nullptr)                 # the REAL rendered normal-SSIM
    if sn > cur and refine_valid():  cur = sn       # accept the whole sweep
    else: restore topology from snapshot            # reject -> exact revert
    stock_pass(step * 0.25)                         # let vertices re-settle into the new mesh
```

### The two design decisions and their rationale

1. **Proxy-select, render-gate (never render per flip).** Per-flip rendering is
   `O(flips x render)` → instant TLE (the graveyard's "per-collapse full re-render" entry).
   `flip_tricost` (area·(1 − n_face·n_ref)) is a cheap, faithful *predictor* of a flip's
   normal-field effect, so it picks candidates; the real render validates the batch. This is
   the identical "cheap proposal, expensive monotonic accept" contract the position ascent
   already uses (cheap gradient step, real-render accept) — so D5 inherits its safety
   properties: **monotonic in the true metric, exact revert on reject, never worse than
   control.**
2. **Interleave with position ascent, don't run flips alone.** After a sweep changes the
   triangulation, the optimal vertex positions change too; `stock_pass` re-settles them into
   the new basin. Alternating is what makes this "connectivity *in the loop*" rather than a
   one-shot pre-pass (which is all `flip_pass` ever was).

### Safety / invariants
- **Manifold:** flipping an interior manifold edge whose opposite-vertex edge doesn't already
  exist keeps the mesh a closed 2-manifold; `EdgeExists(c,d)` enforces it. Boundary edges are
  never touched (a closed input has none).
- **Validity:** `refine_valid()` re-checks every alive face is non-degenerate after the sweep;
  the orientation guard prevents normal inversions.
- **Hausdorff:** vertices never move during a flip → Hausdorff is unchanged by the flip step
  (only `stock_pass` moves them, under its existing displacement cap).
- **Judge default:** `flipopt_for()` returns 0; only `getenv("G_FLIPOPT")` enables it →
  every judged case stays **byte-identical to v109** until a deliberate per-case promotion.

## Expected improvement (honest)

**Direct near-term deliverable: local SSIM headroom on cases 3 & 4.**
The one prior data point is **+0.0005 SSIM** (flips-alone, Session-1). Interleaving should
meet-or-beat it (it adds the position re-settle), but part of the gain may overlap what the
position ascent already captures — so plan for **+0.0005 to +0.002 SSIM** on cases 3/4, with
real downside risk of **~0** if the position optimizer already sits in a flip-insensitive
basin.

**Conversion to score is a separate, later step and is where the uncertainty compounds.**
SSIM does not add score directly — score is `(100/6)(1 − N/V)`; SSIM headroom only pays out
by letting a case **pass at a lower `keep`**. Rough conversion at the wall (slope
≈ 3.5e-5 SSIM/vertex, from the case-5 razor read):

| case | V | +0.0005 SSIM → verts of headroom | pts if realized via lower keep |
|---|---|---|---|
| 3 | 23,201 | ~14 | ~+0.010 |
| 4 | 35,292 | ~14 | ~+0.007 |

So **best-case ~+0.01–0.02 pts total** *if* the local gain transfers to the judge *and* we
then win the keep-lowering razor search. Both caveats are real: local SSIM gains have
historically over-rewarded vs the judge, and the keep search is its own per-run-coin lottery.

**Why do it anyway:** cheap (reuses a proven primitive), safe (env-gated, byte-identical
default, monotonic-or-revert), and it is the *only* structurally-new lever left un-killed.
Positive EV even at high variance. Verdict is gated on the results below, not on this estimate.

## Results

### Finding 1 (2026-07-06): the cheap `flip_tricost` proxy is ANTI-correlated with rendered SSIM — CLOSED

The render-gated batch was rejected on every organic case-3-band proxy (whole-sweep Δ ≈ −0.03).
The `G_FLIPDIAG` prefix ladder (sort candidate flips by proxy gain, apply the top-K, render the
real SSIM) shows the proxy is not merely coarse — **the single best proxy flip already loses**,
and the curve is monotonically negative:

| proxy | #cand | base SSIM | K=1 | K=8 | K=32 | K=128 | all |
|---|---|---|---|---|---|---|---|
| bunny-subdiv @keep .10 (1393 v out) | 544 | 0.815754 | −0.000047 | −0.000614 | −0.003927 | −0.011508 | −0.031305 |
| cow-subdiv @keep .08 (≈930 v out) | 394 | 0.811757 | −0.000002 | −0.001504 | −0.015031 | −0.028337 | −0.045447 |

**Diagnosis.** `flip_tricost = area·(1 − n_face·n_ref)` maximizes triangle-normal *alignment* to
the reference field — a **mean**-alignment objective. But the normal-map SSIM binding term is
*structure* (σxy / local **variance** match). Flipping to align normals *reduces* the local
normal contrast the structure term rewards → every proxy-preferred flip erodes SSIM. This is the
**mean-vs-variance trap** the graveyard names for geometric cost objectives; `flip_tricost` is
one. Confirms the Session-1 note ("this is the cheap-objective form") with data: **flips selected
by any cheap normal-alignment proxy are a dead end.** The manifold-safe primitive, the
render-gated monotonic-accept harness, and this diagnostic are kept (env-gated, judge-inert) as
the foundation for Finding-2 work.

### The redirect: flips must be selected by the REAL rendered SSIM (Finding 2 — TODO)

The Session-1 "+0.0005" was *flips-by-real-SSIM*. To select by real SSIM we need each candidate
flip's rendered-SSIM delta — but a full `refine_score_grad` per candidate is `O(flips × render)`
= the TLE trap at case sizes (7 000-vert output × hundreds of candidates × ~100–300 ms/render).

**The enabling primitive is a dirty-region SSIM delta:** a flip changes exactly 2 faces, touching
a *small image window* in the ≤6 views where they’re visible. Evaluating the box-SSIM change only
over that window (bounded pixels, not the full 512²×6) makes per-flip real evaluation affordable —
then greedily apply real-positive, non-overlapping flips and render-gate the batch. This is a
real build (incremental/dirty-region renderer + local box-SSIM accumulation), not a knob; it is
also **reusable** — the same localized-SSIM kernel could accelerate the whole position optimizer.

| mesh @ keep | band | control | +D5(real-SSIM) | Δ | #flips | valid | wall s |
|---|---|---|---|---|---|---|---|
| _TODO after localized-SSIM build_ | 3 | | | | | | |

### Judge probes — TO FILL

| sub # | case(s) | keep | verdict | score | notes |
|---|---|---|---|---|---|

## How to run the A/B locally

```
# control
./solver/main < mesh.obj > out_ctrl.obj
# D5 on (interleaved render-gated flips)
G_FLIPOPT=1 ./solver/main < mesh.obj > out_d5.obj
# score both with the oracle (imc_eval) and diff vertex counts / validity / Hausdorff
```
Optional knobs: `G_FLIPOPT_R=<rounds>` (default 3).
