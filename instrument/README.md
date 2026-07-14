# INSTRUMENT — proxy c3 calibrato sul giudice (il "ruler that transfers")

STATE: proxy c3 VALIDATO (4 ancore, 2026-07-14) · proxy c5 preliminare · fronte: campagna offline c3
Bank ref: STATUS.md · Autore: Alberto (branch feat/proxy-instrument)

## Cosa risolve

Il collo di bottiglia n.1 del progetto (CLAUDE.md §8.3, ARCHITECT-REVIEW §3.C): i proxy storici
(armadillo *watertight* decimato) sono **troppo lisci** rispetto alle mesh del giudice, quindi gli
A/B locali sul c3 **non trasferiscono** (transfer ratio ≈ 0/negativo — R1, D4, Hoppe morti così).
Questo strumento è un proxy c3 che **riproduce il comportamento della mesh vera del giudice**,
calibrato e validato contro le ancore K-read judge-side. Con questo, un'idea sul c3 si misura
**in locale in ~20s** (solver → S2 su stderr) invece di 1 submission cieca per idea.

## Scoperte fondanti (tutte verificate in questa sessione)

1. **Self-score = oracle.** L'S2 stampato dal solver (`RC3/RL S2=...`) coincide con il FinalSSIM
   dell'oracle Python fino alla 4ª cifra (0.850603 vs 0.8506, armadillo\@4172). Iterare = leggere
   stderr, niente oracle lento. `[LOCAL, verificato]`
2. **Aritmetica dei conteggi del giudice.** Per manifold chiusi genus-0: V = F/2 + 2. Decimando
   con MeshLab QEM a `targetfacenum = 2*(V_judge - 2)` si ottiene **esattamente** il conteggio
   del giudice (c3: 23.201 ✓, c5: 49.987 ✓). `[LOCAL, verificato]`
3. **Convenzione di normalizzazione del dataset:** centro-bbox nell'origine, scala max|v| = 0.999
   (bunny/cow/armadillo watertight la condividono tutte). `[LOCAL, verificato]`
4. **La ruvidità va calibrata per caso.** La mesh del giudice c5 è *più liscia* del decimato puro
   (serve taubin ~70); quella c3 è *leggermente più liscia* (taubin 3). Il c3 del giudice NON è
   armadillo-decimato-pesantemente: la sua difficoltà relativa suggerisce uno scan organico quasi
   nativo. Il knob taubin è una calibrazione fenomenologica, non la prep vera. `[INFERRED]`

## Ricetta del proxy c3 (il file `meshes/c3_proxy_t3.obj`)

```
armadillo Stanford ORIGINALE (172.974 v, graphics.stanford.edu)
  -> MeshLab QEM targetfacenum=46.398   (V = 23.201, conteggio giudice ESATTO)
  -> Taubin smoothing, 3 step
  -> normalizzazione: centro-bbox -> origine, max|v| = 0.999
```
Rigenerabile con `python instrument/scripts/make_proxy.py`.

## Validazioni (4 ancore indipendenti) `[JUDGE-anchored]`

| # | Test | Proxy | Giudice | Fonte ancora |
|---|------|-------|---------|--------------|
| 1 | Conteggio vertici | 23.201 | 23.201 | JUDGE-ENVELOPE §6 |
| 2 | S2 assoluto @6775 | **0.9153** | 0.9145 | K-read 20031760 |
| 3 | Muro implicito (S2 sotto soglia) | ~6585-6600 | 6600-6610 | ladder live (6610/6620 bank, 6600 WA×9) |
| 4 | **Retrodizione meccanismo**: nmetric=3 | S2=0.9095 (−0.0058, sotto soglia) | **WA reale @6775** | sub 20039232/20039251 |
| — | Pendenza S(N) | 9.4e-6/v | 1.25e-5/v (stesso ordine) | read family 07-13 |

La #4 è quella che il vecchio proxy non passava: **retrodice correttamente il segno di un delta
di MECCANISMO** giudicato sul giudice vero. È il criterio di trasferimento di CLAUDE.md §8.2.

## Come si usa (workflow offline c3)

```bash
# baseline (binario bancato, win-patch, vedi sotto):
G_C3T=6775 G_S2=1 ./solver_bancato < instrument/meshes/c3_proxy_t3.obj 2>&1 >/dev/null | grep RC3
#  -> RC3 V=6775 ... S2=0.915332      <- baseline
# variante (qualunque meccanismo/env):
G_C3T=6775 G_S2=1 G_TUAIDEA=1 ./solver_variante < instrument/meshes/c3_proxy_t3.obj ...
#  delta S2 = il segnale. Soglia di rilevanza: ~±0.001 (sotto è rumore di calibrazione).
```
- Confronti **relativi** (variante − baseline) allo **stesso rung**: è lì che il proxy è forte.
- L'assoluto ha bias +0.0008 (ancora #2): per predire pass/fail usare soglia S2 ≈ 0.9135-0.9143.
- Win-patch per compilare su Windows: sostituire `#include <sys/resource.h>` con `<chrono>` e il
  corpo getrusage di `r_elapsed()` con `steady_clock` (2 righe; vedi handoff sessione).

## Bonus: sblocco del compile-cliff (tecnica hand-roll) `[JUDGE-validated]`

mein.cpp è a margine di compilazione ZERO su g++-15 (perfino +1.6 MB template-free va in OOM —
misurato con 4 submission). Sblocco validato: **hand-roll dei costrutti Eigen pesanti** in double
puri — `SelfAdjointEigenSolver<Matrix3d>` → power-iteration (12 iter), solve QEM → Cramer 3×3.
Risultato: 692 MB di picco cc1plus, **14 MB SOTTO l'originale**, submission 20043585 compilata e
girata. Qualunque meccanismo nuovo ora ci sta. (Conferma la regola CLAUDE.md §2.5.)

## Limiti onesti

- Il taubin-K è un fit fenomenologico su ancore (non la prep vera del giudice): extrapolazioni
  lontano dai rung ancorati (6600-6800) vanno ri-ancorate con un K-read.
- Proxy c5 (`c5_proxy_t70.obj`): matcha l'ancora 0.908@4212 entro ~0.002 ma ha UNA sola ancora
  S2 → non ancora validato come il c3 (e il c5 è comunque un caso chiuso/deterministico).
- La pendenza proxy è ~25% più piatta del judge: per stime di rung usare il muro (#3), non
  l'estrapolazione lineare.
- Ancore judge citate da: STATUS.md, handoff/ATTEMPT_LOG.md, handoff/submissions.jsonl.

## Storia della sessione (per ATTEMPT_LOG)

Chiusure judge-validate: c4-jam (non esiste: muro SSIM, 2 probe), nmetric=3 (WA×2, timing
escluso), redistribuzione σxy costruttiva (edge_split + sigma_redistribute: meccanicamente valida
e manifold-safe, ma WA×4 con confound esclusi uno a uno — il deficit c3 è resolution-bound, non
riallocabile). Le primitive restano nel working tree del branch (edge_split è riusabile).
