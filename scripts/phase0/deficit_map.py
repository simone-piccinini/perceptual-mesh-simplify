"""Phase 0 diagnostic — map the case-3 normal deficit the JUDGE actually scores and
decide the mechanism class.

Per-window normal penalty = 1 - l*cs, where cs = (2*sigma_xy + C2)/(sigma_x^2+sigma_y^2+C2)
is the combined contrast*structure term (equals the judge's per-window SSIM up to l~1;
its C2 stabilizer neutralizes flat-window noise, so this is judge-faithful, unlike the
raw structure term s).

Reads:
  .phase0/proxy_c3_orig.obj   (build_proxy.py)
  .phase0/wall_c3.obj         (the pipeline's wall mesh; see RUNBOOK.md step 5)
Writes:
  .phase0/deficit_map.png
Prints: l/c/cs decomposition, concentration (Gini + top-k%), and the two decisive
correlations: corr(deficit, original richness) and corr(deficit, wall face-density).

Run:  py scripts/phase0/deficit_map.py            # 512 px (fast)
      py scripts/phase0/deficit_map.py 1024        # judge res (slow without numba)
"""
import sys
from pathlib import Path
import numpy as np
from scipy.ndimage import uniform_filter
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[2]
WORK = REPO / ".phase0"
sys.path[:0] = [str(REPO), str(REPO / "src")]
from imc_eval.obj_io import load_mesh
from imc_eval.geometry import build_views, face_normals
import imc_eval.render as render
from imc_eval.render import render_view, _rasterize

RES = int(sys.argv[1]) if len(sys.argv) > 1 else 512
# scale focal + principal point with resolution so the fixed camera frames the
# unit-sphere model identically at any render size (matches the solver's own sub-1024 renders)
render.FOCAL = 800.0 * RES / 1024.0
render.CU = render.CV = RES / 2.0
WIN = 11; RAD = WIN // 2; C2 = (0.03 * 255) ** 2
VIEW = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]

Vo, Fo = load_mesh(str(WORK / "proxy_c3_orig.obj"))
Vs, Fs = load_mesh(str(WORK / "wall_c3.obj"))
fno, fns = face_normals(Vo, Fo), face_normals(Vs, Fs)
views = build_views()


def faceid(V, F, view):
    eye, right, up, fwd = view
    rel = V - eye; dp = rel @ fwd; safe = dp.copy(); safe[safe == 0] = 1e-9
    u = render.FOCAL * (rel @ right) / safe + render.CU
    v = render.FOCAL * (rel @ up) / safe + render.CV
    fid, _ = _rasterize(np.ascontiguousarray(u), np.ascontiguousarray(v),
                        np.ascontiguousarray(dp), np.ascontiguousarray(F.astype(np.int64)),
                        RES, RES, 1e-9, False)
    return fid


def edge_density(fid):   # face/edge density proxy: face-id changes per 11x11 window
    b = np.zeros((RES, RES), np.float32)
    b[:, 1:] += (fid[:, 1:] != fid[:, :-1]); b[1:, :] += (fid[1:, :] != fid[:-1, :])
    return uniform_filter(b, WIN)


print(f"Phase-0 deficit map | {RES}px | orig V={len(Vo)} -> wall V={len(Vs)}")
print(f"{'view':>5} | {'l':>6} {'c':>6} {'s':>6} | {'cs':>6} {'1-cs':>7}")
print("-" * 45)
D = []; SX = []; DENS = []; defmaps = []
CS = Lm = Cm = Sm = 0.0; nv = 0
for vi, view in enumerate(views):
    nO, _, cO = render_view(Vo, Fo, fno, view, W=RES, H=RES)
    nS, _, cS = render_view(Vs, Fs, fns, view, W=RES, H=RES)
    cov = cO | cS; m = cov[RAD:-RAD, RAD:-RAD]
    csacc = np.zeros((RES, RES)); sxacc = np.zeros((RES, RES))
    lv = cv = sv = csv = 0.0
    for ch in range(3):
        X = nO[:, :, ch]; Y = nS[:, :, ch]
        mx = uniform_filter(X, WIN); my = uniform_filter(Y, WIN)
        vx = np.maximum(0, uniform_filter(X * X, WIN) - mx * mx)
        vy = np.maximum(0, uniform_filter(Y * Y, WIN) - my * my)
        vxy = uniform_filter(X * Y, WIN) - mx * my
        sx = np.sqrt(vx); sy = np.sqrt(vy)
        C1 = (0.01 * 255) ** 2; C3 = C2 / 2
        l = (2 * mx * my + C1) / (mx * mx + my * my + C1)
        c = (2 * sx * sy + C2) / (vx + vy + C2)
        s = (vxy + C3) / (sx * sy + C3)
        cs = (2 * vxy + C2) / (vx + vy + C2)       # judge's combined term = c*s
        csacc += cs; sxacc += sx
        mm = m
        lv += l[RAD:-RAD, RAD:-RAD][mm].mean(); cv += c[RAD:-RAD, RAD:-RAD][mm].mean()
        sv += s[RAD:-RAD, RAD:-RAD][mm].mean();  csv += cs[RAD:-RAD, RAD:-RAD][mm].mean()
    lv/=3; cv/=3; sv/=3; csv/=3; csacc/=3; sxacc/=3
    Lm+=lv; Cm+=cv; Sm+=sv; CS+=csv; nv+=1
    print(f"{VIEW[vi]:>5} | {lv:6.3f} {cv:6.3f} {sv:6.3f} | {csv:6.3f} {1-csv:7.4f}")
    deficit = np.clip(1 - csacc, 0, None)
    dens = edge_density(faceid(Vs, Fs, view))
    D.append(deficit[RAD:-RAD, RAD:-RAD][m]); SX.append(sxacc[RAD:-RAD, RAD:-RAD][m])
    DENS.append(dens[RAD:-RAD, RAD:-RAD][m])
    full = np.full((RES, RES), np.nan); full[RAD:-RAD, RAD:-RAD] = np.where(m, deficit[RAD:-RAD, RAD:-RAD], np.nan)
    defmaps.append(full)

Lm/=nv; Cm/=nv; Sm/=nv; CS/=nv
print("-" * 45)
print(f"{'mean':>5} | {Lm:6.3f} {Cm:6.3f} {Sm:6.3f} | {CS:6.3f} {1-CS:7.4f}")
print(f"\nnormal-SSIM ~ l*cs = {CS:.4f}   (l={Lm:.3f}, c={Cm:.3f} are ~perfect -> deficit is STRUCTURE)")

D = np.concatenate(D); SX = np.concatenate(SX); DENS = np.concatenate(DENS)
n = D.size; ds = np.sort(D)[::-1]; csum = np.cumsum(ds) / D.sum()
sa = np.sort(D); idx = np.arange(1, n + 1); gini = (2 * (idx * sa).sum() / (n * sa.sum())) - (n + 1) / n
print(f"\n--- concentration ({n:,} fg windows) | Gini={gini:.3f} ---")
for f in (0.05, 0.10, 0.20, 0.30, 0.50):
    print(f"  worst {int(f*100):3d}% hold {csum[int(f*n)-1]*100:5.1f}% of deficit (uniform={f*100:.0f}%)")
cc = lambda a, b: float(np.corrcoef(a, b)[0, 1])
print(f"\n--- the decisive correlations ---")
print(f"corr(deficit, ORIGINAL richness sigma_x) = {cc(D,SX):+.3f}   (<<0 => intrinsic mid-band, per Wang-2004)")
print(f"corr(deficit, WALL face density)         = {cc(D,DENS):+.3f}   (~0 => NOT an allocation problem)")

fig, ax = plt.subplots(2, 3, figsize=(13, 8.5))
vmax = np.nanpercentile(np.concatenate([m.ravel() for m in defmaps]), 99)
for i, a in enumerate(ax.ravel()):
    im = a.imshow(defmaps[i], cmap="inferno", vmin=0, vmax=vmax)
    a.set_title(f"view {VIEW[i]} (1-cs)", fontsize=10); a.axis("off")
fig.suptitle(f"Case-3 judge-scored normal deficit (1-cs) @ {RES}px  |  normal-SSIM={CS:.3f}, Gini={gini:.3f}")
fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02, label="1 - cs")
fig.savefig(WORK / "deficit_map.png", dpi=110, bbox_inches="tight")
print(f"\nmap -> {(WORK/'deficit_map.png')}")
