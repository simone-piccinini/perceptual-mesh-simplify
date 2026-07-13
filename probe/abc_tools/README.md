# ABC-dataset c4 proxy extraction — verified pipeline

STATE: 2026-07-13. Purpose: build a **calibrated c4 local proxy** — real watertight genus-0 CAD
parts at the c4 vertex band (30–40k) — because the synthetic `probe/cache/c4band.obj` (fandisk
union) is unfaithful (collapses freely, SSIM-saturated at 0.9999, two-component Hausdorff artifact).

## Environment facts (verified this machine, 2026-07-13)
- `wget` is NOT installed → use **curl**.
- ABC index path is `…/abc-dataset/**data**/…`, NOT `/v00/` (that 404s).
- Chunks are **`.7z`** (not `.tar.gz`) served from `archive.nyu.edu` → need **7-Zip**
  (`winget install 7zip.7zip`; `7z.exe` at `C:\Program Files\7-Zip\`).
- Index line = 2 cols: `<https://archive.nyu.edu/rest/bitstreams/ID/retrieve>  <name.7z>`.
- **Disk:** C: was full (1.3 GB free); the obj chunk is **7.5 GB (73 GB uncompressed)** → download
  to **E:** (or any drive with ~10 GB free). This is the #1 gotcha.
- stat `.yml` keys are **quoted**: `'#verts'`, `'#parts'`, `'#sharp'`, plus `surfs:` (Plane/Cylinder/
  Sphere/Cone/Torus) and `curves:` — no direct genus/watertight field → check those on the MESH.

## Pipeline
```bash
Z="/c/Program Files/7-Zip/7z.exe"; PY=<python3.11>
# 1. indexes
curl -sSL -o stat_v00.txt https://deep-geometry.github.io/abc-dataset/data/stat_v00.txt
curl -sSL -o obj_v00.txt  https://deep-geometry.github.io/abc-dataset/data/obj_v00.txt
# 2. stat chunk 0 (1.7 MB) -> yml
read U N < <(sed -n '1p' stat_v00.txt); curl -sSL -o "$N" "$U"; "$Z" x "$N" -oabc_stats -y
# 3. filter: #verts in [30k,40k] AND #parts==1, ranked by #sharp -> cand_top.txt (top 40)
$PY abc_stat_filter.py abc_stats           # writes cand_ids.txt (all) ; see script for cand_top
# 4. obj chunk 0 (7.5 GB!) -> E:, extract only candidates
read OU ON < <(sed -n '1p' obj_v00.txt); curl -fSL --retry 3 -o /e/abc_work/"$ON" "$OU"
"$Z" t /e/abc_work/"$ON"                    # MUST verify: "Everything is Ok" (truncated = disk full)
cd /e/abc_work; INCL=(); while read id; do INCL+=("-ir!*${id}*.obj"); done < cand_top.txt
"$Z" x "$ON" -oabc_obj "${INCL[@]}" -y
# 5. authoritative mesh filter: watertight + genus-0 (Euler) + 30-40k -> solver "NV NF" format
$PY abc_filter.py abc_obj c4_proxies
```

## Yield (chunk 0, top-40-by-#sharp)
- 7,168 models in the stat chunk; **227** are #verts∈[30k,40k] & single-part.
- Of the top-40 by #sharp: **all 40 watertight** (ABC "trimesh" objs are closed), **6 genus-0**
  (34 rejected = have holes → genus≥1, correct to exclude for c4's genus-0).

## Calibration (Step 6) — acceptance = reproduce the judge's c4 wall
The topological-floor test is NOT discriminating (unbounded flip/vertex-remove collapse everything
to ~150; the real wall is quality, not a jam — confirmed 2026-07-13). The discriminating signal is
**rendered-normal/depth SSIM at the c4 rung (RC4)**: the fandisk sat at 0.9999 (saturated, useless
for A/B); a real CAD part must show a gradient. First result (00001680 @N=4920): **S2n=0.997 /
S2d=0.967 / S2=0.982** — not saturated, depth channel carries the signal ⇒ already a better c4
instrument. Ranking the family by difficulty (lowest S2 = closest to the judge wall) — see
`c4_ssim_test.log` / STATUS when complete.

Scripts: `abc_stat_filter.py` (stat pre-filter), `abc_filter.py` (mesh watertight/genus/convert).
