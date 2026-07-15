#!/usr/bin/env bash
# MINI-16 K-READ PAIR — the judge test for the zoo's surviving winner (polish cap 8->16).
#
# WHAT: two submissions differing ONLY in the c3 mini_refine iteration cap (8 = banked control,
# 16 = variant), both with the c3 K-read enabled at the DEFAULT safe rung (c3t 6670, passes).
# Decode: K=(V'-out)/4, S2=0.885+5e-4*(K%40); dS2 = (K_var-K_ctrl)%40 * 5e-4 on the REAL c3 mesh.
# Local evidence [zoo, sign-validated instrument]: +0.0014 @6610 -> +0.0026 @6500 (grows below the
# wall), ~zero time cost (bounded by the existing 1.2s repair budget), matches M0's +4.3e-3 ceiling.
#
# MODES: default = PREPARE ONLY (writes the two stripped sources + compile-checks; submit is the
# team's call).  --submit = actually submit both via judge_submit.py with campaign-lock waits.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
OUT="$ROOT/zoo/build"; mkdir -p "$OUT"
CAP_ANCHOR='<= 30000) ? 8 : (1<<30);'
for CFG in ctrl mini16; do
  git checkout -- solver/mein.cpp
  sed -i "s/const int kread = 0;/const int kread = 1;/" solver/mein.cpp
  [ "$CFG" = "mini16" ] && sed -i "s/<= 30000) ? 8 : (1<<30);/<= 30000) ? 16 : (1<<30);/" solver/mein.cpp
  grep -q "kread = 1" solver/mein.cpp || { echo "PATCH FAILED (kread)"; exit 1; }
  py -3 scripts/strip_comments.py solver/mein.cpp "$OUT/mein_read_${CFG}.cpp"
  bash scripts/winbuild.sh "$OUT/read_${CFG}.exe" "$OUT/mein_read_${CFG}.cpp"
  echo "prepared $OUT/mein_read_${CFG}.cpp (compile OK)"
  if [ "$1" = "--submit" ]; then
    while [ -f handoff/.judge_lock ]; do echo "campaign lock; waiting 60s"; sleep 60; done
    py -3 scripts/judge_submit.py "$OUT/mein_read_${CFG}.cpp" \
        --note "MINI16 read pair (${CFG}): polish cap 8 vs 16 @c3t6670 - does the zoo's +0.0014/+0.0026 transfer?"
    [ "$CFG" = "ctrl" ] && sleep 260
  fi
done
git checkout -- solver/mein.cpp
echo "PAIR READY. Decode: dS2 = (K_mini16 - K_ctrl) * 5e-4 (K from V' = out_v + 4K; same-rung pair)"
