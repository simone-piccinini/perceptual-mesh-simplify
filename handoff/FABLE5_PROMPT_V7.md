# HANDOFF V7 — bank 90.4805+, la fame-del-box è caduta, obiettivo dichiarato 92-93

STATE: bank ≥90.480527 (campagna notturna in corso può alzarlo — leggi overnight_log.jsonl);
fronte attivo = dare il MOTORE NUOVO ai casi mai toccati (c6/c7/c4) + cantiere costruttivo;
ultima azione = campagna c5-walk/c4-probe/consolidamento (scripts/night_campaign.py).

## LE TRE SCOPERTE DEL 12/07 (cambiano tutte le priorità)

1. **La coda O(121) affamava il giudice.** Le finestre SSIM di `collapse_delta_local` ora sono
   somme prefisse 2D (O(1)/finestra, ×5-15). Il box wall-clock 6.5s faceva fare al judge META'
   del lavoro locale → i muri "definitivi" c3 6790/6775/6760 erano ARTEFATTI. Con la coda piena:
   c3 6740 e 6720 bancati in 3 ore, muro VERO tipizzato a 6700 (WA×8).
2. **Dual-mode tail**: classic (re-pool ogni RB, migliore S2 a code corte, c3) vs persistent+
   injection (`g_lztinj=1`, ×5, per c5/c4/deep). La differenza è path-dependence greedy (~2.4e-4).
3. **Due morti resuscitati dallo strumento**: c4 tail (era −5.7e-4, ora +4.1e-4) e c5 sotto-4165
   (era "0/12 chiuso", ora +2.4e-3 locale @4150). LEZIONE: ogni verdetto DEAD misurato prima del
   12/07 sera attraverso la coda è SOSPETTO. Riesamina prima di credere al cimitero.

## LA MATEMATICA DEL 93 (l'utente riporta un 93 in classifica — 403 agli script, fidati e verifica a browser)

93 = somma 558 = +15 case-points su di noi. Nessun caso singolo li contiene:
c3@3000=87% (+16 ma irraggiungibile per collasso: asintoto compute-illimitato ~6650),
c4@2500=93% (+7), c5@2500=95% (+3.3), c7@10k=99% (+1.9), c6@4k=98.9% (+1.2).
⇒ il 93 usa un MECCANISMO UNIFORME migliore-per-vertice che gira in 21s CPU single-thread.
Non è tuning: è una rappresentazione/costruzione diversa. Candidati: remesh anisotropo
image-driven costruttivo; sfruttamento aggressivo del flat shading (normal-painting GUIDATO —
la semina cieca è morta, la guidata dal residuo NON è mai stata costruita davvero).

## PIANO GIORNO 2 (in ordine di EV misurabile)

1. **Decodifica campagna** (overnight_log.jsonl: eventi csub/phaseB_done/phaseC_done) e banca.
2. **Motore → c7** (mai avuto refine/tail; muro 28822 del 05/07): budget c7 ~19.7s, margine 1.3s.
   Serve un tail/refine che costi ≤2s: injection-tail con RB alto + pool piccolo sul mesh 28.8k
   (render base 57k facce = ok); l'orig hires (2M facce) è il costo vero — misura prima.
   Ogni −800 verts c7 = +0.013 totale.
3. **Motore → c6** (8705, box-cut razor): stesso discorso, orig render 754k facce. Misura.
4. **c4 JAM attack**: il muro c4 è "gate exhaustion" del NOSTRO greedy (ENVELOPE), non SSIM.
   Diagnosi locale al rung 4880-4900: dove si inceppa (link condition? flip gate?), poi
   flip_unlock/vertex_remove mirati o tail-driven unjam. c4@4500 = +0.20 totale.
5. **MP-CONTINUO** (mai provato): line-search di POSIZIONE continua al commit della coda
   (STATUS 07-11 lo stimava +0.13 in curva). Ora l'eval è O(1)/finestra: costa poco.
6. **Cantiere costruttivo (la via 93)**: v2-construction (growth SSIM-driven da hull) non è mai
   stata competitiva (c3 6990). Sposarla col motore: growth + refine veloce + coda. Scope: giorni.
   Falsifier intermedio: un SOLO caso (c5, deterministico) costruito a 3800 verts che passa
   localmente = la classe esiste; poi porting.

## TRAPPOLE PAGATE (non ripagarle)
- File giudice = mein.cpp → strip → mein_nocomments.cpp. NIENTE nuove istanze template (2 CE
  compile-memory). optimize("O1") = 4-5× più lento sul judge (1 TLE).
- c3 CASETIME 21.5-22 = normale per questa famiglia; il ceiling stimato ~21s del tool è
  conservativo (21.9/22.4 sono PASSATE). >23 = macchina lenta, ri-rolla.
- Pendenza judge c3 = 1.25e-5/vertice (read 20031760: S2=0.9145@6775). Locale = ~5.2e-6/v
  (asintoto) — rapporto ~2.4× per mappare delta locali→judge.
- Ladder/campagna PATCHANO mein.cpp: mai editarlo mentre girano (race). Uccidi prima il pid.
