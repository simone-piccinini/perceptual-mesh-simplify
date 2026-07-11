# The dirty-region SSIM kernel — build, results, and what remains

*2026-07-11. Road B Stage A/B from [../../docs/Future/STRUCTURAL-ROADMAP.md](../../docs/Future/STRUCTURAL-ROADMAP.md).
All work is local (0 judge submissions). Code lives in `solver/main.cpp` under
`#pragma region Dirty-region SSIM kernel`, entirely env-gated and judge-inert (the
default output is byte-identical to the pre-kernel HEAD — verified on bunny).*

---

## 1. Why this exists — the hypothesis

The leaders reach ~92; we sit at ~90.4. The whole gap is case 3 (organic). Phase 0
([../../docs/postmortems/case3-intrinsic-wall.md](../../docs/postmortems/case3-intrinsic-wall.md))
proved the case-3 deficit is **100% the SSIM structure term** — a *registration*
failure: the simplified facets carry the right normal *magnitudes* in the wrong
*pixels* (`l=1.000, c=0.998, s≈0.81`; deficit ⊥ our face allocation).

The decisive observation: **our analytic refine gradient is blind to exactly that
failure.** `refine_score_grad` differentiates the rendered SSIM through the face
*normals* at a **frozen pixel-to-face assignment**. It can *tilt* a facet, but it can
never *slide a facet boundary across a pixel* — and boundary sliding is the first-order
lever on the structure term σxy. A tangential vertex move (or an edge flip) is almost
pure boundary re-registration, invisible to our gradient. That is the subspace the
leaders' appearance-driven optimizers (nvdiffrast / Hasselgren 2021, flagged in
THEORY §8 Road B) descend, and it is exactly where the deficit lives.

To descend it CPU-side without a differentiable rasterizer, we need to score a *local*
mesh edit by its *exact* effect on the rendered SSIM in microseconds. That is the
kernel.

---

## 2. What the kernel is

A persistent per-view render + windowed-SSIM state that supports **incremental** edits:
apply a vertex move or an edge flip, and only the touched pixels are re-rasterized and
only the 11×11 windows whose support meets them are re-scored. The running score is
maintained exactly, so `Δ = kern_score_after − kern_score_before` is the true rendered
ΔSSIM of that edit, computed on the order of a millisecond instead of a 6×1024² frame.

**State** (`KView g_kv[6]`, one per axial camera):
- `pu/pv/pd` — per-vertex projection; `fid`/`zb` — per-pixel front face + depth.
- `Y[3]/Y2[3]/XY[3]` — the encoded current normal image, its square, and its product
  with the stored original — the fields the SSIM box sums consume.
- `Sy/Syy/Sxy` (current) and `Sx/Sxx` (original, fixed) — the 11×11 box sums.
- `Cw`/`Mw` — per-window SSIM value and counted-window mask; `A`/`N` — the view's
  running SSIM sum and window count (view score = `(A/N)/18`, summed over 6 views).
- `tile`/`fb` — a coarse screen-tile → face index (16-px tiles) + per-face pixel bbox,
  so re-rasterizing a dirty rect only tests faces that can cover it.

**Exactness by construction.** Every arithmetic step mirrors `refine_score_grad`
bit-for-bit — the same f32 storage round-trips of the window means, the same window
set, the same SSIM formula, the same z-buffer tie rule (candidates sorted by ascending
face id). So kernel deltas equal full-recompute deltas to float-accumulation ulps, and
revert = re-apply the inverse edit restores the state bit-identically.

**Operations** (documented per-function in
[../../docs/SOLVER-FUNCTION-REFERENCE.md](../../docs/SOLVER-FUNCTION-REFERENCE.md) §12):
`kern_begin` (build the full state), `kern_move(v,p)` (move a vertex → exact ΔSSIM),
`kset_face`+`kern_apply` (rewrite faces, e.g. a flip → exact ΔSSIM), `kern_score`,
and the fast box sum `kboxsum_rect`. Collapses are **not yet** supported (see §6).

---

## 3. How to reproduce (env flags; all local, judge-inert)

Build the case-3 proxy and solver per [../../scripts/phase0/RUNBOOK.md](../../scripts/phase0/RUNBOOK.md),
then on `.phase0/proxy_c3_orig.obj`:

| flag | what it runs |
|---|---|
| `G_KERNVERIFY=1` | Stage-A gate: kernel deltas vs full recompute (moves + flips) + speed, then exit |
| `G_KERNOPT=1` | unconstrained greedy tangential descent, 2 sweeps (evidence probe) |
| `G_KERNOPT2=<s>` | in-box deficit-prioritized descent, `<s>` CPU-seconds, inside the c3 read flow |
| `G_KERNOPT512=<s>` | descend at 512, then measure survival at 1024 (the resolution test) |
| `G_KERNFLIP=<s>` | true-metric edge-flip sweep at 1024, `<s>`-second budget |

`G_KERNOPTS` (sweeps), `G_KERNOPTT` (seconds), `G_KERNN`/`G_KERNM` (verify move/speed
counts) tune the probes. Every run prints a one-line `[kern]`/`KOPT2`/`KFLIP`/`RC3`
summary to stderr.

---

## 4. Results

### 4.1 Stage A — the kernel gate (PASSED)

| property | target | v1 | v2 (kboxsum + cropped begin) |
|---|---|---|---|
| move ΔSSIM vs full recompute | ≤ 1e-6 | **5.6e-16** | 5.6e-16 |
| flip ΔSSIM vs full recompute | ≤ 1e-6 | 3.3e-16 | 3.3e-16 |
| restore drift over 55k+ edits | 0 | **0.0** | 0.0 |
| edits/sec @512 | ~10³ | 381 | **1,241** |
| `kern_begin` cost | — | 0.40 s | **0.15 s** |
| default path judge-inert | byte-identical | ✓ (bunny vs HEAD) | ✓ |

The kernel is exact to machine epsilon and, after the narrow-column box sum
(`kboxsum_rect`) + coverage-cropped `kern_begin`, fast enough for in-box use.

### 4.2 Stage B, moves — registration descent

Greedy tangential descent (4 tangent-plane candidates per vertex, keep the best true-Δ
> 1e-7), from the **converged refine optimum** that defines our current wall:

| resolution | Sn before → after | Δ | note |
|---|---|---|---|
| 512, unconstrained (~5 min) | 0.879300 → 0.886616 | **+0.00732** | captured the full ±0.013 basin spread |
| **1024, unconstrained (~11 min)** | 0.807387 → 0.811755 | **+0.00437** | survives judge resolution, still gaining |

→ **The converged optimizer state is NOT registration-optimal.** The crudest descent
recovers the entire documented basin spread at fixed connectivity. The mechanism is
real.

**Result — the resolution-brittleness law (measured same-run).** Descend at 512, then
score at 1024:

| 512 gain | → 1024 survival |
|---|---|
| +0.000725 | **−0.000120** |
| +0.001460 | **−0.000815** |

Registration gains **invert** across resolution (transfer ≈ −0.5×): the optimizer fits
the pixel assignment of whatever resolution it runs at. This is the measured mechanism
behind the R1 / 768-native / SILv3 judge failures, and a rule going forward: **all
registration/position work must run at judge resolution (1024); sub-resolution local
gains are anti-signals, not weak signals.**

**Result — in-box moves are uneconomic.** At 1024 the descent runs ~350 trials/s; a
3.5 s slice buys +0.00033, an 8 s slice +0.00061 (vs the +0.0044 asymptote at ~140 s).
The deficit is spatially broad (Phase-0 Gini 0.237), so deficit-prioritization
concentrates the yield only ~4×. Net of the phase-B box time it steals, an in-box move
slice is roughly zero-sum.

### 4.3 Stage B, flips — the connectivity channel (works)

The graveyard killed *cheap-proxy* flips (`flip_tricost`, a mean objective,
anti-correlated with SSIM). This is the real thing: every interior edge trialled by its
**exact rendered ΔSSIM** at 1024, accepted only when the true metric rises.

| budget | ΔSn | flips accepted / trialled (of 20,812 edges) |
|---|---|---|
| 8 s (in-box shape) | **+0.00197** | 442 / 4,936 |
| full sweep (~25 s) | **+0.00372** | 1,268 / 17,392 |

~9% of legal flips are net-positive under the true metric; ~660 trials/s (cheaper than
moves); measured **natively at 1024**, so no resolution-transfer question in the local
setup. This is the first flip mechanism to show positive true-metric yield since the
proxy version was buried.

### 4.4 The channels stack

Descent (45 s, +0.00272) then flip sweep (+0.00351; standalone +0.00372 → ~5% overlap),
on the same read-state mesh:

- combined: Sn 0.807417 (baseline) → **0.813653** = **+0.0062 Sn** in ~90 s.
- asymptotic ceiling (descent to +0.0044 convergence + flips +0.0037, ~5% overlap):
  **≈ +0.008 Sn**.

---

## 5. What was established — the honest ledger

1. **The kernel is a proven instrument:** bit-exact, judge-inert, 1,241 edits/s. It is
   reusable infrastructure for every remaining Road-B experiment.
2. **The registration+connectivity headroom is real:** ~+0.008 Sn exists above the
   converged pipeline at judge resolution — the leaders-hypothesis mechanism *is* there.
3. **Registration gains are resolution-brittle** (−0.5× across 512→1024) — a durable
   law that retro-explains three past judge failures.
4. **Post-hoc polishing has a small ceiling.** Convert the asymptotic +0.008 Sn:
   ≈ +0.004 Final ≈ ~114 case-3 vertices (slope 3.5e-5 Final/vertex) ≈ +0.49 case-3
   compression ≈ **+0.08 mean** — and that is the *unconstrained, perfect-transfer*
   ceiling. The **21 s CPU box caps in-box capture at ~+0.002–0.0025 Sn ≈ +0.02–0.03
   mean**. Either way this specific mechanism, alone, is an order of magnitude short of
   the +0.6 mean that 91 needs.

**Conclusion:** post-hoc kernel polishing is a real but minor lever (~+0.02 in-box,
~+0.08 ceiling). It is **not** by itself the road to 91/92. Its value is (a) the first
judge-transferable connectivity signal to test, and (b) proof that the kernel works —
the substrate the actual 91 attempt needs.

---

## 6. What is left to do

### Tier 1 — cheap, decides everything downstream
- **Stage C: judge-transfer test (2 zero-risk READ submissions).** Does *any* of this
  transfer, or is it R1 again? Clean A/B design: in BOTH read arms disable phase-B
  (the box-cut source) so each run is deterministic-per-binary; arm A = current config,
  arm B = the 8 s flip slice in phase-B's place. Judge-side S2 then compares at ±1
  quantum (5e-4), and simultaneously answers "flip slice vs phase-B" allocation.
  De-razor cases 4/6 for clean attribution. *If arm B ≤ arm A on the judge, the whole
  post-hoc channel is dead (proxy over-reward) and Tier 2–3 are not worth building.*

### Tier 2 — the real mechanism (unbuilt; the actual 91 candidate)
Everything above is **post-hoc polishing of a fixed-connectivity wall mesh**. The
approved plan's core — **kernel-driven co-decimation** — is *not yet built*: rank the
final-stretch **collapses** by their true rendered ΔSSIM (not the geometric VSA proxy)
and interleave flips/ascent, so the decimation reaches a **better basin / lower V'_min**
directly, instead of polishing a worse one. This is a bigger lever than post-hoc
polishing because it changes *which* mesh you end at, not just its positions.
- **Prerequisite:** teach the kernel to apply a **collapse** (delete 2 faces + rewire),
  maintaining the incremental state — currently it supports moves and flips only. This
  is the one substantial engineering gap.

### Tier 3 — capture the full channel in-box (the heavy build)
- **Analytic boundary gradient.** The kernel *probes* (4 candidates/vertex, discrete
  flip trials); a differentiable-rasterizer **edge term** (silhouette + internal
  boundary sampling, nvdiffrast-style, on our CPU rasterizer) would give the descent
  direction directly — ~10× fewer evaluations, reaching the +0.008 asymptote inside the
  box instead of ~5% of it. This is the only visible route to capturing the full
  channel within 21 s, and the closest thing to the leaders' actual method.

### Tier 4 — opportunistic
- **Case-5 twin.** Same organic regime; re-run the flip sweep + Stage-C read there for a
  free second win if case 3 transfers.
- **Kernel speed:** the box sum can be SIMD/column-blocked for another ~2–3×; only worth
  it once a mechanism is judge-confirmed.

---

## 7. Risk, stated plainly

This is the same risk class that killed R1 (comparable local gains, 0/3 on the judge):
armadillo-derived proxies systematically over-reward position-space optimization. The
flip channel is a *different subspace* (discrete connectivity vs continuous shading
micro-opt) and is measured natively at 1024, which are reasons for cautious optimism —
but only the judge decides. Per WALL-MODEL §5.5: **no descent on local evidence; the
Stage-C read comes first.** Every number in this document is local.
