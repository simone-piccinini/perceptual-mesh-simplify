# SIGMAXY-REMESH — il meccanismo costruttivo σxy e lo sblocco del compile-cliff

STATE: meccanismo costruito e manifold-validato · ipotesi falsificata sul giudice (WA ×4, confound
esclusi) · compile-cliff SBLOCCATO (hand-roll, judge-validated) — tecnica riusabile per il team
Branch: `sigmaxy-handroll` (figlio di `wall-probes`) · Autore: Alberto

## L'ipotesi (il "paradigma nuovo")

Il termine che vincola il c3 è la struttura σxy del campo di normali (THEORY). La decimazione
ottimizza l'errore geometrico/normale — obiettivo DIVERSO da ciò che il giudice paga. Idea:
**redistribuzione costruttiva a conteggio fisso** — aggiungere DOF (edge split) dove il deficit
renderizzato è alto, toglierli (collapse) dove è saturo, con refine dei nuovi vertici.

## Cosa è stato costruito (nel `solver/mein.cpp` di questo branch)

1. **`edge_split(u, v, p)`** — split manifold-safe di un edge interno: 2 facce → 4, orientazione
   preservata (regola edge-condiviso-opposto), stesse convenzioni di `Collapse` (vfaces/alive/
   face_alive; il chiamante gestisce alive_count). Il vecchio `g_remesh==2` (split-realloc) era
   stato rimosso perché crashava; questo è nuovo e validato: **500 split su c3band → manifold
   perfetto** (ogni edge condiviso da 2 facce, 0 degeneri, 0 indici rotti). `[LOCAL, validato]`
2. **`sigma_redistribute(nswap, rtime)`** — un round di redistribuzione: rank degli edge per
   deficit normale renderizzato (riusa remesh_cache_render/g_rfs/g_orig_n di remesh_flip_local),
   split dei top-deficit, `mini_refine`, collapse dei bottom-deficit fino a ripristinare il
   conteggio (bilanciato 300/300). Sort-free (selezione a soglie multiple) e collasso QEM
   hand-rolled (Cramer 3×3) per la RAM di compilazione.

## I 4 judge-test (tutti WA sul c3, confound esclusi uno a uno)

| Sub | Config | Esito | Confound escluso |
|---|---|---|---|
| **20043585** | redist midpoint, sil2-swap (budget-neutro) | c3 WA 22.1s; c7 passò a 22.2s → c3 COMPLETATO | (primo run giudice del meccanismo) |
| **20044274** | collapse QEM (Cramer hand-rolled) | c3 WA; macchina lenta (c7 TLE 22.7s) | midpoint (localmente QEM: CAD 0.975→0.995) |
| **20044330** | re-roll bytes identici | c3 WA 22.2s completato (c7 passò 22.6s) | coin di macchina |
| **20044572** | refine ampio (cap 40 vs 8) + ctT=0 (coda liberata) | **c3 WA a 16.6s (margine +4.4s)** | refine-starvation E tempo |

**Verdetto: la redistribuzione deficit-driven NON aiuta il c3, nemmeno ben-resourced.**
Interpretazione: il deficit c3 è **resolution-bound** — dove l'originale ha struttura ad alta
frequenza, nessuna mesh a ~6775v la cattura; spostare triangoli lì non ricompra la correlazione.
Chiusura legittima per CLAUDE.md §8.2 (falsificata SUL GIUDICE, non su proxy). Con lo strumento
di `proxy-instrument` una futura variante si può pre-screenare offline in 20s.

**Cosa resta riusabile:** `edge_split` (primitiva costruttiva mancante nel codebase), il pattern
di misura del deficit per-faccia, e soprattutto gli hand-roll (sotto).

## Lo sblocco del compile-cliff (il risultato permanente di questo capitolo)

Il meccanismo non compilava sul giudice: **4 Compile Error a output vuoto** = OOM di cc1plus
(confermato: "g++-15: Killed signal / Compilation memory limit exceeded" — sub 20039320, 20043156,
20043340). Misure locali del picco cc1plus (psutil):

| Versione | Picco RAM | Giudice |
|---|---|---|
| mein.cpp originale | ~706 MB | compila |
| + meccanismo (prima versione) | +26 MB | OOM |
| + sort-free | +4.8 MB | OOM |
| + `__attribute__((optimize("O0")))` | +1.6 MB | **OOM** ⇒ margine ≈ ZERO |
| + **hand-roll Eigen** (sotto) | **692 MB (−14 sotto l'originale)** | **COMPILA E GIRA** (20043585) |

**Hand-roll** (idea di Alberto: "togliere i costrutti pesanti"): sostituiti in double puri —
- 2× `Eigen::SelfAdjointEigenSolver<Matrix3d>` → **power-iteration** 12 passi (stessa direzione
  dominante; usati per i candidati anisotropi c4 e mpc — comportamento localmente invariato);
- solve QEM del collasso → **Cramer 3×3** scritto a mano.

Conferma quantitativa della regola CLAUDE.md §2.5: il file è a margine zero e ogni meccanismo
nuovo deve essere Eigen-free. La tecnica è **riusabile per qualunque meccanismo futuro** e
libera ~14 MB di margine anche per il main track (da coordinare con Emanuel).

## Stato del working tree su questo branch

- `solver/mein.cpp` = STATO DI LABORATORIO: hand-roll + edge_split/sigma_redistribute + config di
  probe (c3t=6775, kread=1, ctT=0, sil2 gated-off, redist default-on). **NON bank-safe così com'è**:
  per un bank attempt revertare la config di probe (5 valori) o ripartire dal mein.cpp di Emanuel
  applicando solo gli hand-roll.
- `mein_sigmaxy_submitted.cpp` = i bytes esatti della sub 20044572 (ultimo judge-test).
