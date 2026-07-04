#!/usr/bin/env python3
"""Autonomous Kattis submit + verdict poller for IMC problem B.

Usage:
    python3 scripts/judge_submit.py [file] [--problem simplifygeometry] [--contest imc2-2]

Reads ~/.kattisrc (download from https://imc2.kattis.com/download/kattisrc while
logged in). Submits the file, polls until the verdict is final, then prints a
machine-readable summary:

    VERDICT <status text>
    SCORE <float or ->
    CPU <time or ->
    CASES <string like ..x..x. where . = accepted, x = rejected, ? = not run>

Case indices are 1-based in Kattis' UI; case 1 is the sample.
"""

import argparse
import configparser
import os
import re
import sys
import time

import requests

HEADERS = {"User-Agent": "kattis-cli-submit"}
RUNNING, COMPILE_ERR, ACCEPTED = 5, 8, 16
STATUS = {
    0: "New", 1: "New", 2: "Waiting for compile", 3: "Compiling",
    4: "Waiting for run", 5: "Running", 6: "Judge Error", 8: "Compile Error",
    9: "Run Time Error", 10: "Memory Limit Exceeded", 11: "Output Limit Exceeded",
    12: "Time Limit Exceeded", 13: "Illegal Function", 14: "Wrong Answer",
    16: "Accepted",
}


def load_cfg():
    cfg = configparser.ConfigParser()
    if not cfg.read([os.path.expanduser("~/.kattisrc")]):
        sys.exit("No ~/.kattisrc — download it from https://imc2.kattis.com/download/kattisrc")
    return cfg


def url(cfg, option, default):
    if cfg.has_option("kattis", option):
        return cfg.get("kattis", option)
    return f"https://{cfg.get('kattis', 'hostname')}/{default}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", default="solver/main.cpp")
    ap.add_argument("--problem", default="simplifygeometry")
    ap.add_argument("--contest", default=None)
    ap.add_argument("--timeout", type=float, default=600.0)
    args = ap.parse_args()

    cfg = load_cfg()
    login = requests.post(
        url(cfg, "loginurl", "login"),
        data={"user": cfg.get("user", "username"), "token": cfg.get("user", "token"),
              "script": "true"},
        headers=HEADERS,
    )
    if login.status_code != 200:
        sys.exit(f"LOGIN FAILED {login.status_code}: {login.text[:200]}")

    data = {"submit": "true", "submit_ctr": 2, "language": "C++",
            "mainclass": "", "problem": args.problem, "tag": "", "script": "true"}
    if args.contest:
        data["contest"] = args.contest
    with open(args.file, "rb") as fh:
        files = [("sub_file[]", (os.path.basename(args.file), fh.read(),
                                 "application/octet-stream"))]
    resp = requests.post(url(cfg, "submissionurl", "submit"), data=data, files=files,
                         cookies=login.cookies, headers=HEADERS)
    if resp.status_code != 200:
        sys.exit(f"SUBMIT FAILED {resp.status_code}: {resp.text[:300]}")
    m = re.search(r"Submission ID: (\d+)", resp.text)
    if not m:
        sys.exit(f"SUBMIT: no id in reply: {resp.text[:300]}")
    sub_id = m.group(1)
    sub_url = f"{url(cfg, 'submissionsurl', 'submissions')}/{sub_id}"
    print(f"SUBMISSION {sub_id} {sub_url}", flush=True)

    t0 = time.time()
    while time.time() - t0 < args.timeout:
        st = requests.get(sub_url + "?json", cookies=login.cookies, headers=HEADERS).json()
        sid = st["status_id"]
        if sid > RUNNING:
            row = st.get("row_html", "")
            cases = ""
            for icon in re.findall(r'<i class="([\w\- ]*)" title', row):
                if "is-empty" in icon:
                    cases += "?"
                elif "accepted" in icon:
                    cases += "."
                elif "rejected" in icon:
                    cases += "x"
            score = re.findall(r"\(([\d.]+)\)", re.sub("<[^>]+>", " ", row))
            cpu = re.findall(r'data-type="cpu">\s*([^<]*)<', row)
            print(f"VERDICT {STATUS.get(sid, sid)}")
            print(f"SCORE {score[0] if score else '-'}")
            print(f"CPU {cpu[0].strip() if cpu else '-'}")
            print(f"CASES {cases}")
            names = [t for t in re.findall(r'title="([^"]*)"', row) if "Test case" in t]
            for t in names:
                if "Accepted" not in t:
                    print(f"FAIL {t}")
            if sid == COMPILE_ERR:
                print(st.get("feedback_html", "")[:500])
            return 0 if sid == ACCEPTED else 1
        time.sleep(2.0)
    sys.exit("POLL TIMEOUT")


if __name__ == "__main__":
    sys.exit(main())
