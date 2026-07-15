#!/usr/bin/env python3
"""run_zoo — build + screen the variant zoo on the calibrated c3 instrument.

Each variant is either an env-configured run of the base binary (7 s) or a generated
patched source zoo/build/mein_<name>.cpp (one file per method) built with the judge-family
flags (-O2, no -march=native: flags flip small A/B signs, measured 2026-07-14).

usage:
  py -3 zoo/run_zoo.py --list            # show the catalog
  py -3 zoo/run_zoo.py --smoke           # base + 1 env + 1 patch variant (~3 min)
  py -3 zoo/run_zoo.py --all             # the full zoo (resumable; ~25-40 min first pass)
  py -3 zoo/run_zoo.py --report          # ranked table -> zoo/RANKED.md (any time)
options: --workers N (default 5) | --mesh path (default dragon_n10) | --rung N (default 6610)
         --only name1 name2 ...          # run a subset
"""
import argparse, concurrent.futures as cf, datetime, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "zoo"))
from variants import VARIANTS, BASE_RUNG

SRC     = os.path.join(ROOT, "solver", "mein.cpp")
BUILD   = os.path.join(ROOT, "zoo", "build")
RESULTS = os.path.join(ROOT, "zoo", "results.jsonl")
RANKED  = os.path.join(ROOT, "zoo", "RANKED.md")
MESH    = os.path.join(ROOT, "probe", "cache", "c3cand", "dragon_n10.obj")
WINLIBS = r"C:\Users\simon\AppData\Local\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.POSIX.UCRT.LLVM_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin"
EIGEN   = os.path.join(ROOT, ".phase0", "eigen")

def gxx_env():
    e = dict(os.environ)
    if os.path.isdir(WINLIBS): e["PATH"] = WINLIBS + os.pathsep + e.get("PATH", "")
    return e

def make_source(v):
    """Apply the variant's substitutions to a COPY (one file per method). Anchors must hit exactly once."""
    src = open(SRC, encoding="utf-8").read()
    for old, new in v.get("subs", []):
        n = src.count(old)
        if n != 1:
            raise RuntimeError(f"{v['name']}: anchor hit {n} times (want 1): {old[:60]!r}")
        src = src.replace(old, new)
    out = os.path.join(BUILD, f"mein_{v['name']}.cpp")
    open(out, "w", encoding="utf-8", newline="\n").write(src)
    return out

def build(v):
    """Build a variant binary (or reuse). Returns exe path or (None, err)."""
    os.makedirs(BUILD, exist_ok=True)
    if v["kind"] == "env":
        exe = os.path.join(BUILD, "base.exe")
        cpp = SRC
    elif v["kind"] == "patch_reuse":
        exe = os.path.join(BUILD, f"{v['reuse']}.exe")
        if not os.path.exists(exe): return None, f"reused binary {v['reuse']} not built yet"
        return exe, None
    else:
        exe = os.path.join(BUILD, f"{v['name']}.exe")
        try: cpp = make_source(v)
        except RuntimeError as ex: return None, str(ex)
    if os.path.exists(exe) and os.path.getmtime(exe) > os.path.getmtime(cpp): return exe, None
    r = subprocess.run(["g++", "-O2", "-std=c++17", "-I" + os.path.join(ROOT, "winbuild"),
                        "-I" + EIGEN, cpp, "-o", exe], capture_output=True, text=True, env=gxx_env())
    return (exe, None) if r.returncode == 0 else (None, "compile: " + r.stderr[-400:])

def run_variant(v, exe, mesh, rung):
    env = dict(os.environ); env["G_S2"] = "1"; env["G_C3T"] = str(rung)
    env.update(v.get("env", {}))
    with open(mesh, "rb") as fin:
        r = subprocess.run([exe], stdin=fin, capture_output=True, text=True, timeout=600, env=env)
    m = re.search(r"RC3 V=(\d+) S2n=([\d.]+) S2d=([\d.]+) S2=([\d.]+) t=([\d.]+)", r.stderr)
    if not m: return None
    return dict(N=int(m.group(1)), S2n=float(m.group(2)), S2d=float(m.group(3)),
                S2=float(m.group(4)), t=float(m.group(5)))

def load_results():
    done = {}
    if os.path.exists(RESULTS):
        for line in open(RESULTS):
            try: r = json.loads(line); done[(r["name"], r["rung"], r["mesh"])] = r
            except Exception: pass
    return done

def report(mesh_name):
    done = load_results()
    rows = [r for r in done.values() if r["mesh"] == mesh_name and r.get("S2") is not None]
    base = [r["S2"] for r in rows if r["name"].startswith("base_") and r["rung"] == BASE_RUNG]
    traj = base + [r["S2"] for r in rows if r["name"].startswith("traj_") and r["rung"] == BASE_RUNG]
    if not base: print("no base runs yet"); return
    bmean = sum(base) / len(base)
    sigma = (sum((x - (sum(traj)/len(traj)))**2 for x in traj) / max(1, len(traj)-1)) ** 0.5 if len(traj) > 1 else 0.0
    floor = max(1.5e-3, 2*sigma)
    vmap = {v["name"]: v for v in VARIANTS}
    lines = [f"# Zoo ranking — mesh {mesh_name}, base rung {BASE_RUNG}",
             f"base S2 = {bmean:.6f} (n={len(base)}) | trajectory sigma = {sigma:.2e} | NOISE FLOOR = {floor:.2e}",
             "", "| variant | family | dS2 | dS2n | verdict | expected | note |",
             "|---|---|---|---|---|---|---|"]
    bS2n = sum(r["S2n"] for r in rows if r["name"].startswith("base_") and r["rung"] == BASE_RUNG) / len(base)
    scored = []
    for r in rows:
        if r["rung"] != BASE_RUNG or r["name"].startswith(("base_",)): continue
        d = r["S2"] - bmean; dn = r["S2n"] - bS2n
        v = vmap.get(r["name"], {})
        if r["S2"] == bmean and r["S2n"] == bS2n: verdict = "DUPE(base)=env inert?"
        elif d > floor:  verdict = "** WIN **"
        elif d < -floor: verdict = "NEG"
        else:            verdict = "flat"
        scored.append((d, f"| {r['name']} | {v.get('family','?')} | {d:+.4f} | {dn:+.4f} | {verdict} | {v.get('expect','?')} | {v.get('note','')[:70]} |"))
    for _, line in sorted(scored, key=lambda x: -x[0]): lines.append(line)
    # controls acceptance
    lines += ["", "## Controls acceptance (instrument sign-fidelity)"]
    ok = bad = 0
    for _, line in scored:
        pass
    for r in rows:
        v = vmap.get(r["name"], {})
        if v.get("expect") in ("-", "+") and r["rung"] == BASE_RUNG:
            d = r["S2"] - bmean
            hit = (d < 0) if v["expect"] == "-" else (d > 0)
            ok += hit; bad += (not hit)
            lines.append(f"- {r['name']}: expected {v['expect']}, read {d:+.4f} -> {'OK' if hit else 'MISS'}")
    lines.append(f"\ncontrols: {ok} OK / {bad} MISS  (MISSes above the floor = instrument doubt; investigate before trusting WINs)")
    open(RANKED, "w", newline="\n").write("\n".join(lines) + "\n")
    print("\n".join(lines))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true"); ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--all", action="store_true");  ap.add_argument("--report", action="store_true")
    ap.add_argument("--only", nargs="+", default=None)
    ap.add_argument("--mesh", default=MESH); ap.add_argument("--rung", type=int, default=BASE_RUNG)
    ap.add_argument("--workers", type=int, default=5)
    a = ap.parse_args()
    mesh_name = os.path.basename(a.mesh)

    if a.list:
        for v in VARIANTS:
            print(f"{v['name']:<12} {v['family']:<9} {v['kind']:<11} expect={v.get('expect','?'):<2} {v['note'][:80]}")
        print(f"\n{len(VARIANTS)} variants"); return
    if a.report: report(mesh_name); return

    sel = VARIANTS
    if a.smoke: sel = [v for v in VARIANTS if v["name"] in ("base_a", "rim_100", "areaq")]
    if a.only:  sel = [v for v in VARIANTS if v["name"] in set(a.only)]

    done = load_results()
    todo = [v for v in sel if (v["name"], a.rung if "G_C3T" not in v.get("env", {}) else int(v["env"]["G_C3T"]), mesh_name) not in done]
    print(f"{len(sel)} selected, {len(sel)-len(todo)} already done, {len(todo)} to run")

    # stage 1: builds. Pre-build base ONCE (env variants share it - parallel builds would race on
    # the same output file), then patch variants in parallel, then patch_reuse (needs donors built).
    if any(v["kind"] == "env" for v in todo):
        exe, err = build(dict(name="__base__", kind="env"))
        if err: sys.exit("base build failed: " + err)
    exes = {}
    ph1 = [v for v in todo if v["kind"] == "patch"]
    ph2 = [v for v in todo if v["kind"] != "patch"]
    with cf.ThreadPoolExecutor(max_workers=min(4, a.workers)) as ex:
        exes.update(zip([v["name"] for v in ph1], ex.map(lambda v: build(v), ph1)))
    for v in ph2: exes[v["name"]] = build(v)
    # stage 2: runs
    def work(v):
        exe, err = exes[v["name"]]
        rung = int(v.get("env", {}).get("G_C3T", a.rung))
        rec = dict(name=v["name"], rung=rung, mesh=mesh_name,
                   utc=datetime.datetime.utcnow().isoformat(timespec="seconds"))
        if err: rec["error"] = err
        else:
            try: rec.update(run_variant(v, exe, a.mesh, rung) or {"error": "no RC3 line (crash?)"})
            except subprocess.TimeoutExpired: rec["error"] = "timeout"
        with open(RESULTS, "a") as f: f.write(json.dumps(rec) + "\n")
        print(f"  {v['name']:<12} {'S2=%.6f' % rec['S2'] if 'S2' in rec else rec.get('error','?')}", flush=True)
        return rec
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(work, todo))
    report(mesh_name)

if __name__ == "__main__":
    main()
