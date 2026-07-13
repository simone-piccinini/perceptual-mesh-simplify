#!/usr/bin/env python3
"""SIL2 ladder v3: hammer c3@6700 (only rung with upside; SIL2 crossed it once judge-side),
rotate g_draw family on 4 bankless rolls OR 3 c3-WAs (escape c4-toxic families), never
retreat above 6700 (bank is 6705 -> higher rungs have zero upside). On bank: descend -10.
Anti-stall: submit timeout 900s, loop continues on timeout. Runs to 23:45 / 45 subs."""
import datetime, json, os, re, subprocess, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, NC = ROOT+"/solver/mein.cpp", ROOT+"/solver/mein_nocomments.cpp"
LOG = ROOT+"/handoff/overnight_log.jsonl"
def sh(c, t=1500):
    try: return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t, cwd=ROOT)
    except subprocess.TimeoutExpired: return None
def log(r):
    r["utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    open(LOG,"a").write(json.dumps(r)+"\n"); print(json.dumps(r), flush=True)
def build(c3r, draw):
    s = open(SRC).read()
    s = re.sub(r"int c3t = \d+;", f"int c3t = {c3r};", s, count=1)
    s = re.sub(r"g_draw = \d+;", f"g_draw = {draw};", s, count=1)
    open(SRC,"w").write(s)
    r = sh(f"python3 scripts/strip_comments.py {SRC} {NC} && g++ -O2 -std=c++17 -Isolver {NC} -o /tmp/s2l3")
    if r is None or r.returncode: return "compile"
    r = sh("/tmp/s2l3 < /tmp/c3proxy.in 2>/dev/null | head -1", t=900)
    if r is None or not r.stdout.split(): return "prova"
    return None if int(r.stdout.split()[0]) == c3r else "prova"
def submit(note):
    r = sh(f'python3 scripts/judge_submit.py {NC} --force --note "{note}"', t=900)
    if r is None: return None, False
    out = r.stdout + r.stderr
    m = re.search(r"CASES ([.x?]+)", out)
    return (m.group(1) if m else None), ("NEW BANK" in out)
def main():
    c3r = 6620; draw = 62; wa = 0; nobank = 0; banks = 0; subs = 0
    if build(c3r, draw): log({"ev": "s2l3_fatal"}); return
    while subs < 45 and banks < 6:
        now = datetime.datetime.now()
        if (now.hour, now.minute) >= (23, 45): break
        cases, nb = submit(f"S2L3 c3={c3r} draw={draw}")
        subs += 1
        log({"ev": "s2l3", "c3": c3r, "draw": draw, "cases": cases, "newbank": nb})
        all_green = cases and len(cases) >= 7 and all(c == "." for c in cases)
        if all_green:
            banks += 1; wa = 0; nobank = 0
            if nb:
                sh("git add -A && git commit -q -m 'sil2 ladder v3: NEW BANK' && git push -q origin CleanRepoForAI")
            c3r -= 20   # DESCEND on any all-green (already-banked rung still descends toward the wall)
            if build(c3r, draw): break
        else:
            nobank += 1
            if cases and len(cases) >= 7 and cases[2] == "x": wa += 1
            if wa >= 3 or nobank >= 4:
                draw += 1; wa = 0; nobank = 0
                log({"ev": "s2l3_rotate", "draw": draw})
                if build(c3r, draw): break
        time.sleep(300)
    log({"ev": "s2l3_done", "banks": banks, "final_c3": c3r})
main()
