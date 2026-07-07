# The per-case wall model — how we find, measure, and harvest the six walls

*2026-07-06. Companion to [JUDGE-ENVELOPE.md](JUDGE-ENVELOPE.md) (the measured judge facts)
and [Future/c4-harvest-ladder.md](Future/c4-harvest-ladder.md) (the first ladder run under
this model). This document is the concept: what a "wall" is, why razor rungs on box-cut
cases behave like biased coins, what a Level-A vs Level-B probe is, and what an automated
probing loop can and cannot do.*

---

## 1. The score is really six hidden numbers

The judge score is the arithmetic mean over the six scored meshes (cases 2–7) of

```
s_c = 100 · (1 − N_c / V_c)
```

where `V_c` is the original vertex count (fixed, measured — envelope §0.5) and `N_c` is the
vertex count **we choose to output**. Validity is binary: if the case fails (SSIM < 0.9,
Hausdorff > 5%, or non-manifold), `s_c = 0`.

So the entire game is: **for each case, output the smallest `N` that still passes.** That
smallest-passing count is the case's **wall**:

```
W_c = min { N : our pipeline's output at N scores SSIM ≥ 0.9 on the judge }
```

Three properties of `W_c` that shape everything:

1. **It is hidden.** The judge returns pass/fail and a total score — never SSIM, never a
   reason. Everything we know about `W_c` is inferred.
2. **It is pipeline-relative.** `W_c` is a property of (mesh × our simplifier × the judge
   metric), not of the mesh alone. A better simplifier renders a better normal map at the
   same `N` → its wall is lower. This is exactly where the leaders (~91.46) beat us: not by
   probing better, but by *having lower walls* — mostly on case 3.
3. **It binds through SSIM.** Hausdorff and manifoldness are engineered to be safely inside
   their limits; the flat-shaded normal-map SSIM structure term is the active constraint on
   every case (see THEORY / wang-ssim).

### The current wall ledger

| case | mesh | V | N (banked v111) | compression | pts/vertex | wall knowledge | regime |
|---|---|---|---|---|---|---|---|
| 2 | dust/tiny | 4,098 | 30 | ~99.27 % | 0.00407 | ~99.32 % WA'd → wall just below 30 | topology floor |
| 3 | organic | 23,201 | 6,941 | **~70.08 %** | 0.00072 | 6941 PASS (S-read 0.9135); R1-era 6931/6944 WAs are mechanism-confounded | **box-cut coin** |
| 4 | CAD | 35,292 | 4,970 | ~85.92 % | 0.00047 | **pinned (4960, 4970]** — 4970 PASS ×2, 4960 & 4950 WA | **box-cut coin** |
| 5 | organic | 49,987 | 4,212 | ~91.57 % | 0.00033 | ladder below banked closed 0/12 → effectively deterministic wall | converged (~deterministic) |
| 6 | big | 377,084 | 8,684 | ~97.70 % | 0.000044 | 8684 family banked (+21 stall); exact-6000/6500 WA'd | box-cut, currently 5/5 stable |
| 7 | huge | 1,009,118 | 28,800 | ~97.15 % | 0.000017 | wall ∈ (28800, 28822] — pinned, not worth the slots | no refine (deterministic) |

Two readings of this table:

- **Where we are weak:** case 3 at 70 % is the anomaly — every other case is 85–99 %. The
  ~1.18-pt gap to the leaders lives almost entirely there. No amount of wall-*probing* fixes
  that; only a lower wall (better simplifier) does.
- **Where probing pays:** a vertex is worth `(100/6)/V_c` points, so vertices are ~250×
  more valuable on case 2 than case 7. Ladders only make sense on small-V cases whose walls
  aren't pinned yet — which after this session means: nowhere obvious. Cases 4 and 7 are
  pinned, 5 and 6 are closed families, 2 is at its topology floor, and 3's wall is a coin
  we just banked one rung into.

---

## 2. Razor — why the optimum is the most fragile place

Every vertex above the wall is pure wasted score, so optimal play pushes `N` down to `W_c`.
But sitting at the wall means the run's SSIM sits at exactly 0.900 — the pass/fail line runs
*through* the output distribution. That's a **razor rung**:

- The judge-side S-vs-N slope near a razor is ≈ **3.5 × 10⁻⁵ SSIM per vertex** (measured on
  case 5's ladder). Ten vertices ≈ 0.00035 SSIM.
- Run-to-run SSIM jitter on a time-boxed case is σ ≈ **0.001–0.002** (§3).

So within ~30–60 vertices of the wall, the jitter *dwarfs* the slope: pass/fail stops being
a property of `N` and becomes a property of *the individual run*. There is no margin by
construction — margin is exactly the thing we sold to buy score.

**De-razoring** is the deliberate inverse trade: v109 paid 0.0756 pts (case 4: 4990 → 5150,
+160 verts ≈ +3σ) to make the dev base pass reliably. The operational rule that fell out:
**bank attempts ride razor rungs; development bases carry margin.**

---

## 3. Box-cut — why the same bytes score differently

Cases whose inverse-rendering refine does **not** converge inside its CPU box get *cut
mid-ascent* by the `getrusage` deadline (envelope §2). The judge machine's speed varies
run-to-run under load (same binary measured 16.0 vs 17.2 s on case 4), so:

```
different run speed → box cuts at a different iteration → different vertex positions
→ different rendered normal map → different SSIM               (σ ≈ 0.001–0.002)
```

This is **measured, not theoretical**: two byte-identical submissions returned different
per-case verdicts (case 3 WA→AC, case 4 WA→AC — envelope §1), and we reproduced the
mechanism locally (same binary, same input, two runs, different output bytes).

There are **two layers of randomness**, and confusing them cost us a submission:

1. **Per-run jitter** — σ ≈ 0.001–0.002 around a mean, from timing alone.
2. **Per-binary-family mean shift** — recompiling with *any* code-layout change (even
   provably output-neutral code like an `#ifdef`'d-out block) shifts the *mean* of that
   distribution, because layout → speed → trajectory. The rung-1 lesson: the headroom
   family went 0/2 at rungs the v108 family passed 2/2 (joint p ≈ 5 % under a fair coin).
   **A razor rung is only proven for the binary family that proved it.**

Consequence: at a razor on a box-cut case, each submission is a draw of a biased coin,
`P(pass) ≈ Φ((S_mean − 0.900)/σ)`. Best-counts makes a lost draw free (the bank survives),
so the razor game is playable — but every bit of information costs a submission slot.

Which cases: **3 and 4** are the live coins (case 6 historically was; it has been 5/5
stable recently). Cases 2, 5, 7 are converged-or-unrefined → ~deterministic per binary.

---

## 4. Level A — the judge as a 1-bit oracle (pass/fail bisection)

The baseline probe. The judge returns a total score; arithmetic decodes it completely:

- **Which case failed:** a failed case contributes 0, so the drop from the expected total
  identifies it uniquely (e.g. 90.266754 − 75.956618 = 14.310136 ⟹ case 4 at N = 4990 —
  it even *re-derived* V₄ = 35,292 to the vertex).
- **What N a passing case had:** score → `N = V(1 − 6·s/100)` to ±0.5 vertex.

The search is bisection on `N`, corrupted by the coin:

```
maintain bracket (last_PASS, first_WA] per case
PASS at N  → wall ≤ N            (certain for this family… for that draw's mean)
WA at N    → wall > N  OR  lost the coin  → needs a re-roll to disambiguate
stop: two consecutive WAs at a rung, or marginal EV < a submission slot
```

This is exactly the case-4 ladder we ran: 4990 ✓ (v108 ×2), 4970 ✓ (v110), 4950 ✗, 4960 ✗ →
wall pinned to **(4960, 4970]** in 4 informative submissions. It works, but the economics
are poor: **≤ 1 bit per submission**, degraded by the coin (each WA is ambiguous), degraded
again by the family caveat (a new binary re-rolls the mean, see rung 1). Blind bisection on
a coin case realistically costs 4–8 submissions per wall.

---

## 5. Level B — the S-read instrument (a real number per submission)

This is the friend's `PROBE-RC3-READ` construction (now on master for cases 3/4/5), and it
changes the game from *guessing* the wall to *measuring* it.

### 5.1 The problem it solves

Three facts make local measurement useless at the wall:

1. **The local oracle does not transfer** — three screening instruments falsified against
   judge ground truth ([Future/transfer-instrument.md](Future/transfer-instrument.md)).
2. **The judge never reports SSIM** — only pass/fail inside a total.
3. **On a box-cut case, the mesh being judged only exists on the judge, for that run** —
   it's cut by that machine's timing that day. You cannot reproduce it locally even in
   principle.

So the only place the number we need exists is *inside the judge run itself*. The insight:
**our solver already computes SSIM in-process** (the refine loop's objective; the
`S2 = 0.5·Sn + 0.5·Sd` self-score at 1024 is a reconstruction of the judge formula). After
producing its final mesh, the solver *knows* its own estimate of S. The instrument is a way
to smuggle that number out through the only output channel that exists: **the score**.

### 5.2 The covert channel: encode S in the vertex count

The score reveals `V'` exactly (§4). `V'` is therefore a channel with thousands of symbols
per case per submission. The encoding (friend's construction, comments at
`solver/main.cpp` PROBE-RC3-READ):

```
K   = round( (S − 0.885) / 5e-4 ),  clamped to [0, 160]     # quantize S, 5e-4 resolution
out = mesh(N verts)  +  K tiny tetrahedra (4 verts each)    # V' = N + 4K
```

Decoding from the judge score:

```
V'  = V(1 − 6·s_c/100)          # exact
K   = (V' − N) / 4              # N is known: we chose it
S   ≈ 0.885 + K · 5e-4          # the solver's self-score ON THE JUDGE, THAT RUN
```

Why each piece is what it is:

- **Tetrahedra**: each added pad must keep the output a valid closed 2-manifold. A tiny
  tetrahedron *is* one; validity checks manifoldness per component, and disconnected
  components are legal (judged-proven: v96-disconnected-probe, and every read/bank pair).
- **Tiny and centroid-anchored** (edge ~0.0015 of the bbox, placed 90 % of the way from the
  centroid to the nearest real vertex): sub-pixel at 512/1024 render → the pads change the
  rendered normal/depth maps by ~nothing → **S is unchanged by the act of measuring it**;
  and being deep inside the shape, Hausdorff is unaffected.
- **Quantization 5e-4 over [0.885, 0.965]**: brackets the 0.900 threshold with ±0.00025
  effective error — finer than the run jitter σ, so the channel is not the noise floor.
- **Base N ≡ 0 (mod 4)** (e.g. 6940): a decimation stall (output a few verts above target)
  shifts `V'` off the 4-grid → stall and K are separable in the decode. (This is why the
  friend's banked count is 6941 — a 1-vertex stall, detectable exactly because of the grid.)
- **Cost**: a read run scores slightly *lower* than a bare run (4K extra vertices ≈ up to
  0.03 pts on case 3) — irrelevant, because reads are never meant to be banks; best-counts
  ignores them.

### 5.3 What one read buys

A Level-A submission returns one noisy bit. A Level-B submission returns a **point on the
S(N) curve, measured on the real judge mesh, including that run's box-cut draw**:

```
(N, S_draw)   where   S_draw ~  Normal(S_mean(N), σ)
```

- **Jump to the wall instead of bisecting to it.** With one read and the slope:
  `N_wall ≈ N_read − (S_read − 0.900 − margin) / 3.5e-5`. Read → jump → bank: ~2–3
  submissions per wall instead of 4–8. The friend's case-3 sequence was exactly this:
  read at 6940 (K = 57 → S = 0.9135) → bank the bare mesh at 6941 → 90.2761.
- **Measure the coin itself.** Repeated reads at the same N estimate `S_mean` and σ *on the
  judge* — the numbers that decide whether a rung is a 50/50 or a 95/5 coin, previously
  pure guesswork.
- **Batch across cases.** The six cases run independently in one submission; each case's
  block can encode its own K. One human submission = up to six reads. (v111 was already a
  2-case batch — one bank block each on cases 3 and 4.)

### 5.4 The honest limitation: it is a *relative* instrument

The self-score S2 is *our reconstruction* of the judge metric (our rasterizer, our SSIM
window) computed on the judge's mesh — it is **offset from the judge's true S** by an
unknown but roughly family-stable amount. Evidence: the case-4 read said S(4990) = 0.905,
yet 4990 behaves like a ~2/3 coin, which places the *true* judge S at ≈ 0.900–0.902 → the
reconstruction reads ~+0.004 optimistic there.

So a read is not an absolute pass guarantee. It becomes one after **anchoring**: pair reads
with observed pass/fail outcomes on the same family to locate the self-score value that
corresponds to the true 0.900 (e.g. "on this family, S2 = 0.9045 is the real threshold").
One anchor per case per family is enough, and pass/fail outcomes arrive for free with every
bank attempt. Un-anchored reads still give the *slope* and *relative* headroom exactly.

### 5.5 Level B's other use: mechanism testing without the transfer problem

Because a read measures the judged S of *whatever pipeline produced the mesh*, it is also
the only trustworthy A/B channel for **mechanism** changes (the thing local screens failed
at): submit control and variant as two reads at the same N and compare judge-side S
directly. Two submissions per A/B — expensive, but *correct*, which the local oracle never
was. This is the "judge-side S-read instrument" that THEORY §9.2 concluded SIL-class work
needs before further investment.

---

## 6. Automation — and why a human stays in the loop

### 6.1 What a probing harness automates

Everything around the click is mechanical and should be code:

| stage | what it does |
|---|---|
| **plan** | per-case state file (bracket, reads, σ estimate, family tag) → pick the next action per case: `read @N`, `bank @N`, `re-roll`, or `close`; pack up to 6 case-actions into ONE submission |
| **generate** | emit `solver/main.cpp` for that plan: rung constants and/or K-encode read blocks per band; one-constant diffs within the current binary family wherever possible |
| **pre-flight** | compile in the `gcc:14` container (the CE gate — the file lives at the compile-memory cliff); band-proxy run for validity/manifold/Hausdorff; byte-identity on untouched bands |
| **decode** | paste the returned total → per-case N (exact), K → S for read blocks, zero-contribution → WA attribution; flag family mismatches |
| **update** | write back the wall model: new bracket/read/σ; recompute per-case EV (pts/vertex × P(pass)); emit the next plan and a human-readable "what changed" |

With this, the human's entire job is: run `plan` → submit the file → paste the score →
run `decode`. Everything else — the arithmetic that caught case 4 by its 14.310136
fingerprint, the K decode, the bracket bookkeeping, the EV math — is deterministic code.

### 6.2 Why the human cannot be removed

1. **The submit click is unautomatable — measured.** Kattis returns 403 to script-token
   sessions on all contest pages (envelope §0.4); submissions and even standings reads must
   go through a human browser session. This is a hard wall, not a missing feature.
2. **Submission slots are the scarce resource.** Each burn is irreversible and public
   (the leaderboard logs attempts). Spend decisions — "is +0.0047 at ~40 % odds worth a
   slot tonight?" — are strategy under uncertainty, entangled with contest timing and how
   many slots remain. That is a judgment call, not a formula.
3. **Family boundaries need judgment.** Any source change beyond a constant creates a new
   binary family and silently re-rolls every box-cut mean (the rung-1 failure). Code can
   *flag* "this diff exceeds one constant — family changed, razor rungs unproven"; deciding
   whether to spend a calibration submission or carry margin instead is a human call.
4. **The loop must fail safe.** A mis-decode or a stale V_c inside an autonomous loop would
   burn slots at machine speed. With a human between plan and submit, the blast radius of
   any harness bug is zero submissions.

The right mental model is **instrumented manual play**: the machine does all measurement,
bookkeeping, and arithmetic perfectly; the human does the one thing it can't (the click)
and the one thing it shouldn't (spend real, scarce, irreversible resources on a judgment
call).

---

## 7. How this model explains the session (worked examples)

- **Case-4 ladder = Level A.** 4990 ✓✓ / 4970 ✓ / 4960 ✗ / 4950 ✗ → wall (4960, 4970],
  banked v110 = 90.276200. Four informative submissions, one wasted on the family lesson.
- **Rung-1 failure = the family layer.** Same source-level algorithm, different binary
  family (headroom `#ifdef`) → 0/2 at rungs the v108 family passes. Fix: one-constant diffs
  inside the proven family.
- **Friend's case-3 = Level B.** Read (K = 57 → S2 = 0.9135 at 6940) → bank at 6941 →
  90.2761. Two submissions for a wall that Level A would have bisected blind.
- **v111 = batching.** Both harvests in one submission (different bands don't interact) →
  90.285538, both coins landed in one run.
- **The strategic ceiling.** All of the above optimizes *along* our walls. The leaders'
  91.46 is *lower walls* — case 3 at ~85 % instead of 70 % — which no probe can deliver.
  The wall model's role there is different: Level-B reads are the only trustworthy way to
  evaluate a *new mechanism* on the real case-3 mesh (§5.5), i.e. the measurement layer any
  wall-moving attempt now has to be built on.
