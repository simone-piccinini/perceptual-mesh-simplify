"""Add G_TELE (Lindstrom-Turk 2000 vertex-teleport, batch form) to the lab binary.

Teleport batch round: (1) per-face deficit from cached base render (g_rfs) vs g_orig_n at 1024;
(2) split the S worst-deficit faces' longest edges at midpoint (reusing dead vertex slots);
(3) seed_heap()+Decimate(N) collapses the globally QEM-cheapest edges back to budget
    (R-zeta: QEM ordering ~ rendered ordering => this IS the 'cheapest collapse' side of LT);
(4) mini_refine polish. R rounds. env: G_TELE=<S splits/round>, G_TELER=<rounds, default 4>.

usage: py -3 patch_tele.py <lab.cpp>
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8", newline="").read().replace("\r\n", "\n")

FN = r'''
// ==== G_TELE: LT-2000 vertex teleports, batch form (LAB experiment; env-gated) ====
static int tele_free_slot(int& scan) {
    const int n = (int)pos.size();
    while (scan < n && alive[scan]) ++scan;
    return (scan < n) ? scan : -1;
}
static void tele_rounds(int S, int R, int target) {
    int scan = 0;
    for (int round = 0; round < R; ++round) {
        // (1) per-face deficit at 1024 from the cached base render
        g_res = 1024; g_refine_res = 1024;
        g_force_nocrop = 1; fnc_fill(); remesh_cache_render(); g_force_nocrop = 0;
        std::vector<double> defc(faces.size(), 0.0);
        for (int vw = 0; vw < 6; ++vw) {
            const int W = g_res;
            for (size_t k = 0; k < (size_t)W*W; ++k) {
                int f = g_rfs[vw][k]; if (f < 0) continue;
                double dsum = 0;
                for (int ch = 0; ch < 3; ++ch)
                    dsum += std::abs((double)g_orig_n[vw][ch][k] - ((g_fnc[f][ch]+1.0)*127.5));
                defc[f] += dsum;
            }
        }
        // (2) split the S worst faces' longest edges (skip faces adjacent to fresh splits)
        std::vector<int> order(faces.size()); for (size_t i=0;i<order.size();++i) order[i]=(int)i;
        std::sort(order.begin(), order.end(), [&](int a,int b){ return defc[a]>defc[b]; });
        std::vector<char> touched(pos.size(), 0);
        int done = 0;
        for (int oi = 0; oi < (int)order.size() && done < S; ++oi) {
            int f = order[oi];
            if (!face_alive[f] || defc[f] <= 0) continue;
            const int* t = faces[f].data();
            if (touched[t[0]] || touched[t[1]] || touched[t[2]]) continue;
            // longest edge (u,v) of f, with its opposite partner face f2
            int bu=-1,bv=-1; double bl=-1;
            for (int e = 0; e < 3; ++e) {
                int u=t[e], v=t[(e+1)%3];
                double l=(pos[u]-pos[v]).squaredNorm();
                if (l>bl){bl=l;bu=u;bv=v;}
            }
            int f2=-1, a=-1, b=-1;
            for (int g2 : vfaces[bu]) { if (g2==f||!face_alive[g2]) continue;
                const int* q=faces[g2].data(); bool hasv=false; for(int k2=0;k2<3;++k2) if(q[k2]==bv) hasv=true;
                if (hasv) { f2=g2; break; } }
            if (f2 < 0) continue;
            for (int k2=0;k2<3;++k2){ if(faces[f][k2]!=bu&&faces[f][k2]!=bv) a=faces[f][k2];
                                      if(faces[f2][k2]!=bu&&faces[f2][k2]!=bv) b=faces[f2][k2]; }
            if (a<0||b<0) continue;
            int w = tele_free_slot(scan); if (w<0) break;
            pos[w] = 0.5*(pos[bu]+pos[bv]); alive[w]=1; ++alive_count;
            vfaces[w].clear();
            // rewrite f: replace bv->w ; new face (w,bv,third) preserving orientation of f
            auto rewrite=[&](int ff){
                std::array<int,3> old=faces[ff];
                for(int k2=0;k2<3;++k2) if(old[k2]==bv) faces[ff][k2]=w;
                std::array<int,3> nf=old;
                for(int k2=0;k2<3;++k2) if(nf[k2]==bu) nf[k2]=w;
                faces.push_back(nf); face_alive.push_back(1);
                int nid=(int)faces.size()-1;
                for(int k2=0;k2<3;++k2){ int vv=nf[k2];
                    vfaces[vv].push_back(nid); }
                // fix membership: ff now excludes bv; nid excludes bu
                auto& lu=vfaces[bv]; for(size_t z=0;z<lu.size();++z) if(lu[z]==ff){ lu.erase(lu.begin()+z); break; }
                vfaces[w].push_back(ff);
            };
            rewrite(f); rewrite(f2);
            touched[bu]=touched[bv]=touched[a]=touched[b]=touched[w]=1;
            ++done;
        }
        if (getenv("G_ITERDBG")) std::fprintf(stderr, "[tele] r%d splits=%d V=%d\n", round, done, alive_count);
        if (!done) break;
        // (3) rebalance: collapse the QEM-cheapest edges back to target
        seed_heap(); Decimate(target);
        for (int rw = 0; rw < 2 && alive_count > target; ++rw)
            if (vertex_remove_pass(alive_count - target) == 0) break;
        // (4) polish
        mini_refine(1.2);
    }
}
'''

subs = []
# function before the c3 band block: anchor on save_obj (defined earlier than main path use)
subs.append((
"static int g_addtet = 0;",
"static int g_addtet = 0;" + FN))
# invoke inside the c3 band after the repair mini_refine
subs.append((
"        mini_refine(1.2);                          // repair burst",
"""        mini_refine(1.2);                          // repair burst
        if (const char* te = getenv("G_TELE")) {   // LAB: LT-2000 teleport rounds
            int S = atoi(te); int R = 4; if (const char* tr = getenv("G_TELER")) R = atoi(tr);
            tele_rounds(S, R, c3t);
        }"""))

for a, b in subs:
    n = s.count(a)
    assert n == 1, ("NOT UNIQUE", n, a[:60])
    s = s.replace(a, b)

open(p, "w", encoding="utf-8", newline="").write(s)
print("G_TELE patched,", len(s), "bytes")
