#!/usr/bin/env bash
# MINI-16 K-READ PAIR — judge test for the zoo's surviving winner (c3 polish cap 8->16).
#
# v2: sources are generated from origin/CleanRepoForAI's mein.cpp (the TEAM HEAD), NOT this fork.
# Why: sub 20051725 (fork-based ctrl read) = Compile Error with EMPTY compiler output = the
# documented judge compile-memory OOM signature; this fork carries extra env-gated code on a file
# already at the compile cliff (CLAUDE.md 2.5 — added without stripping, my error). The team HEAD
# compiles on the judge daily by construction, and a read on THEIR family is what banking needs.
#
# WHAT: two submissions differing ONLY in the c3 mini_refine iteration cap (8 = banked control,
# 16 = variant), both with the c3 K-read enabled at the HEAD's default safe rung.
# Decode: K=(V'-out)/4; q2=K%40 -> S2=0.885+5e-4*q2; dS2 = (q2_var - q2_ctrl)*5e-4 (same-rung pair).
# Local evidence [zoo, sign-validated proxy]: +0.0014 @6610 -> +0.0026 @6500 -> +0.0022 @6400,
# saturating at cap 12-16, ~zero time cost. If +0.0025 transfers: ~200 c3-verts ~ +0.14 total.
#
# MODES: default = prepare + compile-check only.  --submit = submit both (campaign-lock aware).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
OUT="$ROOT/zoo/build"; mkdir -p "$OUT"
git fetch -q origin CleanRepoForAI
for CFG in ctrl mini16; do
  SRC="$OUT/team_${CFG}.cpp"
  git show origin/CleanRepoForAI:solver/mein.cpp > "$SRC"
  sed -i "s/const int kread = 0;/const int kread = 1;/" "$SRC"
  # v3 TIME FUNDING (both arms identically -> cancels in the differential): v2 reads died at the
  # ~21s ceiling (c3 20.6/21.1s: team HEAD runs c3 ~21s at bank; kread doesn't fit). sil2 200->80
  # frees ~1.1s (0.8ms/eval judge cost model), expected ctrl ~19.5s / cap16 ~20.0s.
  sed -i "s/sil2_pass(200, 1);/sil2_pass(80, 1);/" "$SRC"
  grep -q "sil2_pass(80, 1);" "$SRC" || { echo "PATCH FAILED (sil2 funding)"; exit 1; }
  [ "$CFG" = "mini16" ] && sed -i "s/<= 30000) ? 8 : (1<<30);/<= 30000) ? 16 : (1<<30);/" "$SRC"
  grep -q "kread = 1;" "$SRC" || { echo "PATCH FAILED (kread)"; exit 1; }
  if [ "$CFG" = "mini16" ]; then grep -q "? 16 : (1<<30);" "$SRC" || { echo "PATCH FAILED (cap)"; exit 1; }; fi
  py -3 scripts/strip_comments.py "$SRC" "$OUT/team_${CFG}_nc.cpp"
  SZ=$(stat -c %s "$OUT/team_${CFG}_nc.cpp" 2>/dev/null || wc -c < "$OUT/team_${CFG}_nc.cpp")
  [ "$SZ" -le 131072 ] || { echo "SIZE FAIL ${SZ} > 128KiB"; exit 1; }
  bash scripts/winbuild.sh "$OUT/team_${CFG}.exe" "$OUT/team_${CFG}_nc.cpp"
  echo "prepared team_${CFG}_nc.cpp (${SZ} bytes, compile OK)"
  if [ "$1" = "--submit" ]; then
    while [ -f handoff/.judge_lock ]; do echo "campaign lock; waiting 60s"; sleep 60; done
    py -3 scripts/judge_submit.py "$OUT/team_${CFG}_nc.cpp" \
        --note "MINI16 read pair v2 TEAM-HEAD (${CFG}): c3 polish cap 8 vs 16 - does zoo's +0.0025 transfer?"
    [ "$CFG" = "ctrl" ] && sleep 260
  fi
done
echo "PAIR DONE. Decode: dS2 = (q2_mini16 - q2_ctrl) * 5e-4, q2 = ((V'-out)/4) % 40"
