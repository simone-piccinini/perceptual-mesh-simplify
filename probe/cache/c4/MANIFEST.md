# Calibrated c4 proxy family (ABC dataset, 2026-07-13)

Real watertight genus-0 CAD parts (ABC chunk 0), replacing the unfaithful fandisk-union
`c4band.obj`. RC4 = solver rendered SSIM self-score at the natural c4 keep (N~4920). Judge c4
passes at ~0.90 near this rung, so meshes with S2 ~0.85-0.95 REPRODUCE the wall (the fandisk sat
at 0.9999 = useless for A/B). KEY: the loss is in the DEPTH channel (S2d), not normals (S2n) —
the c4 wall is depth-SSIM.

| file | in verts | out N | S2n | S2d | S2 | role |
|------|---------|-------|-----|-----|-----|------|
| 00004867.obj | 39805 | 4920 | 0.741 | 0.752 | 0.747 | hard bracket (below wall) |
| 00005934.obj | 37753 | 4920 | 0.973 | 0.734 | 0.854 | WALL-REGION (primary) |
| 00009281.obj | 33970 | 4851 | 0.973 | 0.924 | 0.949 | WALL-REGION (primary) |
| 00001680.obj | 39349 | 4920 | 0.997 | 0.967 | 0.982 | easy control (mild gradient) |

Rejected: 00002643 (S2=0.994, saturated like fandisk); 00007719 (solver produced no output).
Extract more via probe/abc_tools/ (df: needs a drive with ~10 GB free; the obj chunk is 7.5 GB).

## Phase 3 finding (2026-07-13): depth-aware DECIMATION is inert for c4
Implemented an env-gated depth penalty (`G_ZPEN`: defer collapses that flatten distinct-Z
features, edge-normalized) and subset placement (`G_SUBSET`: keep xbar on a real depth level).
A/B on the wall-region proxies (00005934 S2d=0.734, 00009281 S2d=0.924):

| mesh | baseline S2d | +G_ZPEN(3,8) | +G_SUBSET |
|------|-------------|--------------|-----------|
| 00005934 | 0.734167 | 0.734167 (identical) | 0.734167 (identical) |
| 00009281 | 0.924041 | 0.924041 (identical) | 0.924041 (identical) |

**Byte-identical S2d — both levers inert.** Principled reason: (1) QEM ordering already collapses
flat regions first and preserves feature vertices, so a "defer feature-collapse" penalty duplicates
it; (2) the c4 pipeline runs refine AFTER decimation, which re-optimizes positions to the same
convergent optimum, washing out placement changes. ⇒ **c4 depth-SSIM at the rung is bounded by the
compression ratio + refine convergence, NOT by decimation logic.** The depth-penalty mechanism class
is dead for c4. Target S2d>=0.90 on the hard brackets (00004867 0.75 / 00005934 0.73) is a physical
frontier of 85%-compression on those meshes, not a tuning target. A real c4 lever would have to be
allocation (vertex budget across the mesh) or a different representation — not a collapse penalty.
