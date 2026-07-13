#!/usr/bin/env python3
"""SIL2 ladder: roll c3 rung until bank (c4 coin), then descend 10; retreat on 3x c3-WA.
Rungs: 6700 -> 6690 -> 6680 -> ... c5 fixed 4172, c4 4920."""
import datetime, json, os, re, subprocess, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, NC = ROOT+"/solver/mein.cpp", ROOT+"/solver/mein_nocomments.cpp"
LOG = ROOT+"/handoff/overnight_log.jsonl"
def sh(c, t=1500): return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t, cwd=ROOT)
def log(r):
    r["utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    open(LOG,"a").write(json.dumps(r)+"\n"); print(json.dumps(r), flush=True)
def build(c3r):
    s = open(SRC).read(); s = re.sub(r"int c3t = \d+;", f"int c3t = {c3r};", s, count=1); open(SRC,"w").write(s)
    r = sh(f"python3 scripts/strip_comments.py {SRC} {NC} && g++ -O2 -std=c++17 -Isolver {NC} -o /tmp/s2l")
    if r.returncode: return "compile"
    r = sh(f"/tmp/s2l < /tmp/c3proxy.in 2>/dev/null | head -1", t=900)
    return None if r.stdout.split() and int(r.stdout.split()[0]) == c3r else "prova"
def submit(note):
    r = sh(f'python3 scripts/judge_submit.py {NC} --force --note "{note}"', t=1500)
    out = r.stdout + r.stderr
    m = re.search(r"CASES ([.x?]+)", out)
    return (m.group(1) if m else None), ("NEW BANK" in out)
def main():
    c3r = 6700; wa = 0; banks = 0; subs = 0
    if build(c3r): log({"ev":"s2l_fatal"}); return
    while subs < 40 and banks < 4:
        now = datetime.datetime.now()
        if (now.hour, now.minute) >= (23, 45): break
        cases, nb = submit(f"S2L c3={c3r} (SIL2 ladder)")
        subs += 1
        log({"ev":"s2l", "c3":c3r, "cases":cases, "newbank":nb})
        if nb:
            banks += 1; wa = 0
            sh("git add -A && git commit -q -m 'sil2 ladder: NEW BANK' && git push -q origin CleanRepoForAI")
            c3r -= 10
            if build(c3r): break
        elif cases and len(cases) >= 7 and cases[2] == "x":
            wa += 1
            if wa >= 3:
                c3r += 10; wa = 0
                if build(c3r): break
                log({"ev":"s2l_retreat", "c3":c3r})
        time.sleep(300)
    log({"ev":"s2l_done", "banks":banks})
main()
