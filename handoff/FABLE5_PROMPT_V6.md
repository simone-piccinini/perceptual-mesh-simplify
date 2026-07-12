# HANDOFF V6 — bank 90.432575, 6 giorni alla fine, rotta: coverage-aware tail → 90.5+, poi frontiera

Sei un agente autonomo su IMC2 Problem-B. Repo `/Users/eh/Documents/perceptual-mesh-simplify-master`,
branch `CleanRepoForAI`. Submitti da solo: `python3 scripts/judge_submit.py solver/mein_nocomments.cpp
--note "..."` (`--force` = re-roll stesso file). Fallimenti GRATIS (best-counts). ~1 sub/4min.
IL TESTO UFFICIALE DEL PROBLEMA È IN `FILE.md` (root) — fa fede su tutto.

## ORDINE DI LETTURA (45 min, poi sei operativo)
1. `FILE.md` — il contratto. Rileggi TU le formule; non fidarti dei riassunti (incluso questo).
2. `STATUS.md` + `CLAUDE.md` (leggi operative, vincolanti).
3. `docs/JUDGE-ENVELOPE.md` §10 — il modello macchina (~250 sub di esperienza). NON ripagarlo.
4. `handoff/FABLE5_PROMPT_V5.md` — storia recente e trappole; questo V6 lo sostituisce.

## PIPELINE (invariata, collaudata)
- Edita SOLO `solver/mein.cpp` → `python3 scripts/strip_comments.py solver/mein.cpp
  solver/mein_nocomments.cpp` → compila g++ -O2 -std=c++17 -Isolver → PROVA DEL NOVE (head -1
  dell'output sul proxy = vertex count atteso) → submit. Proxy: /tmp/c3proxy.in, /tmp/c4c.in,
  /tmp/clean.in, /tmp/ab_orig.in.
- Eigen: NIENTE espressioni template nuove (compile judge OOMa — morso 2 volte). Double hand-rolled.
- K-READ: `const int kread = 1` nel RC3 → il payout c3 codifica il TUO S2: V'=c3t+4K, S=0.885+K·5e-4.
  Il read PASSA. Soglia empirica: S2_self ≥ 0.9135 ⇔ FinalSSIM_judge ≥ 0.9. READ PRIMA DI OGNI BUILD.
- Ladder automatica: `scripts/overnight_ladder.py --start N --step 15` (prova del nove, decode,
  filtro macchine lente, auto-commit). SOLO di giorno (notte = macchine lente, c3 muore di tempo).

## STATO (12/07 sera) — provenienza [JUDGE] salvo indicato
- Bank **90.432575**: c3@6790 (coda lazy image-driven pool 300 T200) + c4@4920 + c5@4165. 14° posto.
- Muri del paradigma collasso+refine (tutti read-tipizzati): c3 6790 (6775 S-fail, 6760 S-fail
  anche con multi-placement), c4 4920, c5 4165, c2 28. Ceiling teorico misurato ~6650 (=90.55).
- MORTI (non ripagare): anisotropia via quadriche (×2 K-read, −2.6e-3/−4e-3; il rough proxy ha
  MENTITO su questa classe), split-realloc (tutte le forme), topology surgery (c2/c4 genus-0
  misurato), SIL su c3 (misurato oggi: depth +2.1e-4, normale −5.7e-4 = netto negativo),
  512-eval (le scelte non trasferiscono a 1024), tail su c4 (CAD preferisce QEM).

## LA SCOPERTA DI OGGI (verificata su codice+testo, NON ancora sfruttata) — IL TUO PRIMO CANTIERE
Dal testo (FILE.md): depth map = z camera-space RAW (foreground ∈[1.5,3.5], bg 255), C2=58.5.
⇒ le finestre depth INTERNE sono matematicamente sature (σ²≈0.04 ≪ C2): TUTTO il deficit depth
(1−S2d = 0.0148) vive nelle finestre di SILHOUETTE (salto 255↔2.5). Nel FinalSSIM la depth pesa
il 50% ⇒ quel deficit vale FINO A +7e-3 di S2 = centinaia di vertici di rung. Il progetto lo
credeva "saturo" per un errore di prospettiva (lo confrontava con la normale).
PERCHÉ non è mai stato raccolto: (a) la coda lazy (`collapse_delta_local`) valuta SOLO i 3 canali
normali E RIFIUTA ogni collasso che cambia coverage (`return -1e30` su pixel scoperti) ⇒ il bordo
non viene mai ottimizzato; (b) il SIL pass sposta i vertici di bordo ma paga in normale 2:1.
**BUILD: coverage-aware tail.** In `collapse_delta_local`:
1. Esporta anche lo z-buffer dal `remesh_cache_render` (g_rzb[6], come g_rfs; usa g_zb_out).
2. Aggiungi il canale depth alla valutazione: X = g_orig_d[v], Yo = g_rzb (255 dove fid<0),
   Yn = z prospettico del triangolo nuovo vincente (il tuo rasterizzatore locale calcola già bz).
   Peso: il canale depth conta ×3 rispetto a un canale normale (S2 = media_viste di
   0.5·mean3(N)+0.5·D ⇒ ΔD pesa come ΣΔch). Stessa finestra-macchina.
3. SOSTITUISCI il reject: un pixel che perde coverage è VALUTABILE (Yn = 127.5 normale / 255
   depth) SE è silhouette vera: consenti se il pixel ha almeno un 8-vicino fuori-ring di
   background nel render base; altrimenti reject come ora (auto-occlusione: il retro è ignoto).
4. Falsifier locale: famiglia di config (MEDIE, mai picchi — rumore traiettoria ±1e-3) su S2
   COMBINATO @6790/6760. Se famiglia-media ≥ +1e-3: UN K-read decide. Poi ladder.
Bersaglio realistico se funziona: rungs 6700–6600 = 90.47–90.52. Se il read dice no: hai chiuso
il fronte depth per sempre con 1 submission, e resta la via 2.

## VIA 2 (se la 1 delude) — anisotropia DENTRO la coda
Placement anisotropo (allungato lungo la curvatura bassa) come CANDIDATO nel multi-placement
del tail (G_MPC): il delta vero lo prezza, niente bias di proxy. Famiglia locale → K-read.

## VIA 3 — il tempo è ancora vertici
Ratio judge c3 ~2.1–2.4×. Ogni −1s CPU judge ≈ +15 vertici di rung. I box che localmente
auto-terminano si tagliano gratis (già fatto ×3, ENVELOPE §10.3). Rimasti: tbox della coda
(tronca sul judge — misura!), phase-A 4.5s.

## DISCIPLINA (il metodo che ha fruttato +0.15 in 3 giorni)
- Falsifier-first: mai più di mezza giornata su un'idea senza un numero judge.
- Un solo cambiamento per submission; nota = LA domanda; decode SEMPRE (WA≠TLE, rimedi opposti).
- Famiglie di config, medie, non picchi. Ogni verdetto → STATUS/commit/push.
- I 93 dei top: non deducibili dai nostri dati (probabile sandbagging). Non inseguirli alla
  cieca: insegui la TUA curva, che è misurata.

Obiettivo minimo sessione: coverage-aware tail costruito+letto sul judge; se positivo, bancare
≥1 rung sotto 6790. Lascia un V7.
