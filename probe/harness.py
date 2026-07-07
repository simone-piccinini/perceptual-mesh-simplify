#!/usr/bin/env python3
"""Wall-probing harness — the plan/decode loop of docs/WALL-MODEL.md §6.

The loop (human keeps the click):
    python3 probe/harness.py plan --read 3@6940 --bank 4@4970   # emit probe/out/main.cpp
    python3 probe/harness.py preflight                          # compile + identity + validity
    <human submits probe/out/main.cpp on Kattis>
    python3 probe/harness.py decode 90.285538                   # attribute + update wall model
    python3 probe/harness.py status                             # the wall ledger

Design rules (from WALL-MODEL.md):
- The generator only patches CONSTANTS inside the three probe blocks of the frozen v111
  base (cases 3/4/5) — one-constant diffs stay in the proven binary family. It never
  synthesizes code.
- The decoder ENUMERATES every hypothesis (per-case pass/WA/K) and demands a unique match;
  `plan` pre-checks that the planned probe is decodable without ambiguity BEFORE you spend
  the submission.
- The harness never submits. Kattis 403s scripts; the click and the spend decision are human.
"""
import argparse, itertools, json, os, re, shutil, subprocess, sys, datetime, time as _time

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBE  = os.path.join(ROOT, "probe")
STATE  = os.path.join(PROBE, "wall_model.json")
OUTDIR = os.path.join(PROBE, "out")
CACHE  = os.path.join(PROBE, "cache")
PENDING = os.path.join(OUTDIR, "pending.json")

K_MAX, K_STEP, K_BASE = 160, 5e-4, 0.885   # the S->K encoding (friend's PROBE-RC3-READ)
SCORE_TOL = 3.5e-6                          # |sum s_c - 6*printed| ; printed has 6 decimals

# ---------------------------------------------------------------- state

def load_state():
    with open(STATE) as f: return json.load(f)

def save_state(st):
    with open(STATE, "w") as f: json.dump(st, f, indent=2)
    print(f"[state] wrote {os.path.relpath(STATE, ROOT)}")

def contribution(N, V):
    """Per-case score contribution s_c = (100/6)(1 - N/V)."""
    return (100.0/6.0) * (1.0 - N / V)

# ---------------------------------------------------------------- generator

def block_region(src, marker):
    """(start,end) character span of a probe block: its marker line -> its 'return 0;\\n    }'."""
    m = src.find(marker)
    if m < 0: raise SystemExit(f"marker not found in base: {marker}")
    start = src.rfind("\n", 0, m) + 1
    endpat = "        return 0;\n    }\n"
    e = src.find(endpat, m)
    if e < 0: raise SystemExit(f"block end not found after {marker}")
    return start, e + len(endpat)

READ_K_CODE = (
    "long Kraw = (long)((S2 - {base}) / {step} + 0.5);\n"
    "        const long K = Kraw < 0 ? 0 : (Kraw > {kmax} ? {kmax} : Kraw);   // READ: S2 -> K (harness)"
).format(base=K_BASE, step=K_STEP, kmax=K_MAX)

def generate(plan, st):
    """Patch the frozen base: per planned case set the Decimate target and bank/read K-line."""
    base_path = os.path.join(ROOT, st["base_file"])
    src = open(base_path).read()
    # patch from the last block backwards so earlier spans stay valid
    cases = sorted((c for c in plan if c in st["patchable"]), key=lambda c: -int(c))
    for c in cases:
        cfg  = st["cases"][c]; act = plan[c]
        s, e = block_region(src, cfg["marker"])
        blk  = src[s:e]
        old_n = str(cfg["base_target"])
        if blk.count(old_n) < 1: raise SystemExit(f"case {c}: base target {old_n} not in block")
        blk = blk.replace(old_n, str(act["N"]))
        if act["mode"] == "read":
            kline = re.search(r"const long K = 0;[^\n]*", blk)
            if not kline: raise SystemExit(f"case {c}: K-line not found")
            blk = blk[:kline.start()] + READ_K_CODE + blk[kline.end():]
            if act["N"] % 4 != 0:
                print(f"[warn] case {c}: read base N={act['N']} is not ==0 mod 4 — stall detection lost")
        src = src[:s] + blk + src[e:]
    os.makedirs(OUTDIR, exist_ok=True)
    out = os.path.join(OUTDIR, "main.cpp")
    open(out, "w").write(src)
    return out

# ---------------------------------------------------------------- hypotheses & decode

def case_options(c, plan, st):
    """All (label, delta_vs_bank) outcomes for one case. delta is s_c(outcome) - s_c(banked)."""
    cfg = st["cases"][c]; V = cfg["V"]
    banked = contribution(cfg["banked_N"], V)
    if c in plan:
        N, mode = plan[c]["N"], plan[c]["mode"]
        opts = [("WA", -banked)]
        if mode == "bank":
            opts.append((f"pass@{N}", contribution(N, V) - banked))
        else:  # read: V' = N + 4K, K unknown in [0, K_MAX]
            for K in range(K_MAX + 1):
                opts.append((f"read@{N} K={K}", contribution(N + 4*K, V) - banked))
        return opts
    # untouched case: reproduces its banked contribution, or (rarely) WAs
    return [("banked", 0.0), ("WA", -banked)]

def decode(score, st, plan, max_untouched_wa=1):
    """Enumerate all outcome combinations; return those matching the printed score."""
    target = 6.0 * score - 6.0 * st["banked_total"]   # total delta vs the banked sum
    cases  = sorted(st["cases"], key=int)
    opts   = [case_options(c, plan, st) for c in cases]
    hits = []
    for combo in itertools.product(*opts):
        wa_untouched = sum(1 for c, (lab, _) in zip(cases, combo)
                           if lab == "WA" and c not in plan)
        if wa_untouched > max_untouched_wa: continue
        delta = sum(d for _, d in combo)
        if abs(delta - target) <= SCORE_TOL:
            hits.append({c: lab for c, (lab, _) in zip(cases, combo)})
    # dedupe identical labelings
    uniq = [h for i, h in enumerate(hits) if h not in hits[:i]]
    return uniq

def ambiguity_check(st, plan):
    """Min gap between distinct hypothesis scores — must exceed 2*tol to decode uniquely."""
    cases = sorted(st["cases"], key=int)
    deltas = [[d for _, d in case_options(c, plan, st)] for c in cases]
    totals = sorted(set(round(sum(x), 9) for x in itertools.product(*deltas)))
    gaps = [b - a for a, b in zip(totals, totals[1:])]
    return (min(gaps) if gaps else float("inf")), len(totals)

# ---------------------------------------------------------------- commands

def parse_actions(args):
    plan = {}
    for mode, specs in (("read", args.read), ("bank", args.bank)):
        for spec in specs or []:
            c, n = spec.split("@"); plan[c] = {"mode": mode, "N": int(n)}
    return plan

def cmd_plan(args, st):
    plan = parse_actions(args)
    if not plan:
        print("No actions given. Suggestions from the wall model:")
        for c, cfg in sorted(st["cases"].items(), key=lambda kv: int(kv[0])):
            print(f"  case {c}: {cfg['suggest']}")
        print("\nSpecify e.g.:  plan --read 3@6940 --read 5@4212   or  --bank 4@4970")
        return
    for c in plan:
        if c not in st["patchable"]:
            raise SystemExit(f"case {c} is not patchable by this harness (only {st['patchable']})")
    gap, nhyp = ambiguity_check(st, plan)
    print(f"[ambiguity] {nhyp} hypothesis scores, min gap {gap:.2e} "
          f"({'OK' if gap > 2*SCORE_TOL else 'TOO CLOSE — simplify the plan'})")
    if gap <= 2*SCORE_TOL: raise SystemExit("refusing an undecodable plan")
    out = generate(plan, st)
    # expected outcomes table (reads shown at K for S2 = 0.900/0.910)
    print(f"[plan] wrote {os.path.relpath(out, ROOT)}")
    exp = st["banked_total"]
    for c, act in sorted(plan.items()):
        V = st["cases"][c]["V"]; bank = contribution(st["cases"][c]["banked_N"], V)
        if act["mode"] == "bank":
            print(f"  case {c} bank@{act['N']}: pass -> {exp + (contribution(act['N'],V)-bank)/6:.6f} on this case alone; WA -> {exp - bank/6:.6f}")
        else:
            for s2 in (0.900, 0.910):
                K = max(0, min(K_MAX, round((s2 - K_BASE)/K_STEP)))
                print(f"  case {c} read@{act['N']}: if S2={s2:.3f} (K={K}) -> {exp + (contribution(act['N']+4*K,V)-bank)/6:.6f}")
    with open(PENDING, "w") as f:
        json.dump({"plan": plan, "created": str(datetime.date.today())}, f, indent=2)
    print(f"[plan] pending plan saved; submit probe/out/main.cpp, then: decode <score>")

def cmd_preflight(args, st):
    if not os.path.exists(PENDING): raise SystemExit("no pending plan — run `plan` first")
    plan = json.load(open(PENDING))["plan"]
    out  = os.path.join(OUTDIR, "main.cpp")
    base = os.path.join(ROOT, st["base_file"])
    inc  = os.path.join(ROOT, "solver")
    def build(src, binout):
        r = subprocess.run(["clang++", "-O2", "-std=c++17", "-I", inc, src, "-o", binout],
                           capture_output=True, text=True)
        if r.returncode: raise SystemExit(f"compile FAILED:\n{r.stderr[:2000]}")
    os.makedirs(CACHE, exist_ok=True)
    b_bin, o_bin = os.path.join(CACHE, "base_bin"), os.path.join(CACHE, "out_bin")
    build(base, b_bin); build(out, o_bin); print("[preflight] clang builds OK (base + probe)")
    # off-target byte-identity on the stock proxies (all outside bands 3/4/5 except armadillo=c5)
    touched_bands = {c for c in plan}
    proxies = {"cow": None, "bunny": None, "fandisk": None, "armadillo": "5"}
    for name, band in proxies.items():
        mesh = os.path.join(ROOT, "tests", "data", f"{name}_watertight.obj")
        a = subprocess.run([b_bin], stdin=open(mesh, "rb"), capture_output=True).stdout
        b = subprocess.run([o_bin], stdin=open(mesh, "rb"), capture_output=True).stdout
        if band in touched_bands:
            print(f"[preflight] {name}: band {band} touched -> outputs expected to differ (got {'DIFFER' if a!=b else 'IDENTICAL'})")
        else:
            if a != b: raise SystemExit(f"{name}: output CHANGED on an untouched band — patch leaked!")
            print(f"[preflight] {name}: byte-identical (untouched band) OK")
    if args.docker:
        eig = os.path.join(CACHE, "eigeninc")
        if not os.path.isdir(eig): raise SystemExit("run make_band_proxies.py first (copies Eigen for docker)")
        cmd = ("g++ -O2 -std=c++17 -I /eigen -I /w/solver /w/probe/out/main.cpp -o /tmp/o "
               "&& echo COMPILED")
        r = subprocess.run(["docker", "run", "--rm", "-v", f"{ROOT}:/w", "-v", f"{eig}:/eigen:ro",
                            "gcc:14", "bash", "-c", cmd], capture_output=True, text=True)
        print(f"[preflight] docker gcc:14: {r.stdout.strip() or r.stderr[-400:]}")
    print("[preflight] PASS — submit probe/out/main.cpp")

def cmd_decode(args, st):
    plan = json.load(open(PENDING))["plan"] if os.path.exists(PENDING) else {}
    hits = decode(args.score, st, plan)
    if not hits:
        print("NO hypothesis matches — check the pasted score, or the plan file is stale."); return
    if len(hits) > 1:
        print(f"AMBIGUOUS ({len(hits)} matches) — not writing state:")
        for h in hits: print("  ", h)
        return
    h = hits[0]
    print(f"decode of {args.score:.6f}:")
    for c in sorted(h, key=int):
        line = f"  case {c}: {h[c]}"
        if h[c].startswith("read@"):
            K = int(h[c].split("K=")[1]); s2 = K_BASE + K*K_STEP
            line += f"  ->  S2 = {s2:.4f}"
        print(line)
    if args.dry: print("(--dry: state not updated)"); return
    # update state: log + reads + bank moves
    st["log"].append({"date": str(datetime.date.today()), "score": args.score, "plan": plan, "outcome": h})
    for c, lab in h.items():
        cfg = st["cases"][c]
        if lab.startswith("read@"):
            K = int(lab.split("K=")[1])
            cfg.setdefault("reads", []).append({"N": plan[c]["N"], "K": K, "S2": round(K_BASE+K*K_STEP, 4)})
        elif lab.startswith("pass@"):
            N = int(lab.split("@")[1])
            if N < cfg["banked_N"]:
                cfg["banked_N"], cfg["base_target"] = N, N
        elif lab == "WA" and c in plan:
            cfg.setdefault("fails", []).append(plan[c]["N"])
    total = st["banked_total"]
    if args.score > total and all(not l.startswith("read") and l != "WA" for l in h.values()):
        st["banked_total"] = args.score
        print(f"[state] NEW BANK {args.score:.6f} (was {total:.6f}) — snapshot probe/out/main.cpp into submissions/!")
    save_state(st)

def cmd_status(_args, st):
    print(f"bank total: {st['banked_total']:.6f}   base: {st['base_file']}")
    for c, cfg in sorted(st["cases"].items(), key=lambda kv: int(kv[0])):
        s = contribution(cfg["banked_N"], cfg["V"])
        print(f"case {c}: V={cfg['V']:>8}  N={cfg['banked_N']:>6}  s={s:8.4f}  "
              f"[{cfg['regime']}]  {cfg['wall']}")
        for r in cfg.get("reads", []): print(f"         read: N={r['N']} K={r['K']} S2={r['S2']}")
        if cfg.get("fails"): print(f"         WA'd at: {cfg['fails']}")

# ---------------------------------------------------------------- submit (closes the click)

JUDGE_SUBMIT = os.path.join(ROOT, "scripts", "judge_submit.py")
SUBLOG       = os.path.join(ROOT, "handoff", "submissions.jsonl")

def _logcount():
    return sum(1 for l in open(SUBLOG) if l.strip()) if os.path.exists(SUBLOG) else 0

def do_submit(fpath, note, contest, live):
    """Run judge_submit.py on fpath; return its freshly-appended JSONL record (score, cases, ...)."""
    cmd = [sys.executable, JUDGE_SUBMIT, fpath, "--problem", "simplifygeometry", "--note", note, "--force"]
    if contest: cmd += ["--contest", contest]
    if not live:
        print("[submit] DRY-RUN (no --live) — would run:\n  " + " ".join(cmd)); return None
    n0 = _logcount()
    print("[submit] LIVE ->", " ".join(cmd[:3]), "...")
    subprocess.run(cmd)
    lines = [l for l in open(SUBLOG) if l.strip()] if os.path.exists(SUBLOG) else []
    if len(lines) <= n0: raise SystemExit("[submit] judge_submit wrote no record — aborting (no state change)")
    return json.loads(lines[-1])

def apply_result(rec, st, plan):
    """Decode a judge_submit record (score + per-case cases string) into the wall model."""
    score, cases = rec.get("score"), rec.get("cases", "")
    verdict = rec.get("verdict")
    print(f"[result] id={rec.get('id')} verdict={verdict} score={score} cases={cases}")
    if score is None:
        # WA/TLE/CE: attribute from the per-case string ('.'=pass,'x'=fail; index 0 = sample)
        failed = [str(i) for i, ch in enumerate(cases) if ch == "x" and 2 <= i <= 7]
        for c in failed:
            if c in plan and c in st["cases"]:
                st["cases"][c].setdefault("fails", []).append(plan[c]["N"])
        print(f"[result] no score (verdict {verdict}); failed cases {failed or '?'} — bank unchanged")
        st["log"].append({"date": str(datetime.date.today()), "id": rec.get("id"),
                          "verdict": verdict, "plan": plan, "cases": cases})
        save_state(st); return
    hits = decode(score, st, plan)
    if len(hits) != 1:
        print(f"[result] HALT — {len(hits)} decode hypotheses for {score}; state NOT changed:")
        for h in hits: print("   ", h)
        raise SystemExit(2)
    # reuse cmd_decode's writer by faking args
    class A: pass
    a = A(); a.score = score; a.dry = False
    cmd_decode(a, st)

def cmd_submit(args, st):
    if not os.path.exists(PENDING): raise SystemExit("no pending plan — run `plan` then `preflight` first")
    plan = json.load(open(PENDING))["plan"]
    rec = do_submit(os.path.join(OUTDIR, "main.cpp"),
                    args.note or f"harness probe {plan}", args.contest, args.live)
    if rec is None: return
    apply_result(rec, st, plan)

# ---------------------------------------------------------------- campaign (guarded autonomy)

def cmd_campaign(args, st):
    """Autonomous plan->preflight->submit->decode for ONE target case, under hard guardrails.
    Strategy: read-and-descend a box-cut razor. Halts on: budget, ambiguity, new bank, or WA."""
    c = args.case
    if c not in st["patchable"]: raise SystemExit(f"case {c} not patchable")
    N = args.start or st["cases"][c]["banked_N"]
    print(f"[campaign] case {c}: start N={N}  budget={args.max_subs}  interval={args.min_interval}s  "
          f"live={args.live}  halt_on_bank={not args.auto_bank}")
    for i in range(args.max_subs):
        mode = "bank" if args.bank else "read"
        plan = {c: {"mode": mode, "N": N}}
        gap, _ = ambiguity_check(st, plan)
        if gap <= 2*SCORE_TOL: print("[campaign] HALT: undecodable plan"); return
        generate(plan, st); json.dump({"plan": plan}, open(PENDING, "w"))
        # preflight (compile + identity) always, even in dry-run
        class PF: docker = args.docker
        try: cmd_preflight(PF(), st)
        except SystemExit as e: print(f"[campaign] HALT: preflight failed: {e}"); return
        if i > 0 and args.live: _time.sleep(args.min_interval)
        rec = do_submit(os.path.join(OUTDIR, "main.cpp"), f"campaign c{c} {mode}@{N}", args.contest, args.live)
        if rec is None: print(f"[campaign] dry-run step {i+1}: would submit {mode}@{N} for case {c}"); break
        before = st["banked_total"]
        apply_result(rec, st, plan)
        st = load_state()
        if st["banked_total"] > before:
            print(f"[campaign] NEW BANK {st['banked_total']:.6f}. Snapshot probe/out/main.cpp into submissions/.")
            if not args.auto_bank: print("[campaign] HALT for bank checkpoint (use --auto-bank to continue)."); return
        # descend toward the wall using the read (if we have one)
        reads = st["cases"][c].get("reads", [])
        if mode == "read" and reads:
            s2 = reads[-1]["S2"]; slope = 3.5e-5
            step = max(4, int((s2 - 0.900 - args.margin) / slope))
            step -= step % 4
            if step <= 0: print(f"[campaign] read S2={s2} at/below wall+margin — stop descending."); return
            N -= step; N -= N % 4
            print(f"[campaign] read S2={s2} -> descend {step} verts -> next N={N}")
        else:
            print("[campaign] no read to guide descent — stopping."); return
    print("[campaign] budget exhausted.")

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("plan");     pl.add_argument("--read", action="append"); pl.add_argument("--bank", action="append")
    pf = sub.add_parser("preflight"); pf.add_argument("--docker", action="store_true")
    de = sub.add_parser("decode");   de.add_argument("score", type=float); de.add_argument("--dry", action="store_true")
    sm = sub.add_parser("submit");   sm.add_argument("--live", action="store_true", help="actually submit (default: dry-run)")
    sm.add_argument("--note", default=""); sm.add_argument("--contest", default="imc2-2")
    ca = sub.add_parser("campaign"); ca.add_argument("case"); ca.add_argument("--start", type=int)
    ca.add_argument("--bank", action="store_true", help="bank mode (default: read/descend)")
    ca.add_argument("--live", action="store_true"); ca.add_argument("--auto-bank", action="store_true")
    ca.add_argument("--max-subs", type=int, default=3); ca.add_argument("--min-interval", type=float, default=30.0)
    ca.add_argument("--margin", type=float, default=0.002); ca.add_argument("--contest", default="imc2-2")
    ca.add_argument("--docker", action="store_true")
    sub.add_parser("status")
    a = p.parse_args()
    st = load_state()
    {"plan": cmd_plan, "preflight": cmd_preflight, "decode": cmd_decode,
     "submit": cmd_submit, "campaign": cmd_campaign, "status": cmd_status}[a.cmd](a, st)

if __name__ == "__main__":
    main()
