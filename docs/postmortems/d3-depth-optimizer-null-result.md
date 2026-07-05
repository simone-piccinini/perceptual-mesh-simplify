# D3 (depth-in-optimizer) — JUDGE 88.67146: a null result on the wrong base

> ⚠️ JUDGE RESULT: the D3 build scored **88.67146, 7/7** — **1.57 below the 90.24
> best**. But 88.67146 is not a random regression: it is **v38's exact score to five
> decimals**. That number is the diagnosis. D3 did not break anything and did not help
> anything; it was **net-neutral**, applied to a **stale base**, and tested **without the
> one change that could have made it pay off**. Best remains **90.24** (best-counts
> protects it; this submission is harmless).

## What D3 was

Extend the post-decimation inverse-rendering optimizer to **case 5** and add a **depth
term** to its objective (`0.5·normal + 0.5·depth` on cases 3/5, normal-only on case 4).
Motivated by the D0 proxy diagnostic showing depth slack on organic meshes. Code and
local A/B: [../Future/structural-ideas.md](../Future/structural-ideas.md) (D3).

## Why 88.67146 is the smoking gun

The per-case score is **compression = `100·(1 − V'/V)`**, and `V'` is set **entirely by
`keep_for(V)`**. The optimizer moves **vertex positions, never vertex counts**. So at a
fixed `keep` the optimizer **cannot change compression** — it can only change the score by
**flipping a case's validity** (PASS↔FAIL).

- `keep_for` was **unchanged** by D3 (verified: identical to the pre-D3 snapshot).
- The judge returned **exactly v38's score** → every case passed at v38's **exact vertex
  counts** → nothing flipped validity → **D3 was provably net-neutral on the judge.**

If D3 had *broken* case 5, case 5 would score 0 and the total would be ≈73.6, not 88.67.
If D3 had *helped*, `keep` would have had to drop — it didn't. The only value reachable
with v38's `keep_for` and all-cases-valid is 88.67146, and that is what came back.

## Root cause A — the repo base is v38 (88.67), not the 90.24 best

`solver/main.cpp` in this repo carries v38's operating point
(`keep_for` = 99/67/83/90/97/96 → 88.67146). **The 90.24 improvements were never committed
here.** Every experiment layered on this repo therefore starts at 88.67 and will *look
like* a ~1.57 regression against the real best, regardless of merit. D3 was prototyped on
the wrong base.

## Root cause B — a positions-only optimizer cannot raise the score at fixed keep

This is the methodology error, and it is the important lesson:

> The inverse-rendering optimizer is a **validity-preservation tool, not a compression
> lever.** It buys nothing at a fixed `keep`. It only pays off if you **lower `keep`
> (compress harder)** and rely on the optimizer to claw the rendered SSIM back above 0.9
> at that more aggressive operating point.

D3 was submitted with case 5's `keep` **unchanged at 0.10 (90%)**. So by construction it
could produce **exactly zero** gain — and could only have hurt (by breaking validity).
It didn't hurt, so it scored identically. The experiment was incapable of showing a win.

## Why the local A/B looked positive but meant nothing here

The local armadillo A/B showed the optimizer nudging our SSIM up (+0.004). That measured
"does the optimizer raise **our 320-px oracle's** blended SSIM at fixed positions" — which
is neither "does it raise the **judge's** score at fixed compression" (it *can't*, the
score is `keep`-set) nor "does it let us **compress more**" (untested, because `keep` was
never lowered). Doubly so for the depth term: depth-map scaling is an **explicitly
uncalibrated** oracle gap, so a local depth gain is the least judge-trustworthy signal we have.

## Lessons

1. **A positions-only optimizer never raises the score on its own.** Never test it without
   a **paired `keep` reduction**. The unit of experiment is "lower keep **+** optimizer,"
   not "optimizer" alone.
2. **Establish the true best as the repo base before experimenting.** Measuring against a
   stale 88.67 base makes every result read as a 1.57 regression. Import the actual 90.24
   `solver/main.cpp` first.
3. **Local-oracle SSIM gains are not judge gains** — and depth-term gains least of all
   (uncalibrated depth scaling). Relative structure (D0) is fine for *aiming*; only the
   judge scores.
4. **Read the number, not just its rank.** 88.67146 ≠ "worse" — it is v38 exactly, which
   told us instantly that nothing about the compression changed.

## Status & the correct next test

- **D3 not adopted.** 90.24 remains best. The D3 code stays in `solver/main.cpp` — it is
  validity-safe and **byte-identical on the untouched bands** (bunny/sample verified) — but
  it is **inert until paired with a keep reduction**.
- **The only test that can show a D3 gain**, in order:
  1. Bring the real **90.24 build into the repo as the base** (diff its `keep_for` against
     this one to confirm what actually moved to reach 90.24).
  2. Isolate to **case 5**: lower its `keep` (0.10 → 0.09/0.08 = 91/92%) **with the
     optimizer active**, and sweep the depth weight `wd ∈ {0, 0.5}`.
  3. The optimizer's job there is to hold case 5 **≥ 0.9 at the more aggressive keep**. If
     it does, D3 (or even the normal-only optimizer extension) converts to real score; if
     not, case 5's wall is where 90.24 already put it.
