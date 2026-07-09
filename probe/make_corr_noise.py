#!/usr/bin/env python3
# Corrected de-bias (ARCHITECT-REVIEW 3.C.1 / handoff Part B.1): COHERENT scan-like displacement.
# White per-vertex noise is refine-recoverable (SSIM's 11x11 box averages it into a chaseable
# signal). Instead: white noise SMOOTHED over the mesh graph S times -> correlation length ~ a few
# edges, i.e. window-scale structure the COARSE decimated mesh cannot represent (flat triangles
# can't bend) -> refine genuinely can't chase it. Displace along the vertex normal. Seeded.
import sys, math, random, os
inp, out, amp, smooth = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
V=[]; F=[]
for ln in open(inp):
    p=ln.split()
    if not p: continue
    if p[0]=='v': V.append([float(x) for x in p[1:4]])
    elif p[0]=='f': F.append([int(x.split('/')[0])-1 for x in p[1:4]])
n=len(V)
# adjacency + area-weighted vertex normals
adj=[set() for _ in range(n)]; vn=[[0.0,0.0,0.0] for _ in range(n)]
for a,b,c in F:
    ux,uy,uz=(V[b][i]-V[a][i] for i in range(3)); wx,wy,wz=(V[c][i]-V[a][i] for i in range(3))
    cx,cy,cz=uy*wz-uz*wy, uz*wx-ux*wz, ux*wy-uy*wx
    for v in (a,b,c): vn[v][0]+=cx; vn[v][1]+=cy; vn[v][2]+=cz
    adj[a].update((b,c)); adj[b].update((a,c)); adj[c].update((a,b))
adj=[list(s) for s in adj]
rng=random.Random(int(os.environ.get("SEED","12345")))
s=[rng.gauss(0,1) for _ in range(n)]                       # white scalar field
for _ in range(smooth):                                     # graph-Laplacian smoothing -> correlated
    s=[ (s[v]+sum(s[w] for w in adj[v]))/(1+len(adj[v])) if adj[v] else s[v] for v in range(n)]
# renormalize to unit std (smoothing shrinks variance)
mean=sum(s)/n; var=sum((x-mean)**2 for x in s)/n; sd=math.sqrt(var) if var>0 else 1.0
s=[(x-mean)/sd for x in s]
lo=[min(v[i] for v in V) for i in range(3)]; hi=[max(v[i] for v in V) for i in range(3)]
diag=math.sqrt(sum((hi[i]-lo[i])**2 for i in range(3))); A=amp*diag
for v in range(n):
    l=math.sqrt(sum(vn[v][i]**2 for i in range(3)))
    if l<1e-30: continue
    d=s[v]*A
    for i in range(3): V[v][i]+=d*vn[v][i]/l
with open(out,'w') as f:
    f.write(f"{len(V)} {len(F)}\n")
    for x,y,z in V: f.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
    for a,b,c in F: f.write(f"f {a+1} {b+1} {c+1}\n")
print(f"wrote {os.path.basename(out)}: amp={amp} smooth={smooth} (corr-length ~{smooth} edges)")
