#!/bin/zsh
# Overnight LOCAL sweep: CTAIL grid on c3 + c5-tail probe. Unlimited (no judge).
# Results in handoff/local_sweep.log — one line per config: params, S2n, CPU.
cd "$(dirname "$0")/.."
BIN=/tmp/sweep_bin
LOG=handoff/local_sweep.log
g++ -O2 -std=c++17 -Isolver solver/mein_nocomments.cpp -o $BIN || exit 1
echo "=== sweep start $(date) ===" >> $LOG

# grid: tail T x candidates K x rung
for T in 60 100 140 200 300; do
  for K in 48 64 96; do
    for N in 6805 6790 6775 6760; do
      out=$(G_REMESH=1 G_S2=1 G_CT=$T G_CTK=$K G_C3T=$N $BIN < /tmp/c3proxy.in 2>&1 >/dev/null | grep RC3)
      cpu=$(echo $out | grep -o 't=[0-9.]*')
      s2n=$(echo $out | grep -o 'S2n=[0-9.]*')
      echo "c3 T=$T K=$K N=$N $s2n $cpu" >> $LOG
    done
  done
done

# c5 tail probe (never tested: c5 is organic like c3)
for T in 0 40 80; do
  for N in 4165 4155 4145; do
    out=$(G_C4CT=0 G_C5CT=$T G_C5T=$N $BIN < /tmp/clean.in 2>&1 >/dev/null | grep 'RL ')
    echo "c5 T=$T N=$N $out" >> $LOG
  done
done
echo "=== sweep end $(date) ===" >> $LOG
