// ROAD R-ζ (fail-fast test) — does choosing WHICH edge to collapse by the TRUE rendered
// normal-box-SSIM beat choosing by QEM cost? Same collapse machinery, same placement, same
// manifold gates for both modes — ONLY the selection metric differs, so the comparison is clean.
//
// Boxed by two tested-dead neighbors (nmetric=3 analytic-SSIM selection −0.011; λ-sweep rendered-
// deficit steering, closed), so odds are low. Small-mesh brute-force (full re-render per candidate,
// no incremental machinery). If SSIM-mode can't beat QEM-mode here, the collapse-selection-metric
// family is definitively closed and we don't build the heavy incremental version.
//
// Env: G_MODE=qem|ssim (default qem), G_TARGET=<V'>, G_RES=<selection render res, default 96>,
//      G_K=<candidates scored per step in ssim mode, default 8>.
// Build: g++ -O2 -std=c++17 solver/ssim_greedy.cpp -o /tmp/sg
// Run:   G_MODE=ssim G_TARGET=600 /tmp/sg < mesh.obj > out.obj

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <string>
#include <vector>
#include <array>
#include <algorithm>

struct V3 { double x=0,y=0,z=0;
    V3()=default; V3(double a,double b,double c):x(a),y(b),z(c){}
    V3 operator+(const V3&o)const{return{x+o.x,y+o.y,z+o.z};}
    V3 operator-(const V3&o)const{return{x-o.x,y-o.y,z-o.z};}
    V3 operator*(double s)const{return{x*s,y*s,z*s};}
    double dot(const V3&o)const{return x*o.x+y*o.y+z*o.z;}
    V3 cross(const V3&o)const{return{y*o.z-z*o.y,z*o.x-x*o.z,x*o.y-y*o.x};}
    double norm()const{return std::sqrt(x*x+y*y+z*z);} };

static std::vector<V3> pos;
static std::vector<std::array<int,3>> faces;
static std::vector<char> valive, falive;
static std::vector<std::vector<int>> v2f;   // vertex -> incident face ids
static std::vector<std::array<double,10>> Q; // quadric per vertex: a2 ab ac ad b2 bc bd c2 cd d2

static void load_obj(){ std::string buf; { char c[1<<16]; size_t n; while((n=std::fread(c,1,sizeof c,stdin))>0) buf.append(c,n);}
    char* p=buf.data(); long nv=std::strtol(p,&p,10), nf=std::strtol(p,&p,10); pos.resize(nv); faces.resize(nf);
    for(long v=0;v<nv;++v){ while(*p==' '||*p=='\n'||*p=='\r'||*p=='\t')++p; ++p; pos[v].x=std::strtod(p,&p); pos[v].y=std::strtod(p,&p); pos[v].z=std::strtod(p,&p); }
    for(long f=0;f<nf;++f){ while(*p==' '||*p=='\n'||*p=='\r'||*p=='\t')++p; ++p; faces[f][0]=(int)std::strtol(p,&p,10)-1; faces[f][1]=(int)std::strtol(p,&p,10)-1; faces[f][2]=(int)std::strtol(p,&p,10)-1; } }

static void save_obj(){ std::vector<int> rm(pos.size(),0); int ov=0,of=0;
    for(size_t v=0;v<pos.size();++v) if(valive[v]) rm[v]=++ov;
    for(size_t f=0;f<faces.size();++f) if(falive[f]) ++of;
    std::string out; char l[96]; out.append(l,std::snprintf(l,sizeof l,"%d %d\n",ov,of));
    for(size_t v=0;v<pos.size();++v) if(valive[v]) out.append(l,std::snprintf(l,sizeof l,"v %.17g %.17g %.17g\n",pos[v].x,pos[v].y,pos[v].z));
    for(size_t f=0;f<faces.size();++f) if(falive[f]){ auto&t=faces[f]; out.append(l,std::snprintf(l,sizeof l,"f %d %d %d\n",rm[t[0]],rm[t[1]],rm[t[2]])); }
    std::fwrite(out.data(),1,out.size(),stdout); }

static inline V3 fnormal(int f){ auto&t=faces[f]; V3 c=(pos[t[1]]-pos[t[0]]).cross(pos[t[2]]-pos[t[0]]); double l=c.norm(); return l>0?c*(1.0/l):V3(0,0,1); }
static inline double farea(int f){ auto&t=faces[f]; return 0.5*((pos[t[1]]-pos[t[0]]).cross(pos[t[2]]-pos[t[0]])).norm(); }

static void add_face_quadric(int f){ V3 n=fnormal(f); double d=-n.dot(pos[faces[f][0]]);
    double q[10]={n.x*n.x,n.x*n.y,n.x*n.z,n.x*d, n.y*n.y,n.y*n.z,n.y*d, n.z*n.z,n.z*d, d*d};
    for(int v=0;v<3;++v){ auto&Qv=Q[faces[f][v]]; for(int k=0;k<10;++k) Qv[k]+=q[k]; } }

static bool solve_placement(const std::array<double,10>&q, V3&out){
    double a=q[0],b=q[1],c=q[2],d=q[4],e=q[5],f=q[7];   // 3x3 [[a,b,c],[b,d,e],[c,e,f]]
    double det=a*(d*f-e*e)-b*(b*f-e*c)+c*(b*e-d*c);
    if(std::fabs(det)<1e-12) return false;
    double bx=-q[3],by=-q[6],bz=-q[8];
    double i00=(d*f-e*e), i01=(c*e-b*f), i02=(b*e-c*d);
    double i11=(a*f-c*c), i12=(b*c-a*e), i22=(a*d-b*b);
    out.x=(i00*bx+i01*by+i02*bz)/det; out.y=(i01*bx+i11*by+i12*bz)/det; out.z=(i02*bx+i12*by+i22*bz)/det;
    return true; }
static double qerr(const std::array<double,10>&q,const V3&v){
    return q[0]*v.x*v.x+2*q[1]*v.x*v.y+2*q[2]*v.x*v.z+2*q[3]*v.x
          +q[4]*v.y*v.y+2*q[5]*v.y*v.z+2*q[6]*v.y +q[7]*v.z*v.z+2*q[8]*v.z +q[9]; }

// ---- manifold-safe collapse of edge (i,j): keep j at position P, remove i ----
static bool shared_ok(int i,int j){ // link condition: vertices adjacent to both i and j must form a face (i,j,k)
    std::vector<int> ni,nj;
    for(int f:v2f[i]) if(falive[f]) for(int v=0;v<3;++v){ int w=faces[f][v]; if(w!=i&&w!=j) ni.push_back(w); }
    for(int f:v2f[j]) if(falive[f]) for(int v=0;v<3;++v){ int w=faces[f][v]; if(w!=i&&w!=j) nj.push_back(w); }
    std::sort(ni.begin(),ni.end()); ni.erase(std::unique(ni.begin(),ni.end()),ni.end());
    std::sort(nj.begin(),nj.end()); nj.erase(std::unique(nj.begin(),nj.end()),nj.end());
    std::vector<int> common; std::set_intersection(ni.begin(),ni.end(),nj.begin(),nj.end(),std::back_inserter(common));
    // each common vertex k must be part of a face (i,j,k)
    for(int k:common){ bool found=false;
        for(int f:v2f[i]) if(falive[f]){ auto&t=faces[f]; bool hi=false,hj=false,hk=false; for(int v=0;v<3;++v){ if(t[v]==i)hi=true; if(t[v]==j)hj=true; if(t[v]==k)hk=true;} if(hi&&hj&&hk){found=true;break;} }
        if(!found) return false; }
    return true; }

static bool collapse(int i,int j,const V3&P,double flip_tol){
    if(!shared_ok(i,j)) return false;
    // flip/area check: simulate i,j -> P for faces incident to i or j (excluding the 1-2 shared faces that vanish)
    V3 oldi=pos[i], oldj=pos[j]; pos[i]=P; pos[j]=P;
    bool bad=false;
    for(int who=0;who<2&&!bad;++who){ int u=who?j:i;
        for(int f:v2f[u]){ if(!falive[f]) continue; auto&t=faces[f];
            bool hi=false,hj=false; for(int v=0;v<3;++v){ if(t[v]==i)hi=true; if(t[v]==j)hj=true; }
            if(hi&&hj) continue;                       // vanishing face
            V3 nn=(pos[t[1]]-pos[t[0]]).cross(pos[t[2]]-pos[t[0]]); double ar=0.5*nn.norm();
            if(ar<1e-14){ bad=true; break; }
            // old normal (before move): recompute with oldi/oldj
            V3 op[3]; for(int v=0;v<3;++v){ int w=t[v]; op[v]= (w==i)?oldi:((w==j)?oldj:pos[w]); }
            V3 on=(op[1]-op[0]).cross(op[2]-op[0]); double ol=on.norm(); if(ol>0) on=on*(1.0/ol);
            V3 nnl=nn*(1.0/(2*ar));
            if(on.dot(nnl)<flip_tol){ bad=true; break; } } }
    if(bad){ pos[i]=oldi; pos[j]=oldj; return false; }
    // commit: redirect i->j, drop faces containing edge (i,j)
    for(int f:v2f[i]){ if(!falive[f]) continue; auto&t=faces[f];
        bool hj=false; for(int v=0;v<3;++v) if(t[v]==j) hj=true;
        if(hj){ falive[f]=0; continue; }                 // shared face vanishes
        for(int v=0;v<3;++v) if(t[v]==i) t[v]=j;
        v2f[j].push_back(f); }
    valive[i]=0;
    for(int k=0;k<10;++k) Q[j][k]+=Q[i][k];
    return true; }

// ---- rasterizer: 6 axial views, flat per-face normal, res R; per-channel value maps (n+1)*127.5 ----
static void view_basis(int v,V3&eye,V3&right,V3&up,V3&fwd){
    static const V3 ax[6]={{1,0,0},{-1,0,0},{0,1,0},{0,-1,0},{0,0,1},{0,0,-1}};
    static const V3 uv[6]={{0,0,1},{0,0,1},{0,0,1},{0,0,1},{0,1,0},{0,1,0}};
    V3 a=ax[v],u=uv[v]; eye=a*2.5; fwd=a*-1; right=fwd.cross(u); right=right*(1.0/right.norm()); up=right.cross(fwd); up=up*(1.0/up.norm()); }

// render view v at res R: out[c] = per-pixel normal-channel value (0..255), fg mask; F=800*(R/1024)
static void render(int v,int R,std::vector<std::array<float,3>>&img,std::vector<char>&fg){
    img.assign((size_t)R*R,{127.5f,127.5f,127.5f}); fg.assign((size_t)R*R,0);
    std::vector<float> zb((size_t)R*R,1e30f);
    V3 eye,right,up,fwd; view_basis(v,eye,right,up,fwd);
    const double F=800.0*(R/1024.0), C=R/2.0;
    for(size_t f=0;f<faces.size();++f){ if(!falive[f]) continue; auto&t=faces[f];
        double sx[3],sy[3],cz[3]; bool ok=true;
        for(int k=0;k<3;++k){ V3 d=pos[t[k]]-eye; double cx=d.dot(right),cy=d.dot(up),cztmp=d.dot(fwd);
            if(cztmp<=1e-6){ ok=false; break; } cz[k]=cztmp; sx[k]=F*cx/cztmp+C; sy[k]=F*cy/cztmp+C; }
        if(!ok) continue;
        V3 nn=fnormal((int)f);
        std::array<float,3> col={ (float)((nn.x+1)*127.5),(float)((nn.y+1)*127.5),(float)((nn.z+1)*127.5) };
        double minx=std::min({sx[0],sx[1],sx[2]}),maxx=std::max({sx[0],sx[1],sx[2]});
        double miny=std::min({sy[0],sy[1],sy[2]}),maxy=std::max({sy[0],sy[1],sy[2]});
        int x0=std::max(0,(int)std::floor(minx)),x1=std::min(R-1,(int)std::ceil(maxx));
        int y0=std::max(0,(int)std::floor(miny)),y1=std::min(R-1,(int)std::ceil(maxy));
        double d0x=sx[1]-sx[0],d0y=sy[1]-sy[0],d1x=sx[2]-sx[0],d1y=sy[2]-sy[0];
        double den=d0x*d1y-d1x*d0y; if(std::fabs(den)<1e-12) continue;
        for(int y=y0;y<=y1;++y) for(int x=x0;x<=x1;++x){ double px=x+0.5-sx[0],py=y+0.5-sy[0];
            double b1=(px*d1y-d1x*py)/den, b2=(d0x*py-px*d0y)/den, b0=1-b1-b2;
            if(b0<-1e-6||b1<-1e-6||b2<-1e-6) continue;
            double z=b0*cz[0]+b1*cz[1]+b2*cz[2]; size_t idx=(size_t)y*R+x;
            if(z<zb[idx]){ zb[idx]=(float)z; img[idx]=col; fg[idx]=1; } } } }

// per-channel box-SSIM (11x11) over windows whose center is fg in ref OR cur; returns mean over 3 ch.
static double ssim_norm(int R,const std::vector<std::array<float,3>>&X,const std::vector<char>&fx,
                        const std::vector<std::array<float,3>>&Y,const std::vector<char>&fy){
    const int W=11,H=W/2; const double C1=6.5025,C2=58.5225; double tot=0;
    for(int c=0;c<3;++c){ double sacc=0; long cnt=0;
        for(int y=H;y<R-H;++y) for(int x=H;x<R-H;++x){ size_t ci=(size_t)y*R+x; if(!fx[ci]&&!fy[ci]) continue;
            double sx=0,sy=0,sxx=0,syy=0,sxy=0; for(int dy=-H;dy<=H;++dy) for(int dx=-H;dx<=H;++dx){ size_t p=(size_t)(y+dy)*R+(x+dx); double a=X[p][c],b=Y[p][c]; sx+=a; sy+=b; sxx+=a*a; syy+=b*b; sxy+=a*b; }
            double n=W*W, mx=sx/n,my=sy/n, vx=sxx/n-mx*mx, vy=syy/n-my*my, vxy=sxy/n-mx*my;
            double s=((2*mx*my+C1)*(2*vxy+C2))/((mx*mx+my*my+C1)*(vx+vy+C2)); sacc+=s; ++cnt; }
        if(cnt>0) tot+=sacc/cnt; }
    return tot/3.0; }

static int g_R=96;
static std::vector<std::array<float,3>> REFimg[6]; static std::vector<char> REFfg[6];
static double score_current(){ double s=0; for(int v=0;v<6;++v){ std::vector<std::array<float,3>> img; std::vector<char> fg; render(v,g_R,img,fg); s+=ssim_norm(g_R,REFimg[v],REFfg[v],img,fg); } return s/6.0; }

int main(){ load_obj();
    const char* md=getenv("G_MODE"); bool ssim_mode = md&&!strcmp(md,"ssim");
    int target=getenv("G_TARGET")?atoi(getenv("G_TARGET")):(int)(pos.size()/4);
    g_R=getenv("G_RES")?atoi(getenv("G_RES")):96;
    int K=getenv("G_K")?atoi(getenv("G_K")):8;
    int nv=(int)pos.size(),nf=(int)faces.size();
    valive.assign(nv,1); falive.assign(nf,1); v2f.assign(nv,{}); Q.assign(nv,{});
    for(int f=0;f<nf;++f) for(int v=0;v<3;++v) v2f[faces[f][v]].push_back(f);
    for(int f=0;f<nf;++f) add_face_quadric(f);
    for(int v=0;v<6;++v) render(v,g_R,REFimg[v],REFfg[v]);       // reference = original
    std::fprintf(stderr,"[sg] in V=%d F=%d target=%d mode=%s R=%d K=%d\n",nv,nf,target,ssim_mode?"ssim":"qem",g_R,K);

    int alive=nv;
    auto valid_edges=[&](std::vector<std::array<int,3>>&E){ // unique alive edges i<j with a QEM cost key
        E.clear(); for(int f=0;f<nf;++f){ if(!falive[f]) continue; auto&t=faces[f];
            for(int e=0;e<3;++e){ int a=t[e],b=t[(e+1)%3]; if(a>b) std::swap(a,b); E.push_back({a,b,f}); } }
        std::sort(E.begin(),E.end()); E.erase(std::unique(E.begin(),E.end(),[](auto&x,auto&y){return x[0]==y[0]&&x[1]==y[1];}),E.end()); };

    while(alive>target){
        // rank candidate edges by QEM cost (cheap prefilter)
        std::vector<std::array<int,3>> E; valid_edges(E);
        std::vector<std::pair<double,std::array<int,3>>> cand; cand.reserve(E.size());
        for(auto&e:E){ int i=e[0],j=e[1]; if(!valive[i]||!valive[j]) continue;
            std::array<double,10> qs; for(int k=0;k<10;++k) qs[k]=Q[i][k]+Q[j][k];
            V3 P; if(!solve_placement(qs,P)) P=(pos[i]+pos[j])*0.5;
            cand.push_back({qerr(qs,P),{i,j,0}}); }
        if(cand.empty()) break;
        std::sort(cand.begin(),cand.end(),[](auto&a,auto&b){return a.first<b.first;});

        int bi=-1,bj=-1; V3 bP;
        if(!ssim_mode){ // QEM: cheapest valid collapse
            for(auto&c:cand){ int i=c.second[0],j=c.second[1]; std::array<double,10> qs; for(int k=0;k<10;++k) qs[k]=Q[i][k]+Q[j][k];
                V3 P; if(!solve_placement(qs,P)) P=(pos[i]+pos[j])*0.5;
                V3 si=pos[i],sj=pos[j]; if(collapse(i,j,P,0.2)){ bi=i;bj=j; /*committed*/ break; } (void)si;(void)sj; }
            if(bi<0) break; alive--; continue;
        }
        // SSIM: among K cheapest-QEM valid candidates, pick the one whose collapse yields best normal-SSIM.
        double best=-1; std::array<int,3> bestc{-1,-1,-1}; V3 bestP;
        // snapshot to restore after each trial
        std::vector<V3> sp=pos; std::vector<char> sv=valive,sfp=falive; std::vector<std::array<int,3>> sf=faces; auto sq=Q; auto s2=v2f;
        int tried=0;
        for(auto&c:cand){ if(tried>=K) break; int i=c.second[0],j=c.second[1];
            std::array<double,10> qs; for(int k=0;k<10;++k) qs[k]=Q[i][k]+Q[j][k]; V3 P; if(!solve_placement(qs,P)) P=(pos[i]+pos[j])*0.5;
            if(!collapse(i,j,P,0.2)){ pos=sp;valive=sv;falive=sfp;faces=sf;Q=sq;v2f=s2; continue; }
            ++tried; double s=score_current();
            pos=sp;valive=sv;falive=sfp;faces=sf;Q=sq;v2f=s2;              // undo
            if(s>best){ best=s; bestc={i,j,0}; bestP=P; } }
        if(bestc[0]<0) break;
        if(!collapse(bestc[0],bestc[1],bestP,0.2)) break; alive--;
    }
    std::fprintf(stderr,"[sg] out V=%d\n",alive);
    save_obj(); return 0; }
