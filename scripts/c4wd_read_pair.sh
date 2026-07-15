#!/usr/bin/env bash
# C4 DEPTH-REFINE K-READ PAIR (G_WD mechanism, 2026-07-15) — one question:
#   does adding the depth-SSIM term to the c4 refine gradient (wd=0.5 joint Pareto ascent)
#   raise the BLENDED self-score S2 on the REAL judge c4 mesh?
#
# CONTEXT: c4's refine has always ascended the NORMAL gradient only (depth enters only via accept).
#   zpres [JUDGE 20038774] killed a normal-SACRIFICING depth trade; decimation-time depth mechanisms
#   are dead [C4-CALIBRATION]. This is the untested corner: joint proposal along (1-wd)*gN + wd*gD,
#   monotonic accept on the true blend. Local c4 refine CANNOT run on the dev box (the r_elapsed>6s
#   TLE guard skips refine on throttled CPUs — measured 2026-07-15) — the judge read IS the measurement.
#
# BASE: origin/CleanRepoForAI team HEAD + the G_WD mechanism ported (patch_wd_team.py in the session
#   scratchpad; fork-based arms risk the v1 mini16 compile-OOM — team HEAD is the proven-compiling base).
#   Both arms: c4 rung 4930 -> 4980 (SAFE: harvest wall (4960,4970]) + c4 pads encode BLENDED S2.
#   Variant arm only: g_wd_c4 0.0 -> 0.5 (band-gated inside blended_sg; judge has no env).
#   NOTE both arms share the c4 refine budget 10.5s/24 iters; the wd arm's ~2x per-iter cost may
#   budget-cut it earlier — the read then measures the SHIPPED form (single-diff discipline).
# DECODE: K = (V'_c4 - 4980)/4;  S2_c4 = 0.885 + K*5e-4;  dS2 = (K_wd - K_ctrl)*5e-4.
#   'x' on c4: classify WA vs TLE from casetimes before concluding (opposite remedies).
#
# MODES: default = prepare + compile-check only.  --submit = submit both (campaign-lock aware).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
OUT="$ROOT/zoo/build"; mkdir -p "$OUT"
RUNG="${RUNG:-4980}"
PATCHED="${PATCHED:?set PATCHED=/path/to/patched team_head.cpp (patch_wd_team.py output)}"
grep -q "blended_sg" "$PATCHED" || { echo "PATCHED source lacks the mechanism"; exit 1; }
for CFG in c4ctrl c4wd; do
  SRC="$OUT/${CFG}.cpp"
  cp "$PATCHED" "$SRC"
  # both arms: safe c4 rung + unconditional blended-S2 pad encoding on the c4 output
  sed -i "s/int c4t = 4930;/int c4t = ${RUNG};/" "$SRC"
  sed -i 's|const long K = 0;   // BANK-TWIN-C4 of read 19898354 (S=0.9055): pads stripped|const long K = std::lround(std::max(0.0, std::min(160.0, (S2 - 0.885) / 5e-4)));   // C4WD read: pads encode blended S2|' "$SRC"
  grep -q "int c4t = ${RUNG};" "$SRC" || { echo "PATCH FAILED (rung)"; exit 1; }
  grep -q "(S2 - 0.885) / 5e-4" "$SRC" || { echo "PATCH FAILED (c4 S2 encoding)"; exit 1; }
  if [ "$CFG" = "c4wd" ]; then
    sed -i "s/static double g_wd_c4 = 0.0;/static double g_wd_c4 = 0.5;/" "$SRC"
    grep -q "g_wd_c4 = 0.5;" "$SRC" || { echo "PATCH FAILED (wd)"; exit 1; }
  fi
  py -3 scripts/strip_comments.py "$SRC" "$OUT/${CFG}_nc.cpp"
  SZ=$(wc -c < "$OUT/${CFG}_nc.cpp")
  [ "$SZ" -le 131072 ] || { echo "SIZE FAIL ${SZ} > 128KiB"; exit 1; }
  bash scripts/winbuild.sh "$OUT/${CFG}.exe" "$OUT/${CFG}_nc.cpp"
  echo "prepared ${CFG}_nc.cpp (${SZ} bytes, compile OK)"
  if [ "$1" = "--submit" ]; then
    while [ -f handoff/.judge_lock ]; do echo "campaign lock; waiting 60s"; sleep 60; done
    py -3 scripts/judge_submit.py "$OUT/${CFG}_nc.cpp" \
        --note "C4WD read pair (${CFG}): depth-SSIM term in c4 refine gradient wd=0.5 vs 0, team-HEAD base, rung ${RUNG}, c4 pads=blended S2 - dS2=dK*5e-4"
    [ "$CFG" = "c4ctrl" ] && sleep 260
  fi
done
echo "PAIR DONE. Decode: K = (V'_c4 - ${RUNG})/4; S2 = 0.885 + K*5e-4; dS2 = dK*5e-4"
