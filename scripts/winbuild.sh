#!/usr/bin/env bash
# Stable fast local build (Windows/mingw). No scratchpad deps.
#   Eigen -> .phase0/eigen (provide once; override with $EIGEN). Shim -> winbuild/ (tracked).
#   usage: bash scripts/winbuild.sh [out.exe] [src.cpp]
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EIGEN="${EIGEN:-$ROOT/.phase0/eigen}"
OUT="${1:-/tmp/mein.exe}"; SRC="${2:-$ROOT/solver/mein.cpp}"
WINLIBS="/c/Users/simon/AppData/Local/Microsoft/WinGet/Packages/BrechtSanders.WinLibs.POSIX.UCRT.LLVM_Microsoft.Winget.Source_8wekyb3d8bbwe/mingw64/bin"
[ -d "$WINLIBS" ] && export PATH="$WINLIBS:$PATH"
[ -d "$EIGEN" ] || { echo "EIGEN not found at $EIGEN (set \$EIGEN)"; exit 1; }
# -O2 ONLY: -O3/-march=native/-funroll-loops change float order enough to FLIP the sign of small
# mechanism A/Bs (measured 2026-07-14: alpha=1 on 00005934 = +0.054 at -O2 but -0.036 at -O3-native)
# and diverge from the judge's numerical family. Speed comes from PARALLELISM (fast_sweep.sh), not flags.
"${CXX:-g++}" -O2 -std=c++17 -I"$ROOT/winbuild" -I"$EIGEN" "$SRC" -o "$OUT"
echo "built $OUT (-O2, judge-matching family)"
