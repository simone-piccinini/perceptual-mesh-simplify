#!/usr/bin/env python3
"""Re-audit past submissions: per-case verdict NAMES (WA vs TLE) + CPU time.
Usage: python3 scripts/judge_audit.py ID [ID...]   or  --recent N (scrape my recent list)"""
import argparse, configparser, os, re, sys, requests
HEADERS = {"User-Agent": "kattis-cli-submit"}

def load_cfg():
    cfg = configparser.ConfigParser()
    if not cfg.read([os.path.expanduser("~/.kattisrc")]):
        sys.exit("no kattisrc")
    return cfg

def url(cfg, option, default):
    if cfg.has_option("kattis", option):
        return cfg.get("kattis", option)
    return f"https://{cfg.get('kattis', 'hostname')}/{default}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--recent", type=int, default=0)
    args = ap.parse_args()
    cfg = load_cfg()
    login = requests.post(url(cfg, "loginurl", "login"),
        data={"user": cfg.get("user", "username"), "token": cfg.get("user", "token"), "script": "true"},
        headers=HEADERS)
    ids = list(args.ids)
    if args.recent:
        hostname = cfg.get("kattis", "hostname")
        u = f"https://{hostname}/contests/imc2-2/submissions/user?user={cfg.get('user','username')}"
        r = requests.get(u, cookies=login.cookies, headers=HEADERS)
        found = re.findall(r"submissions/(\d+)", r.text)
        seen = []
        for f in found:
            if f not in seen: seen.append(f)
        ids += seen[:args.recent]
    for sid in ids:
        st = requests.get(f"{url(cfg,'submissionsurl','submissions')}/{sid}?json",
                          cookies=login.cookies, headers=HEADERS).json()
        row = st.get("row_html", "")
        titles = re.findall(r'title="([^"]*)"', row)
        cpu = re.findall(r'data-type="cpu">\s*([^<]*)<', row)
        score = re.findall(r"\(([\d.]+)\)", re.sub("<[^>]+>", " ", row))
        cases = [t for t in titles if "Test case" in t or ":" in t]
        print(f"== {sid}  score={score[0] if score else '-'}  cpu={cpu[0].strip() if cpu else '-'}")
        for t in cases:
            print(f"   {t}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
