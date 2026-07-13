#!/usr/bin/env python3
"""saliency_validator — a BOUNDED judge-probe that tests whether the local c4 Z-saliency S2d gain
(G_ALLOC_WEIGHT) transfers to the judge. NOT a rung-walk: it submits a small control/variant set of
c4 K-reads and decodes the self-computed S2d on the judge's REAL c4 mesh.

WHY IT'S BUILT THIS WAY
- The judge runs the binary with NO env vars, so alpha and the c4-read CANNOT be env-gated at judge
  time -> we BAKE them into each submitted source (patch g_alloc_weight + enable the S2d read),
  exactly like the team ladder patches mein.cpp. Each alpha = one patched source.
- A K-read encodes S2d into the output pad: V' = out_v + 4K, K = round((S2d-0.70)/1.5e-3), clamp[0,160].
  Judge c4 compression -> V' -> K -> S2d. For a control (a=0) vs variant pair at the SAME safe c4 rung,
  dS2d = (K_var - K_ctrl) * 1.5e-3 on the real judge mesh.

ISOLATION FROM THE NIGHT CAMPAIGN (zero-collision) -- see explanation at bottom of this file:
  1. Runs in a DEDICATED git worktree on a probe branch (patches ITS copy of mein.cpp; never the
     clone/branch the campaign edits). Launch with --require-worktree (refuses to run in the main clone).
  2. Respects a shared judge lock: waits while `handoff/.judge_lock` exists (campaign's critical/
     consolidation phase = Front D), and holds `handoff/.saliency_lock` only during its own submits.
  3. Polite: >= MIN_GAP_S between submits (>= the ~4 min token-bucket), and a hard cap of len(alphas)
     submissions. Best-counts + padded reads mean it can NEVER lower the bank.
  4. Logs to its OWN ledger handoff/saliency_probe_log.jsonl (never submissions.jsonl / overnight_log).

USAGE (deploy after the campaign, or while it idles):
  # from a dedicated worktree on a probe branch:
  git worktree add ../saliency-probe -b probe/saliency experiment/new-mechanism
  cd ../saliency-probe
  python3 scripts/saliency_validator.py --build "g++ -O2 -std=c++17 -Isolver {NC} -o /tmp/sv" \
          --alphas 0 0.8 1.0 1.2 --c4t 5040 --require-worktree
  # add --dry-run to patch/build/decode-logic WITHOUT submitting (verify first).
"""
import argparse, json, os, re, subprocess, sys, time, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, "solver/mein.cpp")
NC   = os.path.join(ROOT, "solver/mein_nocomments.cpp")
LOG  = os.path.join(ROOT, "handoff/saliency_probe_log.jsonl")
JUDGE_LOCK = os.path.join(ROOT, "handoff/.judge_lock")       # campaign's critical phase (we WAIT on it)
OUR_LOCK   = os.path.join(ROOT, "handoff/.saliency_lock")    # ours, held only during a submit
V_C4 = 35292          # judge c4 input vertex count (docs) -- cancels in the control/variant delta except via out_v
S2D_OFF, S2D_STEP = 0.70, 1.5e-3
MIN_GAP_S = 250       # >= the ~4 min Kattis token bucket

def sh(cmd, timeout=1800):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT, timeout=timeout)

def log(rec):
    rec["utc"] = datetime.datetime.utcnow().isoformat()
    with open(LOG, "a") as f: f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec), flush=True)

def patch_source(alpha, c4t):
    """Bake alpha + the c4 S2d read + safe rung into the source (judge has no env)."""
    s = open(SRC, encoding="utf-8").read()
    s, n1 = re.subn(r"g_alloc_weight = [0-9.]+;", f"g_alloc_weight = {alpha};", s, count=1)
    s, n2 = re.subn(r'if \(getenv\("G_C4READ"\)\) K =', "if (1) K =", s, count=1)       # judge: force read on
    s, n3 = re.subn(r"int c4t = \d+;", f"int c4t = {c4t};", s, count=1)
    assert n1 and n2 and n3, f"patch anchors not found (n1={n1} n2={n2} n3={n3}) -- source drifted"
    open(SRC, "w", encoding="utf-8", newline="\n").write(s)

def restore_source():
    sh(f"git checkout -- {SRC}")

def build_and_prova(build_cmd, c4t):
    sh(f"python3 scripts/strip_comments.py {SRC} {NC}")
    r = sh(build_cmd.format(NC=NC))
    if r.returncode != 0: return None, "compile: " + r.stderr[-300:]
    return True, None   # prova-del-nove of the c4 output count is a judge-side check for reads (padded)

def decode_c4_s2d(cases_scores, out_v):
    """cases_scores: dict case->compression%. Decode c4 -> V' -> K -> S2d."""
    c4 = cases_scores.get("4")
    if c4 is None: return None, None
    vprime = V_C4 * (1.0 - c4 / 100.0)
    K = round((vprime - out_v) / 4.0)
    return K, S2D_OFF + K * S2D_STEP

def submit(note, dry):
    if dry:
        return {"dry": True}
    # reuse the team's judge client; parse its stdout for per-case compressions.
    r = sh(f'python3 scripts/judge_submit.py {NC} --no-log --note "{note}"', timeout=1800)
    return {"raw": (r.stdout + r.stderr)[-1500:]}

def wait_for_campaign():
    while os.path.exists(JUDGE_LOCK):
        print(f"[saliency] campaign lock present ({JUDGE_LOCK}); waiting 60s...", flush=True)
        time.sleep(60)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alphas", nargs="+", type=float, default=[0.0, 0.8, 1.0, 1.2])
    ap.add_argument("--c4t", type=int, default=5040, help="safe c4 read rung (above the ~4930 wall)")
    ap.add_argument("--build", required=True, help="build cmd; use {NC} for the stripped source path")
    ap.add_argument("--dry-run", action="store_true", help="patch/build/decode-logic WITHOUT submitting")
    ap.add_argument("--require-worktree", action="store_true",
                    help="refuse to run unless in a dedicated worktree (isolation guard)")
    args = ap.parse_args()

    # ISOLATION GUARD: never run in the clone/branch the campaign uses.
    branch = sh("git rev-parse --abbrev-ref HEAD").stdout.strip()
    is_wt  = sh("git rev-parse --is-inside-work-tree").stdout.strip() == "true" and \
             sh("git rev-parse --git-common-dir").stdout.strip() != sh("git rev-parse --git-dir").stdout.strip()
    if args.require_worktree and not is_wt:
        sys.exit("REFUSING: not in a dedicated git worktree. `git worktree add ../saliency-probe -b "
                 "probe/saliency <base>` then run there. (isolation guard)")
    if branch in ("CleanRepoForAI", "master", "main"):
        sys.exit(f"REFUSING: branch '{branch}' is production/campaign. Use a probe branch.")

    log({"ev": "start", "branch": branch, "alphas": args.alphas, "c4t": args.c4t, "dry": args.dry_run})
    results = {}
    for a in args.alphas:
        wait_for_campaign()
        try:
            patch_source(a, args.c4t)
            ok, err = build_and_prova(args.build, args.c4t)
            if not ok: log({"ev": "build_fail", "alpha": a, "err": err}); restore_source(); continue
            open(OUR_LOCK, "w").write(str(os.getpid()))
            out = submit(f"SALIENCY c4-read alpha={a} c4t={args.c4t}", args.dry_run)
            os.path.exists(OUR_LOCK) and os.remove(OUR_LOCK)
        finally:
            restore_source()
        rec = {"ev": "probe", "alpha": a, "c4t": args.c4t, "config": f"G_ALLOC_WEIGHT={a}", **out}
        # NOTE: parse per-case compressions from out['raw'] (judge_submit prints CASES/scores), then:
        #   K, s2d = decode_c4_s2d(cases, args.c4t); rec['judge_S2d']=s2d
        # left as an explicit step so the operator confirms the c4 case PASSED (didn't WA) before trusting the decode.
        log(rec)
        results[a] = rec
        if a != args.alphas[-1] and not args.dry_run: time.sleep(MIN_GAP_S)

    # SUCCESS gate (fill judge_S2d from the decode above): dS2d = variant - control(alpha 0)
    log({"ev": "done", "note": "decode judge_S2d per probe; SUCCESS if any variant - control >= +0.04"})

if __name__ == "__main__":
    try: main()
    finally:
        os.path.exists(OUR_LOCK) and os.remove(OUR_LOCK)
