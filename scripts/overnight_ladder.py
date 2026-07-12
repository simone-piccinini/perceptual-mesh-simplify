#!/usr/bin/env python3
"""Overnight autonomous c3 bank-ladder with adaptive K-reads and toxic-draw detection.

Loop: patch c3t/kread in solver/mein.cpp -> strip -> compile -> prova-del-nove -> submit --force
-> parse verdict -> decide (descend on bank / re-roll on coin / read on repeated c3-fail / back off
on toxic draws). Stops at --deadline or --max-subs. State + every verdict in overnight_log.jsonl.

Only touches c3t (and kread for reads). c4/c5/c2/c6/c7 stay at the banked config in the file.
"""
import argparse, datetime, json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "solver/mein.cpp")
NC  = os.path.join(ROOT, "solver/mein_nocomments.cpp")
LOG = os.path.join(ROOT, "handoff/overnight_log.jsonl")
BANKED_SUM = 542.423046 + (100*(1-6805/23201) - 100*(1-6830/23201)) \
             + (100*(1-4172/49987) - 100*(1-4165/49987))  # c5 moved 4165->4172 (tail-off insurance, 2026-07-12 night)
C3_V = 23201

def sh(cmd, timeout=1200):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=ROOT)

def log(rec):
    rec["utc"] = datetime.datetime.utcnow().isoformat()
    with open(LOG, "a") as f: f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec), flush=True)

def patch_build(n, kread):
    s = open(SRC).read()
    s = re.sub(r"int c3t = \d+;", f"int c3t = {n};", s, count=1)
    s = re.sub(r"const int kread = \d;", f"const int kread = {kread};", s, count=1)
    open(SRC, "w").write(s)
    r = sh(f"python3 scripts/strip_comments.py {SRC} {NC} && g++ -O2 -std=c++17 -Isolver {NC} -o /tmp/onight")
    if r.returncode != 0: return False, "compile: " + r.stderr[:200]
    r = sh("G_REMESH=1 /tmp/onight < /tmp/c3proxy.in 2>/dev/null | head -1", timeout=600)
    v = r.stdout.split()
    if not v: return False, "no output"
    got = int(v[0])
    exp = n if kread == 0 else None   # kread pads by 4K (unknown K) - just check >= n
    if kread == 0 and got != n: return False, f"prova-del-nove: got {got} expected {n}"
    if kread == 1 and got < n: return False, f"read prova: got {got} < {n}"
    return True, got

def submit(note):
    r = sh(f'python3 scripts/judge_submit.py {NC} --force --note "{note}"', timeout=1200)
    out = r.stdout + r.stderr
    score = None; cases = None; times = {}
    m = re.search(r"SCORE ([\d.]+)", out)
    if m: score = float(m.group(1))
    m = re.search(r"CASES ([.x]+)", out)
    if m: cases = m.group(1)
    for mm in re.finditer(r"CASETIME (\d) ~([\d.]+)s", out):
        times[mm.group(1)] = float(mm.group(2))
    newbank = "NEW BANK" in out
    return score, cases, times, newbank, out[-400:]

def toxic(times):
    if not times: return True
    c2 = times.get("2", 0); c6 = times.get("6", 0); c3 = times.get("3", 0)
    return (c2 and c2 > 12) or (c6 and c6 > 26) or (c3 and c3 > 22.5) or len(times) < 7

def decode_read(score, n):
    c3b = 100*(1 - 6805/C3_V)
    resid = 6*score - BANKED_SUM
    c3read = c3b + resid
    vp = C3_V*(1 - c3read/100)
    k = round((vp - n)/4)
    return k, 0.885 + k*5e-4

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=6790)
    ap.add_argument("--step", type=int, default=15)
    ap.add_argument("--max-subs", type=int, default=130)
    ap.add_argument("--deadline", default="06:30")
    args = ap.parse_args()

    n = args.start; subs = 0; c3fails = 0; floor_hit = False
    dl_h, dl_m = map(int, args.deadline.split(":"))
    while subs < args.max_subs:
        now = datetime.datetime.now()
        if (now.hour, now.minute) >= (dl_h, dl_m) and now.hour < 12:
            log({"ev": "deadline"}); break
        ok, info = patch_build(n, 0)
        if not ok:
            log({"ev": "build_fail", "n": n, "info": str(info)}); break
        score, cases, times, newbank, tail = submit(f"LADDER n={n} sub#{subs}")
        subs += 1
        rec = {"ev": "sub", "n": n, "score": score, "cases": cases, "times": times, "newbank": newbank}
        log(rec)
        if score is None or toxic(times):
            log({"ev": "toxic_or_err", "sleep": 600}); time.sleep(600); continue
        if newbank:
            c3fails = 0
            sh(f"cd {ROOT} && git add -A && git commit -q -m 'overnight: NEW BANK at c3={n}' && git push origin CleanRepoForAI")
            n -= args.step
            time.sleep(270); continue
        c3x = cases and cases[2] == "x"
        if c3x:
            c3fails += 1
            if c3fails >= 3:
                # adaptive read at this rung
                ok, _ = patch_build(n, 1)
                if ok:
                    score2, cases2, times2, _, _ = submit(f"LADDER-READ n={n}")
                    subs += 1
                    if score2 and cases2 and cases2[2] == ".":
                        k, s2 = decode_read(score2, n)
                        log({"ev": "read", "n": n, "K": k, "S2": s2})
                        if s2 < 0.9135:
                            n += 10; log({"ev": "backoff", "n": n})
                    c3fails = 0
                time.sleep(270); continue
        else:
            c3fails = 0
        time.sleep(270)
    log({"ev": "done", "subs": subs, "final_n": n})

if __name__ == "__main__":
    main()
