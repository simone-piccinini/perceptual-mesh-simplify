# Revival 4 — Hoppe attribute-quadric placement (R-α, ARCHITECT-REVIEW §3.B.1)

STATE: MORTA — neutro-negativa sullo specchio, nessun picco dose-risposta. 2026-07-14, 0 submission.
Strumento: proxy c3 calibrato + binario bancato con port Hoppe (da main.cpp f10f2ab), rung 6620.

## L'idea (dal parcheggio)
Il placement bancato minimizza l'errore di POSIZIONE (quadrica QEM) e sceglie tra candidati
discreti per l'errore di normale. Hoppe (Vis'99) estende la quadrica con i termini di attributo:
il campo di normali per faccia come interpolante lineare dei corner, minimizzazione congiunta
(posizione, normale), eliminazione dell'attributo via Schur → un solve 3×3 il cui ottimo
CONTINUO minimizza anche l'errore di normale interpolata. I doc la tenevano "PARKED, NOT dead":
giudicata neutra solo sul proxy liscio rotto (Process Law #2 esigeva un test su strumento che
trasferisce). Questo è quel test.

## Metodo
Port del codice storico (commit f10f2ab, già hand-rolled in double puri — compile-cliff safe)
nel motore bancato attuale (48cfbc6): accumulo per-faccia in Initialize, candidato continuo nel
set di Evaluate (giudicato dallo stesso incident_ndist), merge in Collapse. Env G_HOPPE/G_HW.
A/B sullo specchio a 6620, sweep del peso dell'attributo.

## Risultati (baseline G_HOPPE=0: S2=0.913870; rumore misurato ±0.0004)
| HW | 0.1 | 0.2 | 0.3 | 0.5 | 1.0 | 3.0 |
|----|-----|-----|-----|-----|-----|-----|
| ΔS2 | −0.0002 | −0.0006 | +0.00015 | −0.0002 | −0.0003 | −0.0005 |

Nessuna curva dose-risposta: scatter attorno allo zero, deriva negativa ai pesi alti. Il
+0.00015 a HW=0.3 è una fluttuazione isolata dentro il rumore.

## Il dettaglio istruttivo (scomposizione a HW=0.3)
S2n (normali) **+0.0007** — Hoppe fa esattamente ciò che promette — ma S2d (profondità)
**−0.0004**: l'ottimo congiunto si sposta dal punto di minima distorsione di posizione, la
silhouette/profondità paga, e il refine non lo recupera (ascende solo le normali). Il guadagno
teorico esiste ma viene mangiato dal costo geometrico.

## Conclusione
R-α chiusa su un righello che trasferisce (il criterio che i doc richiedevano). Con questa, il
backlog del progetto è SVUOTATO: manopole, best-of-N, ri-cicli, Hoppe (offline) + c4-jam,
nmetric, redistribuzione σxy (judge-side) — tutte le strade elencate sono misurate e chiuse.
Ciò che separa dal 91 è un meccanismo non ancora concepito; lo specchio ne valuta ogni
candidato in ~20 secondi. Port riusabile: il diff Hoppe resta in `_hoppe_test.cpp` era-48cfbc6
(rigenerabile da git: `git diff f10f2ab~1..f10f2ab -- solver/main.cpp`).
