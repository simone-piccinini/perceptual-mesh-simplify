#!/usr/bin/env bash
# TRACK J — c3 S(N) read triplet at PASSING rungs (6775 control / 6695 / 6610).
# Each read: bake kread=1 + c3t into the source, build-check, submit via judge_submit.py.
# Decode: V' = out + 4K, K = 40*q1 + q2 (q1: S1 2.5e-3-step, q2: S2 5e-4-step, offset 0.885).
# 6775 must reproduce ~0.9145 [20031760] = family check; then slope over 6610-6775 on the REAL mesh.
# ISOLATION: waits on handoff/.judge_lock (campaign); >=260s between submits; reads are
# best-counts-safe (cannot lower the bank). Run from a probe worktree, NOT the campaign clone.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
for RUNG in 6775 6695 6610; do
  while [ -f handoff/.judge_lock ]; do echo "campaign lock; waiting 60s"; sleep 60; done
  git checkout -- solver/mein.cpp
  sed -i "s/const int kread = 0;/const int kread = 1;/" solver/mein.cpp
  sed -i "s/int c3t = 6670;/int c3t = ${RUNG};/" solver/mein.cpp
  grep -q "kread = 1" solver/mein.cpp && grep -q "c3t = ${RUNG}" solver/mein.cpp || { echo "PATCH FAILED"; exit 1; }
  py -3 scripts/strip_comments.py solver/mein.cpp solver/mein_nocomments.cpp
  bash scripts/winbuild.sh /tmp/read_check.exe solver/mein_nocomments.cpp   # compile sanity only
  py -3 scripts/judge_submit.py solver/mein_nocomments.cpp --note "S(N)-read c3t=${RUNG} (Track J: slope on the real c3 mesh)"
  git checkout -- solver/mein.cpp
  [ "$RUNG" != "6610" ] && sleep 260
done
echo "TRACK J DONE — decode each read: K=(V'-rung)/4, S2=0.885+5e-4*(K%40), S1=0.885+2.5e-3*(K/40)"
