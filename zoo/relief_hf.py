#!/usr/bin/env python3
"""relief_hf — heightfield relief fit for the +Z view (view-decoupling screen v3).

QEM-decimating the open visible-surface sheet shreds coverage (v2: Sd 0.47 at N=392 while
the UNDECIMATED base scores 0.9945). v3 builds the relief the image-space way: uniform grid
over the +Z depth buffer, z = sampled depth, cells fully inside the footprint triangulated.
Coverage is guaranteed by construction; the budget is the grid resolution.
"""
import os, re, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
MESH = os.path.join(ROOT, "probe", "cache", "c3cand", "happy_qem.obj")


def read_judge(path):
    tok = open(path).read().split()
    nv, nf = int(tok[0]), int(tok[1]); i = 2
    V, F = [], []
    for _ in range(nv):
        V.append((float(tok[i+1]), float(tok[i+2]), float(tok[i+3]))); i += 4
    for _ in range(nf):
        F.append((int(tok[i+1])-1, int(tok[i+2])-1, int(tok[i+3])-1)); i += 4
    return np.array(V), np.array(F, dtype=int)


def main():
    from imc_eval.render import render_view
    from imc_eval.geometry import build_views, face_normals
    V, F = read_judge(MESH)
    views = build_views()
    vz = None
    for w in views:
        eye = np.asarray(w[0])
        if eye[2] > 2.0 and abs(eye[0]) < 1e-6 and abs(eye[1]) < 1e-6:
            vz = w; break
    assert vz is not None
    eye, right, up, forward = [np.asarray(q, dtype=float) for q in vz]
    fn = face_normals(V, F)
    out_r = render_view(V, F, fn, vz)
    dep = out_r[1] if isinstance(out_r, tuple) else out_r  # (normal_img, depth_img)
    H, W = dep.shape
    fg = np.isfinite(dep) & (dep < 200)
    print(f"depth render {W}x{H}, fg px = {fg.sum()}")

    for G in [26, 42, 60, 90]:   # grid resolutions -> vertex budgets
        ys, xs = np.where(fg)
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        gy = np.linspace(y0, y1, G).astype(int); gx = np.linspace(x0, x1, G).astype(int)
        # sample depth with a small median footprint; mark validity
        zz = np.full((G, G), np.nan)
        for i, yy in enumerate(gy):
            for j, xx in enumerate(gx):
                if fg[yy, xx]: zz[i, j] = dep[yy, xx]   # center-pixel depth (median smeared z on steep patches: Hausdorff 4.3e-2)
                else:
                    p = dep[max(0, yy-3):yy+4, max(0, xx-3):xx+4]
                    p = p[np.isfinite(p) & (p < 200)]
                    if p.size >= 8: zz[i, j] = np.median(p)
        # camera at (0,0,2.5) looking -Z, focal 800, center 512: world x=(px-512)*d/800 etc.
        # imc_eval convention: u=F*x/d+C -> x=(u-C)*d/F ; y likewise; world z = 2.5 - d
        Vo, Fo, idx = [], [], -np.ones((G, G), dtype=int)
        for i in range(G):
            for j in range(G):
                if np.isnan(zz[i, j]): continue
                d = zz[i, j]
                xc = (gx[j] + 0.5 - W/2) * d / (800.0 * W / 1024.0)
                yc = (gy[i] + 0.5 - H/2) * d / (800.0 * H / 1024.0)
                pw = eye + xc*right + yc*up + d*forward   # true camera basis (avoids mirror flips)
                idx[i, j] = len(Vo); Vo.append((pw[0], pw[1], pw[2]))
        for i in range(G-1):
            for j in range(G-1):
                a, b, c, dd = idx[i, j], idx[i, j+1], idx[i+1, j], idx[i+1, j+1]
                if min(a, b, c, dd) < 0: continue
                Fo.append((a, c, b)); Fo.append((b, c, dd))
        out = os.path.join(ROOT, "zoo", "build", f"relief_hf_{len(Vo)}.obj")
        with open(out, "w", newline="\n") as f:
            f.write(f"{len(Vo)} {len(Fo)}\n")
            for x, y, z in Vo: f.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
            for t in Fo: f.write(f"f {t[0]+1} {t[1]+1} {t[2]+1}\n")
        r = subprocess.run([sys.executable, "-m", "src.imc_eval.cli", "--input", MESH, "--output", out],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           cwd=ROOT, timeout=1800)
        m = re.search(r"\+Z:\s+([\d.]+)\s+([\d.]+)\s+->\s+([\d.]+)", r.stdout + r.stderr)
        print(f"HF grid {G}x{G}  N={len(Vo):5d}  +Z: {m.group(0) if m else 'PARSE FAIL: ' + (r.stdout + r.stderr)[-300:]}")


if __name__ == "__main__":
    main()
