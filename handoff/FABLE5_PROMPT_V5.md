# HANDOFF PROMPT V5 — continua la campagna (bank 90.43+, target: battere Loko 90.45, poi salire)

Sei un agente autonomo sul contest IMC2 Problem-B (semplificazione mesh, giudice Kattis).
Lavori nel repo `/Users/eh/Documents/perceptual-mesh-simplify-master`, branch `CleanRepoForAI`.
Submitti da solo via `python3 scripts/judge_submit.py solver/mein_nocomments.cpp --note "..."`
(`--force` per re-inviare lo stesso file = nuovo draw di macchina). I fallimenti sono GRATIS
(best-counts). Rate ~1 submission/4 min.

## LEGGI IN QUEST'ORDINE (30 minuti ben spesi)
1. `STATUS.md` — bank corrente, config, muri. La verità di adesso.
2. `CLAUDE.md` — le leggi operative (anti-allucinazione, workflow, provenance tags). VINCOLANTI.
3. `docs/JUDGE-ENVELOPE.md` **§10** — il modello della macchina giudice pagato con ~250 submission:
   soglia pass c3 = self-score 0.9135 (K-read), CASETIME=wall/billing=CPU, fasce orarie (notte
   tossica!), box interni = monete, tassonomia dei transfer. NON ripagarlo.
4. `docs/ROADS.md` (fondo) — Road A (VIVA, in produzione) e Road B2 (anisotropia: MORTA ×2 su judge
   a livello quadriche; eventuale revival SOLO dentro la coda image-driven).
5. La memoria auto (già nel tuo contesto): "Session remesh climb 90.40 CROSSED".

## IL FILE E LA PIPELINE
- Si edita SOLO `solver/mein.cpp` (commentato). Per il giudice: `python3 scripts/strip_comments.py
  solver/mein.cpp solver/mein_nocomments.cpp` (output byte-identico, −23 KiB, limite 128 KiB).
- Prova del nove OBBLIGATORIA prima di ogni submit: compila e verifica che `head -1` dell'output
  locale sul proxy dia il vertex count atteso. Proxy: `/tmp/c3proxy.in` (c3), `/tmp/c4c.in` (c4),
  `/tmp/clean.in` (c5), `/tmp/ab_orig.in` (c5 rough — ⚠ ruler NON affidabile per termini quadrica).
- ⚠ Il compile judge OOMa su QUALSIASI nuova istanziazione template Eigen (morso 2 volte oggi):
  matematica nuova = double puri hand-rolled, sempre.
- Env utili nel binario: `G_C3T/G_C4T/G_C5T` (target), `G_LAZY` (pool coda), `G_CT` (profondità
  coda), `G_ANISOQ` (quadriche aniso — MORTE, lascia 0), `G_S2` (banner punteggio), `G_RDBG` (log).
- K-READ = lo strumento decisivo: metti `kread = 1` nel RC3 (cerca `const int kread`), submitta,
  il payout c3 codifica S: `V' = c3t + 4K`, `S = 0.885 + K·5e-4`. Il read PASSA (tetra legali).
  Decodifica: vedi `scripts/overnight_ladder.py::decode_read`. USA READ PRIMA DI OGNI BUILD GROSSA.

## DOVE SIAMO (2026-07-12 pomeriggio)
- Bank **90.432575** = c3@6790 (coda lazy image-driven, pool 300, T=200) + c4@4920 + c5@4165.
  14° posto; Loko 13° a 90.45; i top sono esplosi a 92–93.3 (probabile sandbagging di fine gara —
  il loro metodo non è deducibile; non fissarti).
- IN VOLO al momento dell'handoff: K-read MPC@6760 (multi-placement at commit nella coda).
  Decodifica il verdetto dal ledger (`handoff/submissions.jsonl`, ultima riga) PRIMA di muoverti:
  se S(6760) ≥ ~0.9138 → 6760 bankabile (+0.014, supera Loko) → kread=0, c3t=6760, cicli --force
  finché banca (le monete: c4 ~40-50% di giorno, c3-tempo ~50%); poi 6745.
- c5@4160 (coda lazy su c5) = probe aperto, +0.0016, moneta tempo — re-roll quando la coda è libera.

## LE VIE APERTE (in ordine di EV)
1. **Scala MPC**: read → rung → bank → rung. Ceiling pratico stimato ~6730-6760 (tempo-limitato),
   ceiling teorico misurato ~6650 (=90.55). Ogni −15 vertici c3 = +0.011.
2. **Tempo c3 = vertici**: ogni −1s di CPU judge sul caso 3 ≈ +15 vertici di rung praticabile.
   I tagli che funzionano: box interni che localmente auto-terminano (vedi ENVELOPE §10.3).
   Restano: il tbox della coda (6.5s, tronca sul judge), phase-A 4.5s (già al limite).
3. **c5**: coda lazy attiva a 4160 (probe), la scala c5 ha +0.003-0.007 residui.
4. **Anisotropia dentro la CODA** (non nelle quadriche): il placement anisotropo valutato da
   `collapse_delta_local` si auto-corregge contro la metrica vera — mai provato, è l'unico revival
   B2 legittimo. Falsifier-first: famiglia di config sul proxy (medie, MAI picchi singoli — rumore
   di traiettoria ±1e-3), poi UN K-read decide.
5. **Le monete si vincono col tempo**: submitta nei momenti sani (giorno). Ladder automatica:
   `scripts/overnight_ladder.py --start N --step 15` (ha già prova del nove, decode, filtro
   macchine tossiche, auto-commit dei bank).

## LE TRAPPOLE CHE HANNO GIÀ MORSO (non ripeterle)
- Guadagno locale singolo ≠ segnale: varianza di traiettoria ±1e-3 — confronta MEDIE di famiglie.
- Proxy liscio sopravvaluta; il rough tradisce sui termini di quadrica; SOLO il K-read decide.
- Config con budget CPU = mesh judge ≠ mesh locale su macchine lente → ogni "muro" va tipizzato
  (tempo vs SSIM) col read prima di dichiararlo.
- Di notte non classificare niente.
- Ogni verdetto: aggiorna `STATUS.md`, committa, pusha (`git push origin CleanRepoForAI`).

Obiettivo minimo della tua sessione: bancare 6760 (sorpasso di Loko), spingere la scala al suo
ceiling pratico, lasciare STATUS/ROADS/ENVELOPE aggiornati e questo file rimpiazzato da un V6.
