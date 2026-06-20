"""Read/write the modified-OBJ mesh format used by the contest.

Format:
    line 1: "V F"
    V lines: "v x y z"   (coordinates)
    F lines: "f a b c"   (1-indexed vertex references)

Internally vertices are float64 (N,3) and faces are int64 (M,3) 0-indexed;
load subtracts 1, save adds it back.
"""

import numpy as np


def parse_mesh(text):
    tok = text.split()
    idx = 0
    nv = int(tok[idx]); idx += 1
    nf = int(tok[idx]); idx += 1

    V = np.empty((nv, 3), np.float64)
    for i in range(nv):
        # token at idx is the literal 'v'
        V[i, 0] = float(tok[idx + 1])
        V[i, 1] = float(tok[idx + 2])
        V[i, 2] = float(tok[idx + 3])
        idx += 4

    F = np.empty((nf, 3), np.int64)
    for i in range(nf):
        # token at idx is the literal 'f'
        F[i, 0] = int(tok[idx + 1]) - 1
        F[i, 1] = int(tok[idx + 2]) - 1
        F[i, 2] = int(tok[idx + 3]) - 1
        idx += 4

    return V, F


def load_mesh(path):
    with open(path, "r") as fh:
        return parse_mesh(fh.read())


def save_mesh(path, V, F, sig=10):
    """Write a mesh, mirroring baseline.cpp's '%.10g' precision budget."""
    fmt = "v %.{}g %.{}g %.{}g".format(sig, sig, sig)
    lines = ["%d %d" % (len(V), len(F))]
    for x, y, z in V:
        lines.append(fmt % (x, y, z))
    for a, b, c in F:
        lines.append("f %d %d %d" % (a + 1, b + 1, c + 1))
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
