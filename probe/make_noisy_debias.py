#!/usr/bin/env python3
# De-bias the c3 proxy (ARCHITECT-REVIEW 3.C.1): add scan-like high-frequency displacement
# ALONG the vertex normal. Deterministic (seeded). Topology unchanged -> stays watertight.
import sys, math, random
inp, out, amp = sys.argv[1], sys.argv[2], float(sys.argv[3])  # amp = fraction of bbox diag
V=[]; F=[]
for ln in open(inp):
    p=ln.split()
    if not p: continue
    if p[0]=='v': V.append([float(x) for x in p[1:4]])
    elif p[0]=='f': F.append([int(x.split('/')[0])-1 for x in p[1:4]])
n=len(V)
# area-weighted vertex normals
vn=[[0.0,0.0,0.0] for _ in range(n)]
for a,b,c in F:
    ux,uy,uz=(V[b][i]-V[a][i] for i in range(3)); wx,wy,wz=(V[c][i]-V[a][i] for i in range(3))
    cx,cy,cz=uy*wz-uz*wy, uz*wx-ux*wz, ux*wy-uy*wx
    for v in (a,b,c): vn[v][0]+=cx; vn[v][1]+=cy; vn[v][2]+=cz
lo=[min(v[i] for v in V) for i in range(3)]; hi=[max(v[i] for v in V) for i in range(3)]
diag=math.sqrt(sum((hi[i]-lo[i])**2 for i in range(3)))
import os
rng=random.Random(int(os.environ.get("SEED","12345"))); A=amp*diag
for v in range(n):
    l=math.sqrt(sum(vn[v][i]**2 for i in range(3)))
    if l<1e-30: continue
    d=rng.gauss(0,1)*A                       # white (high-freq) displacement along normal
    for i in range(3): V[v][i]+=d*vn[v][i]/l
with open(out,'w') as f:
    f.write(f"{len(V)} {len(F)}\n")
    for x,y,z in V: f.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
    for a,b,c in F: f.write(f"f {a+1} {b+1} {c+1}\n")
print(f"wrote {out}: amp={amp} (={A:.5g} world), V={n} F={len(F)}")
