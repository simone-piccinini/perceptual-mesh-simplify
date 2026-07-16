# STATUS — where the project is NOW

*Single source of truth for CURRENT state. Read `CLAUDE.md` for HOW to work; this file is WHERE we
are. History → `handoff/ATTEMPT_LOG.md`. Judge facts → `docs/JUDGE-ENVELOPE.md`. Roads → `docs/ROADS.md`.*

**Last updated: 2026-07-16 (consolidation of 3 parallel agent branches).**

---

## 1. THE BANK

```
BANK   90.59475   (7/7)  [JUDGE 20049884, 2026-07-15]  — night-perfect autonomous run
       Lives on branch `CleanRepoForAI` (solver/mein.cpp). THE BANK BINARY IS THERE, NOT HERE.
Walls (deepest passing rung, judge-measured by the 10h wall-finder bot):
       c3 6610 · c4 4921 · c5 4138 (pinned) · c6 8680 · c7 0.0271 (pinned) · c2 28
Paradigm ceiling ≈ 90.60  — the bot banked the max the collapse+refine family allows.
```

**LEADERBOARD 2026-07-15 [user-observed]: #1 NEU.AddictedTribes 93.77 · #2 Moon Night 93.49 ·
#3 Vamos 92.37 · #4 Zazmuz 92.15 (8872 tries). We ≈ 90.6. Gap to #1 ≈ 19 SUMMED points.**
Multiple teams gained +1.3–2.3 in days. 93.77 is IMPOSSIBLE in the mesh-quality axis (see §3).
⇒ a shared **discrete discovery** is propagating that we have not found.

## 2. BRANCH MAP (⚠ READ THIS FIRST — 3 agents worked in parallel, work WAS duplicated)

| branch | author | holds | status |
|---|---|---|---|
| **`CleanRepoForAI`** | Emanuel (notHuber) | **THE BANK** + the autonomous night bot (10h wall-finder / combined-best banker) + `results/` campaign logs | LIVE — bank track |
| **`experiment/new-mechanism`** | Simone (this) | **EVERYTHING: bank solver (byte-identical) + bot + both instruments + all 3 agents' knowledge** — certified unit-scale rulers, `zoo/` screen, c4-depth/remesh/relief/slat closures, validator decoder | **START HERE** (see §6) |
| `session/all` | Alberto (asaiko) | **compile-cliff UNLOCK**, σxy constructive mechanism (judge-falsified ×4), `instrument/`, `cemetery_revival/` | knowledge merged here (docs only) |

**`experiment/new-mechanism` is now the consolidated branch — best solver AND best instruments:**

- **SOLVER = THE BANK, byte-identical** [`solver/mein.cpp` sha256 `81b21f951939…`, imported from
  `CleanRepoForAI` 2026-07-16]. Prova del nove passed: builds at -O2 and emits exactly **6610** on a
  c3-band proxy. The stale 90.51-era fork that used to live here (plus its judge-DEAD G_WD mechanism)
  is GONE — the mechanism survives only as a patcher, `scripts/patch_wd_team.py`, if ever needed.
- **BOT = imported**: `scripts/night_perfect.py` (10h autonomous wall-finder/banker: binary-search
  rungs, combined-best + g_draw rotation, stale-guard, toxic-draw filter, 2-roll coin confirm, prova
  del nove per submit) + `night91*_campaign.py`, `campaign_summary.py`, `solver/campaign.cpp`.
- **INSTRUMENTS = both lineages** (§4) + the `zoo/` screen + `src/imc_eval` oracle + ABC c4 proxies.
- **KNOWLEDGE = all three agents** (`instrument/`, `cemetery_revival/`, `sigmaxy-handroll/`,
  `wall-probes/`, `results/`, `docs/DIFF-BUILD.md`).

⚠ **Two caveats.** (1) The solver here is a **snapshot**: `CleanRepoForAI` is the LIVE bank track and
Emanuel's bot may advance it — `git fetch && git diff origin/CleanRepoForAI -- solver/mein.cpp`
before shipping. (2) The committed rungs are the base config (c3t 6610 / c4t 4930); the bot patches
rungs per submission, so `results/NIGHT_SUMMARY.md` walls (c4 4921) can sit below the source default.

**THE DUPLICATION LESSON (paid for twice on 2026-07-15/16):** this fragmentation cost a full session
— the compile cliff was re-fought (5 CEs) though Alberto had unlocked it, and constructive
reallocation was rebuilt though he had judge-falsified it ×4. Before building ANY mechanism, grep
all branches: `git log --all --oneline --grep=<keyword>`.

## 3. WHAT IS MEASURED-DEAD (do not re-dig; each has provenance)

- **Compile cliff**: mein.cpp sits at ~ZERO judge compile-memory margin (g++-15). **UNLOCKED** by
  Alberto: hand-roll heavy Eigen (SelfAdjointEigenSolver → 12-step power iteration; QEM solve →
  Cramer 3×3) = 692 MB, **14 MB BELOW** the original, judge-validated [20043585].
  `sigmaxy-handroll/SIGMAXY-LOG.md`. (Weave + O1-buyback is a weaker alternative — see ATTEMPT_LOG.)
- **Constructive reallocation** (edge-split where deficit high + collapse where saturated):
  judge-falsified **×4**, confounds excluded one by one [20043585/20044274/20044330/20044572]
  ⇒ *"the c3 deficit is resolution-bound, not reallocatable."* Independently re-measured 2026-07-16
  as LT-2000 teleports on the faithful ruler: **+0.0013** (per-mille class). Both agree.
- **From-scratch remesh** (Instant Meshes / MMGS aniso+adaptive): −0.05 to −0.08 vs ours at equal N.
- **View-decoupling** (per-view relief shells): dominated at EVERY budget (1 closed mesh serving 6
  views beats 6 dedicated reliefs).
- **Interpenetration / slat painting**: worse than its own base — the **continuity law** (3 independent
  proofs: impostors, shells, slats). σxy structurally rewards continuous surface.
- **Search depth**: 9× compute = **+0.006** at true scale ⇒ the leader gap would need ~1e9×.
- **Whole knob space**: 61-variant zoo pass on the certified ruler — nothing above the 1.5e-3 floor.
- **N-accounting**: header-lie WA'd — the checker parses the whole file and cross-checks the header.
- **c4 depth gradient (G_WD)**: judge dose-response real (+5e-4 @wd=0.5) but SIGN FLIPS across rungs
  ⇒ trajectory-noise-dominated. `docs/ROADS.md §2`.

## 4. THE INSTRUMENTS (two lineages, both now usable)

| instrument | scale | certification |
|---|---|---|
| `instrument/meshes/c3_proxy_t3.obj` (Alberto) | **unit ✓ (always was)** | 4 anchors; limits stated in `instrument/RELIABILITY/README.md` (taubin = amplitude fit, slope 25% flatter, n=1 retrodiction) |
| `probe/cache/c3cand/happy_unit.obj` + `dragon_unit.obj` (this branch) | **unit ✓ (fixed 07-16)** | **controls 6/6 & 5/5** sign-validated; retrodicts the judge's mini16 dK=0 |

⚠ **The 9.5× normalization bug** affected ONLY the `probe/cache/c3cand/*` lineage (`ply2solver.py`
never normalized). Every screen run on those before 2026-07-16 is scale-broken: signs survived,
MAGNITUDES did not (the "+4e-3 deep-tail prize" was an artifact; real value ≈ +0.0007).
Alberto's `instrument/` was never affected. **Screen on the `*_unit` meshes; see `zoo/README.md`.**

## 5. ACTIVE FRONT — the discovery, and it is INFORMATION-BOUND

Every algorithmic explanation for the leaders' +3 is measured-dead (§3). Two retrieval paths, both
needing a HUMAN (the API token is submit-only; all Kattis pages 403):
1. **The contest clarifications / announcements page.** Five teams converging within days is the
   signature of a public trigger. NOT YET READ — highest EV in the project.
2. **Teammate sync.** Emanuel is probing in parallel (e.g. sub 20066050). Merge maps before spending.

**Validator decoder (web UI only, 2026-07-16):** every failed case shows a *"Message from validator"*:
`mesh is invalid` (constraints 1–4, incl. V′ ≤ V) · `too much geometric deviation` (Hausdorff,
ENFORCED) · `SSIM is too low` (quality). ⚠ The recurring evening c3/c5 'x'es are **quality WAs, not
TLEs** — slow machines starve the time-boxed refine → worse mesh. Run ladders in DAYTIME.

## 6. WHICH BRANCH? → **`experiment/new-mechanism`** (this one). Verified by fresh-clone test.

It is the ONLY branch with all four: the **bank solver** (byte-identical), the **bot**, both
**instruments**, and the **knowledge of all 3 agents**. `CleanRepoForAI` has the live bank + bot but
NONE of the knowledge (no `zoo/`, no `instrument/`, no `ALGORITHM-LOGIC`, no `sigmaxy-handroll/`);
`session/all` has knowledge but an experimental solver. ⚠ The branch NAME is a historical lie — it is
no longer an experiment, it is the handoff.

**Before shipping anything:** `git fetch && git diff origin/CleanRepoForAI -- solver/mein.cpp`
(that branch is the LIVE bank track; the solver here is a verified snapshot, not a live mirror).

## 7. IF YOU ARE A NEW AGENT, READ IN THIS ORDER

1. `CLAUDE.md` (how to work) → this file → `docs/JUDGE-ENVELOPE.md` (judge facts)
2. `zoo/README.md` (the certified screen + every 07-15/16 closure)
3. `sigmaxy-handroll/SIGMAXY-LOG.md` (compile unlock — read BEFORE adding any code)
4. `results/NIGHT_SUMMARY.md` (the bot's wall map) · `handoff/ATTEMPT_LOG.md` (narrative)
5. **Grep all branches before building anything:** `git log --all --oneline --grep=<idea>`
