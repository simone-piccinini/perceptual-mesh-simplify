# Revival 3 — Ciclo completo decimate→refine→re-decimate (ARCHITECT-REVIEW §3.B.2)

STATE: NEGATIVO MONOTONO offline + variante Q-rebuild già falsificata sul giudice. 2026-07-14, 0 submission.
Strumento: proxy c3 + binario bancato via argomenti locali (keep) — zero codice nuovo per il test.

## L'idea (dal parcheggio)
R1 (burst di refine in mezzo alla decimazione) è judge-negativo ×2, ma il ciclo COMPLETO è
strutturalmente diverso: decima a N alto → refine completo (i vertici salgono all'ottimo
percettivo) → ri-esegui l'ordering e ri-decima su QUELLA geometria → refine finale. Esplora un
bacino che il one-shot non vede.

## Metodo (scorciatoia senza codice)
Il solver ha argomenti locali (`argv[3]` = keep) che fissano il conteggio della decimazione
principale; `G_C3T` fissa la ri-decimazione finale del blocco RC3. Alzando keep si ottiene
esattamente il ciclo: più alto il keep, più grande la ri-decimazione su geometria rifinita.

## Risultati (rung finale 6620, baseline keep=0.2997 → S2=0.913770)
| keep | dec. principale a | ri-decimazione su geometria rifinita | S2 | ΔS2 |
|---|---|---|---|---|
| 0.35 | ~8.120 | −1.500 v | 0.913208 | −0.0006 |
| 0.45 | ~10.440 | −3.820 v | 0.911970 | −0.0018 |
| 0.60 | ~13.920 | −7.300 v | 0.911177 | **−0.0026** |

Più ri-decimazione sulla geometria rifinita, PEGGIO — monotono, ben oltre il rumore (±0.0002).

## La variante "quadriche stantie" è già morta
Sospetto ovvio: dopo il refine le quadriche descrivono la geometria vecchia → ricostruirle
salverebbe il ciclo? Già provato dal team sul giudice: **RLIVE-Q @4150 (sub 19898329): WA — "the
stale-quadric theory is FALSIFIED"** (ATTEMPT_LOG). Il ciclo non si salva con il Q-rebuild.

## Lettura
Il refine porta i vertici in posizioni percettivamente ottime PER QUEL conteggio; ri-decimare da lì
distrugge quell'ottimizzazione (i collassi spostano i vertici rifiniti) e l'ordering non ricava
informazione extra dalla geometria rifinita. La strada one-shot (ordering sull'originale) resta
la migliore nota.

## Conclusione
Famiglia "ri-cicli" chiusa: R1 (judge ×2), ciclo completo (offline, monotono), Q-rebuild (judge).
Test costato 3 minuti; equivalente pre-specchio: giorni di tuning + submission multiple.
