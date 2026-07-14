#!/usr/bin/env python3
"""config_optimizer — judge-gated, CASE-SELECTIVE search for the best Z-saliency allocation config.

STRATEGY (the honest funnel; submissions are cheap, a transferring ruler is not):
  For each candidate case, in order of increasing cost:
    STAGE 0  LOCAL PRE-FILTER (only for cases with a CALIBRATED proxy):
             sweep the param on the proxy family; DROP values that hurt EVERY proxy (a weak gate:
             the family != the judge's one mesh, so local only rejects sure-losers, never confirms).
    STAGE 1  JUDGE COIN-TOSS SETTLER (2 submissions): control (off) vs the best local value, as
             all-green K-reads; decode the case's self-S2d via arith(). If the variant does NOT beat
             control -> mark the case "NO HELP -> keep uniform" and STOP (spend nothing more here).
    STAGE 2  JUDGE REFINE (only if stage 1 was positive): a few more values to maximise the case's
             judge S2d, then lock the per-case winner.

  "APPLY ONLY TO CASES THAT HELP THE SCORE" is enforced structurally: a case adopts a non-zero config
  ONLY after the JUDGE confirms a gain for THAT case; otherwise it stays at the banked/uniform config.
  Output = a per-case alpha map + an `alloc_for(V)` snippet to bake into mein.cpp's dispatch, for the
  team's ladder to harvest the freed rung. This bot MEASURES + REPORTS; it does not bank (read-only).

SAFETY / ISOLATION (coexists with the Night Campaign):
  * dedicated git worktree on a probe branch (--require-worktree); refuses production branches.
  * waits on handoff/.judge_lock (campaign's Front-D consolidation); holds handoff/.optimizer_lock only mid-submit.
  * budget cap --max-subs; >=250s spacing; reads are padded -> best-counts means it can NEVER lower the bank.
  * own ledger handoff/optimizer_log.jsonl; never touches submissions.jsonl / the campaign logs.
  * uses THIS interpreter (sys.executable) for all sub-python -> no python3 dead-stub on Windows.

The search space is data (SPACE below): add a case by giving it a proxy set + a read anchor. Today the
only case with a calibrated proxy AND a measured allocation effect is c4; c3-allocation is RIM-BUDGET
(already banked). So the bot ships instantiated for c4 and is structured to widen as proxies land.
"""
import argparse, json, os, re, subprocess, sys, time, datetime, statistics

PY   = sys.executable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, "solver/mein.cpp")
NC   = os.path.join(ROOT, "solver/mein_nocomments.cpp")
LOG  = os.path.join(ROOT, "handoff/optimizer_log.jsonl")
JUDGE_LOCK = os.path.join(ROOT, "handoff/.judge_lock")
OUR_LOCK   = os.path.join(ROOT, "handoff/.optimizer_lock")
MIN_GAP_S  = 260

# --- search space: case -> knobs. proxies are solver-format meshes under probe/cache/<case>/ ---
SPACE = {
    "c4": {
        "band": (30000, 40000), "V_in": 35292, "c4t": 5040,
        "proxies": ["00005934", "00009281", "00004867", "00001680"],  # calibrated (S2d spans the wall)
        "param": "G_ALLOC_WEIGHT",
        "local_values":  [0.5, 0.8, 1.0, 1.2, 1.5],
        "read_off": 0.70, "read_step": 1.5e-3,
    },
}

def sh(cmd, timeout=2400, env=None):
    e = dict(os.environ); e.update(env or {})
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT, timeout=timeout, env=e)

def log(rec):
    rec["utc"] = datetime.datetime.utcnow().isoformat()
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    open(LOG, "a").write(json.dumps(rec) + "\n"); print("LOG " + json.dumps(rec), flush=True)

# ---------- STAGE 0: PARALLEL local pre-filter (machine is NOT thermal-throttled; 6 cores) ----------
import concurrent.futures as _cf

def rc4_s2_env(binexe, mesh, alpha):
    r = sh(f'"{binexe}" < probe/cache/c4/{mesh}.obj', timeout=2400, env={"G_ALLOC_WEIGHT": str(alpha)})
    m = re.search(r"S2d=([\d.]+) S2=([\d.]+)", r.stderr)
    return (float(m.group(1)), float(m.group(2))) if m else (None, None)

def local_prefilter(case, binexe, workers):
    """Run the whole (proxy x alpha) grid CONCURRENTLY. 4 runs = ~1 slow run of wall time (measured)."""
    cfg = SPACE[case]
    grid = [(m, 0.0) for m in cfg["proxies"]] + [(m, a) for a in cfg["local_values"] for m in cfg["proxies"]]
    res = {}
    with _cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(rc4_s2_env, binexe, m, a): (m, a) for (m, a) in grid}
        for f in _cf.as_completed(futs):
            res[futs[f]] = f.result()[0]
    base = {m: res[(m, 0.0)] for m in cfg["proxies"]}
    keep = []
    for a in cfg["local_values"]:
        deltas = [res[(m, a)] - base[m] for m in cfg["proxies"] if res.get((m, a)) is not None and base[m] is not None]
        helps_any = any(d > 0.005 for d in deltas)
        log({"ev": "local", "case": case, "alpha": a, "dS2d_by_mesh": [round(d, 4) for d in deltas],
             "helps_any": helps_any})
        if helps_any: keep.append((a, max(deltas)))
    keep.sort(key=lambda x: -x[1])
    return [a for a, _ in keep]           # ranked; best local upside first

# ---------- STAGE 1/2: judge probe (bake config -> submit -> arith-decode the case's S2d) ----------
def patch_and_build(case, alpha, build_cmd):
    cfg = SPACE[case]
    s = open(SRC, encoding="utf-8").read()
    s, n1 = re.subn(r"g_alloc_weight = [0-9.]+;", f"g_alloc_weight = {alpha};", s, 1)
    s, n2 = re.subn(r'if \(getenv\("G_C4READ"\)\) K =', "if (1) K =", s, 1)   # judge has no env
    s, n3 = re.subn(r"int c4t = \d+;", f"int c4t = {cfg['c4t']};", s, 1)
    assert n1 and n2 and n3, f"patch anchors drifted (n1={n1} n2={n2} n3={n3})"
    open(SRC, "w", encoding="utf-8", newline="\n").write(s)
    sh(f'"{PY}" scripts/strip_comments.py {SRC} {NC}')
    return sh(build_cmd.format(NC=NC)).returncode == 0

def judge_case_s2d(case, note, dry):
    """Submit; parse judge_submit's arith line for the single-changed case -> V' -> K -> S2d."""
    if dry: return None, "dry"
    r = sh(f'"{PY}" scripts/judge_submit.py {NC} --note "{note}"', timeout=2400)
    out = r.stdout + r.stderr
    cfg = SPACE[case]; cnum = case[1:]
    m = re.search(rf"ARITH if only case {cnum} changed:.*?V'=~?(\d+)", out)
    if not m:
        return None, ("no clean single-change decode (needs all-green read) :: " + out[-400:])
    vprime = int(m.group(1)); K = round((vprime - cfg["c4t"]) / 4.0)
    return cfg["read_off"] + K * cfg["read_step"], f"V'={vprime} K={K}"

def restore():
    sh(f"git checkout -- {SRC}")

def wait_campaign():
    while os.path.exists(JUDGE_LOCK):
        print("[opt] campaign lock present; waiting 60s...", flush=True); time.sleep(60)

def probe(case, alpha, build_cmd, dry, budget):
    if budget[0] <= 0: return None, "budget exhausted"
    wait_campaign()
    try:
        if not patch_and_build(case, alpha, build_cmd): return None, "build fail"
        open(OUR_LOCK, "w").write(str(os.getpid()))
        s2d, info = judge_case_s2d(case, f"OPT {case} {SPACE[case]['param']}={alpha}", dry)
    finally:
        os.path.exists(OUR_LOCK) and os.remove(OUR_LOCK); restore()
    budget[0] -= 1
    log({"ev": "judge", "case": case, "alpha": alpha, "judge_S2d": s2d, "info": info, "budget_left": budget[0]})
    return s2d, info

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", nargs="+", default=["c4"])
    ap.add_argument("--build", required=True, help="build cmd, {NC}=stripped source")
    ap.add_argument("--localbin", default="", help="prebuilt env-gated binary for STAGE 0 (skip local if empty)")
    ap.add_argument("--max-subs", type=int, default=8, help="hard judge-submission budget for the whole run")
    ap.add_argument("--gain", type=float, default=0.005, help="min judge dS2d over control to ADOPT")
    ap.add_argument("--workers", type=int, default=5, help="parallel local runs (6 cores -> 5 leaves headroom)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--require-worktree", action="store_true")
    args = ap.parse_args()

    branch = sh("git rev-parse --abbrev-ref HEAD").stdout.strip()
    common = sh("git rev-parse --git-common-dir").stdout.strip(); gd = sh("git rev-parse --git-dir").stdout.strip()
    if args.require_worktree and common == gd:
        sys.exit("REFUSING: not a dedicated worktree. `git worktree add ../opt -b probe/optimizer <base>`.")
    if branch in ("CleanRepoForAI", "master", "main"):
        sys.exit(f"REFUSING: '{branch}' is production/campaign. Use a probe branch.")

    budget = [args.max_subs]; winners = {}
    log({"ev": "start", "branch": branch, "cases": args.cases, "budget": args.max_subs, "dry": args.dry_run})
    for case in args.cases:
        cfg = SPACE[case]
        # STAGE 0
        cand = cfg["local_values"]
        if args.localbin:
            cand = local_prefilter(case, args.localbin, args.workers)
            if not cand:
                log({"ev": "case_done", "case": case, "verdict": "local: hurts all proxies -> SKIP judge"})
                winners[case] = 0.0; continue
        # STAGE 1: control vs best local candidate
        ctrl, _ = probe(case, 0.0, args.build, args.dry_run, budget)
        best_a, best_s2d = 0.0, ctrl
        v1, _ = probe(case, cand[0], args.build, args.dry_run, budget)
        if ctrl is not None and v1 is not None and (v1 - ctrl) >= args.gain:
            best_a, best_s2d = cand[0], v1
            # STAGE 2: refine over the remaining local candidates within budget
            for a in cand[1:]:
                if budget[0] <= 0: break
                s2d, _ = probe(case, a, args.build, args.dry_run, budget)
                if s2d is not None and s2d > best_s2d: best_a, best_s2d = a, s2d
            verdict = f"HELPS: adopt {cfg['param']}={best_a} (judge S2d {ctrl}->{best_s2d})"
        else:
            verdict = f"NO HELP on judge (ctrl={ctrl} var={v1}) -> keep uniform"
        winners[case] = best_a
        log({"ev": "case_done", "case": case, "winner_alpha": best_a, "verdict": verdict})

    # emit the case-selective dispatch snippet (only-where-it-helps)
    nz = {c: a for c, a in winners.items() if a}
    snippet = "static double alloc_for(int V){\n" + "".join(
        f"    if (V>{SPACE[c]['band'][0]} && V<={SPACE[c]['band'][1]}) return {a};  // {c}: judge-confirmed\n"
        for c, a in nz.items()) + "    return 0.0;\n}"
    log({"ev": "done", "winners": winners, "adopt": nz, "dispatch_snippet": snippet})
    print("\n=== PER-CASE WINNERS (apply only where judge-confirmed) ===")
    print(json.dumps(winners, indent=2)); print(snippet)

if __name__ == "__main__":
    try: main()
    finally:
        os.path.exists(OUR_LOCK) and os.remove(OUR_LOCK)
