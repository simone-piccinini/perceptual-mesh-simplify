# Submission v2 — quadric cost budget (frac 0.5)

Second submission.

## Approach

Stop collapsing when the cheapest remaining collapse's quadric cost exceeds a
budget derived from the Hausdorff limit:

    eps      = frac * 0.05 * diagonal     (frac = 0.5)
    max_cost = eps^2
    Decimate(target_count = 1, max_cost)  // collapse as far as the budget allows

Adaptive per mesh, computed entirely in C++ from the input's AABB diagonal.

## Judge result

- **2 / 7 test cases passed** — a regression from v1.
- **Test 1 (SAMPLE) PASSED** — now stops at 8 vertices (removes only the
  redundant coplanar vertex), 11.11% compression. The v1 failure is fixed.
- **Secret 1 / 6 passed** — the one mesh flat enough to tolerate ~99% compression.
- **5 secret FAILED** — *"Wrong Answer: too much geometric deviation."*
- **Score = 16.516187 / 100** (the single passing secret case at ~99%, averaged
  over the 6 secret cases).

## Takeaway

The quadric cost is **not** a bound on the true point-to-surface Hausdorff: it
measures distance to infinite *planes* (not bounded triangles), it is an
*average* of squared distances (not the *max*), and it ignores the coverage
direction. So `frac = 0.5` over-compressed to ~99% and blew the deviation limit
on 5 of 6 meshes.

Full analysis: `docs/theory/qem-cost-is-not-hausdorff.md`. Next direction: a
**true point-to-surface deviation guard** during decimation. Best real score so
far remains **v1 (~50)**.
