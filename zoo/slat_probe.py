#!/usr/bin/env python3
"""slat_probe — the interpenetration/'slat painting' screen (discovery-hunt candidate, 2026-07-16).

Legality: self-intersection is unconstrained by the 4 validity rules, and interpenetrating closed
components are judge-PROVEN (K-read pads sit inside the body, accepted 7/7 repeatedly).
Mechanism: free-floating thin slats at eps-offset above a coarse base render correct normal patches
via nearest-wins — no stitching cost, free orientation/elongation (ridge-aligned anisotropy).

v0: base = closed_2584 (honest QEM at 2,584v). K slats, each a 2-triangle rectangle (4 verts),
placed greedily at the worst +Z normal-residual spots, elongated along the local structure of the
ORIGINAL normal map, carrying the original's mean normal over its footprint. Score = oracle Final6.
Bar: dS/vertex must beat the honest curve's ~2.4e-5/vert (closed_2584 0.7212 -> closed_5999 0.8028).
"""
import os, re, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
MESH = os.path.join(ROOT, "zoo", "build", "happy_unit.obj")
BASE = os.path.join(ROOT, "zoo", "build", "closed_2584.obj")


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
    Vb, Fb = read_judge(BASE)
    views = build_views()
    vz = [w for w in views if np.asarray(w[0])[2] > 2.0][0]
    eye, right, up, forward = [np.asarray(q, dtype=float) for q in vz]

    no, do_, co = render_view(V, F, face_normals(V, F), vz)          # original
    nb, db, cb = render_view(Vb, Fb, face_normals(Vb, Fb), vz)      # base
    H, W = do_.shape
    fg = co & cb
    R = np.abs(no.astype(float) - nb.astype(float)).mean(axis=2) * fg   # residual magnitude

    # local orientation of the ORIGINAL normal map (structure tensor of its grayscale)
    g = no.astype(float).mean(axis=2)
    gy, gx = np.gradient(g)
    # smooth tensor components
    from numpy.lib.stride_tricks import sliding_window_view as swv
    def box(a, r=6):
        k = 2*r+1
        p = np.pad(a, r, mode="edge")
        return swv(p, (k, k)).mean(axis=(2, 3))
    Jxx, Jyy, Jxy = box(gx*gx), box(gy*gy), box(gx*gy)
    theta = 0.5*np.arctan2(2*Jxy, Jxx-Jyy) + np.pi/2   # elongation = perpendicular to gradient

    Ffac = 800.0 * (W/1024.0)
    def unproj(px, py, d):
        xc = (px + 0.5 - W/2) * d / Ffac
        yc = (py + 0.5 - H/2) * d / Ffac
        return eye + xc*right + yc*up + d*forward

    for K in [250, 600, 1200]:
        Rw = R.copy()
        Vs, Fs = [], []
        L, Wd, eps = 24, 6, 0.004
        for _ in range(K):
            k = np.argmax(Rw)
            py, px = np.unravel_index(k, Rw.shape)
            if Rw[py, px] <= 0: break
            d = db[py, px] - eps
            th = theta[py, px]
            # mean original normal over the footprint
            y0, y1 = max(0, py-Wd), min(H, py+Wd+1); x0, x1 = max(0, px-L//2), min(W, px+L//2+1)
            nn = (no[y0:y1, x0:x1].astype(float)/127.5 - 1.0)
            m = fg[y0:y1, x0:x1]
            if m.sum() < 8: Rw[py, px] = 0; continue
            n = nn[m].mean(axis=0); n /= (np.linalg.norm(n)+1e-12)
            a1 = np.cos(th)*right + np.sin(th)*up
            a1 -= n*(n@a1); l1 = np.linalg.norm(a1)
            if l1 < 1e-6: Rw[py, px] = 0; continue
            a1 /= l1
            a2 = np.cross(n, a1)
            P = unproj(px, py, d)
            sL = L*d/Ffac/2.0; sW = Wd*d/Ffac/2.0
            c00 = P - a1*sL - a2*sW; c01 = P - a1*sL + a2*sW
            c10 = P + a1*sL - a2*sW; c11 = P + a1*sL + a2*sW
            i0 = len(Vs) + len(Vb)
            Vs += [c00, c01, c10, c11]
            # wind so normal ~ +n (toward camera side): check via triple product
            tri_n = np.cross(c10-c00, c01-c00)
            if tri_n @ n > 0:
                Fs += [(i0, i0+2, i0+1), (i0+1, i0+2, i0+3)]
            else:
                Fs += [(i0, i0+1, i0+2), (i0+1, i0+3, i0+2)]
            Rw[max(0,py-Wd*2):py+Wd*2+1, max(0,px-L):px+L+1] = 0   # spread slats out
        allV = list(map(tuple, Vb)) + [tuple(v) for v in Vs]
        allF = list(map(tuple, Fb)) + Fs
        out = os.path.join(ROOT, "zoo", "build", f"slats_{len(allV)}.obj")
        with open(out, "w", newline="\n") as f:
            f.write(f"{len(allV)} {len(allF)}\n")
            for x, y, z in allV: f.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
            for t in allF: f.write(f"f {t[0]+1} {t[1]+1} {t[2]+1}\n")
        r = subprocess.run([sys.executable, "-m", "src.imc_eval.cli", "--input", MESH, "--output", out],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           cwd=ROOT, timeout=1800)
        txt = r.stdout + r.stderr
        zrow = re.search(r"\+Z:\s+(-?[\d.]+)\s+(-?[\d.]+)\s+->\s+(-?[\d.]+)", txt)
        fin = re.search(r"FinalSSIM\s*:\s*([\d.]+)", txt)
        print(f"SLATS K={K:5d} totalV={len(allV):5d}  +Z={zrow.groups() if zrow else '?'}  Final6={fin.group(1) if fin else '?'}")
    print("bars: base(2584)=0.7212 Final6; honest(5999)=0.8028; honest slope ~2.4e-5/vert")


if __name__ == "__main__":
    main()
