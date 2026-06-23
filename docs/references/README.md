# References

External sources the project builds on. Each vendored PDF gets an entry below
explaining what it is and where we rely on it.

## Papers

### Garland & Heckbert, 1997 — *Surface Simplification Using Quadric Error Metrics*
- File: [`garland-heckbert-1997-qem.pdf`](garland-heckbert-1997-qem.pdf)
- Venue: SIGGRAPH '97.
- **We use it for** the core decimation algorithm. The engine follows
  Section 3.2 (pair selection; we set the threshold `t = 0` → edge-only collapses
  to preserve the manifold), Section 4 (algorithm summary; the optimal-position
  solve `A x = -b`), and Section 5 (the fundamental quadric `K = p pᵀ` and
  `Q[v] = Σ K`). See [../theory/qem-pseudocode.md](../theory/qem-pseudocode.md).
- Key caveat we learned: the quadric error is an *average squared distance to
  planes*, not the *worst-case point-to-surface* distance the judge measures —
  see [../theory/qem-cost-is-not-hausdorff.md](../theory/qem-cost-is-not-hausdorff.md).

### Wang, Bovik, Sheikh & Simoncelli, 2004 — *Image Quality Assessment: From Error Visibility to Structural Similarity*
- File: not vendored (link only) — https://www.cns.nyu.edu/~lcv/ssim/
- Venue: IEEE Transactions on Image Processing.
- **We use it for** the SSIM metric the judge scores with (11×11 window,
  `k1 = 0.01`, `k2 = 0.03`, `L = 255`), reimplemented in `src/imc_eval/ssim.py`.

## Tools / specs

- **Eigen 5.x** — C++ linear algebra. Provided by the judge; vendored locally for
  dev builds by `scripts/setup.sh`. https://eigen.tuxfamily.org
- **Problem statement** — distilled in
  [../problem-statement-summary.md](../problem-statement-summary.md).
