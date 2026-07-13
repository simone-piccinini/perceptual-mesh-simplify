#!/usr/bin/env python3
"""Morning campaign 13/07: harvest c3@6705 (passes 80%) blocked by a toxic c4 family coin.
Rotate g_draw (fresh binary family = fresh box-cut coin) every 6 bankless rolls; adaptive c3."""
import datetime, json, os, re, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "solver/mein.cpp")
NC  = os.path.join(ROOT, "solver/mein_nocomments.cpp")
LOG = os.path.join(ROOT, "handoff/overnight_log.jsonl")

def sh(cmd, timeout=1500):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=ROOT)

def log(rec):
    rec["utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(LOG, "a") as f: f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec), flush=True)

def patch(pairs):
    s = open(SRC).read()
    for rx, rep in pairs:
        s = re.sub(rx, rep, s, count=1)
    open(SRC, "w").write(s)

def build(c3r):
    r = sh(f"python3 scripts/strip_comments.py {SRC} {NC} && g++ -O2 -std=c++17 -Isolver {NC} -o /tmp/morn")
    if r.returncode != 0: return "compile"
    r = sh(f"/tmp/morn < /tmp/c3proxy.in 2>/dev/null | head -1", timeout=900)
    if not r.stdout.split() or int(r.stdout.split()[0]) != c3r: return "prova"
    return None

def submit(note):
    r = sh(f'python3 scripts/judge_submit.py {NC} --force --note "{note}"', timeout=1500)
    out = r.stdout + r.stderr
    cases = None
    m = re.search(r"CASES ([.x?]+)", out)
    if m: cases = m.group(1)
    return cases, ("NEW BANK" in out)

def deadline():
    now = datetime.datetime.now()
    return (now.hour, now.minute) >= (8, 45) and now.hour < 12

def main():
    c3r = 6705; draw = 42; nobank = 0; banks = 0; c3f = 0
    patch([(r"int c3t = \d+;", f"int c3t = {c3r};"), (r"int c4t = \d+;", "int c4t = 4920;"),
           (r"g_draw = \d+;", f"g_draw = {draw};")])
    if build(c3r): log({"ev": "m_buildfail"}); return
    while not deadline() and banks < 3:
        cases, nb = submit(f"MORNING c3={c3r} c4=4920 draw={draw}")
        log({"ev": "m_roll", "c3": c3r, "draw": draw, "cases": cases, "newbank": nb})
        if nb:
            banks += 1; nobank = 0
            sh("git add -A && git commit -q -m 'morning: NEW BANK' && git push origin CleanRepoForAI")
            if c3r == 6705: c3r = 6700   # after a bank, probe one lower with this family
            patch([(r"int c3t = \d+;", f"int c3t = {c3r};")])
            if build(c3r): break
        else:
            nobank += 1
            if cases and len(cases) >= 7 and cases[2] == "x":
                c3f += 1
                if c3f >= 3 and c3r > 6710:
                    c3r = 6710; c3f = 0
                    patch([(r"int c3t = \d+;", f"int c3t = {c3r};")])
                    if build(c3r): break
                    log({"ev": "m_c3_retreat", "c3": c3r})
            if nobank >= 6:
                draw += 1; nobank = 0
                patch([(r"g_draw = \d+;", f"g_draw = {draw};")])
                if build(c3r): break
                log({"ev": "m_newdraw", "draw": draw})
        time.sleep(300)
    log({"ev": "m_done", "banks": banks})

if __name__ == "__main__":
    main()
