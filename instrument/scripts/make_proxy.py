#!/usr/bin/env python3
"""Generate the judge-calibrated proxy meshes (the "transferring instrument").

Recipe (validated 2026-07-14, see instrument/README.md):
  Stanford armadillo ORIGINAL (172,974 v)
    -> MeshLab QEM decimation to targetfacenum = 2*(V_judge - 2)
    -> Taubin smoothing, K steps (K calibrated per case against judge K-read anchors)
    -> dataset normalization: bbox center -> origin, scale so max|v| = 0.999
    -> solver input format ("V F" header + v/f lines)

Requires: pip install pymeshlab ; network for the first download.
Usage:    python instrument/scripts/make_proxy.py
Outputs:  instrument/meshes/c3_proxy_t3.obj   (V=23,201 = judge c3 count, EXACT)
          instrument/meshes/c5_proxy_t70.obj  (V=49,987 = judge c5 count, EXACT)
"""
import os, sys, gzip, urllib.request
import numpy as np
import pymeshlab

HERE = os.path.dirname(os.path.abspath(__file__))
MESHES = os.path.join(HERE, '..', 'meshes')
ORIG = os.path.join(MESHES, 'armadillo_orig.ply')
URL = 'http://graphics.stanford.edu/pub/3Dscanrep/armadillo/Armadillo.ply.gz'

# (name, judge vertex count, taubin steps) — K calibrated per case (README, anchors table)
TARGETS = [
    ('c3_proxy_t3.obj', 23201, 3),
    ('c5_proxy_t70.obj', 49987, 70),
]

def fetch_original():
    if os.path.exists(ORIG):
        return
    print('downloading Stanford armadillo original...')
    gz = ORIG + '.gz'
    urllib.request.urlretrieve(URL, gz)
    with gzip.open(gz, 'rb') as fi, open(ORIG, 'wb') as fo:
        fo.write(fi.read())
    os.remove(gz)

def make(name, v_judge, taubin_k):
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(ORIG)
    # genus-0 closed manifold: V = F/2 + 2  ->  targetfacenum = 2*(V-2) hits V EXACTLY
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum=2 * (v_judge - 2))
    if taubin_k > 0:
        ms.apply_coord_taubin_smoothing(stepsmoothnum=taubin_k)
    m = ms.current_mesh()
    V = m.vertex_matrix().copy(); F = m.face_matrix().copy()
    assert len(V) == v_judge, f'{name}: got {len(V)} verts, expected {v_judge}'
    lo, hi = V.min(0), V.max(0)
    V -= (lo + hi) / 2
    V *= 0.999 / np.linalg.norm(V, axis=1).max()
    out = os.path.join(MESHES, name)
    with open(out, 'w', newline='') as f:
        f.write(f'{len(V)} {len(F)}\n')
        for p in V:
            f.write(f'v {p[0]:.9g} {p[1]:.9g} {p[2]:.9g}\n')
        for t in F:
            f.write(f'f {t[0]+1} {t[1]+1} {t[2]+1}\n')
    print(f'{name}: V={len(V)} F={len(F)} taubin={taubin_k} -> ok')

if __name__ == '__main__':
    os.makedirs(MESHES, exist_ok=True)
    fetch_original()
    for name, v, k in TARGETS:
        make(name, v, k)
    print('done. Validate against the judge anchors per instrument/README.md')
