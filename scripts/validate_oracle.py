"""Self-check that the oracle reproduces the two facts we know for certain.

  1. Identity:    score(M, M)  -> FinalSSIM = 1.0,  compression = 0%.
  2. Sample case: the statement says the 9->8 vertex cube collapse gives
                  FinalSSIM = 1.0 and compression ~ 11.11%, and is valid.

If both hold, the renderer + SSIM + validity machinery is wired correctly.
Run:  python scripts/validate_oracle.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from imc_eval import evaluate, load_mesh  # noqa: E402

DATA = os.path.join(os.path.dirname(__file__), "..", "tests", "data")


def main():
    Vo, Fo = load_mesh(os.path.join(DATA, "sample.in"))
    Vs, Fs = load_mesh(os.path.join(DATA, "sample.out"))
    ok = True

    rid = evaluate(Vo, Fo, Vo, Fo)
    print(f"[identity] FinalSSIM={rid.final_ssim:.6f}  compression={rid.compression:.2f}%  passed={rid.passed}")
    if abs(rid.final_ssim - 1.0) > 1e-6:
        print("   !! expected FinalSSIM == 1.0"); ok = False
    if abs(rid.compression) > 1e-9:
        print("   !! expected compression == 0"); ok = False

    rs = evaluate(Vo, Fo, Vs, Fs)
    print(f"[sample]   FinalSSIM={rs.final_ssim:.6f}  compression={rs.compression:.2f}%  "
          f"valid={rs.validity['all_ok']}  passed={rs.passed}")
    if rs.final_ssim < 0.999:
        print("   !! expected FinalSSIM ~ 1.0"); ok = False
    if abs(rs.compression - 11.11) > 0.1:
        print("   !! expected compression ~ 11.11%"); ok = False
    if not rs.passed:
        print("   !! expected the sample to PASS"); ok = False

    print()
    print("ORACLE VALIDATION:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
