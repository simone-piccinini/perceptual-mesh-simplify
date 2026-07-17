"""Port the C4 DEPTH-REFINE (G_WD) mechanism onto a team-HEAD mein.cpp — WEAVE form.

v1 (separate depth_score_grad function, +4.4KB) CE'd the judge compile 3x
(20055048/067/082) while the mechanism-free bisect 20055094 compiled -> the new
function tipped the compile-memory cliff. v2 (this): weave an optional gradient
into the EXISTING sil_score_depth (FP-order-identical score math; grad code only
behind `if (grad)`), halving the new-code footprint and adding no big new function.

usage: py -3 scripts/patch_wd_team.py <team_head.cpp>   (patches in place)
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8", newline="").read().replace("\r\n", "\n")

subs = []

# W1 — signature + grad init + grad statics
subs.append((
"""static double sil_score_depth() {
    const int W = g_res; double total = 0;
    static std::vector<float> mx,my,xx,yy,xy,Y,t,bx; std::vector<int> fs; std::vector<double> zb;""",
"""static double sil_score_depth(std::vector<Vec3>* grad = nullptr) {
    const int W = g_res; double total = 0;
    if (grad) grad->assign(pos.size(), Vec3::Zero());
    static std::vector<float> mx,my,xx,yy,xy,Y,t,bx,Gm,Gs,Gx,Sm,Ss,Sm2,Sx,Sx2; std::vector<int> fs; std::vector<double> zb;"""))

# W2 — per-view grad buffer reset
subs.append((
"""        for(size_t k=0;k<t.size();++k) t[k]=Xr[k]*Y[k];  r_boxsum(t,bx,W); xy.resize(t.size()); for(size_t k=0;k<t.size();++k) xy[k]=bx[k]/R_WN;
        double acc = 0; long N = 0;""",
"""        for(size_t k=0;k<t.size();++k) t[k]=Xr[k]*Y[k];  r_boxsum(t,bx,W); xy.resize(t.size()); for(size_t k=0;k<t.size();++k) xy[k]=bx[k]/R_WN;
        if (grad) { Gm.assign((size_t)W*W,0.f); Gs.assign((size_t)W*W,0.f); Gx.assign((size_t)W*W,0.f); }
        double acc = 0; long N = 0;"""))

# W3 — window grads (FP-identical acc path: A*B/(Cc*Dd) preserves op order) + chain to vertices
subs.append((
"""            double MX=mx[k],MY=my[k],SX=xx[k]-MX*MX,SY=yy[k]-MY*MY,SXY=xy[k]-MX*MY;
            acc += ((2*MX*MY+R_C1)*(2*SXY+R_C2))/((MX*MX+MY*MY+R_C1)*(SX+SY+R_C2)); ++N; }
        total += (N ? acc/N : 1.0)/6.0;
    }
    g_crop_on = false;
    return total;
}""",
"""            double MX=mx[k],MY=my[k],SX=xx[k]-MX*MX,SY=yy[k]-MY*MY,SXY=xy[k]-MX*MY;
            double A=2*MX*MY+R_C1,B=2*SXY+R_C2,Cc=MX*MX+MY*MY+R_C1,Dd=SX+SY+R_C2;
            acc += (A*B)/(Cc*Dd); ++N;
            if (grad) { Gm[k]=(float)(2*B*(MX*Cc-MY*A)/(Cc*Cc*Dd)); Gs[k]=(float)(-(A*B)/(Cc*Dd*Dd)); Gx[k]=(float)(2*A/(Cc*Dd)); } }
        total += (N ? acc/N : 1.0)/6.0;
        if (grad && N > 0) {
            r_boxsum(Gm,Sm,W); r_boxsum(Gs,Ss,W);
            t.assign((size_t)W*W,0.f); for(size_t k=0;k<t.size();++k) t[k]=Gs[k]*my[k]; r_boxsum(t,Sm2,W);
            r_boxsum(Gx,Sx,W);
            for(size_t k=0;k<t.size();++k) t[k]=Gx[k]*mx[k]; r_boxsum(t,Sx2,W);
            Vec3 eye, right, up, fwd; view_basis(v, eye, right, up, fwd);
            const double inv = 1.0/((double)N*R_WN*6.0);
            const double fx3=fwd.x()/3.0, fy3=fwd.y()/3.0, fz3=fwd.z()/3.0;
            for(size_t k=0;k<(size_t)W*W;++k){ int f=fs[k]; if(f<0) continue;
                double dS = inv*( Sm[k] + 2.0*(Y[k]*Ss[k]-Sm2[k]) + (Xr[k]*Sx[k]-Sx2[k]) );
                const int* tr = faces[f].data();
                for (int j = 0; j < 3; ++j) { Vec3& gr = (*grad)[tr[j]]; gr.x() += fx3*dS; gr.y() += fy3*dS; gr.z() += fz3*dS; } }
        }
    }
    g_crop_on = false;
    return total;
}"""))

# W4 — g_wd globals
subs.append((
"static int    g_mini_maxit = (1<<30);    // C3 DETERMINISM (env G_MINI): fixed-count cap for mini_refine (RC3 repair burst)",
"""static int    g_mini_maxit = (1<<30);    // C3 DETERMINISM (env G_MINI): fixed-count cap for mini_refine (RC3 repair burst)
static double g_wd = 0.0;                // C4 DEPTH-REFINE (env G_WD): weight of the depth-SSIM term in the stock refine
static double g_wd_c4 = 0.0;             // judge-variant knob (sed'd to 0.5 in the variant arm; judge has no env)"""))

# W5 — blended_sg wrapper (small; O1+noinline for cc1plus headroom) before sil_pass
subs.append((
"// SIL: silhouette pass — line-search a single outward displacement delta applied to all",
"""static __attribute__((optimize("O1"),noinline)) double blended_sg(std::vector<Vec3>* grad) {
    if (g_wd <= 0.0 && g_wd_c4 > 0.0 && (int)pos.size() > 30000 && (int)pos.size() <= 40000) g_wd = g_wd_c4;
    double sn = refine_score_grad(grad);
    if (g_wd <= 0.0) return sn;
    static std::vector<Vec3> gd;
    double sd = sil_score_depth(grad ? &gd : nullptr);
    if (grad) for (size_t i = 0; i < grad->size(); ++i) { Vec3& a = (*grad)[i]; const Vec3& b = gd[i];
        a.x() = a.x()*(1.0-g_wd) + b.x()*g_wd; a.y() = a.y()*(1.0-g_wd) + b.y()*g_wd; a.z() = a.z()*(1.0-g_wd) + b.z()*g_wd; }
    return (1.0-g_wd)*sn + g_wd*sd;
}
// SIL: silhouette pass — line-search a single outward displacement delta applied to all"""))

# W6 — swap the four stock-refine call sites
subs.append((
"    double cur=refine_score_grad(nullptr);\n    auto stock_pass",
"    double cur=blended_sg(nullptr);\n    auto stock_pass"))
subs.append((
"        std::vector<Vec3> g; double dummy = refine_score_grad(&g); (void)dummy;",
"        std::vector<Vec3> g; double dummy = blended_sg(&g); (void)dummy;"))
subs.append((
"            std::vector<Vec3> gt; double sn=refine_score_grad(&gt);  // score AND gradient at the trial point",
"            std::vector<Vec3> gt; double sn=blended_sg(&gt);  // score AND gradient at the trial point"))
subs.append((
'        cur = refine_score_grad(nullptr);\n        if (getenv("G_RDBG")) std::fprintf(stderr, "[hyb] 1024 baseline',
'        cur = blended_sg(nullptr);\n        if (getenv("G_RDBG")) std::fprintf(stderr, "[hyb] 1024 baseline'))

# W8 — compile-budget buyback: O1+noinline the 521-line sil2_pass (biggest fn; called once/case
# so runtime impact is bounded). The base compiles at ~24s and ANY addition CE's (4x: 20055048/067/
# 082/135 all die ~24s, bisect 20055094 without the mechanism compiles) -> pay for the mechanism by
# demoting the monster. FAMILY NOTE: O1 changes sil2's float path -> c4/c5 read family shifts, but
# both arms share it (differential clean). NOT for banking without revalidation.
subs.append((
"static void sil2_pass(int bdef = 150, int diag = 0) {",
"static __attribute__((optimize(\"O1\"),noinline)) void sil2_pass(int bdef = 150, int diag = 0) {"))

# W7 — env hook
subs.append((
'    if (const char* e = getenv("G_MAXIT")) g_refine_maxit = atoi(e);',
'''    if (const char* e = getenv("G_MAXIT")) g_refine_maxit = atoi(e);
    if (const char* e = getenv("G_WD")) g_wd = atof(e);   // C4 DEPTH-REFINE weight (judge variant: g_wd_c4 constant)'''))

for a, b in subs:
    n = s.count(a)
    assert n == 1, ("NOT UNIQUE/FOUND", n, a[:70])
    s = s.replace(a, b)

open(p, "w", encoding="utf-8", newline="").write(s)
print("weave patches applied,", len(s), "bytes")
