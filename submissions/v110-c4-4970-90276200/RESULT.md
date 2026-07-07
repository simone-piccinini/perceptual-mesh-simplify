# v110 — c4 harvest @4970 (v108 binary family)

**Score: 90.276200 — 7/7 PASS (NEW BANK, +0.009446 over v108's 90.266754)**

First rung of the case-4 razor re-harvest, landed. Case 4 passed at N=4970 (was banked 4990);
all six other cases reproduced their banked scores. Predicted 90.276199, delivered 90.276200
— exact to six decimals, re-confirming V_c4 = 35,292 and byte-exact reproduction of the rest.

**The one lesson that made it work (see docs/Future/c4-harvest-ladder.md):** the first rung-1
attempt WA'd at 75.956618 (case-4 zero) because it laddered from the compile-*headroom* binary
family. Case 4 is box-cut ⇒ its output depends on binary timing/layout ⇒ each binary family has
its own per-run S mean, and the headroom family's sat just below 0.900 while v108's sat just
above. Rung 1b fixed it: **v108's exact source with a single constant changed**
(`Decimate(4990)` → `Decimate(4970)`), staying in the 2/2-proven family. Standing rule: bank
attempts use the v108-family source + minimal constant edits; the headroom base (N=5150) is the
dev/experiment base only.

Composition: c4 ≈ 85.81 (V′≈4970), all others banked. Next rung: 4950 (→ 90.285644 if it holds).
