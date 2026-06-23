#!/usr/bin/env bash
# One-command setup for the IMC mesh-simplify project.
#
# Builds both halves and verifies them:
#   - Python oracle  : .venv with numpy/scipy (+ numba where available)
#   - C++ solver     : Eigen vendored next to main.cpp, main.cpp compiled
# then runs the oracle self-check (identity + sample) so you know it works.
#
# Usage:
#   ./scripts/setup.sh
#
# Supports macOS (Homebrew) and Linux (apt-provided Eigen).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

say() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }

# --- 0. prerequisites -------------------------------------------------------
say "Checking prerequisites"
OS="$(uname -s)"
command -v python3 >/dev/null || { echo "ERROR: python3 not found"; exit 1; }
CXX="${CXX:-g++}"
command -v "$CXX" >/dev/null 2>&1 || CXX=clang++
command -v "$CXX" >/dev/null 2>&1 || {
  echo "ERROR: no C++ compiler (macOS: xcode-select --install)"; exit 1; }
echo "python3 : $(python3 --version)"
echo "compiler: $($CXX --version | head -1)"

# --- 1. Python oracle environment ------------------------------------------
say "Python oracle (.venv)"
[ -d .venv ] || python3 -m venv .venv
./.venv/bin/python -m pip install -q -U pip
./.venv/bin/python -m pip install -q -e .
echo "installed:"
./.venv/bin/python -m pip list 2>/dev/null | grep -Ei 'numpy|scipy|numba' || true

# --- 2. Eigen for the C++ solver -------------------------------------------
say "Eigen (vendored next to solver/main.cpp)"
EIGEN_DIR=""
if [ "$OS" = "Darwin" ]; then
  command -v brew >/dev/null || { echo "ERROR: Homebrew required (https://brew.sh)"; exit 1; }
  brew list eigen >/dev/null 2>&1 || brew install eigen
  EIGEN_DIR="$(brew --prefix eigen)/include/eigen3/Eigen"
else
  for cand in /usr/include/eigen3/Eigen /usr/local/include/eigen3/Eigen; do
    [ -d "$cand" ] && EIGEN_DIR="$cand" && break
  done
  [ -n "$EIGEN_DIR" ] || {
    echo "ERROR: Eigen not found. Debian/Ubuntu: sudo apt-get install libeigen3-dev"; exit 1; }
fi
ln -sfn "$EIGEN_DIR" solver/Eigen
echo "vendored: solver/Eigen -> $EIGEN_DIR"

# --- 3. build the solver ----------------------------------------------------
say "Build solver/main.cpp"
"$CXX" -O2 -std=c++17 solver/main.cpp -o solver/main
echo "built: solver/main"

# --- 4. verify --------------------------------------------------------------
say "Verify"
./solver/main; echo "solver/main ran (exit $?)"
./.venv/bin/python scripts/validate_oracle.py

say "Setup complete"
cat <<'EOF'
Try it:
  source .venv/bin/activate
  imc-score --input tests/data/sample.in --output tests/data/sample.out
  g++ -O2 -std=c++17 solver/main.cpp -o solver/main
EOF
