# Revival 2 — Best-of-N / basin-diversity (ARCHITECT-REVIEW §3.B.3)

STATE: PREMESSA FALSIFICATA offline — lo spread non esiste dentro un binario. 2026-07-14, 0 submission.
Strumento: proxy c3 + binario bancato con jitter deterministico sui costi (G_BSEED/G_BAMP).

## L'idea (dal parcheggio)
Il punteggio a conteggio fisso "balla" tra draw (±0.001-0.002/coin, e ±0.013 tra famiglie): far
girare N traiettorie di decimazione perturbate, scegliere la migliore col self-score (che = oracle,
verificato), rifinire solo quella. Stima pre-test: +0.15/+0.35 sul totale.

## Metodo
Patch minima nel binario bancato: `cost *= 1 + amp*hash(i,j,seed)` in Evaluate (jitter
deterministico dell'ordine dei collassi). Proxy c3, rung 6620, 6 seed × 4 ampiezze.

## Risultati
| Ampiezza jitter | Spread S2 (max−min sui seed) |
|---|---|
| ±0.01% (riordina quasi-pareggi) | 3.6e-4 |
| ±0.1% | 0.7e-4 |
| ±1% | 1.4e-4 |
| **±10% (stravolge l'ordine)** | **2.3e-4** |

Anche perturbando i costi del ±10%, la qualità finale resta entro ±0.0002 dal baseline.

## Perché (lettura)
La pipeline è un IMBUTO: ordering VSA + steering Pivot-A + refine convergono quasi allo stesso
punto da traiettorie diverse — il refine "lava via" le differenze di percorso. Lo spread storico
tra draw veniva dai TAGLI DI TEMPO (uccisi dalla determinizzazione di Emanuel) e dalle differenze
FP tra binari — non è raccoglibile dall'interno di un processo.

## Conclusione
Best-of-N raccoglierebbe ~+0.0001 (≈8 vertici, +0.006 totale): non vale la macchina (che avrebbe
richiesto una ristrutturazione del cuore del solver). Idea chiusa in 6 minuti; equivalente
pre-specchio: settimane di build + submission.
