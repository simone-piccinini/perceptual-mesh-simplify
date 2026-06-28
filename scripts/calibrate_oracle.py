#!/usr/bin/env python3
"""Calibrate the oracle's GUESSED parameters against the real judge.

The judge is secret; the oracle had to guess the SSIM blend weights (lambda_normal/
lambda_depth) and the SSIM window (box vs gaussian). These can only be pinned by
comparing the oracle's predictions with the judge's real verdicts. This script does
that, deterministically and WITHOUT any network automation: it PREPARES cases and
ANALYSES verdicts that you enter by hand.

Contest rules (verified): no penalty for wrong/multiple submissions, no documented
submission cap, only the best submission counts. So calibration is NOT limited to a
few points — more calibration points = a sharper fit. The only caveat is a possible
undocumented cooldown: treat it as a wait between submissions, not a hard limit.

Two steps:

  1) python scripts/calibrate_oracle.py generate
       Builds DISCRIMINATING near-gate cases (where different parameter guesses would
       give OPPOSITE accept/reject verdicts — the only cases that teach anything),
       saves the solver outputs as .obj, records the per-config predictions in
       calibration/cases.json, and writes a calibration/verdicts.json template.
       You then submit those outputs to the judge and fill in the real verdicts.

  2) python scripts/calibrate_oracle.py calibrate
       Reads your verdicts, grid-searches (lambda, window) for the combination that
       best matches the judge, reports how much it cuts the disagreement, and saves
       the tuned parameters to calibration/oracle_config.json (which evaluate() can
       load). If the cases are too few or non-discriminating, it says so and suggests
       which case to submit next.

HONEST CAVEAT: the judge scores its 7 HIDDEN cases; these calibration meshes are
chosen by you. A good fit here is the best available signal but does NOT guarantee a
perfect fit on the hidden cases. More (and more discriminating) points = more trust.
"""

import json
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "tests"))

import check_structural_validity as T            # noqa: E402  generators + solver helpers
import check_constraints_and_fidelity as C       # noqa: E402  gen_irregular0, etc.
from imc_eval import evaluate, OracleConfig       # noqa: E402

CAL_DIR = os.path.join(REPO, "calibration")
CASES_DIR = os.path.join(CAL_DIR, "cases")
CASES_JSON = os.path.join(CAL_DIR, "cases.json")
VERDICTS_JSON = os.path.join(CAL_DIR, "verdicts.json")
CONFIG_JSON = os.path.join(CAL_DIR, "oracle_config.json")

GATE = 0.90

# The grid of candidate parameter combinations to search over. Only the genuinely
# ambiguous knobs vary (blend weights + window); the low-impact edge/tie knobs stay
# at default. lambda_depth is 1 - lambda_normal so the weights sum to 1.
GRID_LAMBDA_N = [0.50, 0.55, 0.60, 0.65, 0.70]
GRID_WINDOW = ["box", "gaussian"]


def grid_configs():
    out = []
    for ln in GRID_LAMBDA_N:
        for w in GRID_WINDOW:
            out.append(OracleConfig(lambda_normal=ln, lambda_depth=round(1 - ln, 4),
                                    ssim_window=w))
    return out


def config_key(cfg):
    return f"ln{cfg.lambda_normal:.2f}_{cfg.ssim_window}"


# Proxies where the perceptual gate actually bites (curved, contest-relevant), so a
# near-gate frac exists and the window/weight choice can flip the verdict.
def proxies():
    return [
        ("sfera_642", lambda: T.gen_sphere(3)),
        ("sfera_2562", lambda: T.gen_sphere(4)),
        ("toro_392", lambda: T.gen_torus()),
        ("irregolare_642", lambda: (lambda VF: (VF[0], VF[1] - 1))(C.gen_irregular(3))),
    ]


def _channels(Vin, Fin1, Vout, Fout1, window):
    """Per-view (s_normal, s_depth) under a given window (lambda-independent), plus
    the config-independent hard-constraint facts. One evaluate() call per window;
    every lambda is then a cheap re-blend."""
    cfg = OracleConfig(ssim_window=window)            # lambda 0.5/0.5 (irrelevant here)
    rep = evaluate(Vin, Fin1 - 1, Vout, Fout1 - 1, cfg)
    chan = [(pv["normal"], pv["depth"]) for pv in rep.per_view]
    return chan, rep.hausdorff_ok, rep.validity["all_ok"], rep.compression


def _final_ssim(chan, ln, ld):
    return float(np.mean([ln * n + ld * d for n, d in chan]))


def _predict(final_ssim, haus_ok, valid):
    return "ACCEPTED" if (final_ssim >= GATE and haus_ok and valid) else "WRONG_ANSWER"


def _predictions_for_case(chan_by_window, haus_ok, valid):
    """Predicted (final_ssim, verdict) for every grid config."""
    preds = {}
    for cfg in grid_configs():
        chan = chan_by_window[cfg.ssim_window]
        fs = _final_ssim(chan, cfg.lambda_normal, cfg.lambda_depth)
        preds[config_key(cfg)] = {"final_ssim": round(fs, 5),
                                  "verdict": _predict(fs, haus_ok, valid)}
    return preds


def generate():
    os.makedirs(CASES_DIR, exist_ok=True)
    solver = T.build_solver()
    print(f"[solver] {solver}")
    print("Cerco casi DISCRIMINANTI vicino al gate (dove i parametri cambiano il verdetto)...\n")

    fracs = [0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.13, 0.16, 0.20]
    cases = []
    for name, gen in proxies():
        V0, F0 = gen()
        V = np.ascontiguousarray(V0, np.float64); F1 = np.ascontiguousarray(F0, np.int64) + 1
        obj_in = T.mesh_to_obj(V, F1)
        best = None
        for fr in fracs:
            try:
                _, _, Vo, Fo = T.parse_obj(T.run_solver(solver, obj_in, fr))
            except Exception:
                continue
            chan_box, haus_ok, valid, comp = _channels(V, F1, Vo, Fo, "box")
            chan_gau, _, _, _ = _channels(V, F1, Vo, Fo, "gaussian")
            chan_by_window = {"box": chan_box, "gaussian": chan_gau}
            preds = _predictions_for_case(chan_by_window, haus_ok, valid)
            default_fs = preds[config_key(OracleConfig())]["final_ssim"]
            # lambda-discriminating (the HIGH-impact knob): box verdict flips across
            # the lambda grid. window-discriminating: any grid config disagrees.
            box_verdicts = {preds[f"ln{ln:.2f}_box"]["verdict"] for ln in GRID_LAMBDA_N}
            lambda_disc = len(box_verdicts) > 1
            any_disc = len({p["verdict"] for p in preds.values()}) > 1
            dist = abs(default_fs - GATE)
            key = (0 if lambda_disc else 1, 0 if any_disc else 1, dist)
            if best is None or key < best[0]:
                best = (key, fr, Vo, Fo, preds, default_fs, comp, haus_ok, valid,
                        lambda_disc or any_disc, lambda_disc)
        if best is None:
            print(f"  {name}: nessun output valido, salto.")
            continue
        _, fr, Vo, Fo, preds, default_fs, comp, haus_ok, valid, disc, lambda_disc = best
        cid = f"{name}_f{fr}"
        with open(os.path.join(CASES_DIR, cid + "_input.obj"), "w") as fh:
            fh.write(obj_in)
        with open(os.path.join(CASES_DIR, cid + "_output.obj"), "w") as fh:
            fh.write(T.mesh_to_obj(Vo, Fo))
        cases.append({
            "id": cid, "proxy": name, "frac": fr,
            "v_in": len(V), "v_out": len(Vo), "compression": round(comp, 2),
            "hard_ok": bool(haus_ok and valid),
            "default_final_ssim": default_fs,
            "discriminating": bool(disc),
            "lambda_discriminating": bool(lambda_disc),
            "predictions": preds,
            "output_obj": os.path.relpath(os.path.join(CASES_DIR, cid + "_output.obj"), REPO),
            "input_obj": os.path.relpath(os.path.join(CASES_DIR, cid + "_input.obj"), REPO),
        })
        tag = ("DISCRIMINANTE su lambda" if lambda_disc
               else "discriminante su finestra" if disc
               else "non discriminante (vicino al gate)")
        print(f"  {name}: frac={fr}  compr={comp:.1f}%  default SSIM={default_fs:.4f}  [{tag}]")

    with open(CASES_JSON, "w") as fh:
        json.dump({"gate": GATE, "grid": [config_key(c) for c in grid_configs()],
                   "cases": cases}, fh, indent=2)

    # verdicts template (do not overwrite an existing, partially filled one)
    if not os.path.exists(VERDICTS_JSON):
        tmpl = {c["id"]: {"judge": "", "constraint": "", "score": None} for c in cases}
        with open(VERDICTS_JSON, "w") as fh:
            json.dump(tmpl, fh, indent=2)

    ndisc = sum(1 for c in cases if c["discriminating"])
    print(f"\nSalvati {len(cases)} casi in {os.path.relpath(CASES_JSON, REPO)} "
          f"({ndisc} discriminanti).")
    print(f"File .obj in {os.path.relpath(CASES_DIR, REPO)}/")
    print(f"\nORA: sottometti gli output al giudice e compila '{os.path.relpath(VERDICTS_JSON, REPO)}'")
    print("     con 'judge': 'ACCEPTED' o 'WRONG_ANSWER' (e 'constraint'/'score' se noti).")
    print("     Poi:  python scripts/calibrate_oracle.py calibrate")
    print("\nNota: il giudice valuta i suoi 7 casi nascosti; questi sono casi tuoi. Una buona")
    print("      concordanza qui e' il miglior segnale disponibile, non una garanzia.")
    return 0


def calibrate():
    if not os.path.exists(CASES_JSON):
        print("Manca calibration/cases.json. Esegui prima:  calibrate_oracle.py generate")
        return 1
    with open(CASES_JSON) as fh:
        data = json.load(fh)
    cases = data["cases"]
    verdicts = {}
    if os.path.exists(VERDICTS_JSON):
        with open(VERDICTS_JSON) as fh:
            verdicts = json.load(fh)

    labelled = [c for c in cases
                if verdicts.get(c["id"], {}).get("judge", "") in ("ACCEPTED", "WRONG_ANSWER")]
    print(f"Casi con verdetto reale inserito: {len(labelled)}/{len(cases)}")
    if len(labelled) == 0:
        print("Nessun verdetto reale. Compila calibration/verdicts.json e riprova.")
        return 1

    real = {c["id"]: verdicts[c["id"]]["judge"] for c in labelled}
    real_set = set(real.values())

    # score each grid config: how many real verdicts it reproduces
    scores = {}
    for cfg in grid_configs():
        k = config_key(cfg)
        match = sum(1 for c in labelled if c["predictions"][k]["verdict"] == real[c["id"]])
        scores[k] = match
    default_k = config_key(OracleConfig())
    best_k = max(scores, key=lambda k: (scores[k], k == default_k))  # tie -> prefer default
    n = len(labelled)

    print(f"\nGriglia (parametri -> verdetti azzeccati su {n}):")
    for k in sorted(scores, key=lambda k: -scores[k]):
        star = "  <- default" if k == default_k else ("  <- MIGLIORE" if k == best_k else "")
        print(f"   {k:16s}  {scores[k]}/{n}{star}")

    print(f"\nDefault ({default_k}): {scores[default_k]}/{n} azzeccati.")
    print(f"Migliore ({best_k}): {scores[best_k]}/{n} azzeccati "
          f"(+{scores[best_k] - scores[default_k]} rispetto al default).")

    top = [k for k, v in scores.items() if v == scores[best_k]]
    if len(set(scores.values())) == 1:
        # every config scores the same -> these cases carry no information
        print("\n⚠️  I casi attuali NON distinguono i parametri (ogni combinazione "
              "azzecca lo stesso numero).")
        disc = [c["id"] for c in cases if c.get("lambda_discriminating") and c["id"] not in real]
        if disc:
            print(f"    Sottometti anche un caso discriminante su lambda: {disc[0]}")
        else:
            print("    Genera piu' casi vicino al gate (calibrate_oracle.py generate).")
    elif len(top) > 1:
        # there is signal, but several configs tie for first
        print(f"\n⚠️  {len(top)} combinazioni pareggiano in cima ({', '.join(sorted(top))});")
        print("    scelta la meno estrema. Servono piu' casi vicino al gate per separarle.")

    # save the tuned config
    ln = float(best_k.split("_")[0][2:])
    win = best_k.split("_")[1]
    best_cfg = OracleConfig(lambda_normal=ln, lambda_depth=round(1 - ln, 4), ssim_window=win)
    best_cfg.save(CONFIG_JSON)
    print(f"\nParametri tarati salvati in {os.path.relpath(CONFIG_JSON, REPO)}:")
    print(f"   lambda_normal={best_cfg.lambda_normal}  lambda_depth={best_cfg.lambda_depth}  "
          f"ssim_window={best_cfg.ssim_window}")
    print("   Caricali con: OracleConfig.load('calibration/oracle_config.json')")
    print(f"\nOnesta': taratura su {n} punti. Piu' punti di calibrazione = piu' affidabile; "
          "resta una stima del giudice segreto.")
    return 0


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "generate":
        return generate()
    if cmd == "calibrate":
        return calibrate()
    print(__doc__)
    print("Uso:  python scripts/calibrate_oracle.py [generate|calibrate]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
