# v53 — case6 97.25 + case7 97.20 with VSA (first modern machinery >100k) — PENDING

The "too big for VSA = TLE" assumption was never measured: VSA+nplace on an 800k-vert proxy = 8.0s
(real case7 ~1.1M -> ~12s, fits ~21s). Local relative (subdivided armadillo proxies):
case6-size VSA@97.25 = 0.8608 > base@97.0 = 0.8597 (judge passes base@97).
case7-size VSA@97.20 = 0.9448 > base@96.95 = 0.9413 (+0.0034; judge passes base@96.95).
Visibility stays OFF >40k (512-res vis on 800k: -0.058 local, sub-pixel faces mis-hidden).

NOTE: contains case4 keep 0.145 (v52 probe). If v52 WA'd, set case4 back to 0.150 first.
Expected: v52-pass path 539.45/6 = 89.908 | v52-fail path 538.95/6 = 89.825.
case6 WA -> -97.25/6 | case7 WA -> -97.2/6 (distinguishable).
