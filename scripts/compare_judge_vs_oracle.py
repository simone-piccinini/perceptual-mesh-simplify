#!/usr/bin/env python3
"""Compare the oracle's prediction with the real judge verdict, and keep a history.

This closes the loop: every time you submit something and learn the judge's real
verdict, this records whether the oracle PREDICTED it correctly — so over time you
see if the oracle is getting more trustworthy as you calibrate it.

It is DISTINCT from calibrate_oracle.py:
  * calibrate_oracle.py  TUNES the oracle's guessed parameters to match the judge.
  * this script          MEASURES agreement with the current parameters and logs it.

TWO DIFFERENT THINGS — never conflated in the output:
  * "MIGLIORAMENTO SOLUZIONE" = how much the SOLVER compresses (your contest score).
  * "CALIBRAZIONE ORACOLO"    = how well the ORACLE predicts the judge. THIS SCRIPT
                                is only about the second.

No network automation: it reads judge verdicts you entered by hand and the cases
prepared by calibrate_oracle.py (or any input/output .obj pair you pass).

Usage:
  python scripts/compare_judge_vs_oracle.py                 # use calibration/cases.json
  python scripts/compare_judge_vs_oracle.py in.obj out.obj ACCEPTED   # a single ad-hoc pair
"""

import datetime
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from imc_eval import evaluate, load_mesh, OracleConfig, DEFAULT_CONFIG  # noqa: E402

CAL_DIR = os.path.join(REPO, "calibration")
CASES_JSON = os.path.join(CAL_DIR, "cases.json")
VERDICTS_JSON = os.path.join(CAL_DIR, "verdicts.json")
CONFIG_JSON = os.path.join(CAL_DIR, "oracle_config.json")
HISTORY = os.path.join(CAL_DIR, "judge_history.jsonl")
GATE = 0.90


def current_config():
    if os.path.exists(CONFIG_JSON):
        return OracleConfig.load(CONFIG_JSON), "calibrata (calibration/oracle_config.json)"
    return DEFAULT_CONFIG, "default (non ancora calibrata)"


def oracle_predict(input_obj, output_obj, cfg):
    Vo, Fo = load_mesh(input_obj)
    Vs, Fs = load_mesh(output_obj)
    rep = evaluate(Vo, Fo, Vs, Fs, cfg)
    verdict = "ACCEPTED" if rep.passed else "WRONG_ANSWER"
    return verdict, rep.final_ssim, rep.compression


def _collect_cases(argv):
    """Yield (case_id, input_obj, output_obj, real_verdict)."""
    if len(argv) >= 4:
        in_obj, out_obj, real = argv[1], argv[2], argv[3].upper()
        yield ("ad-hoc", in_obj, out_obj, real)
        return
    if not os.path.exists(CASES_JSON):
        return
    cases = json.load(open(CASES_JSON))["cases"]
    verdicts = json.load(open(VERDICTS_JSON)) if os.path.exists(VERDICTS_JSON) else {}
    for c in cases:
        real = verdicts.get(c["id"], {}).get("judge", "")
        if real in ("ACCEPTED", "WRONG_ANSWER"):
            yield (c["id"], os.path.join(REPO, c["input_obj"]),
                   os.path.join(REPO, c["output_obj"]), real)


def main(argv):
    cfg, cfg_desc = current_config()
    rows = list(_collect_cases(argv))
    if not rows:
        print("Nessun caso con verdetto reale. Prepara i casi e i verdetti con")
        print("  python scripts/calibrate_oracle.py generate   (poi compila verdicts.json)")
        print("oppure passa una coppia:  compare_judge_vs_oracle.py in.obj out.obj ACCEPTED")
        return 1

    print("=" * 78)
    print(" CALIBRAZIONE ORACOLO — quanto l'oracolo predice bene il giudice")
    print(f" (config oracle: {cfg_desc})")
    print(" NB: e' diverso dal MIGLIORAMENTO SOLUZIONE = quanto comprime il solver.")
    print("=" * 78)
    print("  {:18s} {:>16s}   {:>13s}   {:8s} {}".format(
        "caso", "oracolo predice", "giudice reale", "accordo", "se no: direzione"))

    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    agree_n = 0
    hist_lines = []
    for cid, in_obj, out_obj, real in rows:
        pred, fs, comp = oracle_predict(in_obj, out_obj, cfg)
        agree = (pred == real)
        agree_n += agree
        oracle_str = (f"{pred} ({comp:.0f}%)" if pred == "ACCEPTED" else pred)
        if agree:
            direction = ""
        elif pred == "ACCEPTED" and real == "WRONG_ANSWER":
            direction = f"oracolo troppo OTTIMISTA (SSIM {fs:.3f}, {fs - GATE:+.3f} vs gate)"
        else:
            direction = f"oracolo troppo PESSIMISTA (SSIM {fs:.3f}, {fs - GATE:+.3f} vs gate)"
        print("  {:18s} {:>16s}   {:>13s}   {:8s} {}".format(
            cid, oracle_str, real, "si'" if agree else "NO", direction))
        hist_lines.append({"when": stamp, "case": cid, "oracle_verdict": pred,
                           "oracle_final_ssim": round(fs, 5), "judge_verdict": real,
                           "agree": bool(agree), "config": cfg.to_dict()})

    n = len(rows)
    print("-" * 78)
    print(f" SINTESI: su {n} casi, l'oracolo ha predetto il verdetto giusto in "
          f"{agree_n}/{n} ({100*agree_n/n:.0f}%).")

    # append-only history so the trajectory of oracle reliability is visible over time
    os.makedirs(CAL_DIR, exist_ok=True)
    with open(HISTORY, "a") as fh:
        for line in hist_lines:
            fh.write(json.dumps(line) + "\n")
    total = sum(1 for _ in open(HISTORY)) if os.path.exists(HISTORY) else 0
    print(f" Storico aggiornato: {os.path.relpath(HISTORY, REPO)} ({total} righe totali).")
    print()
    print(" Onesta': il verdetto del giudice sui 7 casi NASCOSTI e' la verita'; questi")
    print(" sono casi scelti da te. Alta concordanza qui e' il miglior indicatore")
    print(" disponibile, ma non garantisce concordanza perfetta sui casi nascosti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
