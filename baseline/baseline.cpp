// Starter scaffold for "Perception-Aware Lossless Simplification of 3D Meshes".
//
// It reads the mesh, does not optimize it and then out put it.
// Implement your simplification inside simplify()
//
// To run:
//   g++ -O2 -I /path/to/Eigen baseline.cpp -o baseline
//   ./baseline < mesh.in > mesh.out

#include "Eigen/Dense"

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

using namespace std;

// Mesh representation. Rows are vertices/faces.
//   V : |vertices| x 3 matrix of (x, y, z) coordinates.
//   F : |faces|    x 3 matrix of 0-indexed vertex references (input is
//                  1-indexed; load_obj subtracts 1, save_obj adds it back).
using MeshV = Eigen::Matrix<double, Eigen::Dynamic, 3, Eigen::RowMajor>;
using MeshF = Eigen::Matrix<int, Eigen::Dynamic, 3, Eigen::RowMajor>;

static MeshV V;
static MeshF F;

// --- fast input -------------------------------------------------------------

static vector<char> slurp_stdin() {
    vector<char> buf;
    buf.reserve(1 << 27);
    char chunk[1 << 16];
    size_t n;
    while ((n = fread(chunk, 1, sizeof(chunk), stdin)) > 0)
        buf.insert(buf.end(), chunk, chunk + n);
    buf.push_back('\0');
    return buf;
}

static void load_obj() {
    vector<char> buf = slurp_stdin();
    char* p = buf.data();

    long nv = strtol(p, &p, 10);
    long nf = strtol(p, &p, 10);
    V.resize(nv, 3);
    F.resize(nf, 3);

    for (long i = 0; i < nv; ++i) {
        // 'v'
        while (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t') ++p;
        ++p;
        V(i, 0) = strtod(p, &p);
        V(i, 1) = strtod(p, &p);
        V(i, 2) = strtod(p, &p);
    }
    for (long i = 0; i < nf; ++i) {
        // 'f'
        while (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t') ++p;
        ++p;
        F(i, 0) = (int)strtol(p, &p, 10) - 1;
        F(i, 1) = (int)strtol(p, &p, 10) - 1;
        F(i, 2) = (int)strtol(p, &p, 10) - 1;
    }
}


// --- fast output -----------------------------------------------------------------

// Print the mesh. Print 10 significant digits using %.10g for performance
static void save_obj() {
    string out;
    out.reserve((size_t)V.rows() * 40 + (size_t)F.rows() * 24 + 32);
    char line[96];

    out.append(line, snprintf(line, sizeof line, "%ld %ld\n",
                              (long)V.rows(), (long)F.rows()));
    for (Eigen::Index i = 0; i < V.rows(); ++i)
        out.append(line, snprintf(line, sizeof line, "v %.10g %.10g %.10g\n",
                                  V(i, 0), V(i, 1), V(i, 2)));
    for (Eigen::Index i = 0; i < F.rows(); ++i)
        out.append(line, snprintf(line, sizeof line, "f %d %d %d\n",
                                  F(i, 0) + 1, F(i, 1) + 1, F(i, 2) + 1));

    fwrite(out.data(), 1, out.size(), stdout);
}

// --- your implementation --------------------------------------------------------------

// Optimize the mesh: replace V and F
static void simplify() {
    // TODO: implement mesh simplification here.
}

int main() {
    load_obj();
    simplify();
    save_obj();
    return 0;
}
