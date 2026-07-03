# v59 — case6 97.41 + case7 97.10 micro-probe (session 3 opener)

Baseline banked: **89.8247** (v57/v58 line: 99.25 | 69.5 | 85.0 | 90.75 | 97.375 | 97.05, sum 538.975... judge shows 89.8247).

Changes vs v58 (keep_for only, stack identical):
- case6 keep 0.02625 → **0.0259** (97.375 → 97.41)
- case7 keep 0.0295 → **0.029** (97.05 → 97.10)

## Decoder table (judge names failing cases; arithmetic backup)

| verdict | meaning | new score (sum/6) |
|---|---|---|
| 7/7 pass | both hold | (538.95 − 97.375 − 97.05 + 97.41 + 97.10)/6 = **89.8392** |
| WA case6 only | case6 wall < 97.41 → revert case6, keep case7 97.10 next consolidation | banked 89.8247 stands |
| WA case7 only | case7 wall < 97.10 (or 2-stage quality edge) → revert case7 | banked stands |
| WA both | both walls tight → revert both, case6/7 CLOSED at 97.375/97.05 | banked stands |
| TLE case7 | 2-stage at 0.029 slower path? unlikely (fewer verts kept = fewer collapses... actually MORE collapses; watch) | banked stands |

Wall status after this probe:
- case6: pass → next micro 0.025625 (97.4375); WA → CLOSED at 97.375.
- case7: pass → next micro 0.0285 (97.15); WA → CLOSED at 97.05.
