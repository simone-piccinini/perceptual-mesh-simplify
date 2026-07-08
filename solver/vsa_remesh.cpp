// ROAD 1 — Full VSA remesh with RETRIANGULATION (case-3 different-algorithm program).
// Standalone experiment (does NOT touch the banked solver/main.cpp). See
// submissions/case3-lab/IDEAS.md "PARADIGM ROADS".
//
// Pipeline:
//   1. load mesh (stdin, "V F" + v/f lines, 1-indexed) — same format as main.cpp.
//   2. lloyd_partition(K, iters): Cohen-Steiner 2004 VSA — flood faces into K regions
//      minimising the L2,1 normal metric fa*(1 - n.dot(proxy)); Lloyd-relax the proxies.
//      (ported verbatim from main.cpp:240 so the partition matches the banked one.)
//   3. RETRIANGULATE (the unbuilt frontier): anchors = original vertices where >=3 regions
//      meet; walk each region's boundary loop keeping the region on the left; the ordered
//      anchors are the region polygon; fan-triangulate; weld on shared anchors.
//   4. validate: watertight 2-manifold (every undirected edge in exactly 2 faces),
//      non-degenerate, indices in range — the judge's output constraints.
//
// Env: G_K (regions, default 800), G_ITERS (Lloyd iters, default 12).
// Build:  g++ -O2 -std=c++17 solver/vsa_remesh.cpp -o /tmp/vsa
// Run:    /tmp/vsa < mesh.obj > out.obj   (diagnostics on stderr)

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <string>
#include <vector>
#include <array>
#include <queue>
#include <unordered_map>
#include <unordered_set>
#include <algorithm>

struct Vec3 {
    double x=0,y=0,z=0;
    Vec3()=default; Vec3(double a,double b,double c):x(a),y(b),z(c){}
    Vec3 operator+(const Vec3&o)const{return {x+o.x,y+o.y,z+o.z};}
    Vec3 operator-(const Vec3&o)const{return {x-o.x,y-o.y,z-o.z};}
    Vec3 operator*(double s)const{return {x*s,y*s,z*s};}
    Vec3 operator/(double s)const{return {x/s,y/s,z/s};}
    double dot(const Vec3&o)const{return x*o.x+y*o.y+z*o.z;}
    Vec3 cross(const Vec3&o)const{return {y*o.z-z*o.y, z*o.x-x*o.z, x*o.y-y*o.x};}
    double norm()const{return std::sqrt(x*x+y*y+z*z);}
};

static std::vector<Vec3>              pos;
static std::vector<std::array<int,3>> faces;
static std::vector<int>               g_flabel;   // per-face region label

// ---------- I/O (format identical to main.cpp) ----------
static void load_obj() {
    std::string buf;
    { char chunk[1<<16]; size_t n;
      while ((n=std::fread(chunk,1,sizeof chunk,stdin))>0) buf.append(chunk,n); }
    char* p = buf.data();
    const long nv = std::strtol(p,&p,10);
    const long nf = std::strtol(p,&p,10);
    pos.resize(nv); faces.resize(nf);
    for (long v=0; v<nv; ++v) {
        while (*p==' '||*p=='\n'||*p=='\r'||*p=='\t') ++p; ++p;
        pos[v].x=std::strtod(p,&p); pos[v].y=std::strtod(p,&p); pos[v].z=std::strtod(p,&p);
    }
    for (long f=0; f<nf; ++f) {
        while (*p==' '||*p=='\n'||*p=='\r'||*p=='\t') ++p; ++p;
        faces[f][0]=(int)std::strtol(p,&p,10)-1;
        faces[f][1]=(int)std::strtol(p,&p,10)-1;
        faces[f][2]=(int)std::strtol(p,&p,10)-1;
    }
}
static void save_obj(const std::vector<Vec3>& P, const std::vector<std::array<int,3>>& F) {
    std::string out; out.reserve(P.size()*40 + F.size()*24 + 32);
    char line[96];
    out.append(line, std::snprintf(line,sizeof line,"%d %d\n",(int)P.size(),(int)F.size()));
    for (const auto& v : P)
        out.append(line, std::snprintf(line,sizeof line,"v %.17g %.17g %.17g\n",v.x,v.y,v.z));
    for (const auto& t : F)
        out.append(line, std::snprintf(line,sizeof line,"f %d %d %d\n",t[0]+1,t[1]+1,t[2]+1));
    std::fwrite(out.data(),1,out.size(),stdout);
}

// ---------- VSA partition (ported from main.cpp:240) ----------
static void lloyd_partition(int k, int iters) {
    const int nf=(int)faces.size();
    if (k<1||nf==0||iters<1) return; if (k>nf) k=nf;
    std::vector<Vec3> fn(nf); std::vector<double> fa(nf);
    for (int f=0; f<nf; ++f) { const int* t=faces[f].data();
        Vec3 c=(pos[t[1]]-pos[t[0]]).cross(pos[t[2]]-pos[t[0]]); double l=c.norm();
        fa[f]=0.5*l; fn[f]=(l>0.0)?(c/l):Vec3(0,0,1); }
    std::unordered_map<long long,int> emap; emap.reserve((size_t)nf*2);
    std::vector<std::array<int,3>> adj(nf,{-1,-1,-1});
    const long long NV=(long long)pos.size();
    for (int f=0; f<nf; ++f) { const int* t=faces[f].data();
        for (int e=0;e<3;++e){ int a=t[e],b=t[(e+1)%3]; if(a>b) std::swap(a,b);
            auto ins=emap.emplace((long long)a*NV+b,f);
            if(!ins.second){ const int g=ins.first->second;
                for(int s=0;s<3;++s) if(adj[f][s]<0){adj[f][s]=g;break;}
                for(int s=0;s<3;++s) if(adj[g][s]<0){adj[g][s]=f;break;} } } }
    std::vector<int> seed(k); std::vector<Vec3> proxy(k);
    for (int r=0;r<k;++r){ seed[r]=(int)((long long)r*nf/k); proxy[r]=fn[seed[r]]; }
    g_flabel.assign(nf,-1);
    struct QE{ double c; int f,r; bool operator>(const QE&o)const{return c>o.c;} };
    for (int it=0; it<iters; ++it) {
        std::priority_queue<QE,std::vector<QE>,std::greater<QE>> pq;
        std::fill(g_flabel.begin(),g_flabel.end(),-1);
        for (int r=0;r<k;++r){ g_flabel[seed[r]]=r;
            for(int s=0;s<3;++s){ const int g=adj[seed[r]][s];
                if(g>=0) pq.push({fa[g]*(1.0-fn[g].dot(proxy[r])),g,r}); } }
        while(!pq.empty()){ const QE e=pq.top(); pq.pop();
            if(g_flabel[e.f]>=0) continue; g_flabel[e.f]=e.r;
            for(int s=0;s<3;++s){ const int g=adj[e.f][s];
                if(g>=0&&g_flabel[g]<0) pq.push({fa[g]*(1.0-fn[g].dot(proxy[e.r])),g,e.r}); } }
        std::vector<Vec3> acc(k,Vec3(0,0,0));
        for(int f=0;f<nf;++f){ const int r=g_flabel[f]; if(r>=0) acc[r]=acc[r]+fn[f]*fa[f]; }
        for(int r=0;r<k;++r){ const double l=acc[r].norm(); if(l>0.0) proxy[r]=acc[r]/l; }
        std::vector<double> best(k,1e300);
        for(int f=0;f<nf;++f){ const int r=g_flabel[f]; if(r<0) continue;
            const double c=fa[f]*(1.0-fn[f].dot(proxy[r])); if(c<best[r]){best[r]=c; seed[r]=f;} }
    }
}

// ---------- RETRIANGULATION (the new part) ----------
// Half-edge he = 3*f+e represents directed edge (faces[f][e] -> faces[f][(e+1)%3]).
static inline int he_next(int he){ int f=he/3,e=he%3; return 3*f+(e+1)%3; }
static inline int he_org (int he){ return faces[he/3][he%3]; }
static inline int he_dst (int he){ return faces[he/3][(he%3+1)%3]; }
static inline int he_face(int he){ return he/3; }

// 2D ear-clipping of a simple polygon given in order; emits triangles as index triples into the
// input. Does NOT reverse (preserves caller orientation). Bails (returns < n-2 tris) if the polygon
// is non-simple, so the caller can fall back to a fan.
static void earclip(const std::vector<std::array<double,2>>& P, std::vector<std::array<int,3>>& tris){
    const int n=(int)P.size(); if(n<3) return;
    std::vector<int> idx(n); for(int i=0;i<n;++i) idx[i]=i;
    auto cross=[&](int a,int b,int c){ const auto&A=P[a];const auto&B=P[b];const auto&C=P[c];
        return (B[0]-A[0])*(C[1]-A[1])-(B[1]-A[1])*(C[0]-A[0]); };
    double area=0; for(int i=0;i<n;++i){ const auto&a=P[i]; const auto&b=P[(i+1)%n]; area+=a[0]*b[1]-b[0]*a[1]; }
    const double s = area>=0 ? 1.0 : -1.0;   // convex test sign follows the polygon's own winding
    auto inTri=[&](int a,int b,int c,int p){ double d1=s*cross(a,b,p),d2=s*cross(b,c,p),d3=s*cross(c,a,p);
        return d1>=0&&d2>=0&&d3>=0; };
    int guard=0;
    while((int)idx.size()>3 && ++guard<200000){
        const int m=(int)idx.size(); bool clipped=false;
        for(int i=0;i<m;++i){ int a=idx[(i+m-1)%m], b=idx[i], c=idx[(i+1)%m];
            if(s*cross(a,b,c)<=0) continue;                 // reflex/degenerate corner
            bool ear=true; for(int j=0;j<m;++j){ int p=idx[j]; if(p==a||p==b||p==c) continue;
                if(inTri(a,b,c,p)){ ear=false; break; } }
            if(ear){ tris.push_back({a,b,c}); idx.erase(idx.begin()+i); clipped=true; break; } }
        if(!clipped) break;
    }
    if((int)idx.size()==3) tris.push_back({idx[0],idx[1],idx[2]});
}

int main() {
    load_obj();
    const int K     = std::getenv("G_K")     ? std::atoi(std::getenv("G_K"))     : 800;
    const int ITERS = std::getenv("G_ITERS") ? std::atoi(std::getenv("G_ITERS")) : 12;
    const int nv=(int)pos.size(), nf=(int)faces.size();
    std::fprintf(stderr,"[vsa] in: V=%d F=%d  K=%d iters=%d\n",nv,nf,K,ITERS);

    lloyd_partition(K, ITERS);

    // per-region proxy normal (area-weighted average of member face normals) — the plane each
    // region's anchor polygon is triangulated in, and the outward direction for its triangles.
    std::vector<Vec3> g_proxy(K, Vec3(0,0,1));
    { std::vector<Vec3> acc(K,Vec3(0,0,0));
      for (int f=0; f<nf; ++f){ int r=g_flabel[f]; if(r<0) continue; const int* t=faces[f].data();
          Vec3 c=(pos[t[1]]-pos[t[0]]).cross(pos[t[2]]-pos[t[0]]); acc[r]=acc[r]+c*0.5; }
      for (int r=0;r<K;++r){ double l=acc[r].norm(); if(l>0) g_proxy[r]=acc[r]/l; } }

    // twin map: (org,dst) -> he
    std::unordered_map<long long,int> hemap; hemap.reserve((size_t)nf*3*2);
    const long long NV=(long long)nv;
    for (int he=0; he<3*nf; ++he) hemap[(long long)he_org(he)*NV+he_dst(he)]=he;
    auto twin=[&](int he)->int{ auto it=hemap.find((long long)he_dst(he)*NV+he_org(he));
                                return it==hemap.end()?-1:it->second; };

    // anchor = original vertex incident to >=3 distinct regions
    std::vector<std::unordered_set<int>> vlab(nv);
    for (int f=0; f<nf; ++f){ int r=g_flabel[f]; if(r<0) continue;
        for(int e=0;e<3;++e) vlab[faces[f][e]].insert(r); }
    std::vector<char> is_anchor(nv,0); int nanchor=0;
    for (int v=0; v<nv; ++v) if((int)vlab[v].size()>=3){ is_anchor[v]=1; ++nanchor; }

    // next boundary he of region r after `he` (region r stays on the left)
    auto next_boundary=[&](int he,int r)->int{
        int e=he_next(he);                       // (b->c), still in region r's face
        int guard=0;
        while (true) { int t=twin(e);
            if (t<0) break;                      // mesh boundary (shouldn't happen: closed)
            if (g_flabel[he_face(t)]!=r) break;  // e is a boundary edge of r
            e=he_next(t);                        // rotate around b, still inside r
            if(++guard>1000000) break; }
        return e;
    };

    // PASS 1: extract every region boundary loop as a FULL ordered vertex sequence.
    struct Loop { int r; std::vector<int> verts; };
    std::vector<Loop> loops;
    std::vector<char> he_seen(3*nf,0);
    int n_multiloop_regions=0; std::vector<int> loops_per_region(K,0);
    std::vector<std::vector<int>> reg_bhe(K);
    for (int he=0; he<3*nf; ++he){ int r=g_flabel[he_face(he)]; if(r<0) continue;
        int t=twin(he); if(t<0||g_flabel[he_face(t)]!=r) reg_bhe[r].push_back(he); }
    for (int r=0; r<K; ++r)
        for (int start : reg_bhe[r]) {
            if (he_seen[start]) continue;
            Loop L; L.r=r; int he=start,guard=0; bool ok=true;
            do { he_seen[he]=1; L.verts.push_back(he_org(he)); he=next_boundary(he,r);
                 if(++guard>2000000){ok=false;break;} } while (he!=start);
            if (ok && L.verts.size()>=3) { loops.push_back(std::move(L)); loops_per_region[r]++; }
        }
    for (int r=0;r<K;++r) if(loops_per_region[r]>1) ++n_multiloop_regions;

    // PASS 2: anchor insertion — every loop must expose >=3 anchors so it triangulates to a
    // proper polygon (Cohen-Steiner: under-cornered regions get boundary vertices promoted).
    // Promotion is GLOBAL (is_anchor) so the shared arc between two regions splits identically
    // in both loops -> the collapsed anchor edge is shared -> manifold weld holds.
    int n_promoted=0;
    for (auto& L : loops) {
        int cnt=0; for(int v:L.verts) if(is_anchor[v]) ++cnt;
        if (cnt>=3) continue;
        const int need=3-cnt, n=(int)L.verts.size();
        for (int j=0;j<need;++j){ int v=L.verts[(long long)j*n/need];
            if(!is_anchor[v]){ is_anchor[v]=1; ++nanchor; ++n_promoted; } }
    }

    // PASS 2b: the "lens" fix — two distinct boundary arcs sharing the same anchor pair (a,b)
    // both collapse to edge (a,b) -> that edge lands in 4 faces (non-manifold). Split all but one
    // such arc by promoting its middle vertex to an anchor, giving it distinct endpoints.
    int n_split=0;
    for (int rep=0; rep<4; ++rep) {   // a split can expose a new collision; a few passes converge
        // pair(a,b) -> {arc signature -> promote-vertex}. Signature = min interior vertex id
        // (reversal-invariant: the arc is walked in OPPOSITE order from its two adjacent regions,
        // so a direction-dependent signature would double-count one arc). -1 = direct edge (no
        // interior, unsplittable). >1 distinct signatures on a pair = a lens -> non-manifold.
        std::unordered_map<long long,std::unordered_map<int,int>> pair_arc;
        for (auto& L : loops) {
            const int n=(int)L.verts.size();
            int firstA=-1; for(int i=0;i<n;++i) if(is_anchor[L.verts[i]]){firstA=i;break;}
            if(firstA<0) continue;
            int i=firstA;
            do {
                int a=L.verts[i], j=(i+1)%n; std::vector<int> mids;
                while(!is_anchor[L.verts[j]]){ mids.push_back(L.verts[j]); j=(j+1)%n; if(j==i)break; }
                int b=L.verts[j];
                long long pkey=(long long)std::min(a,b)*NV+std::max(a,b);
                int sig = mids.empty()? -1 : *std::min_element(mids.begin(),mids.end());
                int prom= mids.empty()? -1 : mids[mids.size()/2];
                pair_arc[pkey].emplace(sig,prom);
                i=j;
            } while(i!=firstA);
        }
        int this_split=0;
        for (auto& kv : pair_arc){ auto& arcs=kv.second; if(arcs.size()<=1) continue;
            const bool has_direct = arcs.count(-1)>0;   // direct arc can't be split -> keep it, split the rest
            bool kept=false;
            for(auto& a : arcs){ if(a.first<0) continue;      // skip the direct arc
                if(!has_direct && !kept){ kept=true; continue; }   // no direct: keep one real arc
                if(a.second>=0 && !is_anchor[a.second]){ is_anchor[a.second]=1; ++nanchor; ++this_split; } } }
        n_split+=this_split;
        if(this_split==0) break;
    }

    // PASS 3: triangulate each loop's anchor polygon (fan; skip degenerate/duplicate corners).
    std::vector<int> anchor_out(nv,-1);
    std::vector<Vec3> outP; std::vector<std::array<int,3>> outF;
    auto anchor_idx=[&](int v)->int{ if(anchor_out[v]<0){ anchor_out[v]=(int)outP.size(); outP.push_back(pos[v]); } return anchor_out[v]; };
    int n_bad_loops=0, n_regions_meshed=0; std::vector<char> region_meshed(K,0);
    for (auto& L : loops) {
        std::vector<int> poly; for(int v:L.verts) if(is_anchor[v]) poly.push_back(v);
        // drop consecutive duplicates (arc that returns to same anchor)
        std::vector<int> pc; for(int v:poly) if(pc.empty()||pc.back()!=v) pc.push_back(v);
        if(pc.size()>=2 && pc.front()==pc.back()) pc.pop_back();
        if ((int)pc.size()<3){ ++n_bad_loops; continue; }
        // triangulate the anchor polygon in the region's proxy plane (ear-clip), orient outward.
        const Vec3 pn=g_proxy[L.r];
        Vec3 tt=(std::abs(pn.x)<0.9)?Vec3(1,0,0):Vec3(0,1,0);
        Vec3 uu=pn.cross(tt); { double l=uu.norm(); uu = l>0?uu/l:Vec3(1,0,0); }
        Vec3 vv=pn.cross(uu);
        std::vector<std::array<double,2>> P2; P2.reserve(pc.size());
        for(int vid:pc) P2.push_back({pos[vid].dot(uu), pos[vid].dot(vv)});
        std::vector<std::array<int,3>> tris; earclip(P2,tris);
        auto emit=[&](int i0,int i1,int i2){
            int A=anchor_idx(pc[i0]),B=anchor_idx(pc[i1]),C=anchor_idx(pc[i2]);
            Vec3 fn=(outP[B]-outP[A]).cross(outP[C]-outP[A]); if(fn.norm()<1e-18) return;
            if(fn.dot(pn)<0) std::swap(B,C);                 // face outward like the proxy
            outF.push_back({A,B,C});
        };
        if((int)tris.size()==(int)pc.size()-2) for(auto&t:tris) emit(t[0],t[1],t[2]);
        else for(size_t i=1;i+1<pc.size();++i) emit(0,(int)i,(int)i+1);   // fan fallback (non-simple polygon)
        if(!region_meshed[L.r]){ region_meshed[L.r]=1; ++n_regions_meshed; }
    }

    // ---------- validate: watertight 2-manifold ----------
    std::unordered_map<long long,int> edge_mult; edge_mult.reserve(outF.size()*3*2);
    const long long ONV=(long long)outP.size();
    int degenerate=0;
    for (auto& t : outF){
        if (t[0]==t[1]||t[1]==t[2]||t[0]==t[2]) { ++degenerate; }
        for (int e=0;e<3;++e){ int a=t[e],b=t[(e+1)%3]; if(a>b) std::swap(a,b);
            edge_mult[(long long)a*ONV+b]++; }
    }
    int e_ok=0,e_boundary=0,e_nonmanifold=0,maxmult=0;
    for (auto& kv : edge_mult){ int m=kv.second; maxmult=std::max(maxmult,m);
        if(m==2) ++e_ok; else if(m==1) ++e_boundary; else ++e_nonmanifold; }

    std::fprintf(stderr,
      "[vsa] partition: regions_meshed=%d anchors=%d (promoted=%d lens_split=%d)  multiloop_regions=%d bad_loops=%d\n"
      "[vsa] OUT: V=%d F=%d  degenerate_faces=%d\n"
      "[vsa] manifold: edges2=%d boundary(m=1)=%d nonmanifold(m>2)=%d maxmult=%d  => %s\n",
      n_regions_meshed, (int)outP.size(), n_promoted, n_split, n_multiloop_regions, n_bad_loops,
      (int)outP.size(),(int)outF.size(), degenerate,
      e_ok, e_boundary, e_nonmanifold, maxmult,
      (e_boundary==0 && e_nonmanifold==0 && degenerate==0) ? "WATERTIGHT-MANIFOLD" : "INVALID");

    save_obj(outP, outF);
    return 0;
}
