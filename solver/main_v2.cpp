// IMC2 Problem B (simplifygeometry) — SECOND SOLVER, built from scratch (2026-07-06).
//
// This is NOT a variant of solver/main.cpp. main.cpp's algorithm (greedy QEM/VSA-lite
// edge-collapse decimation) is a DECIMATION method: it starts from the full mesh and removes
// vertices. This file is a CONSTRUCTION method: it starts from almost nothing and ADDS
// vertices where the rendered image is wrong. The two are unrelated at the algorithm level.
//
// What IS shared with main.cpp, deliberately: the parts that are not "the algorithm" but the
// judge's own specification — OBJ I/O, the 6-camera rasterizer, the SSIM formula. There is
// exactly one correct way to implement an external spec; reproducing it here is not reusing
// a design decision, it is satisfying a scoring contract. Every other choice below (seed
// topology, growth order, split rule, vertex placement) is independent of main.cpp.
//
// STATUS (2026-07-06): first working skeleton. Seed = convex hull of the input vertices
// (genus-0 by construction; verified genus-0 on the judge for 2 cases and on every local
// proxy for the rest — see docs/JUDGE-ENVELOPE.md). Growth = split the face whose rendered
// SSIM deficit (summed over 6 views via backprojection) is worst; new vertex placed at the
// split point, pulled toward the nearest point on the ORIGINAL surface. This is a genuinely
// new search direction (build up, not tear down) — expected to be UNCOMPETITIVE on day one;
// this file is scaffolding for a multi-day effort, not a submission candidate.
//
// NEVER submit this file to the judge without an explicit local A/B against the current bank
// AND a judge read via the measured-mesh instrument (see docs/THEORY.md §9.4) at a SAFE rung.

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <vector>
#include <array>
#include <algorithm>
#include <chrono>
#include <random>
#include <map>
#include <set>
#include <queue>
#include "Eigen/Dense"

using Vec3 = Eigen::Vector3d;

// ===================== I/O (judge OBJ subset: "V F" header, v/f lines) =====================
static std::vector<Vec3> pos;
static std::vector<std::array<int,3>> faces;

static void load_obj() {
    std::string buf; buf.reserve(1 << 26);
    char chunk[1 << 16];
    size_t n;
    while ((n = std::fread(chunk, 1, sizeof(chunk), stdin)) > 0) buf.append(chunk, n);
    const char* p = buf.c_str();
    long V = std::strtol(p, (char**)&p, 10);
    long F = std::strtol(p, (char**)&p, 10);
    pos.resize(V);
    for (long i = 0; i < V; ++i) {
        while (*p && *p != 'v') ++p; ++p;
        double x = std::strtod(p, (char**)&p);
        double y = std::strtod(p, (char**)&p);
        double z = std::strtod(p, (char**)&p);
        pos[i] = Vec3(x, y, z);
    }
    faces.resize(F);
    for (long i = 0; i < F; ++i) {
        while (*p && *p != 'f') ++p; ++p;
        long a = std::strtol(p, (char**)&p, 10);
        long b = std::strtol(p, (char**)&p, 10);
        long c = std::strtol(p, (char**)&p, 10);
        faces[i] = {(int)(a - 1), (int)(b - 1), (int)(c - 1)};
    }
}

static void save_obj(const std::vector<Vec3>& P, const std::vector<std::array<int,3>>& Fa) {
    std::string out; out.reserve(P.size() * 40 + Fa.size() * 24);
    char line[128];
    out.append(line, std::snprintf(line, sizeof line, "%d %d\n", (int)P.size(), (int)Fa.size()));
    for (const Vec3& v : P)
        out.append(line, std::snprintf(line, sizeof line, "v %.17g %.17g %.17g\n", v.x(), v.y(), v.z()));
    for (const auto& f : Fa)
        out.append(line, std::snprintf(line, sizeof line, "f %d %d %d\n", f[0]+1, f[1]+1, f[2]+1));
    std::fwrite(out.data(), 1, out.size(), stdout);
}

// ===================== Judge camera model (PROBLEM-AND-JUDGE.md spec) =====================
// 6 fixed axial cameras, distance D=2.5, focal length F=800px at resolution 1024, principal
// point at the image center. Flat shading: each pixel takes the constant normal of the
// nearest face covering its center. Depth = perspective-correct camera-space z. Background:
// normal encodes to neutral gray (127.5), depth to 255.
static void view_basis(int v, Vec3& eye, Vec3& right, Vec3& up, Vec3& fwd) {
    static const Vec3 ax[6] = {{1,0,0},{-1,0,0},{0,1,0},{0,-1,0},{0,0,1},{0,0,-1}};
    static const Vec3 upref[6] = {{0,0,1},{0,0,1},{0,0,1},{0,0,1},{0,1,0},{0,1,0}};
    eye = 2.5 * ax[v];
    fwd = -ax[v];
    right = fwd.cross(upref[v]).normalized();
    up = right.cross(fwd).normalized();
}

// screen-space projection of every vertex for view v at resolution W (judge camera model) --
// factored out of render() so candidate-scoring code can rasterize hypothetical local changes
// using the SAME per-vertex projections as the real render, without re-deriving the formula.
static void project_view(const std::vector<Vec3>& P, int v, int W,
                          std::vector<double>& su, std::vector<double>& sv, std::vector<double>& sd) {
    const double F = 800.0 * (W / 1024.0), C = W / 2.0;
    Vec3 eye, right, up, fwd; view_basis(v, eye, right, up, fwd);
    const int n = (int)P.size();
    su.assign(n, 0.0); sv.assign(n, 0.0); sd.assign(n, 0.0);
    for (int i = 0; i < n; ++i) {
        Vec3 r = P[i] - eye;
        double x = r.dot(right), y = r.dot(up), d = r.dot(fwd);
        if (d == 0) d = 1e-9;
        su[i] = F * x / d + C; sv[i] = F * y / d + C; sd[i] = d;
    }
}

// Render the given mesh from view v at resolution W: per-pixel face id (-1 = background) and
// per-pixel camera-space depth (perspective-correct via 1/z barycentric interpolation).
static void render_proj(const std::vector<Vec3>& P, const std::vector<std::array<int,3>>& Fa,
                         int W, const std::vector<double>& su, const std::vector<double>& sv,
                         const std::vector<double>& sd, std::vector<int>& fid, std::vector<double>& depth) {
    fid.assign((size_t)W * W, -1);
    depth.assign((size_t)W * W, 255.0);
    std::vector<double> zbuf((size_t)W * W, 1e30);
    for (int f = 0; f < (int)Fa.size(); ++f) {
        const auto& t = Fa[f];
        double d0 = sd[t[0]], d1 = sd[t[1]], d2 = sd[t[2]];
        if (d0 <= 0 || d1 <= 0 || d2 <= 0) continue;
        double u0 = su[t[0]], v0 = sv[t[0]], u1 = su[t[1]], v1 = sv[t[1]], u2 = su[t[2]], v2 = sv[t[2]];
        double det = (v1 - v2) * (u0 - u2) + (u2 - u1) * (v0 - v2);
        if (det > -1e-12 && det < 1e-12) continue;
        double inv = 1.0 / det;
        int mnx = std::max(0, (int)std::floor(std::min({u0, u1, u2})));
        int mxx = std::min(W - 1, (int)std::ceil(std::max({u0, u1, u2})));
        int mny = std::max(0, (int)std::floor(std::min({v0, v1, v2})));
        int mxy = std::min(W - 1, (int)std::ceil(std::max({v0, v1, v2})));
        for (int py = mny; py <= mxy; ++py) {
            double cy = py + 0.5;
            for (int px = mnx; px <= mxx; ++px) {
                double cx = px + 0.5;
                double w0 = ((v1 - v2) * (cx - u2) + (u2 - u1) * (cy - v2)) * inv;
                double w1 = ((v2 - v0) * (cx - u2) + (u0 - u2) * (cy - v2)) * inv;
                double w2 = 1 - w0 - w1;
                if (w0 < -1e-9 || w1 < -1e-9 || w2 < -1e-9) continue;
                double den = w0 / d0 + w1 / d1 + w2 / d2;
                if (den <= 0) continue;
                double z = 1.0 / den;
                size_t k = (size_t)py * W + px;
                if (z < zbuf[k]) { zbuf[k] = z; fid[k] = f; depth[k] = z; }
            }
        }
    }
}

static void render(const std::vector<Vec3>& P, const std::vector<std::array<int,3>>& Fa,
                    int v, int W, std::vector<int>& fid, std::vector<double>& depth) {
    std::vector<double> su, sv, sd;
    project_view(P, v, W, su, sv, sd);
    render_proj(P, Fa, W, su, sv, sd, fid, depth);
}

static inline Vec3 face_normal(const std::vector<Vec3>& P, const std::array<int,3>& t) {
    Vec3 n = (P[t[1]] - P[t[0]]).cross(P[t[2]] - P[t[0]]);
    double l = n.norm();
    return l > 1e-15 ? Vec3(n / l) : Vec3::Zero();
}

// ===================== SSIM (11x11 box window, judge constants) =====================
static const double C1 = 6.5025, C2 = 58.5225;
static const int RAD = 5, WN = 121;

// Separable 11x11 box sum, WxW image.
static void box_sum(const std::vector<double>& img, int W, std::vector<double>& out) {
    static std::vector<double> tmp;
    tmp.assign((size_t)W * W, 0.0); out.assign((size_t)W * W, 0.0);
    for (int y = 0; y < W; ++y) {
        double s = 0;
        for (int x = 0; x <= RAD && x < W; ++x) s += img[(size_t)y * W + x];
        for (int x = 0; x < W; ++x) {
            tmp[(size_t)y * W + x] = s;
            int add = x + RAD + 1, rem = x - RAD;
            if (add < W) s += img[(size_t)y * W + add];
            if (rem >= 0) s -= img[(size_t)y * W + rem];
        }
    }
    for (int x = 0; x < W; ++x) {
        double s = 0;
        for (int y = 0; y <= RAD && y < W; ++y) s += tmp[(size_t)y * W + x];
        for (int y = 0; y < W; ++y) {
            out[(size_t)y * W + x] = s;
            int add = y + RAD + 1, rem = y - RAD;
            if (add < W) s += tmp[(size_t)add * W + x];
            if (rem >= 0) s -= tmp[(size_t)rem * W + x];
        }
    }
}

// Per-pixel SSIM map between two WxW scalar images (already in judge encoded space).
static void ssim_map(const std::vector<double>& X, const std::vector<double>& Y, int W,
                      std::vector<double>& out) {
    static std::vector<double> mx, my, xx, yy, xy;
    box_sum(X, W, mx); box_sum(Y, W, my);
    std::vector<double> t(X.size());
    for (size_t k = 0; k < X.size(); ++k) t[k] = X[k] * X[k]; box_sum(t, W, xx);
    for (size_t k = 0; k < X.size(); ++k) t[k] = Y[k] * Y[k]; box_sum(t, W, yy);
    for (size_t k = 0; k < X.size(); ++k) t[k] = X[k] * Y[k]; box_sum(t, W, xy);
    out.assign(X.size(), 0.0);
    for (size_t k = 0; k < X.size(); ++k) {
        double MX = mx[k] / WN, MY = my[k] / WN;
        double SX = xx[k] / WN - MX * MX, SY = yy[k] / WN - MY * MY, SXY = xy[k] / WN - MX * MY;
        double A = 2 * MX * MY + C1, B = 2 * SXY + C2, D1 = MX * MX + MY * MY + C1, D2 = SX + SY + C2;
        out[k] = (A * B) / (D1 * D2);
    }
}

// ===================== convex hull (incremental, O(n log n) avg) =====================
// Standard incremental 3D convex hull: start from a tetrahedron, add points outside the
// current hull one at a time, remove faces visible from the new point, patch the resulting
// hole with a fan to the new vertex. Robust enough for a seed mesh (not perf-critical: runs
// once on <=1.1M points but only needs the OUTER shape, so pre-filter to a coarse voxel-grid
// sample first to keep this fast on the largest case).
static void convex_hull(const std::vector<Vec3>& pts, std::vector<Vec3>& hullV,
                         std::vector<std::array<int,3>>& hullF) {
    const int n = (int)pts.size();
    // seed tetrahedron: extreme point on X, then farthest from it, then farthest from the
    // line, then farthest from the plane.
    int i0 = 0; for (int i = 1; i < n; ++i) if (pts[i].x() < pts[i0].x()) i0 = i;
    int i1 = 0; double best = -1;
    for (int i = 0; i < n; ++i) { double d = (pts[i] - pts[i0]).squaredNorm(); if (d > best) { best = d; i1 = i; } }
    int i2 = 0; best = -1;
    Vec3 dir = (pts[i1] - pts[i0]).normalized();
    for (int i = 0; i < n; ++i) {
        Vec3 r = pts[i] - pts[i0]; double d = (r - dir * r.dot(dir)).squaredNorm();
        if (d > best) { best = d; i2 = i; }
    }
    int i3 = 0; best = -1;
    Vec3 nrm = (pts[i1] - pts[i0]).cross(pts[i2] - pts[i0]).normalized();
    for (int i = 0; i < n; ++i) {
        double d = std::fabs((pts[i] - pts[i0]).dot(nrm));
        if (d > best) { best = d; i3 = i; }
    }
    std::vector<Vec3> V = {pts[i0], pts[i1], pts[i2], pts[i3]};
    Vec3 centroid = (V[0] + V[1] + V[2] + V[3]) / 4.0;
    auto mk = [&](int a, int b, int c) -> std::array<int,3> {
        Vec3 n = (V[b] - V[a]).cross(V[c] - V[a]);
        if (n.dot(V[a] - centroid) < 0) std::swap(b, c);
        return {a, b, c};
    };
    std::vector<std::array<int,3>> F = {mk(0,1,2), mk(0,1,3), mk(0,2,3), mk(1,2,3)};

    std::vector<char> used(n, 0);
    used[i0] = used[i1] = used[i2] = used[i3] = 1;

    for (int i = 0; i < n; ++i) {
        if (used[i]) continue;
        const Vec3& p = pts[i];
        std::vector<char> visible(F.size(), 0);
        bool any = false;
        for (size_t f = 0; f < F.size(); ++f) {
            const auto& t = F[f];
            Vec3 n = (V[t[1]] - V[t[0]]).cross(V[t[2]] - V[t[0]]);
            if (n.dot(p - V[t[0]]) > 1e-12) { visible[f] = 1; any = true; }
        }
        if (!any) continue;   // point is inside the current hull
        // horizon edges: edges of visible faces not shared with another visible face
        std::vector<std::pair<int,int>> horizon;
        for (size_t f = 0; f < F.size(); ++f) {
            if (!visible[f]) continue;
            const auto& t = F[f];
            int e[3][2] = {{t[0],t[1]},{t[1],t[2]},{t[2],t[0]}};
            for (auto& ed : e) {
                bool shared = false;
                for (size_t g = 0; g < F.size(); ++g) {
                    if (g == f || !visible[g]) continue;
                    const auto& t2 = F[g];
                    for (int k = 0; k < 3; ++k) {
                        int a = t2[k], b = t2[(k+1)%3];
                        if (a == ed[1] && b == ed[0]) shared = true;
                    }
                }
                if (!shared) horizon.push_back({ed[0], ed[1]});
            }
        }
        std::vector<std::array<int,3>> nf;
        for (size_t f = 0; f < F.size(); ++f) if (!visible[f]) nf.push_back(F[f]);
        int newIdx = (int)V.size();
        V.push_back(p);
        for (auto& e : horizon) nf.push_back({e.first, e.second, newIdx});
        F = std::move(nf);
        used[i] = 1;
    }

    // day 7 finding (bug present since day 1, never caught until the day-7 clustering path's
    // Euler-characteristic sanity check exposed it): if a NEW point's visibility region fully
    // SURROUNDS an existing hull vertex (every one of that vertex's faces is visible, so none
    // survive), that vertex has no horizon edge through it and is silently orphaned -- all its
    // faces removed, but the vertex itself is never dropped from V. Measured: exactly 3 orphaned
    // (degree-0) vertices out of 20 on the bunny's 24-point farthest-sample seed, giving
    // V-E+F=5 instead of the genus-0 sphere's 2 -- topologically invalid despite every edge
    // still being cleanly shared by exactly 2 faces (that check alone can't see this). Strip any
    // 0-degree vertex and recompact indices, same fix as the day-7 clustered-mesh repair.
    std::vector<char> deg(V.size(), 0);
    for (const auto& t : F) for (int k = 0; k < 3; ++k) deg[t[k]] = 1;
    std::vector<int> remap(V.size(), -1);
    std::vector<Vec3> newV;
    for (size_t v = 0; v < V.size(); ++v) if (deg[v]) { remap[v] = (int)newV.size(); newV.push_back(V[v]); }
    for (auto& t : F) for (int k = 0; k < 3; ++k) t[k] = remap[t[k]];
    hullV = std::move(newV); hullF = std::move(F);
}

// ===================== adaptive refinement growth loop =====================
// Score the CURRENT mesh against the ORIGINAL's stored renders at `res`, find the face whose
// backprojected rendered deficit is worst, split it at the centroid, place the new vertex
// toward the nearest point on the original surface.

struct OrigViews {
    std::vector<std::vector<double>> nX[3];  // 6 views x per-pixel encoded normal, channel c
    std::vector<std::vector<double>> dX;     // 6 views x per-pixel depth
    std::vector<std::vector<int>> covF;      // 6 views x face-id (for attribution only)
    int res = 0;
};

static void capture_original(const std::vector<Vec3>& P, const std::vector<std::array<int,3>>& Fa,
                              int res, OrigViews& O) {
    O.res = res;
    for (int c = 0; c < 3; ++c) O.nX[c].assign(6, {});
    O.dX.assign(6, {});
    O.covF.assign(6, {});
    for (int v = 0; v < 6; ++v) {
        std::vector<int> fid; std::vector<double> depth;
        render(P, Fa, v, res, fid, depth);
        O.covF[v] = fid;
        O.dX[v] = depth;
        for (int c = 0; c < 3; ++c) {
            std::vector<double> ch((size_t)res * res, 127.5);
            for (size_t k = 0; k < ch.size(); ++k)
                if (fid[k] >= 0) ch[k] = (face_normal(P, Fa[fid[k]])[c] + 1.0) * 127.5;
            O.nX[c][v] = std::move(ch);
        }
    }
}

// ===================== EXACT LOCAL-DELTA SCORING (day 4) =====================
// Replaces the day 1-3 proxy (an isolated per-triangle normal-distortion score, removed —
// see docs/V2-CONSTRUCTION.md day 3 for the full account of the 4 bugs it caused) with JD's
// validated technique from the same session (docs/ATTEMPT_LOG.md, 2026-07-06): an insertion's
// screen footprint is LOCAL (bounded by the old triangle's + new point's screen positions), so
// only SSIM windows touching that footprint can change. Compute the EXACT before/after
// rendered SSIM delta there instead of scoring a candidate in isolation — this automatically
// down-scores coplanar no-ops, already-covered "magnet" points, and wrongly-attributed
// targets, since all three provably fail to increase the TRUE rendered SSIM.

struct ViewCache {
    std::vector<int> fid;
    std::vector<double> depth;
    std::vector<double> su, sv, sd;
    double N3 = 0, Nd = 0;   // global valid-window count (same for all 3 normal channels: same coverage rule)
};
static ViewCache VC[6];
static int VC_RES = 0;

// build the current-mesh render cache (once per growth iteration) and the global valid-window
// counts used to convert a local rect delta-sum into a delta of the GLOBAL mean SSIM.
static void build_view_cache(const std::vector<Vec3>& P, const std::vector<std::array<int,3>>& Fa,
                              int RES, const OrigViews& O) {
    VC_RES = RES;
    for (int v = 0; v < 6; ++v) {
        project_view(P, v, RES, VC[v].su, VC[v].sv, VC[v].sd);
        render_proj(P, Fa, RES, VC[v].su, VC[v].sv, VC[v].sd, VC[v].fid, VC[v].depth);
        long n3 = 0;
        for (int y = RAD; y < RES - RAD; ++y) for (int x = RAD; x < RES - RAD; ++x) {
            size_t k = (size_t)y * RES + x;
            if (O.covF[v][k] >= 0 || VC[v].fid[k] >= 0) ++n3;
        }
        VC[v].N3 = (double)n3; VC[v].Nd = (double)n3;
    }
}

// local separable box-sum, tw x th tile — identical algorithm to box_sum(), just scoped to a
// small tile instead of the full RES x RES image (reproduces box_sum's value bit-for-bit at
// any center whose 2*RAD neighborhood is fully covered by the tile).
static void local_box_sum(const std::vector<double>& img, int tw, int th, std::vector<double>& out) {
    static std::vector<double> tmp;
    tmp.assign((size_t)tw * th, 0.0); out.assign((size_t)tw * th, 0.0);
    for (int y = 0; y < th; ++y) {
        double s = 0;
        for (int x = 0; x <= RAD && x < tw; ++x) s += img[(size_t)y * tw + x];
        for (int x = 0; x < tw; ++x) {
            tmp[(size_t)y * tw + x] = s;
            int add = x + RAD + 1, rem = x - RAD;
            if (add < tw) s += img[(size_t)y * tw + add];
            if (rem >= 0) s -= img[(size_t)y * tw + rem];
        }
    }
    for (int x = 0; x < tw; ++x) {
        double s = 0;
        for (int y = 0; y <= RAD && y < th; ++y) s += tmp[(size_t)y * tw + x];
        for (int y = 0; y < th; ++y) {
            out[(size_t)y * tw + x] = s;
            int add = y + RAD + 1, rem = y - RAD;
            if (add < th) s += tmp[(size_t)add * tw + x];
            if (rem >= 0) s -= tmp[(size_t)rem * tw + x];
        }
    }
}

static inline Vec3 tri_normal(const Vec3& p0, const Vec3& p1, const Vec3& p2) {
    Vec3 n = (p1 - p0).cross(p2 - p0);
    double l = n.norm();
    return l > 1e-15 ? Vec3(n / l) : Vec3::Zero();
}

// Exact per-view ΔFinalSSIM contribution of replacing old face `oldF` (vertices va,vb,vc, all
// existing curP indices) with 3 new triangles (va,vb,newIdx),(vb,vc,newIdx),(vc,va,newIdx),
// where the new vertex sits at position `p` (not yet in curP). Mirrors JD's flip evaluator:
// erase the old face's pixels, rasterize the 3 new triangles with a z-test, guarded by the
// SAME 2 safety checks (window-count match, foreign-face intrusion) plus a crack check for
// unfilled erased pixels — bails (returns false) rather than trust an ambiguous read.
static bool eval_insertion_view(int v, int oldF, int va, int vb, int vc, const Vec3& p,
                                 const std::vector<Vec3>& curP, const std::vector<std::array<int,3>>& curF,
                                 const OrigViews& O, double dsum[4], double cnt[4]) {
    const int W = VC_RES;
    const auto& su = VC[v].su; const auto& sv = VC[v].sv; const auto& sd = VC[v].sd;

    double pd; double pu, pv;
    {   // project the single new point p into this view (not cached: p is not in curP yet)
        Vec3 eye, right, up, fwd; view_basis(v, eye, right, up, fwd);
        Vec3 r = p - eye; double x = r.dot(right), y = r.dot(up), d = r.dot(fwd);
        if (d == 0) d = 1e-9;
        const double F = 800.0 * (W / 1024.0), C = W / 2.0;
        pu = F * x / d + C; pv = F * y / d + C; pd = d;
    }
    double qd[4] = {sd[va], sd[vb], sd[vc], pd};
    if (qd[0] <= 0 || qd[1] <= 0 || qd[2] <= 0 || qd[3] <= 0) return false;
    double qu[4] = {su[va], su[vb], su[vc], pu}, qv[4] = {sv[va], sv[vb], sv[vc], pv};
    double umin = std::min({qu[0],qu[1],qu[2],qu[3]}), umax = std::max({qu[0],qu[1],qu[2],qu[3]});
    double vmin = std::min({qv[0],qv[1],qv[2],qv[3]}), vmax = std::max({qv[0],qv[1],qv[2],qv[3]});
    int bx0 = (int)std::floor(umin), bx1 = (int)std::ceil(umax);
    int by0 = (int)std::floor(vmin), by1 = (int)std::ceil(vmax);
    if (bx1 < 0 || bx0 > W-1 || by1 < 0 || by0 > W-1) return false;
    if (bx0 < 0) bx0 = 0; if (bx1 > W-1) bx1 = W-1; if (by0 < 0) by0 = 0; if (by1 > W-1) by1 = W-1;
    int cx0 = std::max(RAD, bx0-RAD), cx1 = std::min(W-RAD-1, bx1+RAD);
    int cy0 = std::max(RAD, by0-RAD), cy1 = std::min(W-RAD-1, by1+RAD);
    if (cx0 > cx1 || cy0 > cy1) return false;
    int tx0 = std::max(0, bx0-2*RAD), tx1 = std::min(W-1, bx1+2*RAD);
    int ty0 = std::max(0, by0-2*RAD), ty1 = std::min(W-1, by1+2*RAD);
    const int tw = tx1-tx0+1, th = ty1-ty0+1;
    if ((long)tw*th > 40000) return false;   // safety cap: pathological candidate, skip

    static std::vector<int> afid; static std::vector<float> azb;
    afid.assign((size_t)tw*th, -1); azb.assign((size_t)tw*th, 1e30f);
    for (int ty = 0; ty < th; ++ty) for (int tx = 0; tx < tw; ++tx) {
        size_t gk = (size_t)(ty0+ty)*W + (tx0+tx);
        int f = VC[v].fid[gk];
        if (f == oldF) { afid[(size_t)ty*tw+tx] = -2; continue; }   // erased, pending redraw
        afid[(size_t)ty*tw+tx] = f; azb[(size_t)ty*tw+tx] = (float)VC[v].depth[gk];
    }
    bool intruded = false;
    auto raster_tri = [&](int i0, int i1, int i2, int tag) {
        double td0 = qd[i0], td1 = qd[i1], td2 = qd[i2];
        double lu0 = qu[i0]-tx0, lv0 = qv[i0]-ty0, lu1 = qu[i1]-tx0, lv1 = qv[i1]-ty0, lu2 = qu[i2]-tx0, lv2 = qv[i2]-ty0;
        double det = (lv1-lv2)*(lu0-lu2)+(lu2-lu1)*(lv0-lv2); if (det>-1e-12&&det<1e-12) return; double inv=1.0/det;
        int mnx=(int)std::floor(std::min({lu0,lu1,lu2})),mxx=(int)std::ceil(std::max({lu0,lu1,lu2}));
        int mny=(int)std::floor(std::min({lv0,lv1,lv2})),mxy=(int)std::ceil(std::max({lv0,lv1,lv2}));
        if (mnx<0)mnx=0; if (mny<0)mny=0; if (mxx>tw-1)mxx=tw-1; if (mxy>th-1)mxy=th-1;
        for (int py=mny;py<=mxy;++py){double cy=py+0.5; for (int px=mnx;px<=mxx;++px){double cx=px+0.5;
            double w0=((lv1-lv2)*(cx-lu2)+(lu2-lu1)*(cy-lv2))*inv,w1=((lv2-lv0)*(cx-lu2)+(lu0-lu2)*(cy-lv2))*inv,w2=1-w0-w1;
            if (w0<-1e-9||w1<-1e-9||w2<-1e-9) continue; double den=w0/td0+w1/td1+w2/td2; if (den<=0) continue; double z=(float)(1.0/den);
            size_t k=(size_t)py*tw+px; if ((float)z<azb[k]){ if (afid[k] >= 0) intruded = true; azb[k]=(float)z; afid[k]=tag; } }}
    };
    // qu/qv/qd index: 0=va, 1=vb, 2=vc, 3=p. New triangles: (va,vb,p)=tag-3, (vb,vc,p)=tag-4, (vc,va,p)=tag-5.
    raster_tri(0, 1, 3, -3);
    raster_tri(1, 2, 3, -4);
    raster_tri(2, 0, 3, -5);
    if (intruded) return false;
    for (size_t k = 0; k < afid.size(); ++k) if (afid[k] == -2) return false;   // unfilled crack

    Vec3 nA = tri_normal(curP[va], curP[vb], p);
    Vec3 nB = tri_normal(curP[vb], curP[vc], p);
    Vec3 nC = tri_normal(curP[vc], curP[va], p);
    // "before" encode: any REAL face id (the cache's own content, untouched by this candidate).
    auto encode_before = [&](int f, double z, int ch) -> double {
        if (ch == 3) return (f >= 0) ? z : 255.0;
        if (f < 0) return 127.5;
        return (face_normal(curP, curF[f])[ch] + 1.0) * 127.5;
    };
    // "after" encode: -1 background, -3/-4/-5 one of the 3 new triangles, otherwise a REAL
    // face id copied unchanged from the cache (an untouched neighbor, not oldF).
    auto encode_after = [&](int f, float z, int ch) -> double {
        if (ch == 3) return (f == -1) ? 255.0 : (double)z;
        if (f == -1) return 127.5;
        if (f == -3) return (nA[ch] + 1.0) * 127.5;
        if (f == -4) return (nB[ch] + 1.0) * 127.5;
        if (f == -5) return (nC[ch] + 1.0) * 127.5;
        return (face_normal(curP, curF[f])[ch] + 1.0) * 127.5;
    };

    bool ok = true;
    for (int ch = 0; ch < 4 && ok; ++ch) {
        static std::vector<double> X, Ybefore, Yafter, mx, mby, may_, xx, yb, ya, xyb, xya, t;
        X.assign((size_t)tw*th, 0.0); Ybefore.assign((size_t)tw*th, 0.0); Yafter.assign((size_t)tw*th, 0.0);
        for (int ty = 0; ty < th; ++ty) for (int tx = 0; tx < tw; ++tx) {
            size_t lk = (size_t)ty*tw+tx, gk = (size_t)(ty0+ty)*W + (tx0+tx);
            X[lk] = (ch == 3) ? O.dX[v][gk] : O.nX[ch][v][gk];
            Ybefore[lk] = encode_before(VC[v].fid[gk], VC[v].depth[gk], ch);
            Yafter[lk] = encode_after(afid[lk], azb[lk], ch);
        }
        local_box_sum(X, tw, th, mx);
        t.assign(X.size(), 0.0);
        for (size_t k = 0; k < X.size(); ++k) t[k] = X[k]*X[k]; local_box_sum(t, tw, th, xx);
        local_box_sum(Ybefore, tw, th, mby);
        for (size_t k = 0; k < X.size(); ++k) t[k] = Ybefore[k]*Ybefore[k]; local_box_sum(t, tw, th, yb);
        for (size_t k = 0; k < X.size(); ++k) t[k] = X[k]*Ybefore[k]; local_box_sum(t, tw, th, xyb);
        local_box_sum(Yafter, tw, th, may_);
        for (size_t k = 0; k < X.size(); ++k) t[k] = Yafter[k]*Yafter[k]; local_box_sum(t, tw, th, ya);
        for (size_t k = 0; k < X.size(); ++k) t[k] = X[k]*Yafter[k]; local_box_sum(t, tw, th, xya);

        double sBefore = 0, sAfter = 0; long nBefore = 0, nAfter = 0;
        for (int gy = cy0; gy <= cy1; ++gy) for (int gx = cx0; gx <= cx1; ++gx) {
            int ty = gy - ty0, tx = gx - tx0; size_t lk = (size_t)ty*tw+tx;
            size_t gk = (size_t)gy*W+gx;
            const double MX = mx[lk]/WN, SX = xx[lk]/WN - MX*MX;
            {
                const double MYb = mby[lk]/WN, SYb = yb[lk]/WN - MYb*MYb, SXYb = xyb[lk]/WN - MX*MYb;
                bool covB = (O.covF[v][gk] >= 0) || (VC[v].fid[gk] >= 0);
                if (covB) {
                    double A=2*MX*MYb+C1, B=2*SXYb+C2, D1=MX*MX+MYb*MYb+C1, D2=SX+SYb+C2;
                    sBefore += (A*B)/(D1*D2); ++nBefore;
                }
            }
            {
                const double MYa = may_[lk]/WN, SYa = ya[lk]/WN - MYa*MYa, SXYa = xya[lk]/WN - MX*MYa;
                bool covA = (O.covF[v][gk] >= 0) || (afid[lk] != -1);
                if (covA) {
                    double A=2*MX*MYa+C1, B=2*SXYa+C2, D1=MX*MX+MYa*MYa+C1, D2=SX+SYa+C2;
                    sAfter += (A*B)/(D1*D2); ++nAfter;
                }
            }
        }
        if (nBefore != nAfter) { ok = false; break; }   // silhouette-adjacent case: bail, don't misscore
        dsum[ch] = sAfter - sBefore; cnt[ch] = (double)nBefore;
    }
    return ok;
}

// Sum the exact ΔFinalSSIM of inserting `p` as the new vertex splitting old face `oldF`
// (a,b,c) across all 6 views. Aggregation identical to JD's (docs/ATTEMPT_LOG.md 2026-07-06):
// normal channels contribute 0.5*(1/18)*(dsum[c]/N3[v]), depth contributes 0.5*(1/6)*(dsum[3]/Nd[v]).
static double exact_insertion_delta(int oldF, int va, int vb, int vc, const Vec3& p,
                                     const std::vector<Vec3>& curP, const std::vector<std::array<int,3>>& curF,
                                     const OrigViews& O) {
    double total = 0.0;
    for (int v = 0; v < 6; ++v) {
        double dsum[4] = {0,0,0,0}, cnt[4] = {0,0,0,0};
        if (!eval_insertion_view(v, oldF, va, vb, vc, p, curP, curF, O, dsum, cnt)) continue;
        for (int ch = 0; ch < 3; ++ch) if (cnt[ch] > 0) total += 0.5 * (dsum[ch] / VC[v].N3) / 18.0;
        if (cnt[3] > 0) total += 0.5 * (dsum[3] / VC[v].Nd) / 6.0;
    }
    return total;
}

// closest point on a SINGLE triangle to a query point (standard Ericson "Real-Time Collision
// Detection" region test) — factored out so both the brute-force scan and the spatial-grid
// query below share one implementation.
static inline Vec3 closest_point_on_triangle(const Vec3& q, const Vec3& a, const Vec3& b, const Vec3& c) {
    Vec3 ab = b - a, ac = c - a, ap = q - a;
    double d1 = ab.dot(ap), d2 = ac.dot(ap);
    if (d1 <= 0 && d2 <= 0) return a;
    Vec3 bp = q - b; double d3 = ab.dot(bp), d4 = ac.dot(bp);
    if (d3 >= 0 && d4 <= d3) return b;
    double vc = d1*d4 - d3*d2;
    if (vc <= 0 && d1 >= 0 && d3 <= 0) { double w = d1/(d1-d3); return a + w*ab; }
    Vec3 cp = q - c; double d5 = ab.dot(cp), d6 = ac.dot(cp);
    if (d6 >= 0 && d5 <= d6) return c;
    double vb = d5*d2 - d1*d6;
    if (vb <= 0 && d2 >= 0 && d6 <= 0) { double w = d2/(d2-d6); return a + w*ac; }
    double va = d3*d6 - d5*d4;
    if (va <= 0 && (d4-d3) >= 0 && (d5-d6) >= 0) { double w = (d4-d3)/((d4-d3)+(d5-d6)); return b + w*(c-b); }
    double denom = 1.0/(va+vb+vc); double vv = vb*denom, ww = vc*denom;
    return a + ab*vv + ac*ww;
}

// nearest point on ANY mesh's surface to a query point, and which face it landed on.
// Brute-force O(faces) — kept for correctness reference and tiny meshes; day 5's SpatialGrid
// (below) is the accelerated path used everywhere performance matters.
static Vec3 closest_point_on_mesh(const Vec3& q, const std::vector<Vec3>& OP,
                                   const std::vector<std::array<int,3>>& OF, int* faceOut) {
    double best = 1e300; Vec3 bestP = q; int bestF = 0;
    for (int fi = 0; fi < (int)OF.size(); ++fi) {
        const auto& t = OF[fi];
        Vec3 p = closest_point_on_triangle(q, OP[t[0]], OP[t[1]], OP[t[2]]);
        double d = (p - q).squaredNorm();
        if (d < best) { best = d; bestP = p; bestF = fi; }
    }
    if (faceOut) *faceOut = bestF;
    return bestP;
}

// ===================== SPATIAL GRID (day 5) =====================
// Uniform 3D grid over triangle bounding boxes, queried by expanding rings of cells around the
// query point's own cell. Provably correct (not approximate): a ring is only accepted as
// "final" once the geometric distance from the query point to the boundary of the searched
// region exceeds the best candidate found so far, so no closer triangle in an unsearched cell
// can exist. Reduces closest_point_on_mesh from O(faces) to roughly O(faces^(1/3)) per query —
// the dominant cost this whole file pays (candidate generation, the Hausdorff sample scan, and
// the min-separation check all call it many times per growth iteration).
struct SpatialGrid {
    const std::vector<Vec3>* P = nullptr;
    const std::vector<std::array<int,3>>* F = nullptr;
    Vec3 lo, hi;
    int G = 1;
    double cellSize = 1.0;
    std::vector<std::vector<int>> cells;

    int cellIdx(double v, double lo0) const {
        int i = (int)std::floor((v - lo0) / cellSize);
        return std::max(0, std::min(G - 1, i));
    }
    size_t cellKey(int x, int y, int z) const { return ((size_t)x * G + (size_t)y) * G + (size_t)z; }

    void build(const std::vector<Vec3>& Pin, const std::vector<std::array<int,3>>& Fin) {
        P = &Pin; F = &Fin;
        lo = Vec3(1e300, 1e300, 1e300); hi = -lo;
        for (const Vec3& p : Pin) { lo = lo.cwiseMin(p); hi = hi.cwiseMax(p); }
        Vec3 ext = hi - lo;
        double maxExt = std::max({ext.x(), ext.y(), ext.z(), 1e-9});
        lo -= Vec3::Constant(maxExt * 0.02); hi += Vec3::Constant(maxExt * 0.02);
        maxExt *= 1.04;
        const int nf = (int)Fin.size();
        G = std::max(1, (int)std::round(std::cbrt(std::max(1, nf) / 2.0)));
        cellSize = maxExt / G;
        cells.assign((size_t)G * G * G, {});
        for (int fi = 0; fi < nf; ++fi) {
            const auto& t = Fin[fi];
            Vec3 tlo = Pin[t[0]].cwiseMin(Pin[t[1]]).cwiseMin(Pin[t[2]]);
            Vec3 thi = Pin[t[0]].cwiseMax(Pin[t[1]]).cwiseMax(Pin[t[2]]);
            int gx0 = cellIdx(tlo.x(), lo.x()), gx1 = cellIdx(thi.x(), lo.x());
            int gy0 = cellIdx(tlo.y(), lo.y()), gy1 = cellIdx(thi.y(), lo.y());
            int gz0 = cellIdx(tlo.z(), lo.z()), gz1 = cellIdx(thi.z(), lo.z());
            for (int gx = gx0; gx <= gx1; ++gx) for (int gy = gy0; gy <= gy1; ++gy) for (int gz = gz0; gz <= gz1; ++gz)
                cells[cellKey(gx, gy, gz)].push_back(fi);
        }
    }

    Vec3 query(const Vec3& q, int* faceOut) const {
        int qx = cellIdx(q.x(), lo.x()), qy = cellIdx(q.y(), lo.y()), qz = cellIdx(q.z(), lo.z());
        double best = 1e300; Vec3 bestP = q; int bestF = -1;
        for (int ring = 0; ; ++ring) {
            bool anyCellInRange = false;
            for (int dx = -ring; dx <= ring; ++dx) for (int dy = -ring; dy <= ring; ++dy) for (int dz = -ring; dz <= ring; ++dz) {
                if (std::max({std::abs(dx), std::abs(dy), std::abs(dz)}) != ring) continue;
                int gx = qx+dx, gy = qy+dy, gz = qz+dz;
                if (gx < 0 || gx >= G || gy < 0 || gy >= G || gz < 0 || gz >= G) continue;
                anyCellInRange = true;
                for (int fi : cells[cellKey(gx, gy, gz)]) {
                    const auto& t = (*F)[fi];
                    Vec3 p = closest_point_on_triangle(q, (*P)[t[0]], (*P)[t[1]], (*P)[t[2]]);
                    double d = (p - q).squaredNorm();
                    if (d < best) { best = d; bestP = p; bestF = fi; }
                }
            }
            // safe stopping bound: once every axis's distance from q to the searched box's
            // boundary exceeds sqrt(best), no unsearched cell can contain a closer point.
            double bx0 = lo.x() + (qx-ring)*cellSize, bx1 = lo.x() + (qx+ring+1)*cellSize;
            double by0 = lo.y() + (qy-ring)*cellSize, by1 = lo.y() + (qy+ring+1)*cellSize;
            double bz0 = lo.z() + (qz-ring)*cellSize, bz1 = lo.z() + (qz+ring+1)*cellSize;
            double escape = std::min({q.x()-bx0, bx1-q.x(), q.y()-by0, by1-q.y(), q.z()-bz0, bz1-q.z()});
            bool exhausted = (qx-ring < 0 && qx+ring >= G && qy-ring < 0 && qy+ring >= G && qz-ring < 0 && qz+ring >= G);
            if (bestF >= 0 && (escape*escape >= best || exhausted)) break;
            if (!anyCellInRange && exhausted) break;   // nothing left to search at all
        }
        if (faceOut) *faceOut = bestF;
        return bestP;
    }
};

static SpatialGrid g_origGrid;   // built once from the fixed original mesh
static SpatialGrid g_curGrid;    // rebuilt once per growth iteration from the current mesh
static std::vector<Vec3> g_featurePoints;   // day 6: region-boundary/corner points, set once in main()

// Generate a small candidate set of split positions for face (a,b,c): the closest point on the
// original surface from the centroid (position baseline), the actual nearest ORIGINAL VERTEX
// (real, unmodified surface data), and small tangent-plane offsets of the baseline RE-PROJECTED
// onto the original surface (so every candidate stays on-surface by construction — an earlier
// off-surface version broke Hausdorff, 0.249 vs the 0.119 limit). Filters out candidates that
// would be degenerate (near-zero sub-triangle area) or land within `minSep` of an existing
// current-mesh vertex (day-3 bug: a single distinctive original vertex/crease acted as a
// magnet, with many different parent faces all converging on the SAME 3D point).
//
// Day 1-3 used an ISOLATED per-triangle "induced normal distortion" score to pick among these
// candidates — proven unreliable (docs/V2-CONSTRUCTION.md day 3: 4 distinct bugs, all
// variations of "the proxy doesn't correlate with whether this candidate helps the actual
// rendered image"). Day 4 replaces that scoring with the exact local-delta technique
// (exact_insertion_delta) applied by the CALLER to whichever candidates this generates.
static long g_areaRejects = 0, g_sepRejects = 0;   // day 5 diagnostic: which filter is actually exhausting candidates
static void generate_split_candidates(const Vec3& a, const Vec3& b, const Vec3& c,
                                       const std::vector<Vec3>& OP, const std::vector<std::array<int,3>>& OF,
                                       const SpatialGrid& origGrid,
                                       const std::vector<Vec3>& curP, double edgeScale, double minArea,
                                       double minSep, const std::vector<Vec3>& featurePts,
                                       std::vector<Vec3>& out) {
    out.clear();
    Vec3 centroid = (a + b + c) / 3.0;
    int fi; Vec3 p0 = origGrid.query(centroid, &fi);
    Vec3 trueN = face_normal(OP, OF[fi]);

    std::vector<Vec3> cand = {p0};
    {
        const auto& t = OF[fi];
        double bd = 1e300; Vec3 bv = p0;
        for (int k = 0; k < 3; ++k) { double d = (OP[t[k]] - centroid).squaredNorm(); if (d < bd) { bd = d; bv = OP[t[k]]; } }
        cand.push_back(bv);
    }
    Vec3 ref = std::fabs(trueN.x()) < 0.9 ? Vec3(1,0,0) : Vec3(0,1,0);
    Vec3 t1 = trueN.cross(ref).normalized(), t2 = trueN.cross(t1).normalized();
    for (double s : {0.3, -0.3}) {
        cand.push_back(origGrid.query(p0 + s * edgeScale * t1, nullptr));
        cand.push_back(origGrid.query(p0 + s * edgeScale * t2, nullptr));
    }
    // day 6: also offer the nearest region-segmentation feature point (boundary/corner where
    // the ORIGINAL surface's normal genuinely changes) as a candidate -- NOT inserted blindly
    // (that measured WORSE than pure SSIM-driven growth, see docs day 6), just added to the
    // pool the exact-delta scorer already picks from. It only wins if it demonstrably beats
    // every other option on the real rendered metric, same bar as everything else here.
    if (!featurePts.empty()) {
        double bd = 1e300; Vec3 bv = p0;
        for (const Vec3& fp : featurePts) { double d = (fp - centroid).squaredNorm(); if (d < bd) { bd = d; bv = fp; } }
        cand.push_back(bv);
    }
    auto filterInto = [&](const std::vector<Vec3>& in) {
        for (const Vec3& p : in) {
            double a1 = 0.5*(a-p).cross(b-p).norm(), a2 = 0.5*(b-p).cross(c-p).norm(), a3 = 0.5*(c-p).cross(a-p).norm();
            if (a1 <= minArea || a2 <= minArea || a3 <= minArea) { ++g_areaRejects; continue; }
            bool tooClose = false;
            for (const Vec3& ev : curP) if ((ev - p).squaredNorm() < minSep * minSep) { tooClose = true; break; }
            if (tooClose) { ++g_sepRejects; continue; }
            out.push_back(p);
        }
    };
    filterInto(cand);
    // day 5: the fixed 6-point set above was a PERMANENT dead end once every candidate
    // collided with the minSep guard against existing vertices (more vertices globally only
    // ever shrink the valid set, never grow it back) -- measured: this stalled growth at
    // V=1167 of a 1742 target well within budget, i.e. candidate exhaustion, not time, was
    // the limiter. But eagerly evaluating a wide fan for EVERY face made the common
    // (still-has-room) case ~4x more expensive for no benefit. So: only pay for a wider
    // search when the cheap set above came back completely empty.
    if (out.empty()) {
        std::vector<Vec3> wide;
        for (double r : {0.15, 0.05, 0.02}) {
            for (int k = 0; k < 8; ++k) {
                double ang = k * (2.0 * M_PI / 8.0);
                Vec3 dir = std::cos(ang) * t1 + std::sin(ang) * t2;
                wide.push_back(origGrid.query(p0 + r * edgeScale * dir, nullptr));
            }
        }
        filterInto(wide);
    }
}

// farthest-point sampling: greedily pick K points that are well spread over the input surface.
// A convex hull can never have more vertices than its input set, so hulling a K-point sample
// GUARANTEES a seed of at most K vertices — unlike hulling the full point set (measured on
// the bunny proxy: 3485 points -> a genuinely valid 647-vertex hull, already bigger than a
// 5%-budget target). This is a well-known sampling technique, independent of any decimator.
// day 6: face-to-face adjacency of the ORIGINAL mesh via shared edges (up to 3 neighbors per
// face). Needed for normal-based region growing below -- an independent mechanism from
// main.cpp's decimation, built for a construction context: main.cpp collapses edges ORDERED by
// induced normal distortion; this instead SEGMENTS the original surface into normal-coherent
// regions up front and treats the boundaries between regions as insertion targets. Same
// underlying insight (flat regions matter more than raw vertex density), independently applied.
static std::vector<std::array<int,3>> build_face_adjacency(const std::vector<std::array<int,3>>& F) {
    std::map<std::pair<int,int>, std::vector<int>> edgeFaces;
    auto keyOf = [](int a, int b) { return a < b ? std::make_pair(a, b) : std::make_pair(b, a); };
    for (int f = 0; f < (int)F.size(); ++f) {
        const auto& t = F[f];
        int e[3][2] = {{t[0],t[1]}, {t[1],t[2]}, {t[2],t[0]}};
        for (auto& ee : e) edgeFaces[keyOf(ee[0], ee[1])].push_back(f);
    }
    std::vector<std::array<int,3>> adj(F.size(), {-1,-1,-1});
    for (int f = 0; f < (int)F.size(); ++f) {
        const auto& t = F[f];
        int e[3][2] = {{t[0],t[1]}, {t[1],t[2]}, {t[2],t[0]}};
        for (int k = 0; k < 3; ++k) {
            auto& lst = edgeFaces[keyOf(e[k][0], e[k][1])];
            for (int g : lst) if (g != f) { adj[f][k] = g; break; }
        }
    }
    return adj;
}

// Best-first (Dijkstra-like) multi-source region growing: seed K faces spread over the mesh
// (farthest-point sampling in centroid space, same generic technique as the hull seed), then
// flood outward, always claiming the cheapest (best normal-aligned) unclaimed neighbor next,
// updating each region's running area-weighted normal as it grows. This is a standard seeded
// segmentation strategy (independent of, and much simpler than, a full Lloyd-relaxed VSA), good
// enough to expose region BOUNDARIES, which is all this needs it for.
struct Segmentation { std::vector<int> regionOf; std::vector<Vec3> regionNormal; };
static Segmentation segment_by_normal(const std::vector<Vec3>& P, const std::vector<std::array<int,3>>& F,
                                       const std::vector<std::array<int,3>>& adj, int K) {
    const int nf = (int)F.size();
    std::vector<Vec3> fn(nf), fc(nf);
    std::vector<double> fa(nf);
    for (int f = 0; f < nf; ++f) {
        fn[f] = face_normal(P, F[f]);
        const auto& t = F[f];
        fc[f] = (P[t[0]] + P[t[1]] + P[t[2]]) / 3.0;
        fa[f] = 0.5 * (P[t[1]]-P[t[0]]).cross(P[t[2]]-P[t[0]]).norm();
    }
    K = std::max(1, std::min(K, nf));
    std::vector<int> seeds; seeds.reserve(K);
    {
        std::vector<double> mind(nf, 1e300);
        int cur = 0;
        for (int i = 1; i < nf; ++i) if (fc[i].x() < fc[cur].x()) cur = i;
        seeds.push_back(cur);
        for (int it = 1; it < K; ++it) {
            for (int i = 0; i < nf; ++i) mind[i] = std::min(mind[i], (fc[i]-fc[cur]).squaredNorm());
            double best = -1; int bi = 0;
            for (int i = 0; i < nf; ++i) if (mind[i] > best) { best = mind[i]; bi = i; }
            cur = bi; seeds.push_back(cur);
        }
    }
    Segmentation seg; seg.regionOf.assign(nf, -1);
    std::vector<Vec3> regionNormal(seeds.size());
    std::vector<double> regionArea(seeds.size(), 0.0);
    for (size_t r = 0; r < seeds.size(); ++r) {
        seg.regionOf[seeds[r]] = (int)r;
        regionNormal[r] = fn[seeds[r]];
        regionArea[r] = fa[seeds[r]];
    }
    struct QE { double cost; int face; int region; };
    struct Cmp { bool operator()(const QE& a, const QE& b) const { return a.cost > b.cost; } };
    std::priority_queue<QE, std::vector<QE>, Cmp> pq;
    for (size_t r = 0; r < seeds.size(); ++r)
        for (int nb : adj[seeds[r]]) if (nb >= 0 && seg.regionOf[nb] < 0)
            pq.push({1.0 - fn[nb].dot(regionNormal[r]), nb, (int)r});
    while (!pq.empty()) {
        QE e = pq.top(); pq.pop();
        if (seg.regionOf[e.face] >= 0) continue;   // already claimed by a cheaper path
        seg.regionOf[e.face] = e.region;
        regionNormal[e.region] = (regionNormal[e.region]*regionArea[e.region] + fn[e.face]*fa[e.face]).normalized();
        regionArea[e.region] += fa[e.face];
        for (int nb : adj[e.face]) if (nb >= 0 && seg.regionOf[nb] < 0)
            pq.push({1.0 - fn[nb].dot(regionNormal[e.region]), nb, e.region});
    }
    // faces unreached by adjacency (shouldn't happen on a closed manifold, but guard anyway)
    // get their own singleton region rather than being left unassigned.
    for (int f = 0; f < nf; ++f) if (seg.regionOf[f] < 0) {
        seg.regionOf[f] = (int)seeds.size(); seeds.push_back(f);
        regionNormal.push_back(fn[f]); regionArea.push_back(fa[f]);
    }
    seg.regionNormal = regionNormal;
    return seg;
}

// Where the segmentation actually pays off: a vertex touched by 2 distinct regions sits on a
// region BOUNDARY (a fold/seam in the true surface); a vertex touched by 3+ is a CORNER where
// multiple seams meet -- both are exactly the points a good triangulation needs to place
// vertices at to avoid a single triangle straddling a real normal discontinuity. Every point
// carries a PRIORITY score (corners: how many regions meet there, i.e. valence; edge points:
// the dihedral angle between the two regions it separates) -- inserting all of them unranked
// wastes budget on marginal points ahead of ones that actually matter (measured: unranked
// insertion scored WORSE than the pure SSIM-driven baseline it was meant to beat).
struct FeaturePoint { Vec3 p; double priority; int vIdx; };
struct FeatureSet { std::vector<FeaturePoint> corners; std::vector<FeaturePoint> edgePts; };
static FeatureSet extract_features(const std::vector<Vec3>& P, const std::vector<std::array<int,3>>& F,
                                    const std::vector<int>& regionOf, const std::vector<Vec3>& regionNormal) {
    const int nv = (int)P.size();
    std::vector<std::set<int>> vertRegions(nv);
    for (int f = 0; f < (int)F.size(); ++f) {
        const auto& t = F[f];
        for (int k = 0; k < 3; ++k) vertRegions[t[k]].insert(regionOf[f]);
    }
    FeatureSet fs;
    for (int v = 0; v < nv; ++v) {
        if (vertRegions[v].size() >= 3) {
            fs.corners.push_back({P[v], (double)vertRegions[v].size(), v});
        } else if (vertRegions[v].size() == 2) {
            auto it = vertRegions[v].begin();
            int r0 = *it; ++it; int r1 = *it;
            double dihedral = 1.0 - regionNormal[r0].dot(regionNormal[r1]);   // 0=coplanar, 2=fold back
            fs.edgePts.push_back({P[v], dihedral, v});
        }
    }
    std::sort(fs.corners.begin(), fs.corners.end(), [](const FeaturePoint& a, const FeaturePoint& b) { return a.priority > b.priority; });
    std::sort(fs.edgePts.begin(), fs.edgePts.end(), [](const FeaturePoint& a, const FeaturePoint& b) { return a.priority > b.priority; });
    return fs;
}

// day 7: vertex-clustering construction (Rossignac & Borrel 1993 style) -- a genuinely
// different, ONE-SHOT algorithm from both the hull-and-grow approach (days 1-6, iteratively
// ADDS vertices) and from main.cpp's iterative edge-collapse decimation (iteratively REMOVES
// them). Choose a KEPT vertex set anchored on the region-segmentation feature points (so
// region boundaries are preserved exactly from the start, not discovered by slow greedy
// per-pixel search), map every other original vertex to its nearest kept vertex, and quotient
// the ORIGINAL triangulation onto that map in a single pass: a triangle whose 3 corners map to
// 3 DISTINCT kept vertices survives (relabeled); one that collapses to <3 distinct vertices is
// dropped. This inherits the original mesh's manifoldness almost automatically (it is a
// topological quotient of a known-good mesh, not built from nothing) -- validated below, never
// assumed: a clustering quotient CAN still pinch two well-separated parts of the surface
// together into a non-manifold edge, so every result is checked before being trusted as a seed.
struct ClusteredMesh { std::vector<Vec3> P; std::vector<std::array<int,3>> F; bool manifoldOk; };
static ClusteredMesh build_clustered_mesh(const std::vector<Vec3>& origP, const std::vector<std::array<int,3>>& origF,
                                           const Segmentation& seg, const FeatureSet& feat, int budget) {
    const int nv = (int)origP.size();
    std::vector<int> kept;
    std::vector<char> isKept(nv, 0);
    auto tryKeep = [&](int v) { if (!isKept[v]) { isKept[v] = 1; kept.push_back(v); } };

    // Follow-up item 1: boundary feature points (corners+edges) used to be allowed to consume
    // the ENTIRE budget before interior representatives ever got a look-in. Measured: in every
    // test so far, edge points alone (hundreds to thousands) vastly outnumbered any realistic
    // budget, so interior allocation almost NEVER triggered -- a region's interior got
    // triangulated purely from whatever its boundary vertices happen to form among themselves,
    // correct for a genuinely FLAT region but chord-cutting any real curvature inside a curved
    // one. Cap boundary points to a fraction of budget (corners are rare and important, always
    // included in full), reserving the rest for interior coverage.
    const double BOUNDARY_FRAC = 0.7;
    int boundaryBudget = std::min(budget, std::max((int)feat.corners.size(), (int)(BOUNDARY_FRAC * budget)));
    for (const auto& fp : feat.corners) { if ((int)kept.size() >= boundaryBudget) break; tryKeep(fp.vIdx); }
    for (const auto& fp : feat.edgePts) { if ((int)kept.size() >= boundaryBudget) break; tryKeep(fp.vIdx); }

    if ((int)kept.size() < budget) {
        int nr = (int)seg.regionNormal.size();
        std::vector<double> area(nr, 0.0);
        for (int f = 0; f < (int)origF.size(); ++f) {
            const auto& t = origF[f];
            double a = 0.5*(origP[t[1]]-origP[t[0]]).cross(origP[t[2]]-origP[t[0]]).norm();
            area[seg.regionOf[f]] += a;
        }
        // Follow-up item 1 continued: give each region a number of interior points
        // PROPORTIONAL to its area (greedy largest-remaining-share allocation, same idea as
        // D'Hondt apportionment), not a flat "1 each" -- a tiny region and a huge one used to
        // get identical interior representation.
        int interiorBudget = budget - (int)kept.size();
        std::vector<int> pointCount(nr, 0);
        for (int i = 0; i < interiorBudget; ++i) {
            int best = -1; double bestRatio = -1;
            for (int r = 0; r < nr; ++r) {
                if (area[r] <= 0) continue;
                double ratio = area[r] / (1.0 + pointCount[r]);
                if (ratio > bestRatio) { bestRatio = ratio; best = r; }
            }
            if (best < 0) break;
            ++pointCount[best];
        }
        // per-vertex majority-region tag (which region most of a vertex's incident faces
        // belong to), used only to pool candidates for farthest-point-sampling WITHIN a region
        // -- doesn't need to be exact, just a reasonable "this vertex is roughly in region r".
        std::vector<int> vertRegion(nv, -1);
        {
            std::vector<std::vector<int>> votes(nv);
            for (int f = 0; f < (int)origF.size(); ++f) {
                const auto& t = origF[f];
                for (int k = 0; k < 3; ++k) votes[t[k]].push_back(seg.regionOf[f]);
            }
            for (int v = 0; v < nv; ++v) {
                if (votes[v].empty()) continue;
                std::sort(votes[v].begin(), votes[v].end());
                int bestR = votes[v][0], bestCount = 1, curR = votes[v][0], curCount = 1;
                for (size_t i = 1; i < votes[v].size(); ++i) {
                    if (votes[v][i] == curR) ++curCount; else { curR = votes[v][i]; curCount = 1; }
                    if (curCount > bestCount) { bestCount = curCount; bestR = curR; }
                }
                vertRegion[v] = bestR;
            }
        }
        std::vector<std::vector<int>> regionVerts(nr);
        for (int v = 0; v < nv; ++v) if (vertRegion[v] >= 0) regionVerts[vertRegion[v]].push_back(v);

        for (int r = 0; r < nr; ++r) {
            if (pointCount[r] <= 0 || regionVerts[r].empty()) continue;
            // index-based farthest-point sample among this region's OWN vertices, spreading
            // the region's interior points out instead of clustering them all near one centroid.
            auto& cand = regionVerts[r];
            std::vector<double> mind(cand.size(), 1e300);
            int cur = 0;
            std::vector<int> chosen = {cand[cur]};
            for (int it = 1; it < pointCount[r] && it < (int)cand.size(); ++it) {
                for (size_t i = 0; i < cand.size(); ++i)
                    mind[i] = std::min(mind[i], (origP[cand[i]]-origP[cand[cur]]).squaredNorm());
                double best = -1; int bi = 0;
                for (size_t i = 0; i < cand.size(); ++i) if (mind[i] > best) { best = mind[i]; bi = (int)i; }
                cur = bi; chosen.push_back(cand[cur]);
            }
            for (int v : chosen) { if ((int)kept.size() >= budget) break; tryKeep(v); }
        }
    }

    // Map every original vertex to its nearest KEPT vertex via GRAPH (surface) distance, not
    // raw Euclidean distance. Euclidean nearest-point can jump across a thin gap or fold to a
    // point that's close in 3D but far along the surface, silently merging two unrelated
    // sheets into one cluster -- measured: this produced 125 of 1109 edges shared by >2 faces
    // (pervasive non-manifold pinching, not a rare edge case) plus 58 orphaned boundary edges.
    // Multi-source Dijkstra over the mesh's own edge graph, weighted by edge length, respects
    // connectivity instead of jumping through empty space.
    std::vector<std::vector<int>> vAdj(nv);
    {
        std::set<std::pair<int,int>> seenEdge;
        for (const auto& t : origF) {
            int e[3][2] = {{t[0],t[1]}, {t[1],t[2]}, {t[2],t[0]}};
            for (auto& ee : e) {
                auto key = ee[0] < ee[1] ? std::make_pair(ee[0], ee[1]) : std::make_pair(ee[1], ee[0]);
                if (seenEdge.insert(key).second) { vAdj[ee[0]].push_back(ee[1]); vAdj[ee[1]].push_back(ee[0]); }
            }
        }
    }
    std::vector<int> nearestKept(nv, -1);
    std::vector<double> distTo(nv, 1e300);
    struct DE { double d; int v; };
    struct DCmp { bool operator()(const DE& a, const DE& b) const { return a.d > b.d; } };
    std::priority_queue<DE, std::vector<DE>, DCmp> dpq;
    for (int k : kept) { distTo[k] = 0.0; nearestKept[k] = k; dpq.push({0.0, k}); }
    while (!dpq.empty()) {
        DE e = dpq.top(); dpq.pop();
        if (e.d > distTo[e.v]) continue;
        for (int u : vAdj[e.v]) {
            double nd = e.d + (origP[u]-origP[e.v]).norm();
            if (nd < distTo[u]) { distTo[u] = nd; nearestKept[u] = nearestKept[e.v]; dpq.push({nd, u}); }
        }
    }
    // any vertex unreached (disconnected component -- shouldn't happen on a closed manifold,
    // but guard) falls back to Euclidean-nearest kept vertex rather than leaving it unmapped.
    for (int v = 0; v < nv; ++v) if (nearestKept[v] < 0) {
        double bd = 1e300; int bk = kept[0];
        for (int k : kept) { double d = (origP[v]-origP[k]).squaredNorm(); if (d < bd) { bd = d; bk = k; } }
        nearestKept[v] = bk;
    }

    std::vector<int> compact(nv, -1);
    ClusteredMesh out;
    for (int k : kept) { compact[k] = (int)out.P.size(); out.P.push_back(origP[k]); }
    auto keyOf = [](int a, int b) { return a < b ? std::make_pair(a, b) : std::make_pair(b, a); };

    // Accept quotient faces GREEDILY, capping every edge at 2 uses by construction (not just
    // detecting the violation afterward) -- an edge shared by >2 faces is never actually valid
    // geometry, so there is nothing to "repair" about a 3rd occurrence; it must be dropped.
    std::set<std::array<int,3>> seen;
    std::map<std::pair<int,int>, int> edgeCount;
    for (const auto& t : origF) {
        int a = compact[nearestKept[t[0]]], b = compact[nearestKept[t[1]]], c = compact[nearestKept[t[2]]];
        if (a == b || b == c || c == a) continue;
        std::array<int,3> key = {a, b, c};
        std::array<int,3> sortedKey = key; std::sort(sortedKey.begin(), sortedKey.end());
        if (!seen.insert(sortedKey).second) continue;   // dedup: many original faces in a flat
                                                          // region can quotient onto the same 3 points
        int e[3][2] = {{a,b}, {b,c}, {c,a}};
        bool ok = true;
        for (auto& ee : e) if (edgeCount[keyOf(ee[0], ee[1])] >= 2) { ok = false; break; }
        if (!ok) continue;
        for (auto& ee : e) ++edgeCount[keyOf(ee[0], ee[1])];
        out.F.push_back(key);
    }

    // Repair pass: dropping faces above (either the degenerate/dedup skips or the edge-cap
    // above) can leave boundary edges (shared by only 1 face) -- an actual hole, which the
    // growth loop below can only ever SUBDIVIDE, never span. Close small boundary loops via
    // simple fan triangulation rather than discarding an otherwise-good seed over a few holes.
    // Iterative: a fan triangle can itself be rejected by the edge cap (its edge is already
    // shared by unrelated accepted geometry), leaving a smaller residual loop behind -- re-scan
    // and retry until no more progress is made, rather than accepting whatever the first pass
    // alone could close.
    for (int pass = 0; pass < 8; ++pass) {
        std::map<int, std::vector<int>> boundaryNext;
        for (const auto& kv : edgeCount) if (kv.second == 1) {
            boundaryNext[kv.first.first].push_back(kv.first.second);
            boundaryNext[kv.first.second].push_back(kv.first.first);
        }
        if (boundaryNext.empty()) break;
        size_t addedThisPass = 0;
        std::set<int> visited;
        for (auto& kv : boundaryNext) {
            int start = kv.first;
            if (visited.count(start)) continue;
            std::vector<int> loop;
            int prev = -1, cur = start;
            bool ok = true;
            while (true) {
                loop.push_back(cur); visited.insert(cur);
                int next = -1;
                for (int n : boundaryNext[cur]) if (n != prev) { next = n; break; }
                if (next < 0) { ok = false; break; }
                prev = cur; cur = next;
                if (cur == start) break;
                if ((int)loop.size() > (int)out.P.size()) { ok = false; break; }   // malformed graph guard
            }
            if (!ok || loop.size() < 3) continue;
            // Proper ear-clipping, not a fixed fan apex: a fixed apex (e.g. always loop[0]) can
            // fail identically on every retry if ITS edges happen to already be at capacity,
            // even when plenty of OTHER valid ears exist elsewhere in the same loop. Among all
            // valid ears in the current ring, take the BEST one by shape quality (largest
            // minimum angle -- the standard ear-clipping heuristic to avoid slivers), not just
            // the first one found; these hole patches are a tiny fraction of the mesh, so this
            // is a small, low-risk win rather than the main lever (see items 1-2 above).
            std::vector<int> ring = loop;
            while (ring.size() >= 3) {
                int bestI = -1; double bestQuality = -1e300;
                for (size_t i = 0; i < ring.size(); ++i) {
                    int a = ring[(i + ring.size() - 1) % ring.size()];
                    int b = ring[i];
                    int c = ring[(i + 1) % ring.size()];
                    if (a == c) continue;
                    int e[3][2] = {{a,b}, {b,c}, {c,a}};
                    bool okTri = true;
                    for (auto& ee : e) if (edgeCount[keyOf(ee[0], ee[1])] >= 2) { okTri = false; break; }
                    if (!okTri) continue;
                    Vec3 pa = out.P[a], pb = out.P[b], pc = out.P[c];
                    Vec3 uab = (pb-pa).normalized(), ubc = (pc-pb).normalized(), uca = (pa-pc).normalized();
                    double angA = std::acos(std::clamp(-uca.dot(uab), -1.0, 1.0));
                    double angB = std::acos(std::clamp(-uab.dot(ubc), -1.0, 1.0));
                    double angC = std::acos(std::clamp(-ubc.dot(uca), -1.0, 1.0));
                    double quality = std::min({angA, angB, angC});
                    if (quality > bestQuality) { bestQuality = quality; bestI = (int)i; }
                }
                if (bestI < 0) break;   // no ear in the current ring works -- leave the rest
                size_t i = (size_t)bestI;
                int a = ring[(i + ring.size() - 1) % ring.size()];
                int b = ring[i];
                int c = ring[(i + 1) % ring.size()];
                int e[3][2] = {{a,b}, {b,c}, {c,a}};
                for (auto& ee : e) ++edgeCount[keyOf(ee[0], ee[1])];
                out.F.push_back({a, b, c});
                ring.erase(ring.begin() + (long)i);
                ++addedThisPass;
            }
        }
        if (addedThisPass == 0) break;   // no progress -- further passes would just repeat this
    }

    // Repair pass: an edge-manifold mesh (every edge shared by <=2 faces, guaranteed above) can
    // still have a NON-MANIFOLD VERTEX -- two otherwise-disconnected fans of triangles touching
    // only at one shared point (a "pinch"), a classic vertex-clustering artifact a pure edge
    // count can't catch. Detect via per-vertex fan connectivity (two faces sharing an edge
    // THROUGH this vertex are in the same fan) and split any pinch vertex into one duplicate per
    // disconnected fan -- the standard, minimal fix (never assume clustering avoided this).
    // Iterated together with the isolated-vertex strip below: at larger scale (more kept
    // vertices, denser edge-point sets) a single pass of each left V-E+F=4 instead of 2 --
    // splitting a pinch can, in principle, leave a vertex 0-face on one side, and stripping can
    // shift which vertex a later pass would have found; loop both until nothing changes rather
    // than assuming one pass of each suffices.
    for (int repairPass = 0; repairPass < 6; ++repairPass) {
        int pinchesFound = 0;
        {
            int nvOut = (int)out.P.size();
            std::vector<std::vector<int>> incident(nvOut);
            for (int f = 0; f < (int)out.F.size(); ++f) for (int k = 0; k < 3; ++k) incident[out.F[f][k]].push_back(f);
            for (int v = 0; v < nvOut; ++v) {
                auto& facesV = incident[v];
                if (facesV.size() <= 1) continue;
                std::vector<std::vector<int>> adjF(facesV.size());
                for (size_t i = 0; i < facesV.size(); ++i) {
                    const auto& fi = out.F[facesV[i]];
                    std::vector<int> oi; for (int k = 0; k < 3; ++k) if (fi[k] != v) oi.push_back(fi[k]);
                    for (size_t j = i + 1; j < facesV.size(); ++j) {
                        const auto& fj = out.F[facesV[j]];
                        std::vector<int> oj; for (int k = 0; k < 3; ++k) if (fj[k] != v) oj.push_back(fj[k]);
                        bool shareEdge = false;
                        for (int a : oi) for (int b : oj) if (a == b) shareEdge = true;
                        if (shareEdge) { adjF[i].push_back((int)j); adjF[j].push_back((int)i); }
                    }
                }
                std::vector<int> comp(facesV.size(), -1); int nc = 0;
                for (size_t i = 0; i < facesV.size(); ++i) {
                    if (comp[i] >= 0) continue;
                    std::vector<size_t> stack = {i}; comp[i] = nc;
                    while (!stack.empty()) {
                        size_t u = stack.back(); stack.pop_back();
                        for (int w : adjF[u]) if (comp[w] < 0) { comp[w] = nc; stack.push_back((size_t)w); }
                    }
                    ++nc;
                }
                if (nc <= 1) continue;   // manifold vertex, nothing to do
                ++pinchesFound;
                std::vector<int> newIdxForComp(nc, v);
                for (int c = 1; c < nc; ++c) { newIdxForComp[c] = (int)out.P.size(); out.P.push_back(out.P[v]); }
                for (size_t i = 0; i < facesV.size(); ++i) {
                    int c = comp[i]; if (c == 0) continue;
                    auto& f = out.F[facesV[i]];
                    for (int k = 0; k < 3; ++k) if (f[k] == v) f[k] = newIdxForComp[c];
                }
            }
            if (getenv("V2_DBG") && pinchesFound) std::fprintf(stderr, "[v2cluster] pass %d: pinch vertices split: %d\n", repairPass, pinchesFound);
        }

        // Repair pass: a KEPT vertex whose entire cluster's faces all got dropped (degenerate
        // quotient or edge-cap rejection), OR a pinch-split's freshly duplicated vertex that
        // happened to get zero faces on its side, survives with ZERO incident faces -- inflating
        // vertex count without touching edge/face count, silently breaking the genus-0 Euler
        // invariant. Strip any 0-face vertex and recompact indices.
        int stripped;
        {
            std::vector<char> used(out.P.size(), 0);
            for (const auto& t : out.F) for (int k = 0; k < 3; ++k) used[t[k]] = 1;
            std::vector<int> remap(out.P.size(), -1);
            std::vector<Vec3> newP;
            for (size_t v = 0; v < out.P.size(); ++v) if (used[v]) { remap[v] = (int)newP.size(); newP.push_back(out.P[v]); }
            stripped = (int)out.P.size() - (int)newP.size();
            out.P = newP;
            for (auto& t : out.F) for (int k = 0; k < 3; ++k) t[k] = remap[t[k]];
            if (getenv("V2_DBG") && stripped) std::fprintf(stderr, "[v2cluster] pass %d: stripped %d isolated (0-face) vertices\n", repairPass, stripped);
        }
        if (pinchesFound == 0 && stripped == 0) break;   // stable, no more progress possible
    }

    // Repair pass: none of the above (edge cap, ear-clipping, pinch-split, isolated-strip) can
    // catch a mesh that got cut into multiple fully DISCONNECTED closed pieces -- a different
    // signature (chi=4 = 2+2, two separate spheres, not chi=3's single-shared-point pinch).
    // Measured at larger scale (K=20, ~2000-vertex budget on armadillo): 2 connected components,
    // where the smaller size scale test never triggered it. A chain of dropped/rejected faces
    // can, in principle, fully sever part of the surface once enough of them cluster together.
    // Pragmatic fix: keep only the LARGEST component (by face count) and re-close whatever
    // boundary holes that creates, then re-run the pinch/isolated repair once more -- discarding
    // is safe only if the leash still holds afterward, checked by the caller's manifoldOk gate
    // plus main()'s own Hausdorff sanity check either way.
    for (int compPass = 0; compPass < 3; ++compPass) {
        std::map<std::pair<int,int>, std::vector<int>> ef2;
        for (int f = 0; f < (int)out.F.size(); ++f) {
            const auto& t = out.F[f];
            int e[3][2] = {{t[0],t[1]}, {t[1],t[2]}, {t[2],t[0]}};
            for (auto& ee : e) ef2[keyOf(ee[0], ee[1])].push_back(f);
        }
        std::vector<std::vector<int>> fadj(out.F.size());
        for (auto& kv : ef2) if (kv.second.size() == 2) { fadj[kv.second[0]].push_back(kv.second[1]); fadj[kv.second[1]].push_back(kv.second[0]); }
        std::vector<int> fcomp(out.F.size(), -1); std::vector<int> compSize; int ncomp = 0;
        for (int f = 0; f < (int)out.F.size(); ++f) {
            if (fcomp[f] >= 0) continue;
            std::vector<int> stack = {f}; fcomp[f] = ncomp; int sz = 0;
            while (!stack.empty()) { int u = stack.back(); stack.pop_back(); ++sz; for (int w : fadj[u]) if (fcomp[w] < 0) { fcomp[w] = ncomp; stack.push_back(w); } }
            compSize.push_back(sz); ++ncomp;
        }
        if (ncomp <= 1) break;   // single piece -- nothing to prune
        int best = 0; for (int c = 1; c < ncomp; ++c) if (compSize[c] > compSize[best]) best = c;
        std::vector<std::array<int,3>> kept2;
        for (int f = 0; f < (int)out.F.size(); ++f) if (fcomp[f] == best) kept2.push_back(out.F[f]);
        if (getenv("V2_DBG"))
            std::fprintf(stderr, "[v2cluster] compPass %d: %d components, dropping %zu faces outside the largest\n",
                         compPass, ncomp, out.F.size() - kept2.size());
        out.F = kept2;

        // re-close boundary holes the pruning just created, same ear-clipping as before.
        edgeCount.clear();
        for (const auto& t : out.F) { int e[3][2]={{t[0],t[1]},{t[1],t[2]},{t[2],t[0]}}; for (auto& ee:e) ++edgeCount[keyOf(ee[0],ee[1])]; }
        for (int pass2 = 0; pass2 < 8; ++pass2) {
            std::map<int, std::vector<int>> bnext;
            for (const auto& kv : edgeCount) if (kv.second == 1) { bnext[kv.first.first].push_back(kv.first.second); bnext[kv.first.second].push_back(kv.first.first); }
            if (bnext.empty()) break;
            size_t added2 = 0; std::set<int> vis2;
            for (auto& kv : bnext) {
                int start = kv.first; if (vis2.count(start)) continue;
                std::vector<int> loop2; int prev = -1, cur = start; bool ok2 = true;
                while (true) {
                    loop2.push_back(cur); vis2.insert(cur);
                    int next = -1; for (int n : bnext[cur]) if (n != prev) { next = n; break; }
                    if (next < 0) { ok2 = false; break; }
                    prev = cur; cur = next;
                    if (cur == start) break;
                    if ((int)loop2.size() > (int)out.P.size()) { ok2 = false; break; }
                }
                if (!ok2 || loop2.size() < 3) continue;
                std::vector<int> ring2 = loop2;
                while (ring2.size() >= 3) {
                    // same best-ear-by-quality selection as the main hole-closing pass above
                    int bestI2 = -1; double bestQ2 = -1e300;
                    for (size_t i = 0; i < ring2.size(); ++i) {
                        int a = ring2[(i+ring2.size()-1)%ring2.size()], b = ring2[i], c = ring2[(i+1)%ring2.size()];
                        if (a == c) continue;
                        int e[3][2] = {{a,b},{b,c},{c,a}}; bool okTri2 = true;
                        for (auto& ee : e) if (edgeCount[keyOf(ee[0],ee[1])] >= 2) { okTri2 = false; break; }
                        if (!okTri2) continue;
                        Vec3 pa = out.P[a], pb = out.P[b], pc = out.P[c];
                        Vec3 uab = (pb-pa).normalized(), ubc = (pc-pb).normalized(), uca = (pa-pc).normalized();
                        double angA = std::acos(std::clamp(-uca.dot(uab), -1.0, 1.0));
                        double angB = std::acos(std::clamp(-uab.dot(ubc), -1.0, 1.0));
                        double angC = std::acos(std::clamp(-ubc.dot(uca), -1.0, 1.0));
                        double q2 = std::min({angA, angB, angC});
                        if (q2 > bestQ2) { bestQ2 = q2; bestI2 = (int)i; }
                    }
                    if (bestI2 < 0) break;
                    size_t i = (size_t)bestI2;
                    int a = ring2[(i+ring2.size()-1)%ring2.size()], b = ring2[i], c = ring2[(i+1)%ring2.size()];
                    int e[3][2] = {{a,b},{b,c},{c,a}};
                    for (auto& ee : e) ++edgeCount[keyOf(ee[0],ee[1])];
                    out.F.push_back({a,b,c}); ring2.erase(ring2.begin()+(long)i);
                    ++added2;
                }
            }
            if (added2 == 0) break;
        }

        // pruning + re-closing can itself create fresh pinch/isolated defects -- one more pass.
        {
            int nvOut = (int)out.P.size();
            std::vector<std::vector<int>> incident(nvOut);
            for (int f = 0; f < (int)out.F.size(); ++f) for (int k = 0; k < 3; ++k) incident[out.F[f][k]].push_back(f);
            for (int v = 0; v < nvOut; ++v) {
                auto& facesV = incident[v]; if (facesV.size() <= 1) continue;
                std::vector<std::vector<int>> adjF(facesV.size());
                for (size_t i = 0; i < facesV.size(); ++i) {
                    const auto& fi = out.F[facesV[i]]; std::vector<int> oi; for (int k=0;k<3;++k) if (fi[k]!=v) oi.push_back(fi[k]);
                    for (size_t j = i+1; j < facesV.size(); ++j) {
                        const auto& fj = out.F[facesV[j]]; std::vector<int> oj; for (int k=0;k<3;++k) if (fj[k]!=v) oj.push_back(fj[k]);
                        bool se = false; for (int a:oi) for (int b:oj) if (a==b) se=true;
                        if (se) { adjF[i].push_back((int)j); adjF[j].push_back((int)i); }
                    }
                }
                std::vector<int> comp(facesV.size(), -1); int nc = 0;
                for (size_t i = 0; i < facesV.size(); ++i) {
                    if (comp[i] >= 0) continue;
                    std::vector<size_t> stack = {i}; comp[i] = nc;
                    while (!stack.empty()) { size_t u = stack.back(); stack.pop_back(); for (int w : adjF[u]) if (comp[w] < 0) { comp[w] = nc; stack.push_back((size_t)w); } }
                    ++nc;
                }
                if (nc <= 1) continue;
                std::vector<int> newIdxForComp(nc, v);
                for (int c = 1; c < nc; ++c) { newIdxForComp[c] = (int)out.P.size(); out.P.push_back(out.P[v]); }
                for (size_t i = 0; i < facesV.size(); ++i) { int c = comp[i]; if (c==0) continue; auto& f = out.F[facesV[i]]; for (int k=0;k<3;++k) if (f[k]==v) f[k]=newIdxForComp[c]; }
            }
            std::vector<char> used2(out.P.size(), 0);
            for (const auto& t : out.F) for (int k = 0; k < 3; ++k) used2[t[k]] = 1;
            std::vector<int> remap2(out.P.size(), -1); std::vector<Vec3> newP2;
            for (size_t v = 0; v < out.P.size(); ++v) if (used2[v]) { remap2[v] = (int)newP2.size(); newP2.push_back(out.P[v]); }
            out.P = newP2;
            for (auto& t : out.F) for (int k = 0; k < 3; ++k) t[k] = remap2[t[k]];
        }
    }

    // Final check: after the edge-cap + repair pass, require a properly CLOSED 2-manifold
    // (every edge shared by exactly 2 faces) -- never assume the repair pass succeeded.
    edgeCount.clear();
    for (const auto& t : out.F) {
        int e[3][2] = {{t[0],t[1]}, {t[1],t[2]}, {t[2],t[0]}};
        for (auto& ee : e) ++edgeCount[keyOf(ee[0], ee[1])];
    }
    long badEdges = 0, oneEdges = 0; int worstCount = 0;
    for (const auto& kv : edgeCount) {
        if (kv.second == 1) ++oneEdges;
        if (kv.second > 2) { ++badEdges; worstCount = std::max(worstCount, kv.second); }
    }
    long eulerChar = (long)out.P.size() - (long)edgeCount.size() + (long)out.F.size();
    // genus-0 sphere: V-E+F=2. A pinch vertex the fan-split above missed (or a different defect
    // entirely) shows up as a wrong Euler characteristic even when every edge count is clean --
    // gate on it explicitly rather than trusting edge counts alone.
    out.manifoldOk = (badEdges == 0 && oneEdges == 0 && eulerChar == 2);
    if (getenv("V2_DBG")) {
        // chi=4 (off by exactly 2) is the signature of TWO fully disconnected closed components
        // (2+2=4), distinct from a pinch (2+2-1=3) -- check directly rather than guess.
        int nvOut = (int)out.P.size();
        std::vector<std::vector<int>> fadj(out.F.size());
        std::map<std::pair<int,int>, std::vector<int>> edgeFaces2;
        for (int f = 0; f < (int)out.F.size(); ++f) {
            const auto& t = out.F[f];
            int e[3][2] = {{t[0],t[1]}, {t[1],t[2]}, {t[2],t[0]}};
            for (auto& ee : e) edgeFaces2[keyOf(ee[0], ee[1])].push_back(f);
        }
        for (auto& kv : edgeFaces2) if (kv.second.size() == 2) { fadj[kv.second[0]].push_back(kv.second[1]); fadj[kv.second[1]].push_back(kv.second[0]); }
        std::vector<int> fcomp(out.F.size(), -1); int ncomp = 0;
        for (int f = 0; f < (int)out.F.size(); ++f) {
            if (fcomp[f] >= 0) continue;
            std::vector<int> stack = {f}; fcomp[f] = ncomp;
            while (!stack.empty()) { int u = stack.back(); stack.pop_back(); for (int w : fadj[u]) if (fcomp[w] < 0) { fcomp[w] = ncomp; stack.push_back(w); } }
            ++ncomp;
        }
        (void)nvOut;
        std::fprintf(stderr, "[v2cluster] connected components (by face adjacency): %d\n", ncomp);
        std::fprintf(stderr, "[v2cluster] edges=%zu badEdges(>2)=%ld boundaryEdges(=1)=%ld worstCount=%d V-E+F=%ld\n",
                     edgeCount.size(), badEdges, oneEdges, worstCount, eulerChar);
    }
    return out;
}

static std::vector<Vec3> farthest_point_sample(const std::vector<Vec3>& P, int K) {
    const int n = (int)P.size();
    K = std::min(K, n);
    std::vector<Vec3> out; out.reserve(K);
    std::vector<double> mind(n, 1e300);
    int cur = 0;
    for (int i = 1; i < n; ++i) if (P[i].x() < P[cur].x()) cur = i;   // deterministic start
    out.push_back(P[cur]);
    for (int it = 1; it < K; ++it) {
        for (int i = 0; i < n; ++i) mind[i] = std::min(mind[i], (P[i] - P[cur]).squaredNorm());
        double best = -1; int bi = 0;
        for (int i = 0; i < n; ++i) if (mind[i] > best) { best = mind[i]; bi = i; }
        cur = bi; out.push_back(P[cur]);
    }
    return out;
}

int main(int argc, char** argv) {
    load_obj();
    const int Vin = (int)pos.size();
    const double keepOverride = (argc > 1) ? std::atof(argv[1]) : -1.0;   // local testing only
    if (Vin < 100) { save_obj(pos, faces); return 0; }   // sample: too small to matter, echo

    // ---- target vertex count: same per-case dispatch table as main.cpp (judge-measured
    // sizes), but the KEEP fractions here are placeholders — this file has not been tuned. ----
    auto keep_for = [](int V) -> double {
        if (V <= 7000)   return 0.05;      // tiny budget: hull-based construction wins easily here
        if (V <= 30000)  return 0.30;
        if (V <= 40000)  return 0.15;
        if (V <= 100000) return 0.085;
        if (V <= 400000) return 0.023;
        return 0.029;
    };
    double kf = (keepOverride > 0) ? keepOverride : keep_for(Vin);
    int target = std::max(4, (int)(kf * Vin));

    // ---- day 6/7: normal-based region segmentation (independent of main.cpp's decimation) ----
    // Diagnosed the gap to the decimator at matched V: normal SSIM ~0.21 (hull-and-grow) vs
    // ~0.56 (decimator, back-derived), depth comparable. The decimator starts from the full
    // mesh, so it inherits every correct normal and just has to not lose them; hull-and-grow
    // starts from nothing and discovers shape purely from a per-pixel error signal with no
    // notion of "this triangle straddles a real fold." Segment the ORIGINAL mesh into
    // normal-coherent regions (independent implementation: best-first/Dijkstra-like region
    // growing, not main.cpp's QEM/VSA-lite collapse order) and extract where regions meet
    // (boundary points, corners) -- both the day-7 clustered seed below AND any leftover
    // SSIM-driven growth (`g_featurePoints`, consumed inside `generate_split_candidates`) use
    // this same segmentation.
    auto adj = build_face_adjacency(faces);
    // K swept 1-350 on the bunny proxy (day 6): K~15-20 gave a small, NOT robust gain when used
    // only as extra SSIM-search candidates; the same sweep on armadillo showed no effect at any
    // K. Kept modest and non-cherry-picked rather than re-tuned for day 7's different use.
    int K = std::max(8, std::min((int)faces.size(), 20));
    if (getenv("V2_SEGK")) K = atoi(getenv("V2_SEGK"));   // local testing only
    Segmentation seg = segment_by_normal(pos, faces, adj, K);
    FeatureSet feat = extract_features(pos, faces, seg.regionOf, seg.regionNormal);
    for (const auto& fp : feat.corners) g_featurePoints.push_back(fp.p);
    for (const auto& fp : feat.edgePts) g_featurePoints.push_back(fp.p);
    std::fprintf(stderr, "[v2feat] K=%d corners=%zu edgePts=%zu\n", K, feat.corners.size(), feat.edgePts.size());

    // ---- day 7: seed = vertex-clustering construction anchored on the segmentation features
    // above (see build_clustered_mesh) -- falls back to day 1's convex-hull-of-farthest-points
    // seed if the clustering quotient fails its own manifold check (never assumed clean).
    std::vector<Vec3> curP; std::vector<std::array<int,3>> curF;
    bool usedCluster = false;
    if (!getenv("V2_NOCLUSTER")) {
        // Follow-up item 2, TESTED AND REVERTED: tried reserving a POLISH fraction of target
        // for the existing SSIM-driven refinement (days 4-5) to run on top of a deliberately
        // under-filled clustered seed, on the theory that the two mechanisms are complementary.
        // Measured on bunny V=522: MONOTONIC regression as the reserved fraction grows (0.6842
        // at 0%, 0.6803/0.6742/0.6731/0.6678 at 5/10/15/20%) -- not noise, a clean trend in the
        // wrong direction. In hindsight this makes sense: item 1 made clustering the STRONGER
        // per-vertex mechanism, so taking budget away from it to feed the weaker SSIM-greedy
        // loop is a net loss more often than a complementary gain. Default kept at 0 (clustering
        // gets the full target, as before item 2 was tried); the env var is left in place for
        // further experimentation, not because a positive default was found.
        double polishFrac = getenv("V2_POLISHFRAC") ? atof(getenv("V2_POLISHFRAC")) : 0.0;
        int clusterBudget = std::max(4, (int)((1.0 - polishFrac) * target));
        ClusteredMesh cm = build_clustered_mesh(pos, faces, seg, feat, clusterBudget);
        std::fprintf(stderr, "[v2cluster] kept=%zu faces=%zu manifoldOk=%d (clusterBudget=%d of target=%d)\n",
                     cm.P.size(), cm.F.size(), (int)cm.manifoldOk, clusterBudget, target);
        if (cm.manifoldOk && cm.P.size() >= 4 && !cm.F.empty()) {
            curP = cm.P; curF = cm.F; usedCluster = true;
        }
    }
    if (!usedCluster) {
        const int SEED_K = 24;
        std::vector<Vec3> hullPts = farthest_point_sample(pos, SEED_K);
        convex_hull(hullPts, curP, curF);
        std::fprintf(stderr, "[v2] hull seed V=%zu F=%zu (from %d farthest-point samples of %d)\n",
                     curP.size(), curF.size(), SEED_K, Vin);
        if (getenv("V2_DBG")) {
            long Eh = 0; std::map<std::pair<int,int>,int> ech;
            auto koh = [](int a,int b){return a<b?std::make_pair(a,b):std::make_pair(b,a);};
            for (const auto& t : curF) { int e[3][2]={{t[0],t[1]},{t[1],t[2]},{t[2],t[0]}}; for (auto& ee: e) ech[koh(ee[0],ee[1])]=1; }
            Eh = (long)ech.size();
            std::fprintf(stderr, "[v2] hull seed sanity: V-E+F=%ld (genus-0 expects 2)\n",
                         (long)curP.size() - Eh + (long)curF.size());
        }
    }
    target = std::max((int)curP.size(), target);   // never target fewer than the seed itself

    int RES = 256;   // day-1 steering resolution (cheap iteration; judge-res validation separately)
    if (getenv("V2_RES")) RES = atoi(getenv("V2_RES"));   // local testing only
    OrigViews O; capture_original(pos, faces, RES, O);
    g_origGrid.build(pos, faces);   // built ONCE: the original mesh never changes (day 5 perf pass)

    if (getenv("V2_GRIDTEST")) {
        // correctness check for SpatialGrid: compare against brute force on random-ish query
        // points (never runs on the judge; env-gated, day-5 diligence before trusting the grid
        // for performance-critical code).
        std::minstd_rand rng(42);
        std::uniform_real_distribution<double> U(-1.5, 1.5);
        int mismatches = 0, tested = 200;
        for (int i = 0; i < tested; ++i) {
            Vec3 q(U(rng), U(rng), U(rng));
            int fBrute; Vec3 pBrute = closest_point_on_mesh(q, pos, faces, &fBrute);
            int fGrid; Vec3 pGrid = g_origGrid.query(q, &fGrid);
            double dBrute = (pBrute - q).norm(), dGrid = (pGrid - q).norm();
            if (std::fabs(dBrute - dGrid) > 1e-9) {
                ++mismatches;
                std::fprintf(stderr, "[gridtest] MISMATCH q=(%.3f,%.3f,%.3f) dBrute=%.9f dGrid=%.9f\n",
                             q.x(), q.y(), q.z(), dBrute, dGrid);
            }
        }
        std::fprintf(stderr, "[gridtest] tested=%d mismatches=%d\n", tested, mismatches);
        return mismatches ? 1 : 0;
    }
    if (getenv("V2_VALIDATE")) {
        // ===== EXACT-DELTA VALIDATION (env-gated; never runs on the judge) =====
        // Same discipline as JD's validation earlier this session: predict each candidate
        // insertion's delta via exact_insertion_delta, then perform it for REAL, rescore fully
        // with the same render()+ssim_map() machinery used everywhere else in this file, and
        // compare. Zero trust extended to the new scoring code until this passes.
        auto full_score = [&](const std::vector<Vec3>& P, const std::vector<std::array<int,3>>& F) {
            double sn = 0.0; long nn = 0, dn = 0; double sd_ = 0.0;
            for (int v = 0; v < 6; ++v) {
                std::vector<int> fid; std::vector<double> depth;
                render(P, F, v, RES, fid, depth);
                for (int c = 0; c < 3; ++c) {
                    std::vector<double> Y((size_t)RES*RES, 127.5);
                    for (size_t k = 0; k < Y.size(); ++k) if (fid[k] >= 0) Y[k] = (face_normal(P, F[fid[k]])[c]+1.0)*127.5;
                    std::vector<double> smap; ssim_map(O.nX[c][v], Y, RES, smap);
                    for (size_t k = 0; k < smap.size(); ++k) { if (fid[k]<0) continue; sn += smap[k]; ++nn; }
                }
                std::vector<double> Yd((size_t)RES*RES, 255.0);
                for (size_t k = 0; k < Yd.size(); ++k) if (fid[k] >= 0) Yd[k] = depth[k];
                std::vector<double> smapD; ssim_map(O.dX[v], Yd, RES, smapD);
                for (size_t k = 0; k < smapD.size(); ++k) { if (fid[k]<0) continue; sd_ += smapD[k]; ++dn; }
            }
            double meanN = nn ? sn/nn : 1.0, meanD = dn ? sd_/dn : 1.0;
            return 0.5*meanN + 0.5*meanD;
        };

        std::vector<Vec3> vP = curP; std::vector<std::array<int,3>> vF = curF;
        if (const char* mp = getenv("V2_VALMESH")) {   // test on a pre-grown mesh instead of the raw seed
            FILE* mf = std::fopen(mp, "r");
            int mv, mfc; if (std::fscanf(mf, "%d %d", &mv, &mfc) == 2) {
                vP.assign(mv, Vec3::Zero()); vF.assign(mfc, {0,0,0});
                for (int i = 0; i < mv; ++i) { double x,y,z; std::fscanf(mf, " v %lf %lf %lf", &x,&y,&z); vP[i]=Vec3(x,y,z); }
                for (int i = 0; i < mfc; ++i) { int a,b,c; std::fscanf(mf, " f %d %d %d", &a,&b,&c); vF[i]={a-1,b-1,c-1}; }
            }
            std::fclose(mf);
            std::fprintf(stderr, "[v2val] loaded alt mesh from %s: V=%zu F=%zu\n", mp, vP.size(), vF.size());
        }
        build_view_cache(vP, vF, RES, O);
        double baseline = full_score(vP, vF);
        std::fprintf(stderr, "[v2val] baseline FinalSSIM=%.9f V=%zu F=%zu\n", baseline, vP.size(), vF.size());
        int tested = 0, matched = 0;
        const int K = getenv("V2_VALK") ? atoi(getenv("V2_VALK")) : 20;
        const double TOL = 2e-6;
        for (int f = 0; f < (int)vF.size() && tested < K; ++f) {
            const auto& t = vF[f];
            Vec3 a = vP[t[0]], b = vP[t[1]], c = vP[t[2]];
            Vec3 centroid = (a+b+c)/3.0;
            int fi; Vec3 p0 = closest_point_on_mesh(centroid, pos, faces, &fi);
            double edgeScale = std::max({(b-a).norm(), (c-b).norm(), (a-c).norm()});
            Vec3 tinyLocal = centroid + 0.01 * edgeScale * (a - centroid).normalized();
            std::fprintf(stderr, "  [v2val-info] face=%d edgeScale=%.4f |centroid-p0|=%.4f (ratio=%.2f)\n",
                         f, edgeScale, (centroid-p0).norm(), (centroid-p0).norm()/edgeScale);
            // a handful of candidates per face: position-baseline, a few offsets, and a TINY
            // local perturbation (to isolate whether locality-violation is the cause)
            std::vector<Vec3> cands = {p0, centroid, tinyLocal};
            for (const Vec3& p : cands) {
                if (tested >= K) break;
                double predicted = exact_insertion_delta(f, t[0], t[1], t[2], p, vP, vF, O);
                if (getenv("V2_VALDBG") && tested == atoi(getenv("V2_VALDBG"))) {
                    for (int vv = 0; vv < 6; ++vv) {
                        double dsum[4]={0,0,0,0}, cnt[4]={0,0,0,0};
                        bool okv = eval_insertion_view(vv, f, t[0], t[1], t[2], p, vP, vF, O, dsum, cnt);
                        std::fprintf(stderr, "    [view %d] ok=%d dsum=%.6f,%.6f,%.6f,%.6f cnt=%.0f,%.0f,%.0f,%.0f N3=%.0f Nd=%.0f\n",
                                     vv, okv, dsum[0],dsum[1],dsum[2],dsum[3], cnt[0],cnt[1],cnt[2],cnt[3], VC[vv].N3, VC[vv].Nd);
                    }
                }
                // perform for real: replace face f with 3 new triangles, rescore fully
                std::vector<Vec3> tp = vP; std::vector<std::array<int,3>> tf = vF;
                int newIdx = (int)tp.size(); tp.push_back(p);
                tf.push_back({t[0], t[1], newIdx});
                tf.push_back({t[1], t[2], newIdx});
                tf[f] = {t[2], t[0], newIdx};
                double after = full_score(tp, tf);
                double actual = after - baseline;
                double err = std::fabs(actual - predicted);
                bool ok = err < TOL;
                std::fprintf(stderr, "[v2val] #%d face=%d predicted=%+.9f actual=%+.9f err=%.2e %s\n",
                             tested, f, predicted, actual, err, ok ? "OK" : "MISMATCH");
                if (ok) ++matched;
                ++tested;
            }
        }
        std::fprintf(stderr, "[v2val] SUMMARY tested=%d matched=%d\n", tested, matched);
        save_obj(curP, curF);
        return 0;
    }

    const auto t0 = std::chrono::steady_clock::now();
    auto elapsed = [&]{ return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count(); };
    double BUDGET = 16.0;
    if (getenv("V2_BUDGET")) BUDGET = atof(getenv("V2_BUDGET"));   // local testing only

    // Hausdorff leash (judge rule: 5% of the ORIGINAL AABB diagonal). A sparse growth process
    // can satisfy the RENDERED metric while still leaving a geometric bridge far from the true
    // surface (measured on the bunny proxy: pure SSIM-deficit splitting FAILED Hausdorff, 0.227
    // vs the 0.119 limit, even though it was clearly making rendering progress). Every iteration
    // therefore also samples the original surface and forces a split near any leash violation,
    // ahead of the SSIM criterion — this is a validity requirement, not a quality preference.
    Vec3 lo = pos[0], hi = pos[0];
    for (const Vec3& q : pos) { lo = lo.cwiseMin(q); hi = hi.cwiseMax(q); }
    const double diag = (hi - lo).norm();
    const double LEASH = 0.05 * diag;
    std::vector<Vec3> hausSample = farthest_point_sample(pos, 400);

    // day 5 perf: exact_insertion_delta was being recomputed for EVERY tried face EVERY
    // iteration, even for faces whose local neighborhood is untouched since the last split --
    // measured as the dominant, growing cost (tried 15->110 faces/iter over the run, ~90% of
    // per-iteration time by V=300). A face's best-candidate delta only changes when (a) its OWN
    // 3 vertices move (never happens here -- vertices are only ever added) or (b) a NEW vertex
    // lands close enough to shrink its candidate set via the minSep guard, or (c) the rendered
    // view cache near it changes because a split happened in a screen-overlapping region. Cache
    // the per-face result and only invalidate (mark dirty) faces touched by the vertices of the
    // most recent split; monotonic w.r.t. minSep (more vertices can only invalidate candidates,
    // never revalidate one), so a cached "no candidate" result never needs to be reconsidered
    // unless the face itself is marked dirty again.
    std::vector<double> cacheDelta(curF.size(), -1e300);
    std::vector<Vec3> cachePos(curF.size(), Vec3::Zero());
    std::vector<char> cacheDirty(curF.size(), 1);
    auto growCache = [&]() {
        while (cacheDirty.size() < curF.size()) {
            cacheDelta.push_back(-1e300); cachePos.push_back(Vec3::Zero()); cacheDirty.push_back(1);
        }
    };
    auto markTouched = [&](int a, int b, int c, int d) {
        for (size_t f = 0; f < curF.size(); ++f) {
            const auto& tf = curF[f];
            for (int vtx : {tf[0], tf[1], tf[2]})
                if (vtx == a || vtx == b || vtx == c || vtx == d) { cacheDirty[f] = 1; break; }
        }
    };
    long cacheHits = 0, cacheMiss = 0;

    int iters = 0;
    // day 7: the loop used to stop purely on vertex COUNT (curP.size() < target), which was fine
    // when every seed started tiny and grew -- but the day-7 clustered seed can already MEET
    // target on its own, and Hausdorff satisfaction is a hard judge requirement, not a nice-to-
    // have tied to budget. Measured on armadillo: clustered seed hit target with the leash still
    // violated (0.2112 vs a 0.1229 limit) and the OLD condition would have exited immediately,
    // silently shipping an invalid mesh. Now: keep looping past target, HAUS-ONLY (no further
    // SSIM-driven growth once budget is met), until the leash is satisfied or a generous safety
    // cap is hit -- bounded, not unconditional, in case some mesh can never fully satisfy it.
    const int HAUS_HARD_CAP = target + std::max(200, target / 2);
    while (elapsed() < BUDGET && (int)curP.size() < HAUS_HARD_CAP) {
        const double t_iterStart = elapsed();
        // day 5 perf: build the view cache ONCE at the top of the iteration and have both the
        // deficit scan below AND the candidate scorer (exact_insertion_delta) read from it --
        // measured duplicate: this used to be rendered twice per iteration (once here via a
        // throwaway render() call, once again via build_view_cache() just before candidate
        // scoring), a pure 2x waste since curP/curF are unchanged in between.
        build_view_cache(curP, curF, RES, O);
        // score current mesh per face: accumulate rendered SSIM deficit onto contributing faces
        std::vector<double> faceDeficit(curF.size(), 0.0);
        double dbgSumSsim = 0.0; long dbgN = 0;
        for (int v = 0; v < 6; ++v) {
            const auto& fid = VC[v].fid;
            for (int c = 0; c < 3; ++c) {
                std::vector<double> Y((size_t)RES * RES, 127.5);
                for (size_t k = 0; k < Y.size(); ++k)
                    if (fid[k] >= 0) Y[k] = (face_normal(curP, curF[fid[k]])[c] + 1.0) * 127.5;
                std::vector<double> smap;
                ssim_map(O.nX[c][v], Y, RES, smap);
                for (size_t k = 0; k < smap.size(); ++k) {
                    if (fid[k] < 0) continue;
                    faceDeficit[fid[k]] += std::max(0.0, 1.0 - smap[k]);
                    dbgSumSsim += smap[k]; ++dbgN;
                }
            }
        }
        const double t_afterDeficit = elapsed();
        if (getenv("V2_DBG") && iters % 20 == 0)
            std::fprintf(stderr, "[v2score] iter=%d V=%zu meanNormalSSIM=%.4f t=%.2f\n", iters, curP.size(),
                         dbgN ? dbgSumSsim / dbgN : -1.0, elapsed());

        // ===== DEEP DIAGNOSTIC (V2_DIAG): find the worst face and inspect WHY its deficit
        // resists correction — is the true cause of the error actually located elsewhere on
        // the mesh (self-occlusion / attribution mismatch), not fixable by splitting THIS face?
        if (getenv("V2_DIAG") && iters == atoi(getenv("V2_DIAG"))) {
            int wf = 0; double wv = -1;
            for (size_t f = 0; f < faceDeficit.size(); ++f) if (faceDeficit[f] > wv) { wv = faceDeficit[f]; wf = (int)f; }
            const auto& wt = curF[wf];
            Vec3 wa = curP[wt[0]], wb = curP[wt[1]], wc = curP[wt[2]];
            Vec3 wcentroid = (wa + wb + wc) / 3.0;
            std::fprintf(stderr, "\n[DIAG] worst face=%d deficit=%.4f verts=(%d,%d,%d)\n", wf, wv, wt[0], wt[1], wt[2]);
            std::fprintf(stderr, "[DIAG]   pos a=(%.4f,%.4f,%.4f) b=(%.4f,%.4f,%.4f) c=(%.4f,%.4f,%.4f)\n",
                         wa.x(),wa.y(),wa.z(), wb.x(),wb.y(),wb.z(), wc.x(),wc.y(),wc.z());
            int wfi; Vec3 wcp = closest_point_on_mesh(wcentroid, pos, faces, &wfi);
            std::fprintf(stderr, "[DIAG]   closest ORIGINAL point to centroid: dist=%.4f, on original face %d\n",
                         (wcp - wcentroid).norm(), wfi);
            for (int v = 0; v < 6; ++v) {
                std::vector<int> fid; std::vector<double> depth;
                render(curP, curF, v, RES, fid, depth);
                long cnt = 0; int mnx=RES,mxx=-1,mny=RES,mxy=-1;
                for (int y = 0; y < RES; ++y) for (int x = 0; x < RES; ++x) {
                    if (fid[(size_t)y*RES+x] == wf) { ++cnt; mnx=std::min(mnx,x); mxx=std::max(mxx,x); mny=std::min(mny,y); mxy=std::max(mxy,y); }
                }
                if (cnt == 0) { std::fprintf(stderr, "[DIAG]   view %d: not visible (0 pixels)\n", v); continue; }
                // per-view deficit contribution and a sample pixel at the bbox center
                int px = (mnx+mxx)/2, py = (mny+mxy)/2;
                size_t pk = (size_t)py*RES+px;
                Vec3 curN = face_normal(curP, curF[fid[pk]]);
                // what does the ORIGINAL render show at this exact pixel?
                std::vector<int> ofid; std::vector<double> odepth;
                render(pos, faces, v, RES, ofid, odepth);
                int origFaceAtPixel = ofid[pk];
                std::fprintf(stderr, "[DIAG]   view %d: %ld px, bbox=(%d,%d)-(%d,%d), sample px=(%d,%d)\n",
                             v, cnt, mnx,mny,mxx,mxy, px, py);
                if (origFaceAtPixel < 0) {
                    std::fprintf(stderr, "[DIAG]     original render: BACKGROUND at this pixel (current mesh extends past the true silhouette here)\n");
                } else {
                    Vec3 origN = face_normal(pos, faces[origFaceAtPixel]);
                    double cosang = curN.dot(origN);
                    std::fprintf(stderr, "[DIAG]     current normal=(%.3f,%.3f,%.3f) original normal=(%.3f,%.3f,%.3f) cos=%.4f original_face=%d\n",
                                 curN.x(),curN.y(),curN.z(), origN.x(),origN.y(),origN.z(), cosang, origFaceAtPixel);
                    // is the ORIGINAL face's own centroid actually closest (on the CURRENT mesh)
                    // to a DIFFERENT current face than the one rendering there? That would mean
                    // the true matching geometry is elsewhere -- an attribution/occlusion mismatch.
                    Vec3 ot = (pos[faces[origFaceAtPixel][0]] + pos[faces[origFaceAtPixel][1]] + pos[faces[origFaceAtPixel][2]]) / 3.0;
                    int matchFi; closest_point_on_mesh(ot, curP, curF, &matchFi);
                    std::fprintf(stderr, "[DIAG]     original face %d's own closest CURRENT face = %d (rendering here = %d) %s\n",
                                 origFaceAtPixel, matchFi, wf, matchFi == wf ? "[MATCH]" : "[MISMATCH -- attribution problem]");
                }
            }
            std::fprintf(stderr, "[DIAG] end\n\n");
        }
        // find the worst-violating original sample point (max distance to the CURRENT surface,
        // via true point-to-triangle distance, not just nearest vertex — a nearest-VERTEX
        // guard was measured to plateau: boosting faces touching the nearest vertex does not
        // guarantee the next split actually lands inside the violating gap).
        g_curGrid.build(curP, curF);   // rebuilt once per iteration: cheap vs. the O(400*faces)
                                       // brute-force scan it replaces below (day 5 perf pass)
        double worstGeom = -1; Vec3 worstPt; int worstFace = -1;
        for (const Vec3& s : hausSample) {
            int fi; Vec3 cp = g_curGrid.query(s, &fi);
            double d = (cp - s).norm();
            if (d > worstGeom) { worstGeom = d; worstPt = s; worstFace = fi; }
        }
        const double t_afterHaus = elapsed();
        if (getenv("V2_DBG") && iters % 20 == 0)
            std::fprintf(stderr, "[v2] iter=%d V=%zu worstGeom=%.4f leash=%.4f\n", iters, curP.size(), worstGeom, LEASH);

        // A candidate split is only accepted if all 3 resulting sub-triangles clear a minimum
        // area (relative to the mesh scale) — a face repeatedly re-selected as "worst" can
        // converge its own centroid onto an already-existing vertex (the closest point on the
        // original surface stops moving once the local patch is well covered), producing a
        // zero-area sliver on repeat. Measured: this was NOT a rare edge case (89% of faces
        // ended up degenerate on the bunny proxy before this guard existed) — every candidate
        // must be validated, with a fallback to the next-best candidate on rejection.
        const double MIN_AREA = 1e-8 * diag * diag;
        auto split_areas_ok = [&](const std::array<int,3>& t, const Vec3& np) {
            const Vec3 &a = curP[t[0]], &b = curP[t[1]], &c = curP[t[2]];
            double a1 = 0.5*(a-np).cross(b-np).norm();
            double a2 = 0.5*(b-np).cross(c-np).norm();
            double a3 = 0.5*(c-np).cross(a-np).norm();
            return a1 > MIN_AREA && a2 > MIN_AREA && a3 > MIN_AREA;
        };
        std::vector<int> ssimOrder(curF.size());
        for (size_t f = 0; f < curF.size(); ++f) ssimOrder[f] = (int)f;
        std::sort(ssimOrder.begin(), ssimOrder.end(),
                  [&](int a, int b) { return faceDeficit[a] > faceDeficit[b]; });

        int splitFace = -1; Vec3 newPos; int tried = 0; bool haus = false;
        bool overBudget = (int)curP.size() >= target;
        if (worstGeom > LEASH && split_areas_ok(curF[worstFace], worstPt)) {
            splitFace = worstFace; newPos = worstPt; haus = true;
        } else if (overBudget) {
            // Budget met AND the leash is satisfied (or the only remaining violation can't be
            // fixed by a valid split) -- nothing left to do. Never fall through to the
            // SSIM-driven search once over budget; that would silently keep growing past target.
            if (getenv("V2_DBG"))
                std::fprintf(stderr, "[v2] target reached, worstGeom=%.4f leash=%.4f at V=%zu -- stopping\n",
                             worstGeom, LEASH, curP.size());
            break;
        } else {
            // day 4: score candidates by the EXACT local-delta rendered SSIM change (validated
            // against a bit-exact full rescore, docs/V2-CONSTRUCTION.md day 4), not the day 1-3
            // isolated-normal proxy that caused 4 distinct bugs. Accept bar kept conservative
            // (JD's pattern this session): only a clearly-positive true gain wins.
            const double ACCEPT_BAR = 1e-5;
            // view cache already built at the top of this iteration (day 5 perf fix) --
            // curP/curF have not changed since, so it's still valid here.
            std::vector<Vec3> cands;
            int recomputed = 0;
            for (int cand : ssimOrder) {
                ++tried;
                // Cache-check (V2_CACHECHECK) proved markTouched's vertex-adjacency invalidation
                // misses real staleness from screen-space-adjacent (non-topological) overlap --
                // drift above ACCEPT_BAR appears within a SINGLE iteration, so no flush cadence
                // can bound it. Safe fix: the cache may only be used to cheaply SKIP a face
                // (clean AND cached-value looks bad -- worst case is a missed opportunity, a
                // quality cost only), never to ACCEPT one. Any face whose cache is dirty, OR
                // whose cached value suggests it clears the bar, always gets a fresh recompute
                // before that decision is trusted.
                bool needFresh = cacheDirty[cand] || cacheDelta[cand] > ACCEPT_BAR;
                if (needFresh) {
                    ++recomputed;
                    if (cacheDirty[cand]) ++cacheMiss; else ++cacheHits;
                    const auto& t = curF[cand];
                    const Vec3 &fa = curP[t[0]], &fb = curP[t[1]], &fc = curP[t[2]];
                    double edgeScale = std::max({(fb-fa).norm(), (fc-fb).norm(), (fa-fc).norm()});
                    double minSep = 0.02 * edgeScale;
                    generate_split_candidates(fa, fb, fc, pos, faces, g_origGrid, curP, edgeScale, MIN_AREA, minSep, g_featurePoints, cands);
                    double bestDelta = -1e300; Vec3 bestP = fa;
                    for (const Vec3& p : cands) {
                        double d = exact_insertion_delta(cand, t[0], t[1], t[2], p, curP, curF, O);
                        if (d > bestDelta) { bestDelta = d; bestP = p; }
                    }
                    cacheDelta[cand] = bestDelta; cachePos[cand] = bestP; cacheDirty[cand] = 0;
                } else {
                    ++cacheHits;
                }
                if (cacheDelta[cand] > ACCEPT_BAR) { splitFace = cand; newPos = cachePos[cand]; break; }
                if (recomputed >= 150) break;   // cap the real work: exact-delta scoring is
                                          // per-candidate expensive (6-view local rescore);
                                          // free cache-skips don't count against this cap
            }
        }
        if (getenv("V2_DBG") && iters % 20 == 0) {
            std::fprintf(stderr, "[v2cand] iter=%d haus=%d tried=%d of %zu faces, deficit=%.4f face=%d newPos=(%.5f,%.5f,%.5f)\n",
                         iters, (int)haus, tried, curF.size(), splitFace >= 0 ? faceDeficit[splitFace] : -1.0,
                         splitFace, newPos.x(), newPos.y(), newPos.z());
            const double t_end = elapsed();
            std::fprintf(stderr, "[v2time] deficit=%.3fs haus=%.3fs cand=%.3fs total=%.3fs cacheHits=%ld cacheMiss=%ld\n",
                         t_afterDeficit - t_iterStart, t_afterHaus - t_afterDeficit, t_end - t_afterHaus, t_end - t_iterStart,
                         cacheHits, cacheMiss);
        }
        if (splitFace < 0) {   // every candidate degenerate: mesh has converged as far as this
            std::fprintf(stderr, "[v2] no valid split candidate at V=%zu — stopping early\n", curP.size());
            break;
        }
        const auto t = curF[splitFace];
        int newIdx = (int)curP.size();
        curP.push_back(newPos);
        curF.push_back({t[0], t[1], newIdx});
        curF.push_back({t[1], t[2], newIdx});
        curF[splitFace] = {t[2], t[0], newIdx};
        // day 5 perf cache: the split touched vertices t[0],t[1],t[2],newIdx -- grow the cache
        // for the 2 newly-appended faces (dirty by default) and invalidate any OTHER existing
        // face that shares one of these 4 vertices, since its candidate set or local rendering
        // may have changed.
        growCache();
        markTouched(t[0], t[1], t[2], newIdx);

        // day 5 cache-soundness check (opt-in, expensive): re-derive every CLEAN cached face's
        // delta from scratch and diff against the cached value. The only way a clean (untouched-
        // vertex) face's cache can legitimately go stale is a screen-space-adjacent split that
        // doesn't share a vertex (e.g. silhouette overlap) -- markTouched can't catch that by
        // construction, so this is the only way to confirm it isn't actually happening in
        // practice rather than assuming it away.
        static const int cacheCheckEvery = getenv("V2_CACHECHECK_EVERY") ? atoi(getenv("V2_CACHECHECK_EVERY")) : 20;
        if (getenv("V2_CACHECHECK") && iters % cacheCheckEvery == 0) {
            build_view_cache(curP, curF, RES, O);   // re-sync VC to the just-committed mesh
            long checked = 0, mismatched = 0; double worstErr = 0;
            std::vector<Vec3> ccands;
            for (size_t f = 0; f < curF.size(); ++f) {
                if (cacheDirty[f]) continue;
                ++checked;
                const auto& tf = curF[f];
                const Vec3 &fa = curP[tf[0]], &fb = curP[tf[1]], &fc = curP[tf[2]];
                double edgeScale = std::max({(fb-fa).norm(), (fc-fb).norm(), (fa-fc).norm()});
                double minSep = 0.02 * edgeScale;
                generate_split_candidates(fa, fb, fc, pos, faces, g_origGrid, curP, edgeScale, MIN_AREA, minSep, g_featurePoints, ccands);
                double freshBest = -1e300;
                for (const Vec3& p : ccands) {
                    double d = exact_insertion_delta((int)f, tf[0], tf[1], tf[2], p, curP, curF, O);
                    if (d > freshBest) freshBest = d;
                }
                double err = std::fabs(freshBest - cacheDelta[f]);
                if (err > worstErr) worstErr = err;
                if (err > 1e-9) ++mismatched;
            }
            std::fprintf(stderr, "[v2cachecheck] iter=%d checked=%ld mismatched=%ld worstErr=%.3e\n",
                         iters, checked, mismatched, worstErr);
        }
        ++iters;
    }
    std::fprintf(stderr, "[v2] grown to V=%zu F=%zu in %d splits, %.1fs\n",
                 curP.size(), curF.size(), iters, elapsed());
    std::fprintf(stderr, "[v2] candidate rejects: area=%ld sep=%ld\n", g_areaRejects, g_sepRejects);
    if (getenv("V2_DBG")) {
        build_view_cache(curP, curF, RES, O);
        double sn = 0.0; long nn = 0, dn = 0; double sd_ = 0.0;
        for (int v = 0; v < 6; ++v) {
            const auto& fid = VC[v].fid; const auto& depth = VC[v].depth;
            for (int c = 0; c < 3; ++c) {
                std::vector<double> Y((size_t)RES*RES, 127.5);
                for (size_t k = 0; k < Y.size(); ++k) if (fid[k] >= 0) Y[k] = (face_normal(curP, curF[fid[k]])[c]+1.0)*127.5;
                std::vector<double> smap; ssim_map(O.nX[c][v], Y, RES, smap);
                for (size_t k = 0; k < smap.size(); ++k) { if (fid[k]<0) continue; sn += smap[k]; ++nn; }
            }
            std::vector<double> Yd((size_t)RES*RES, 255.0);
            for (size_t k = 0; k < Yd.size(); ++k) if (fid[k] >= 0) Yd[k] = depth[k];
            std::vector<double> smapD; ssim_map(O.dX[v], Yd, RES, smapD);
            for (size_t k = 0; k < smapD.size(); ++k) { if (fid[k]<0) continue; sd_ += smapD[k]; ++dn; }
        }
        double meanN = nn ? sn/nn : 1.0, meanD = dn ? sd_/dn : 1.0;
        std::fprintf(stderr, "[v2] FinalSSIM=%.4f (normal=%.4f depth=%.4f)\n", 0.5*meanN+0.5*meanD, meanN, meanD);

        // day 7 sanity check: the clustered seed is a NEW code path (days 1-6 always started
        // from a convex hull, which is degenerate-face-free and genus-0 by construction) --
        // verify those same properties are not silently violated here, don't just trust it
        // because it rendered well.
        long degenerate = 0;
        const double MIN_AREA_CHK = 1e-10 * diag * diag;
        for (const auto& t : curF) {
            double a = 0.5*(curP[t[1]]-curP[t[0]]).cross(curP[t[2]]-curP[t[0]]).norm();
            if (a <= MIN_AREA_CHK) ++degenerate;
        }
        double worstHaus = -1;
        g_curGrid.build(curP, curF);
        for (const Vec3& s : hausSample) { int fi; Vec3 cp = g_curGrid.query(s, &fi); worstHaus = std::max(worstHaus, (cp-s).norm()); }
        long E = 0; { std::map<std::pair<int,int>,int> ec; auto ko=[](int a,int b){return a<b?std::make_pair(a,b):std::make_pair(b,a);};
            for (const auto& t : curF) { int e[3][2]={{t[0],t[1]},{t[1],t[2]},{t[2],t[0]}}; for (auto& ee: e) ec[ko(ee[0],ee[1])]=1; } E = (long)ec.size(); }
        long eulerChar = (long)curP.size() - E + (long)curF.size();
        std::fprintf(stderr, "[v2] sanity: degenerateFaces=%ld worstHausdorff=%.4f (limit %.4f) V-E+F=%ld (genus-0 expects 2)\n",
                     degenerate, worstHaus, LEASH, eulerChar);
    }

    save_obj(curP, curF);
    return 0;
}
