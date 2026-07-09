# Phase-0 runbook — reproduce & extend the case-3 diagnostic locally (Windows)

Everything here runs **locally, no judge submissions**. It compiles the solver,
decimates a faithful organic case-3 proxy through the real pipeline to its wall, and
maps where the normal-map SSIM structure deficit lives. Verdict of the run this
produced: [`docs/postmortems/case3-intrinsic-wall.md`](../../docs/postmortems/case3-intrinsic-wall.md).

All commands are run from the **repo root** with **Git Bash** (the `py` launcher = the
Windows Python 3.11). Everything lands in `.phase0/` (git-ignored).

---

## 0. One-time setup

```bash
# Python deps (numpy/scipy usually already present; numba is optional and absent here)
py -m pip install numpy scipy matplotlib fast_simplification ziglang

# A C++ toolchain WITHOUT installing one: ziglang ships clang+libc++ via pip (above).
py -m ziglang version          # expect 0.16.x

# Eigen headers (the repo's solver/Eigen is a broken macOS symlink on Windows)
git clone --depth 1 https://gitlab.com/libeigen/eigen.git .phase0/eigen
```

Why zig: there is no `g++`/MSVC here, and `py -m ziglang c++` is a drop-in clang that
cross-compiles with a bundled libc++ — no system install, no admin.

---

## 1. The five steps

```bash
# 1) Patch the solver for a local Windows build (drops POSIX getrusage/sys-resource;
#    swaps the refine time-box to wall-clock). LOCAL ONLY -- never submit this file.
py scripts/phase0/patch_solver_win.py                       # -> .phase0/c3_solver.cpp

# 2) Compile it
py -m ziglang c++ -O2 -std=c++17 -w -I .phase0/eigen \
    .phase0/c3_solver.cpp -o .phase0/c3_solver.exe          # -> .phase0/c3_solver.exe

# 3) Build the faithful organic case-3 proxy (armadillo -> 23,201 v, matching real V)
py scripts/phase0/build_proxy.py                            # -> .phase0/proxy_c3_orig.obj

# 4) Run the REAL pipeline (Pivot-A + VSA-lite + refine) to the case-3 wall (~17 s)
./.phase0/c3_solver.exe < .phase0/proxy_c3_orig.obj \
    > .phase0/wall_c3.obj 2> .phase0/rc3_stderr.txt
grep RC3 .phase0/rc3_stderr.txt        # the solver's own 1024 self-score (S2n/S2d/S2)

# 5) Map & quantify the deficit
py scripts/phase0/deficit_map.py                            # 512 px (fast)
# py scripts/phase0/deficit_map.py 1024                     # judge res (minutes; no numba)
#   -> prints l/c/cs decomposition, Gini, and the two decisive correlations
#   -> writes .phase0/deficit_map.png
```

**Expected (this machine):** self-score normal ~0.808; decomposition l=1.000, c≈0.998
(deficit is 100% structure); Gini ~0.24; `corr(deficit, richness) ~ -0.5`;
`corr(deficit, face-density) ~ 0`. Read: the deficit is intrinsic mid-band structure,
uncorrelated with our allocation -> reallocation mechanisms can't move it. See the memo.

---

## 2. How to read the outputs

- **decomposition** (`l`, `c`, `cs`): if `l` and `c` are ~1 and `cs` is the low term,
  the loss is the SSIM **structure** factor (registration), not mean or variance.
- **Gini + "worst k% hold X%"**: concentration of the deficit. Low Gini + view-uniform
  => broad, no hotspot to exploit. (Note: redistribution conserves the SSIM mean, so
  concentration alone is *not* recoverable score — the correlations below decide it.)
- **corr(deficit, richness sigma_x)**: `<< 0` => worst where the surface is gently
  curved (the Wang-2004 masking mid-band) => intrinsic. `>> 0` => worst on sharp
  features => a feature-registration mechanism might help.
- **corr(deficit, face-density)**: `~0` => NOT an allocation problem (bad regions
  aren't starved). `<< 0` => starved regions => reallocation headroom.

---

## 3. Extend it — test a case-3 mechanism locally (A/B)

The solver is one big per-case-gated file; case 3 is the band `7000 < V <= 30000`.
Every mechanism is toggled by a `G_*` env var (the judge sets none, so these are
dev-only overrides). To A/B a mechanism: produce two wall meshes and compare their
`normal-SSIM` from `deficit_map.py` (point it at each).

```bash
# control vs variant (example: ablate Pivot-A steering)
./.phase0/c3_solver.exe            < .phase0/proxy_c3_orig.obj > .phase0/wall_ctrl.obj 2>/dev/null
G_NOLAMBDA=1 ./.phase0/c3_solver.exe < .phase0/proxy_c3_orig.obj > .phase0/wall_var.obj  2>/dev/null
# then cp each to .phase0/wall_c3.obj and run deficit_map.py, or edit its input path.
```

**Useful `G_*` flags for case-3 experiments** (full list: search `getenv` in
`solver/main.cpp`):

| flag | effect |
|---|---|
| `G_NOLAMBDA=1` | turn OFF Pivot-A steering (clean VSA/QEM baseline) |
| `G_LAMBDA=<x>` | force Pivot-A strength (default case3 = 16) |
| `G_SDEF=<0/1>` | structure-deficit steering (the mid-band lever) on/off |
| `G_NDECIM=<0/1>` | VSA-lite normal-error ordering on/off |
| `G_NMETRIC=<0..4>` | normal-distortion metric variant (3/4 = closed-form flat-window SSIM) |
| `G_RES=<px>` | in-loop steering render resolution (default 160) |
| `G_PASSES=<n>` | staged decimation passes (default 8) |
| `G_REFINE=<0/1>` | inverse-rendering position optimizer on/off |
| `G_BUDGET=<s>` | refine CPU/wall budget seconds (default ~16) |
| `G_ADAM=1` / `G_HOP=1` | Adam+basin-hop / jitter-restart optimizers |
| `G_SHARP=1` | unsharp normal re-dispersion pass |
| `G_LAPL=<x>` | Sobolev/Laplacian gradient preconditioning |
| `G_VIS=<0/1>` | hidden-face free-collapse |
| `G_RDBG=1` | verbose refine/optimizer trace to stderr |

CLI args (local only): `c3_solver.exe <a|k> <margin> <keep> <refine_res>` — e.g. force a
different wall: `./.phase0/c3_solver.exe k 0.045 0.28 < proxy... ` (keep 0.28 ~ 72%).
Note the case-3 `PROBE-RC3-READ` block hard-codes a final `Decimate(6940)`; to sweep the
wall N, edit that constant in `solver/main.cpp` (then re-patch + re-compile).

---

## 4. Critical caveats (do not skip)

1. **The patched `.phase0/c3_solver.cpp` is LOCAL-ONLY.** The real judge is Linux and
   needs the original `getrusage` CPU timer (it bills CPU, not wall). **Submit
   `solver/main.cpp`, never the patched copy.**
2. **The proxy is a stand-in, not the hidden mesh.** It reproduces the *binding number*
   (normal-SSIM ~0.81) and the *structure* of the deficit, but absolute values and any
   mechanism's exact gain will differ on the judge.
3. **Local A/B does NOT transfer to the judge** (three screening instruments were
   falsified — `docs/Future/transfer-instrument.md`). Use local A/B only for
   sign/sanity and debugging; a real mechanism must be confirmed judge-side with a
   de-razored S-read. The `~1e-4` local noise floor swallows small effects.
4. **512 vs 1024:** the diagnostic renders at 512 for speed (no numba). Concentration
   and correlations are resolution-robust; absolute `s` is not.

---

## 5. File map

```
scripts/phase0/
  patch_solver_win.py   solver/main.cpp -> .phase0/c3_solver.cpp (Windows-buildable)
  build_proxy.py        armadillo -> .phase0/proxy_c3_orig.obj (organic, ~23,201 v)
  deficit_map.py        orig vs wall -> l/c/cs, Gini, correlations, .phase0/deficit_map.png
  RUNBOOK.md            this file
.phase0/                git-ignored working dir (eigen, exe, meshes, png)
docs/postmortems/case3-intrinsic-wall.md   the verdict this produced
```
