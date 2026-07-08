# case-3 LIMITS — the honest map of what is tested, what is dead, what is open

**Purpose.** case-3 is the anomaly: we sit at ~70% while every other case is 85–99%. (The leader's
case-3 is plausibly ~72–77%, NOT the ~85% the docs used to claim — see Front B for the arithmetic.)
This file is the reference for *what we can still do and what we cannot*, across every front, with a
provenance tag on every claim. Read the TL;DR, then the front that matters to your idea. Truthful
and English by rule — update it on every probe.

**Provenance legend (applied per line):**

| tag | meaning | trust |
|---|---|---|
| `[JUDGE]` | confirmed on the real Kattis judge | hard fact |
| `[INFERRED]` | arithmetic from judge scores (V, N, wall) | hard fact |
| `[LOCAL]` | screened on a proxy mesh only — **does NOT transfer** (Front E, §9.1) | weak evidence |
| `[UNTESTED]` | never probed on the judge | unknown |

**One-line state.** case-3 = **v111, N=6941, 70.083% compression** (banked in the 90.285538 total).
Input V=23,201. Score per case = `100·(1 − N/V)`. Wall is a per-run coin, not a sharp N.

---

## TL;DR — the answer, up front

| front | question | answer | provenance |
|---|---|---|---|
| **A. Compression wall** | Can we ship fewer vertices with *this* pipeline? | **No. Wall = (6912, 6941], effectively closed.** 6941 passes; 6912/6900/6800/6700 all WA. | `[JUDGE]` |
| **B. Mechanism** | Can a *better* simplifier lower the wall? | **Prize is small (leader_c3 ~72–77%, not 85%). Every cheap lever is dead; VSA remesh (paradigm change) now measured dead too.** | mixed |
| **C. Judge/metric** | What actually binds case-3 at 0.90? | **Normal-map structure (σxy correlation).** Depth saturated, Hausdorff loose, topology genus-0. | `[JUDGE]` |
| **D. CPU budget** | Is time the wall? | **No.** case-3 refine converges ~13–14s of the 21s box. It is a quality wall, not a time wall. | `[JUDGE]` |
| **E. Instruments** | Can we trust local screens / the S-read? | **No, near the wall.** S2 self-score ~+0.010 optimistic; local proxy gains transfer ≈ 0. | `[JUDGE]` |
| **F. Automation** | Can an agent pin this without a human? | **Yes, submit is scripted.** One wrinkle: a coin-loss on an untouched case breaks auto-decode. | `[JUDGE]` |

**Bottom line:** the *compression* limit of the current pipeline is now **pinned and exhausted**
— nothing left to harvest below 6941. The remaining opportunity (Front B) is **smaller than the
docs claimed** (leader_c3 ~72–77%, a ≤7-pt gap likely shared with other cases, not a 15-pt case-3
mystery) and **hard**: cheap tweaks are dead and the first paradigm change (VSA remesh) is now
measured dead too. What's left (isotropic remesh, differentiable co-opt) is heavy and low-odds.

---

## Front A — The compression wall (lowest N that still passes)

The wall is **pipeline-relative** (WALL-MODEL §1) and a **box-cut coin**: CPU-box timing jitter
re-rolls the float order → a slightly different mesh each run, so near the razor it is a
distribution `P(pass | N)`, not a hard threshold (σ ≈ 0.001–0.002 SSIM).

| N | compression | status | provenance |
|---|---|---|---|
| 6954 | 70.027% | PASS (old family, pre-twin) | `[JUDGE]` |
| **6941** | **70.083%** | **PASS ×2 — BANKED (v111)** | `[JUDGE]` twin-read bank 19898599 |
| 6940 | 70.087% | PASS, self-score S2=0.9135 | `[JUDGE]` S-read 19898572 |
| 6912 | 70.208% | **WA** (friend's probe) | `[JUDGE]` |
| 6900 | 70.260% | **WA** | `[JUDGE]` 2026-07-07 (id 19912982) |
| 6800 | 70.691% | **WA** | `[JUDGE]` 2026-07-07 (id 19912949) |
| 6700 | 71.122% | **WA** (c4 also coin-lost that run) | `[JUDGE]` 2026-07-07 (id 19912623) |

**Verdict: wall ∈ (6912, 6941]. CLOSED.** Four independent probes below 6941 all WA
(6912/6900/6800/6700), and three separate mechanisms were falsified below 6941 in prior sessions
(ATTEMPT_LOG line 772). The harvest below 6941 is ≤29 vertices ≈ +0.125 pts on case-3
(≈ +0.021 on the total) *if 6912 even passed — and it does not.* Realistic harvest = **0**.

**Why the S2=0.9135 "headroom" is a mirage.** The self-score read 0.9135 at N=6940, which looks
like +0.0135 of slack above 0.90. It is **not harvestable**: that margin is anchored to the
*banked-primary family*'s exact float trajectory (ATTEMPT_LOG line 736). Any code change that
would let you cut deeper re-rolls the family and the margin evaporates — which is exactly why
6900 WA'd despite the read. **Lesson: near the wall, trust judge pass/fail, never the optimistic
S2.** (This corrected the earlier "+0.10 un-harvested" guess, which was wrong.)

---

## Front B — The mechanism limit (can a better simplifier lower the wall itself?)

This is the front with the real prize, but the prize is **smaller than the docs claimed**.
⚠ CORRECTED 2026-07-08: the old "leaders ~85% on case-3" is arithmetically wrong. Total gap to the
leader (91.46 − 90.286 = 1.174 on the MEAN) = **7.05 summed** over 6 cases; if the *entire* gap were
case-3, leader_c3 = 70.08 + 7.05 = **77.1%**, and it almost surely spreads across c4/c5/c6/c7 too →
leader's case-3 is plausibly **72–77%**, only **2–7 pts** above ours. `[INFERRED]`. So there is no
"2× efficiency" mystery. The wall is still *our pipeline's* (history proves it moves when the
mechanism improves), but the realistic headroom is modest — favor cheap bets over heavy builds.

### B.1 — How the wall was lowered historically (past work that WORKED) `[JUDGE]`

| milestone | case-3 | lever that moved it |
|---|---|---|
| baseline greedy QEM | ~66% | plain edge-collapse |
| + visibility culling | 67% | drop faces never seen by the 6 cameras |
| **+ VSA-lite** | **69%** | **order collapses by induced normal distortion (L2,1) — largest single lever** |
| + Pivot-A λ=16 (per-case retune) | 69.75% | metric-in-the-loop contrast-deficit steering |
| + s-def steering | 69.875% | structure-deficit steering (broke a wall closed ×5) |
| + ST hybrid-1024 refine | 70.031% | re-render original at 1024 for the final refine pass |
| + twin-read family selection | **70.083% (6941)** | pick the box-cut family that reads deepest |

So the wall fell ~4 points over the project — but **entirely via normal-distortion-aware
ordering/placement and refine throughput**, never via a cheap post-hoc tweak. Those levers are
all ON in v111 and are now jointly saturated.

### B.2 — Mechanisms that FAILED on case-3 (do NOT repeat without a new angle)

Judge-tested dead (`[JUDGE]` — real submissions):

| idea | judge result |
|---|---|
| R1 interleaved decimate↔refine | +0.0015–0.002 local, **WA'd banked rung ×2** — proxies over-reward it |
| 768-native refine | local +0.00067, **judge-negative** |
| λ 12/24 sweep | 70.06 rung **WA'd both regimes** → λ set closed |
| descent 6931 / 6944 (R1-era) | WA'd (mechanism-confounded — R1 was on) |
| construction paradigm (main_v2) | caps ~64 globally; collapse-mesh rounds features; **not a case-3 win** |

Local-screened negative (`[LOCAL]` — weak evidence, see Front E; not judge-tested):

| lever | local Δ self-score | note |
|---|---|---|
| nmetric=3 (true closed-form SSIM-loss placement) | **−0.010** | family closed; also worse on c4/c5 |
| nmetric=4 (tempered SSIM-loss) | −0.0013 | only plausible transfer-flip, low odds |
| SIL (silhouette/depth channel) on c3 | −0.0012 | depth +0.0005, but normal −0.003 (rim hurts interior) |
| Laplacian/Sobolev preconditioner (G_LAPL) | negative | λ=8/20/50 all worse |
| unsharp-mask vertex sharpen (G_SHARP) | picks α=0 | no gain under real SSIM |
| projected-area VSA weight (G_PROJW) | +0.0000 on c3 | (+0.0008 c4, +0.0009 c5 — not c3) |
| Lloyd relaxation (G_LLOYDM) | negative | P=1/4 both below baseline |
| global output scale sweep | peaks at 1.0 | ±0.0005 both directions |
| deficit-guided edge-split reallocation (A) | closed (E1 proxy) | the "split budget where SSIM hurts" idea — no transfer |
| **Full VSA remesh (new topology)** — ROAD 1 | **−0.10 at equal V** | **STRUCTURAL** loss (0.75 vs QEM 0.85 @ 4200v on the organic proxy); built + valid, measured >2.5× less efficient. Flat facets are wrong for organic. Struck 2026-07-08. |

**Verdict: the cheap mechanism space is EXHAUSTED, and now the first paradigm change (VSA) is dead
too.** Everything that costs one knob lost; VSA (a genuinely different topology) lost STRUCTURALLY
by −0.10 at equal V — and a structural local loss is strong evidence (unlike position-tweak local
noise). What VSA taught: the winning case-3 mesh is **smooth + dense + adaptive** (the QEM family);
flat/partition topology is the wrong direction for an organic surface. So the remaining candidates
must stay in the smooth family (Front B.3), and the honest odds there are low.

### B.3 — The remaining doors (all UNBUILT, all low-odds after VSA + the premise correction)

VSA's death + the 77%-not-85% correction shrink this. The candidates, honestly ranked:
1. **Curvature-adaptive isotropic remesh** — a smooth NEW triangulation (small quality triangles,
   edge-length ∝ feature size), NOT flat VSA. In the right (smooth) family; might beat QEM's
   error-driven triangle shapes. Heavy, untested — the only genuinely-new smooth idea.
2. **Differentiable co-optimization during reduction** (THEORY Road B item 2) — optimize positions
   *during* reduction on the rendered-SSIM gradient. But R1 (its burst form) was judge-NEGATIVE ×2,
   and the refine already does the post-hoc version (converged) → close to measured-dead.
Both are `[UNTESTED]`, heavy, and transfer-risky (Front E: position-space gains have transferred at
ratio ≈ 0). Given the corrected prize (≤7 pts, not 15) and VSA's death, neither is an obvious spend
— the honest read is that case-3's mechanism front may simply be near its practical ceiling.

---

## Front C — Judge/metric limits (what actually binds case-3) `[JUDGE]`

- **FinalSSIM = 0.5·normal + 0.5·depth ≥ 0.90.** case-3 self-score split: normal ≈ 0.805,
  depth ≈ 0.984. The deficit is entirely on the normal side.
- **The binding term is normal-map STRUCTURE** — the σxy correlation term of SSIM, not luminance
  or contrast (PROBLEM-AND-JUDGE §7; the l·c·s split shows σ matches, correlation doesn't).
- **Depth is saturated (≈0.984).** SIL reaches only +0.0005 on depth → depth is **not a lever**
  for case-3. Do not spend effort there.
- **Hausdorff is vertex-to-vertex, ≤5% AABB diagonal — loose, NEVER binds** at case-3's N. Faces
  (the surface) carry no geometric constraint. Stop treating it as active.
- **Topology is genus-0.** Surgery/handle-removal has **zero prize** here. Disconnected & nested
  output is legal (the S-read exploits this with invisible tetrahedra).
- **SSIM window is 11×11 BOX, not Gaussian** — a Gaussian window mis-reads the operating point by
  ~0.047, so any local oracle must use the box window or it lies.

---

## Front D — CPU / budget limits `[JUDGE]`

- **Ceiling = [21, 22)s single-thread**, billed **summed across threads** → multithreading is
  suicide (v60/v63 TLE lesson). A `sleep(25)` TLEs; `sleep(sub-21)` passes.
- **case-3 refine converges ~13–14s** (float32) of that box → **case-3 is a quality wall, not a
  time wall.** More time would not help; a better trajectory would.
- Because the pipeline finishes with box-cut headroom, **any code change re-rolls the box-cut
  mean of the OTHER cases** (WALL-MODEL §3) — this is why an isolated case-3 edit can WA case-4.
- Source ≤128 KiB; compile-memory is at the cliff — **strip dead code (Eigen/Sparse, G_LAPL,
  G_ADAM) before adding** any new mechanism, or it won't compile.

---

## Front E — Instrument limits (why local measurements don't decide) `[JUDGE]`

This is the trap that has burned every "it's +0.002 locally" bet.

- **The transfer wall (§9.1).** Local position-space optimizer gains on proxy meshes (armadillo-
  derived) transfer to the judge at ratio **≈ 0 to negative** — measured across three mechanisms.
  Proxies over-reward fine optimization. So a `[LOCAL]` win is **weak evidence**, and a large
  `[LOCAL]` loss flipping to a judge win is **unsupported**. We cannot train on case-3's real
  mesh locally (we don't have it) — this is the core reason case-3 is hard to attack offline.
- **What DOES transfer:** raw throughput (float32, more iterations of the *same* trajectory,
  ratio ≈ 1) and the **SIL coverage channel** (systematic chord-bias correction, ratio ≈ 0.3).
  Both are already banked. Everything *intensifying* them further has hit zero.
- **The S-read (Level B) is ~+0.010 optimistic near the wall** — worse than the doc's original
  +0.005 estimate. Proof: S2=0.9135 read at 6940, yet 6900 WA'd. Use the S-read for *relative
  A/B at a SAFE N above the wall*, never to predict the absolute wall.

---

## Front F — Automation limits `[JUDGE]`

- **Submit IS scriptable.** `scripts/judge_submit.py` logs in and submits via the `~/.kattisrc`
  token; 403 only affects standings scraping, not submission. The plan→preflight→submit→decode
  loop (probe/harness.py) runs autonomously.
- **Known wrinkle:** the harness auto-decode assumes untouched cases pass. When an *untouched*
  case coin-loses in the same run (e.g. c4 during the @6700 read), auto-decode breaks and the
  agent must attribute the extra WA to the coin and decode manually.
- **No rejudging + best-counts** → every failed probe is free forever. Probe aggressively; the
  bank is protected.

---

## The doors left (and the honest odds)

Everything cheap is measured and closed; the compression wall is pinned at 6941; and the first
paradigm change (VSA remesh, ROAD 1) is now measured dead — flat/partition topology is the wrong
direction for an organic surface (the winning mesh is smooth+dense+adaptive, the QEM family). The
premise is also corrected: leader_c3 ~72–77%, not 85%, so the prize is ≤7 pts and likely shared
with other cases. What remains (all `[UNTESTED]`, heavy, low-odds): a curvature-adaptive isotropic
remesh (smooth NEW triangulation — the one genuinely-new idea in the right family) and
differentiable co-optimization during reduction (≈ the judge-negative R1). The honest read: case-3's
mechanism front may be near its practical ceiling; big gains, if anywhere, may not be case-3-shaped.

*Sources: WALL-MODEL.md, JUDGE-ENVELOPE.md, THEORY.md §8–§9, PROBLEM-AND-JUDGE.md, ATTEMPT_LOG.md,
RESULTS.md, and case3-lab judge probes 2026-07-06/07.*
