"""Authoritative mesh-level filter: watertight + genus-0 + 30-40k verts -> solver format.
ABC objs are standard OBJ and frequently NOT watertight. Usage: python abc_filter.py <obj_dir> <out_dir>"""
import glob, os, sys
from collections import defaultdict
OBJ_DIR = sys.argv[1] if len(sys.argv) > 1 else "abc_obj"
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "c4_proxies"

def load_obj(p):
    V, F = [], []
    for ln in open(p, errors="ignore"):
        t = ln.split()
        if not t: continue
        if t[0] == "v":
            try: V.append((float(t[1]), float(t[2]), float(t[3])))
            except: pass
        elif t[0] == "f":
            idx = [int(x.split("/")[0]) - 1 for x in t[1:]]
            for k in range(1, len(idx) - 1): F.append((idx[0], idx[k], idx[k+1]))
    return V, F

def analyze(V, F):
    ec = defaultdict(int)
    for a, b, c in F:
        for u, w in ((a, b), (b, c), (c, a)): ec[(min(u, w), max(u, w))] += 1
    E = len(ec)
    counts = list(ec.values())
    watertight = bool(counts) and all(n == 2 for n in counts)
    bad = sum(1 for n in counts if n != 2)
    genus = (2 - (len(V) - E + len(F))) / 2 if watertight else None
    return watertight, genus, len(V), len(F), bad

def write_solver(V, F, out):
    with open(out, "w", newline="\n") as f:
        f.write(f"{len(V)} {len(F)}\n")
        for x, y, z in V: f.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
        for a, b, c in F: f.write(f"f {a+1} {b+1} {c+1}\n")

os.makedirs(OUT_DIR, exist_ok=True)
objs = glob.glob(os.path.join(OBJ_DIR, "**", "*.obj"), recursive=True)
print(f"scanning {len(objs)} objs")
kept = 0; stats = {"count_off": 0, "not_watertight": 0, "genus_nz": 0}
for p in objs:
    V, F = load_obj(p)
    if not (30000 <= len(V) <= 40000): stats["count_off"] += 1; continue
    wt, g, nv, nf, bad = analyze(V, F)
    if not wt: stats["not_watertight"] += 1; continue
    if abs(g) >= 0.5: stats["genus_nz"] += 1; continue
    name = os.path.splitext(os.path.basename(p))[0]
    write_solver(V, F, os.path.join(OUT_DIR, name + ".obj"))
    kept += 1; print(f"KEEP {name}  v={nv} f={nf} genus={g:.0f}")
print(f"\nrejected: {stats}")
print(f"kept {kept} watertight genus-0 30-40k meshes -> {OUT_DIR}/")
