#!/usr/bin/env bash
# Parallel local c4 A/B sweep on a multi-core box. ~1 slow-run of wall time per wave, not the sum.
#   usage: bash scripts/fast_sweep.sh "0 1.0 2.0" [workers]   (BIN=/path overrides the binary)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
BIN="${BIN:-/tmp/mein.exe}"; ALPHAS="${1:-0 1.0}"; W="${2:-5}"
[ -x "$BIN" ] || bash scripts/winbuild.sh "$BIN"
OUT="$(mktemp)"; : > "$OUT"
job(){ local m=$1 a=$2
  local rc=$(G_ALLOC_WEIGHT=$a "$BIN" < "probe/cache/c4/$m.obj" 2>&1 >/dev/null | grep -o 'S2d=[0-9.]* S2=[0-9.]*')
  printf '%-9s a=%-5s %s\n' "$m" "$a" "$rc" >> "$OUT"; }
n=0
for m in $(ls probe/cache/c4/*.obj | xargs -n1 basename | sed 's/\.obj//'); do
  for a in $ALPHAS; do job "$m" "$a" & n=$((n+1)); [ $((n % W)) -eq 0 ] && wait; done
done
wait; sort "$OUT"; rm -f "$OUT"
