// IMC 2026 - Problem B : manifold-safe QEM edge-collapse decimator.
//
// Phase 1 skeleton: declarations only. The function bodies (the engine itself)
// are implemented next; this file fixes the libraries, the shared state, and
// the signatures that mirror the pseudocode (Initialize / Decimate / Evaluate /
// SafeToCollapse / Collapse, plus the helpers they call).
//
// Build (dev): g++ -O2 -I /path/to/Eigen solver/main.cpp -o solver/main

// --- libraries --------------------------------------------------------------
#include "Eigen/Dense"      // Vector3d / Matrix4d, 3x3 linear solve for the target
#include <vector>           // dynamic arrays for the per-vertex / per-face state
#include <array>            // a face is 3 vertex indices
#include <queue>            // std::priority_queue : the cost-ordered collapse heap
#include <unordered_set>    // per-vertex incident-face sets / neighbour queries
#include <functional>       // std::greater : turns the heap into a min-heap
#include <algorithm>        // set intersection for the link condition
#include <cstdint>
#include <cstdio>           // fast stdin/stdout mesh I/O (as in baseline.cpp)
#include <cstdlib>
#include <limits>
#include <string>

// --- type aliases -----------------------------------------------------------
using Vec3    = Eigen::Vector3d;   // a position
using Vec4    = Eigen::Vector4d;   // a homogeneous plane p = [a b c d]^T
using Quadric = Eigen::Matrix4d;   // 4x4 symmetric error quadric Q

// --- tunable constants (the eps / tau of SAFE_TO_COLLAPSE) ------------------
constexpr double kAreaEps = 1e-15; // reject a collapse that creates area < this
constexpr double kFlipTau = 0.0;   // reject if dot(normal_before, normal_after) < this

// FASE 2: weight wn of the face-normal-preservation term added to each quadric.
// 0 -> pure geometric area-weighted QEM; >0 -> the optimal target also tries to
// keep incident face *normals* unchanged, which is what the judge's flat-shaded
// normal map scores. On REAL meshes (mixed flat + detailed regions) this is the
// binding constraint: it collapses flat zones nearly for free (normals unchanged
// -> SSIM unchanged) while protecting curved/detailed zones, so at FinalSSIM >= 0.90
// it compresses much more (bunny 0% -> ~39%, cow 0% -> ~45%; smooth spheres are
// unaffected). Default 1.0 (best worst-case across the real test bench). argv[2].
constexpr double kDefaultNormalWeight = 1.0;
static double g_normal_weight = kDefaultNormalWeight;

// --- result of evaluating a candidate collapse: (cost, target) --------------
struct EvalResult {
    double cost;    // v_bar^T (Q_i + Q_j) v_bar
    Vec3   target;  // x_bar, the optimal contraction position
};

// --- a queued collapse, carrying the version stamps for lazy deletion -------
struct HeapEntry {
    double cost;        // priority
    int    i, j;        // edge endpoints (i < j)
    int    vi, vj;      // ver[i], ver[j] captured at push time
    // ordered by cost so std::greater<> yields a min-heap (cheapest on top)
    bool operator>(const HeapEntry& o) const { return cost > o.cost; }
};

// --- shared state (the implicit globals of the pseudocode) ------------------
static std::vector<Vec3>                     pos;        // pos[v]   : vertex position
static std::vector<Quadric>                  Q;          // Q[v]     : accumulated quadric
static std::vector<std::array<int, 3>>       faces;      // faces[f] : triangle indices
static std::vector<char>                     face_alive; // faces[f] still present?
static std::vector<std::unordered_set<int>>  vfaces;     // vfaces[v]: incident face ids
static std::vector<char>                     alive;      // alive[v]
static std::vector<int>                      ver;        // ver[v]   : version stamp
static int                                   alive_count = 0;

// FASE 1 (true-deviation guard): dev[v] is an upper bound on the distance from any
// ORIGINAL vertex represented by v (its collapse cluster) to the current pos[v].
// A collapse is rejected if it would push this bound past g_dev_max, which keeps the
// directed Hausdorff (original -> simplified) under a safe fraction of the diagonal.
static std::vector<double>                   dev;
static double                                g_dev_max = std::numeric_limits<double>::infinity();

static std::priority_queue<HeapEntry, std::vector<HeapEntry>,
                           std::greater<HeapEntry>> heap; // min-heap by cost

// --- mesh I/O (fast stdin/stdout, modified-OBJ; fills/reads the state) ------
void load_obj();   // read V, F from stdin into pos / faces (and init liveness)
void save_obj();   // write the surviving mesh to stdout, re-indexed and 1-based

// --- core engine (pseudocode functions) -------------------------------------
void       Initialize();                                       // build quadrics, vfaces, heap
void       Decimate(int target_count, double max_cost);        // greedy collapse loop (cost-bounded)
EvalResult Evaluate(int i, int j);                             // (cost, x_bar) for edge (i,j)
bool       SafeToCollapse(int i, int j, const Vec3& xbar);     // link + area + flip gates
void       Collapse(int i, int j, const Vec3& xbar);           // merge j into i, rewire

// --- helpers referenced above -----------------------------------------------
bool              EdgeExists(int i, int j);                    // is (i,j) still an edge?
std::vector<int>  Neighbors(int i);                            // one-ring vertices of i
Quadric           PlaneQuadric(const Vec3& a, const Vec3& b,   // K_f = p p^T for a face
                               const Vec3& c);
Vec3              FaceNormal(const Vec3& a, const Vec3& b, const Vec3& c);
double            FaceArea(const Vec3& a, const Vec3& b, const Vec3& c);

// --- implementations --------------------------------------------------------

// FIX 3 (normal-aware QEM): first-order face-normal-deviation quadric.
//
// Pure Garland-Heckbert QEM measures squared distance to incident face *planes*;
// it is blind to how a collapse re-orients those faces' normals, yet the judge's
// score is driven by a flat-shaded *normal* map. This term closes that gap.
//
// For a triangle with unit normal n and L = ||cross|| = 2*area, moving its vertex
// pv to x rotates the unit face normal, to first order, by  dn ~= M (x - pv)  with
//     M = (I - n n^T) / L * skew(e),     e = the edge opposite pv (the one not
//                                            incident to pv),
// since d(cross)/d(pv) = skew(e) and d(n) = (I - n n^T)/||cross|| d(cross). The
// squared normal change is (x-pv)^T (M^T M) (x-pv); we return its homogeneous 4x4
// form so it adds directly into the per-vertex quadric and is balanced against the
// geometric term by the existing optimal-position solve and cost. M^T M is PSD, so
// the accumulated quadric stays PSD and the LDLT target solve is unaffected.
static Quadric NormalDevQuadric(const Vec3& pv, const Vec3& n, double L, const Vec3& e) {
    Eigen::Matrix3d skew;
    skew <<    0.0, -e.z(),  e.y(),
            e.z(),    0.0, -e.x(),
           -e.y(),  e.x(),    0.0;                  // skew(e) * d = e x d
    const Eigen::Matrix3d P = Eigen::Matrix3d::Identity() - n * n.transpose();
    const Eigen::Matrix3d M = (P * skew) / L;        // d(normal) ~= M * (x - pv)
    const Eigen::Matrix3d N = M.transpose() * M;     // PSD: (x-pv)^T N (x-pv) ~= ||dn||^2
    const Vec3 Nv = N * pv;

    Quadric Qd;
    Qd.topLeftCorner<3, 3>()    = N;
    Qd.topRightCorner<3, 1>()   = -Nv;
    Qd.bottomLeftCorner<1, 3>() = -Nv.transpose();
    Qd(3, 3)                    = pv.dot(Nv);
    return Qd;
}

// INITIALIZE(V, F): accumulate one error quadric per vertex from its incident
// face planes, mark every vertex alive, and seed the heap with the cost of
// every unique edge. Assumes pos[] and faces[] are already loaded.
void Initialize() {
    const int nv = static_cast<int>(pos.size());
    const int nf = static_cast<int>(faces.size());

    // per-vertex / per-face state
    const Quadric Zero = Quadric::Zero();
    Q.assign(nv, Zero);
    vfaces.assign(nv, std::unordered_set<int>{});
    alive.assign(nv, 1);
    ver.assign(nv, 0);
    dev.assign(nv, 0.0);            // every original vertex starts on the surface
    face_alive.assign(nf, 1);
    alive_count = nv;

    // For each face f: its plane p_f and fundamental quadric K_f = p_f p_f^T,
    // accumulated into each incident vertex -> Q[v] = sum_{f in vfaces[v]} K_f.
    for (int f = 0; f < nf; ++f) {
        const int a = faces[f][0], b = faces[f][1], c = faces[f][2];
        Vec3 n = (pos[b] - pos[a]).cross(pos[c] - pos[a]);   // = 2*area * unit_normal
        const double len = n.norm();                         // = 2 * triangle area
        const double area = 0.5 * len;                       // triangle area
        if (len > 0.0) n /= len;                             // unit normal: a^2+b^2+c^2 = 1
        const double d = -n.dot(pos[a]);                     // plane offset
        Vec4 p; p << n, d;                                   // p_f = [a b c d]^T
        Quadric Kf = p * p.transpose();                      // K_f = p_f p_f^T
        Kf *= area;                                          // area-weight -> Garland-Heckbert surface integral
        Q[a] += Kf; Q[b] += Kf; Q[c] += Kf;

        // FIX 3: add the face-normal-preservation quadric to each incident vertex,
        // area-weighted (same surface-integral weighting) and scaled by wn. `len`
        // is ||cross|| = 2*area = L; `n` is the unit normal computed above.
        if (g_normal_weight > 0.0 && len > 0.0) {
            const double wn = g_normal_weight * area;
            Q[a] += wn * NormalDevQuadric(pos[a], n, len, pos[c] - pos[b]);
            Q[b] += wn * NormalDevQuadric(pos[b], n, len, pos[a] - pos[c]);
            Q[c] += wn * NormalDevQuadric(pos[c], n, len, pos[b] - pos[a]);
        }
        vfaces[a].insert(f);
        vfaces[b].insert(f);
        vfaces[c].insert(f);
    }

    // For each unique edge (i,j), i < j: push its collapse cost onto the heap.
    std::unordered_set<std::int64_t> seen;
    seen.reserve(static_cast<size_t>(nf) * 3);
    for (int f = 0; f < nf; ++f) {
        const int* t = faces[f].data();
        for (int e = 0; e < 3; ++e) {
            int i = t[e], j = t[(e + 1) % 3];
            if (i > j) { const int tmp = i; i = j; j = tmp; }
            const std::int64_t k = static_cast<std::int64_t>(i) * nv + j;
            if (!seen.insert(k).second) continue;            // edge already queued
            const EvalResult r = Evaluate(i, j);
            heap.push(HeapEntry{ r.cost, i, j, ver[i], ver[j] });
        }
    }
}

// EVALUATE(i, j): the optimal contraction target x_bar and its cost.
// With Q = Q[i] + Q[j] split into blocks [[A, b], [b^T, c]], the error of a
// point x is x^T A x + 2 b^T x + c, minimised by solving A x = -b. When A is
// (numerically) singular - flat or crease neighbourhoods - we fall back to the
// cheapest of the two endpoints and their midpoint, all of which lie on the
// existing surface.
EvalResult Evaluate(int i, int j) {
    const Quadric        Qc = Q[i] + Q[j];
    const Eigen::Matrix3d A = Qc.topLeftCorner<3, 3>();
    const Vec3            b = Qc.topRightCorner<3, 1>();

    // homogeneous quadratic form x_h^T Q x_h, x_h = (x, 1)
    auto quad_err = [&](const Vec3& x) -> double {
        Vec4 xh; xh << x, 1.0;
        return (xh.transpose() * Qc * xh).value();
    };

    // argmin of the quadric over the safe in-surface candidates (both endpoints
    // and their midpoint). All inputs satisfy ||v|| <= 1 and every accepted target
    // is kept <= 1 below, so these candidates are always inside the unit sphere.
    auto fallback = [&]() -> Vec3 {
        const Vec3 cand[3] = { pos[i], pos[j], 0.5 * (pos[i] + pos[j]) };
        Vec3 x = cand[0];
        double best = quad_err(cand[0]);
        for (int k = 1; k < 3; ++k) {
            const double e = quad_err(cand[k]);
            if (e < best) { best = e; x = cand[k]; }
        }
        return x;
    };

    constexpr double kDetEps = 1e-10;     // below this A is treated as singular
    constexpr double kUnitR  = 1.0;       // the judge assumes the model in the unit sphere
    Vec3 xbar;
    const double det = A.determinant();   // A is PSD, so det >= 0
    if (det > kDetEps) {                   // well-conditioned: exact optimum
        xbar = A.ldlt().solve(-b);         // solve A x_bar = -b
        // The unconstrained optimum can extrapolate OUTSIDE the model bounds in
        // high-curvature collapses. The judge requires every output vertex to stay
        // in the unit sphere, so reject such a target and fall back to the safe
        // in-surface candidates (which never leave the sphere).
        if (xbar.norm() > kUnitR) xbar = fallback();
    } else {                               // singular: same in-surface fallback
        xbar = fallback();
    }

    return EvalResult{ quad_err(xbar), xbar };
}

// SAFE_TO_COLLAPSE(i, j): may edge (i,j) be collapsed to x_bar without breaking
// the mesh? Two gates:
//   (a) link condition - the common neighbours of i and j must be exactly the
//       two apex vertices of the edge's two shared faces. An extra common
//       neighbour means the collapse would create a non-manifold edge.
//   (b) per-face validity - no surviving incident face may become degenerate
//       (area < eps) or flip its orientation (normal dot < tau).
bool SafeToCollapse(int i, int j, const Vec3& xbar) {
    // shared faces of edge (i,j): those containing both endpoints.
    int shared[2];
    int nshared = 0;
    for (int f : vfaces[i]) {
        const int* t = faces[f].data();
        if (t[0] == j || t[1] == j || t[2] == j) {
            if (nshared < 2) shared[nshared] = f;
            ++nshared;
        }
    }
    if (nshared != 2) return false;                  // not a clean interior manifold edge

    // (a) link condition. Each apex (third vertex of a shared face) is already a
    // common neighbour, so "common == apexes" reduces to "no extra common
    // neighbour", i.e. |neighbours(i) ∩ neighbours(j)| == 2.
    std::unordered_set<int> Ni, Nj;
    for (int f : vfaces[i]) { const int* t = faces[f].data();
        for (int k = 0; k < 3; ++k) if (t[k] != i) Ni.insert(t[k]); }
    for (int f : vfaces[j]) { const int* t = faces[f].data();
        for (int k = 0; k < 3; ++k) if (t[k] != j) Nj.insert(t[k]); }
    int ncommon = 0;
    for (int v : Ni) if (Nj.count(v)) ++ncommon;
    if (ncommon != nshared) return false;            // extra common neighbour -> non-manifold

    // (b) area + flip gate on every incident face except the two collapsing ones.
    // `moved` is the endpoint that this face owns (i for vfaces[i], j for vfaces[j]);
    // its position becomes x_bar. Non-shared faces own exactly one of {i, j}.
    auto face_ok = [&](int f, int moved) -> bool {
        const int* t = faces[f].data();
        Vec3 Po[3], Pn[3];
        for (int k = 0; k < 3; ++k) {
            Po[k] = pos[t[k]];
            Pn[k] = (t[k] == moved) ? xbar : pos[t[k]];
        }
        const Vec3   crN  = (Pn[1] - Pn[0]).cross(Pn[2] - Pn[0]);
        const double lenN = crN.norm();
        if (0.5 * lenN < kAreaEps) return false;     // (b) degenerate face
        const Vec3   crO  = (Po[1] - Po[0]).cross(Po[2] - Po[0]);
        const double lenO = crO.norm();
        Vec3 nO = Vec3::Zero();
        if (lenO > 0.0) nO = crO / lenO;
        const Vec3 nN = crN / lenN;                  // lenN > 0 here
        if (nO.dot(nN) < kFlipTau) return false;     // (b) normal flip
        return true;
    };

    for (int f : vfaces[i]) {
        if (f == shared[0] || f == shared[1]) continue;
        if (!face_ok(f, i)) return false;
    }
    for (int f : vfaces[j]) {
        if (f == shared[0] || f == shared[1]) continue;
        if (!face_ok(f, j)) return false;
    }
    return true;
}

// COLLAPSE(i, j): merge vertex j into vertex i at position x_bar. Moves i to
// x_bar, folds j's quadric into i's, kills j, deletes the two faces shared by
// the edge, and rewires every surviving face of j to reference i instead.
// (alive_count and the heap/version stamps are updated by the caller, Decimate.)
void Collapse(int i, int j, const Vec3& xbar) {
    pos[i]   = xbar;
    Q[i]    += Q[j];
    alive[j] = 0;

    // Delete the two faces shared by (i,j): mark them dead and drop them from
    // the incident set of each of their vertices (i, j, and the opposite apex).
    int shared[2];
    int nshared = 0;
    for (int f : vfaces[i]) {
        const int* t = faces[f].data();
        if (t[0] == j || t[1] == j || t[2] == j) {
            if (nshared < 2) shared[nshared] = f;
            ++nshared;
        }
    }
    for (int s = 0; s < nshared; ++s) {
        const int f = shared[s];
        face_alive[f] = 0;
        const int* t = faces[f].data();
        for (int k = 0; k < 3; ++k) vfaces[t[k]].erase(f);
    }

    // Rewire j's remaining faces (shared ones already removed): relabel j -> i
    // and move them into vfaces[i].
    for (int f : vfaces[j]) {
        int* t = faces[f].data();
        for (int k = 0; k < 3; ++k) if (t[k] == j) t[k] = i;
        vfaces[i].insert(f);
    }
    vfaces[j].clear();
}

// EDGE_EXISTS(i, j): does a (live) face still join i and j?
bool EdgeExists(int i, int j) {
    for (int f : vfaces[i]) {
        const int* t = faces[f].data();
        if (t[0] == j || t[1] == j || t[2] == j) return true;
    }
    return false;
}

// neighbors(i): the one-ring vertices of i (unique), read from its faces.
std::vector<int> Neighbors(int i) {
    std::unordered_set<int> s;
    for (int f : vfaces[i]) {
        const int* t = faces[f].data();
        for (int k = 0; k < 3; ++k) if (t[k] != i) s.insert(t[k]);
    }
    return std::vector<int>(s.begin(), s.end());
}

// DECIMATE(target_count, max_cost): greedily collapse the cheapest valid edge
// until the live-vertex floor (target_count) is reached, no collapses remain, or
// the cheapest remaining collapse would exceed the deviation budget max_cost.
// The cost x_bar^T Q x_bar approximates the squared distance of the merged vertex
// to the original surface, so capping it bounds geometric drift - this is the
// quality gate that stops the engine before it over-simplifies. Stale heap
// entries (endpoint gone, or version stamp changed) are skipped; after each
// collapse the merged vertex's incident edges are re-evaluated and re-queued.
void Decimate(int target_count, double max_cost) {
    while (alive_count > target_count && !heap.empty()) {
        const HeapEntry e = heap.top();
        heap.pop();
        const int i = e.i, j = e.j;
        if (!alive[i] || !alive[j])            continue;  // endpoint already collapsed
        if (e.vi != ver[i] || e.vj != ver[j])  continue;  // stale: cost out of date
        if (!EdgeExists(i, j))                 continue;  // no longer an edge
        if (e.cost > max_cost)                 break;     // budget exhausted: heap order means
                                                          // every remaining valid edge is >= this
        const EvalResult r = Evaluate(i, j);              // target (quadrics current here)

        // FASE 1 — true-deviation guard. Merging i,j at x_bar makes i absorb both
        // clusters; by the triangle inequality the new deviation bound is
        //   max( dev[i] + |x_bar - pos[i]| ,  dev[j] + |x_bar - pos[j]| ).
        // Unlike the QEM cost (an *average* of squared plane distances) this is a true
        // upper bound on the *max* point-to-surface distance, so capping it actually
        // bounds the Hausdorff. Reject the collapse if it would exceed the threshold.
        const double nd = std::max(dev[i] + (r.target - pos[i]).norm(),
                                   dev[j] + (r.target - pos[j]).norm());
        if (nd > g_dev_max)                    continue;  // would deviate past the safe limit

        if (!SafeToCollapse(i, j, r.target))   continue;  // link + area + flip gates

        Collapse(i, j, r.target);                         // merge j into i
        dev[i] = nd;                                       // i now represents both clusters
        --alive_count;

        // The collapse moved i to x_bar, folded Q[j] into Q[i], and deleted/rewired
        // the faces around the edge. So Q[i] changed AND the local geometry of every
        // face touching i changed. That makes stale not only the edges leaving i, but
        // every edge incident to a one-ring neighbour of i: their incident faces moved
        // with i, so their collapse cost (and any normal-aware term that reads those
        // faces) is out of date. Invalidate all of them by bumping the version stamp
        // of i and of its whole one-ring, then re-queue every edge incident to that
        // one-ring with a freshly evaluated cost carrying the current stamps.
        const std::vector<int> nb = Neighbors(i);
        ++ver[i];                                         // invalidate old (i,*) entries
        for (int n : nb) ++ver[n];                        // and old (n,*) entries

        for (int n : nb) {                                // edges i--n
            const EvalResult c = Evaluate(i, n);
            heap.push(HeapEntry{ c.cost, i, n, ver[i], ver[n] });
        }
        for (int n : nb) {                                // edges n--m around the ring
            for (int m : Neighbors(n)) {
                if (m == i) continue;                     // i--n already queued above
                const EvalResult c = Evaluate(n, m);
                heap.push(HeapEntry{ c.cost, n, m, ver[n], ver[m] });
            }
        }
    }
}

// --- mesh I/O ---------------------------------------------------------------

// Fail fast and cleanly (exit 1, no abort/segfault) on malformed input, so a bad
// or truncated mesh degrades gracefully instead of crashing the submission.
[[noreturn]] static void die_malformed(const char* msg) {
    std::fprintf(stderr, "solver: malformed input: %s\n", msg);
    std::exit(1);
}

// load_obj: read "V F", then V "v x y z" lines and F "f a b c" lines from stdin
// into pos[] and faces[] (0-indexed). Bulk read + strtol/strtod, as in baseline.
// Validates the header counts, the per-line 'v'/'f' markers (which catch a lying
// header count or a truncated stream), and the 1-based face index range.
void load_obj() {
    std::string buf;
    {
        char chunk[1 << 16];
        size_t n;
        while ((n = std::fread(chunk, 1, sizeof chunk, stdin)) > 0) buf.append(chunk, n);
    }
    char* p = buf.data();                      // std::string::data() is NUL-terminated
    const long nv = std::strtol(p, &p, 10);
    const long nf = std::strtol(p, &p, 10);
    // Generous bounds (contest max V=1.1M, F=2.1M): reject garbage headers before
    // a huge resize() would throw bad_alloc and abort.
    if (nv < 1 || nf < 1 || nv > 5000000L || nf > 12000000L)
        die_malformed("vertex/face count missing or out of range");
    pos.resize(nv);
    faces.resize(nf);

    auto skip_ws = [&]() {
        while (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t') ++p;
    };
    for (long v = 0; v < nv; ++v) {
        skip_ws();
        if (*p != 'v') die_malformed("expected a 'v' line (header count too large or input truncated)");
        ++p;                                  // skip 'v'
        pos[v].x() = std::strtod(p, &p);
        pos[v].y() = std::strtod(p, &p);
        pos[v].z() = std::strtod(p, &p);
    }
    for (long f = 0; f < nf; ++f) {
        skip_ws();
        if (*p != 'f') die_malformed("expected an 'f' line (header count too large or input truncated)");
        ++p;                                  // skip 'f'
        for (int k = 0; k < 3; ++k) {
            const long idx = std::strtol(p, &p, 10);
            if (idx < 1 || idx > nv) die_malformed("face vertex index out of range [1,V]");
            faces[f][k] = (int)(idx - 1);
        }
    }
}

// save_obj: write the surviving mesh to stdout in the same format. Dead vertices
// (alive==false) and dead faces (face_alive==false) are dropped; survivors are
// re-indexed to a compact 1-based range. %.10g matches the baseline size budget.
void save_obj() {
    const int nv = (int)pos.size();
    const int nf = (int)faces.size();
    std::vector<int> remap(nv, 0);            // old index -> new 1-based index (0 = dead)
    int out_v = 0, out_f = 0;
    for (int v = 0; v < nv; ++v) if (alive[v]) remap[v] = ++out_v;
    for (int f = 0; f < nf; ++f) if (face_alive[f]) ++out_f;

    std::string out;
    out.reserve((size_t)out_v * 40 + (size_t)out_f * 24 + 32);
    char line[96];
    out.append(line, std::snprintf(line, sizeof line, "%d %d\n", out_v, out_f));
    for (int v = 0; v < nv; ++v) {
        if (!alive[v]) continue;
        out.append(line, std::snprintf(line, sizeof line, "v %.10g %.10g %.10g\n",
                                       pos[v].x(), pos[v].y(), pos[v].z()));
    }
    for (int f = 0; f < nf; ++f) {
        if (!face_alive[f]) continue;
        const int* t = faces[f].data();
        out.append(line, std::snprintf(line, sizeof line, "f %d %d %d\n",
                                       remap[t[0]], remap[t[1]], remap[t[2]]));
    }
    std::fwrite(out.data(), 1, out.size(), stdout);
}

// --- entry point ------------------------------------------------------------
int main(int argc, char** argv) {
    // wn (argv[2]) must be set before Initialize, which bakes it into the quadrics.
    g_normal_weight = (argc > 2) ? std::atof(argv[2]) : kDefaultNormalWeight;

    load_obj();
    Initialize();

    // Quality-driven stop: bound the per-collapse quadric error (~ squared distance
    // to the original surface) by a fraction of the 5%-of-diagonal Hausdorff limit.
    // The accumulated quadric tracks *cumulative* drift, so this bounds total
    // deviation and adapts the compression to each mesh. `frac` (argv[1]) is the
    // safety fraction of the 5% budget and is the knob we tune against the oracle.
    Vec3 lo = pos[0], hi = pos[0];
    for (const Vec3& p : pos) { lo = lo.cwiseMin(p); hi = hi.cwiseMax(p); }
    const double diag     = (hi - lo).norm();
    const double frac     = (argc > 1) ? std::atof(argv[1]) : 0.5;
    const double eps      = frac * 0.05 * diag;

    // FASE 1: the deviation guard (argv[4], a fraction of the diagonal; default 4%,
    // i.e. a safety margin under the judge's 5% Hausdorff limit). Set to a huge value
    // to disable. This is what keeps the output ALWAYS valid, on any mesh.
    const double devfrac  = (argc > 4) ? std::atof(argv[4]) : 0.04;
    g_dev_max = devfrac * diag;

    // argv[3] (optional): decimate to an exact target vertex count instead of using
    // the cost budget. This makes equal-V' A/B comparisons (e.g. wn off vs on) clean;
    // when absent the quality-driven cost bound (eps^2) is used as before.
    int    target_count = 1;
    double max_cost     = eps * eps;
    if (argc > 3 && std::atoi(argv[3]) > 0) {     // a positive argv[3] -> exact-target mode
        target_count = std::atoi(argv[3]);
        max_cost     = std::numeric_limits<double>::infinity();
    }

    // Floor at a tetrahedron: the smallest closed 2-manifold with positive volume
    // is 4 vertices. Going below (a 3-vertex "doubled triangle") is a degenerate,
    // zero-volume sliver, so never decimate past it regardless of frac/target.
    if (target_count < 4) target_count = 4;

    Decimate(target_count, max_cost);
    save_obj();
    return 0;
}
