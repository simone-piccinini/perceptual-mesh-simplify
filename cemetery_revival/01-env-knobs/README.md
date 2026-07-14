# Revival 1 — Lo spazio delle manopole env sul c3 (offline, specchio)

STATE: CHIUSO — la config bancata è ottima nel suo spazio di manopole. 2026-07-14, 0 submission.
Strumento: `instrument/meshes/c3_proxy_t3.obj` + binario bancato (48cfbc6, win-patch), rung 6620.

## Domanda
Il ladder di Emanuel lascia punti sul tavolo nelle variabili d'ambiente del solver? (Prima dello
specchio, ogni test costava una submission — questo spazio non era mai stato spazzolato.)

## Metodo
Binario bancato pulito, proxy c3 calibrato, `G_C3T=6620 G_S2=1`, una manopola per run,
delta S2 vs baseline 0.913770. Soglia di rilevanza ±0.001 (rumore misurato ±0.0002).

## Risultati (12 varianti)
| Manopola | S2 | ΔS2 | Verdetto |
|---|---|---|---|
| BASELINE | 0.913770 | — | riferimento |
| G_NMETRIC=4 (σxy temperata) | 0.912256 | **−0.0015** | NEGATIVA — famiglia σxy-analitica chiusa (3 e 4) |
| G_CT=500 (coda profonda) | 0.913593 | −0.0002 | rumore |
| G_LSITER=2 | 0.913626 | −0.0001 | rumore |
| G_FLIPON=1 | 0.914032 | **+0.00026** | unico +; costa +2.3s → rischio TLE, EV negativo |
| G_MPC=2 / G_MPC=4 | 0.91387 / 0.91386 | +0.0001 | rumore |
| G_RIMK=0 (rim off) | 0.913896 | +0.0001 | rumore (rim paga al muro, non a 6620) |
| G_PHASEB=10 | 0.913890 | +0.0001, +2s | rumore, costa tempo |
| G_MINI=14 | 0.913870 | +0.0001 | rumore |
| G_SIL2=400 | — | — | HANG locale >10min: manopola da evitare |

## Conclusione
Nessun pasto gratis nello spazio env: la configurazione bancata è localmente ottima.
Verificato in ~25 minuti offline; equivalente pre-specchio: ~10 submission cieche.
