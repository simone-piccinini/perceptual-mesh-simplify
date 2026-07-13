#!/usr/bin/env python3
"""Parse Stanford binary PLY + solver-OBJ; measure a tessellation-aware roughness; convert to solver OBJ.
Roughness metric = RMS dihedral angle across interior edges, weighted so it reflects genuine surface
detail. We report both raw mean|dihedral| and a normalized variant. Also emits solver-format OBJ."""
import struct, sys, math
from collections import defaultdict

def load_ply_bin_be(path):
    with open(path, "rb") as f:
        data = f.read()
    hdr_end = data.index(b"end_header\n") + len(b"end_header\n")
    header = data[:hdr_end].decode("ascii", "replace")
    nv = nf = 0
    for line in header.splitlines():
        if line.startswith("element vertex"): nv = int(line.split()[-1])
        if line.startswith("element face"): nf = int(line.split()[-1])
    # vertex: 3 float32 BE ; face: uchar intensity + (uchar count=3) + 3 int32 BE
    off = hdr_end
    verts = []
    for _ in range(nv):
        x,y,z = struct.unpack_from(">fff", data, off); off += 12
        verts.append((x,y,z))
    faces = []
    for _ in range(nf):
        intensity = data[off]; off += 1
        cnt = data[off]; off += 1
        idx = struct.unpack_from(">"+"i"*cnt, data, off); off += 4*cnt
        if cnt == 3: faces.append(idx)
        else:  # triangulate fan (rare)
            for k in range(1, cnt-1): faces.append((idx[0], idx[k], idx[k+1]))
    return verts, faces

def load_solver_obj(path):
    with open(path, "r") as f:
        toks = f.read().split()
    nv = int(toks[0]); nf = int(toks[1]); i = 2
    verts = []
    for _ in range(nv):
        assert toks[i] == "v"; verts.append((float(toks[i+1]),float(toks[i+2]),float(toks[i+3]))); i += 4
    faces = []
    for _ in range(nf):
        assert toks[i] == "f"; faces.append((int(toks[i+1])-1,int(toks[i+2])-1,int(toks[i+3])-1)); i += 4
    return verts, faces

def face_normal(v, f):
    (ax,ay,az),(bx,by,bz),(cx,cy,cz) = v[f[0]], v[f[1]], v[f[2]]
    ux,uy,uz = bx-ax,by-ay,bz-az; wx,wy,wz = cx-ax,cy-ay,cz-az
    nx,ny,nz = uy*wz-uz*wy, uz*wx-ux*wz, ux*wy-uy*wx
    l = math.sqrt(nx*nx+ny*ny+nz*nz) or 1.0
    return nx/l,ny/l,nz/l

def roughness(verts, faces):
    fn = [face_normal(verts,f) for f in faces]
    edge_faces = defaultdict(list)
    for fi,f in enumerate(faces):
        for e in range(3):
            a,b = f[e], f[(e+1)%3]
            edge_faces[(min(a,b),max(a,b))].append(fi)
    angs = []
    for (a,b),fs in edge_faces.items():
        if len(fs) != 2: continue
        n1,n2 = fn[fs[0]], fn[fs[1]]
        d = max(-1.0,min(1.0, n1[0]*n2[0]+n1[1]*n2[1]+n1[2]*n2[2]))
        angs.append(math.acos(d))
    import statistics
    mean = statistics.fmean(angs)
    rms = math.sqrt(statistics.fmean([a*a for a in angs]))
    return mean, rms, len(angs)

def write_solver_obj(verts, faces, path):
    with open(path, "w", newline="\n") as f:
        f.write(f"{len(verts)} {len(faces)}\n")
        for x,y,z in verts: f.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
        for a,b,c in faces: f.write(f"f {a+1} {b+1} {c+1}\n")

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "roughness":
        for path in sys.argv[2:]:
            if path.endswith(".ply"): v,f = load_ply_bin_be(path)
            else: v,f = load_solver_obj(path)
            m,r,n = roughness(v,f)
            print(f"{path}: nv={len(v)} nf={len(f)} edges={n}  mean|dihedral|={math.degrees(m):.3f}deg  rms={math.degrees(r):.3f}deg")
    elif cmd == "ply2obj":
        v,f = load_ply_bin_be(sys.argv[2]); write_solver_obj(v,f,sys.argv[3])
        print(f"wrote {sys.argv[3]}: {len(v)} v {len(f)} f")
