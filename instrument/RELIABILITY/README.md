# Analisi di affidabilità del giudice offline ("lo specchio")

STATE: analisi del 2026-07-14, riferita al proxy c3 (`meshes/c3_proxy_t3.obj`) + binario bancato 48cfbc6.
Lo specchio ha DUE componenti con affidabilità diverse: (1) il METRO (il punteggio S2 auto-misurato
dal solver) e (2) il CAMPIONE (la mesh proxy). Vanno valutate separatamente.

---

## 1. Il metro (S2 = SSIM auto-misurata) — affidabilità: MOLTO ALTA

- **S2 = oracle Python alla 4ª cifra** (0.850603 vs 0.8506, verificato sull'armadillo@4172).
  Non è un'approssimazione: il solver calcola la stessa matematica dell'oracle.
- **L'oracle = la convenzione del giudice**: l'unico dubbio storico (i pixel di sfondo nelle
  finestre SSIM) è stato risolto con una sonda reale (sub 20029777: il giudice INCLUDE lo sfondo,
  come noi). La matematica del metro è judge-verificata.
- **Un asterisco**: vicino ai muri il self-score è documentato come ~+0.005/+0.010 OTTIMISTA
  rispetto al pass/fail vero del giudice. Ma le nostre ancore sono K-read (self-score misurato SUL
  giudice) → confrontiamo mele con mele. L'ottimismo conta solo per predire il pass/fail assoluto.

## 2. Il campione (la mesh proxy) — affidabilità: BUONA nel suo dominio, con confini precisi

Le 4 validazioni (misurate, non sperate):

| Ancora | Proxy | Giudice | Errore |
|---|---|---|---|
| Conteggio vertici | 23.201 | 23.201 | **0** |
| S2 assoluto @6775 | 0.9153 | 0.9145 [K-read 20031760] | **+0.0008** (bias noto, correggibile) |
| Posizione del muro | ~6585-6600 | 6600-6610 (ladder viva) | **~15-25 vertici** |
| Retrodizione meccanismo (nmetric=3) | −0.0058, boccia | WA reale (20039232/51) | **segno e ordine di grandezza corretti** |

**Rumore di fondo misurato**: ±0.0002-0.0004 tra run ripetuti → lo strumento risolve delta ≥0.001
in un run singolo; sotto servono ripetizioni.

---

## 3. I limiti onesti (dove NON fidarsi)

1. **Il taubin-3 è un fit, non la prep vera.** È calibrata la QUANTITÀ di ruvidità, non la sua
   STRUTTURA: lo smoothing Taubin è isotropo, lo scan vero ha rumore con firma diversa
   (direzionale, del sensore). Un meccanismo che interagisce con la micro-struttura del rumore
   (non solo con la sua ampiezza) potrebbe leggere sbagliato. È il rischio residuo principale.
2. **Pendenza 25% più piatta** (9.4e-6 vs 1.25e-5 per vertice) → le ESTRAPOLAZIONI lontano dai
   rung ancorati (6600-6800) degradano. A 6000 o 7500 lo specchio è cieco finché non si ri-ancora.
3. **Una sola retrodizione di meccanismo** (n=1). È la validazione più forte che abbiamo, ma un
   solo caso non è una legge: classi di meccanismo molto diverse meritano una conferma judge-side.
4. **Vale solo per il c3.** Il proxy c5 ha una sola ancora (~0.002 di errore); c2/c4/c6/c7 non
   hanno specchio.
5. **Deriva delle ancore**: la 0.9145@6775 è della famiglia deep-tail del 13/07. Il motore evolve —
   se la famiglia bancata cambia molto, va RI-ANCORATO (1 K-read).
6. **Niente predizioni di tempo**: CPU locale ≠ giudice (~3.2× su alcune op). TLE e CASETIME si
   misurano solo sul giudice. Alcuni path hanno un segfault Windows-only → non misurabili in locale.

---

## 4. Il verdetto operativo (a cosa credere, in pratica)

| Uso | Affidabilità | Perché |
|---|---|---|
| **A/B relativo di meccanismi** a rung fisso 6600-6800, delta ≥0.001 | **ALTA** — il core business | retrodizione + bias costante che si cancella nella differenza |
| **Bocciature** (delta negativo/neutro) | **ALTISSIMA** | pipeline-imbuto + bias ottimista: se non funziona sullo specchio clemente, non funziona |
| S2 assoluto vicino alle ancore | MEDIA | bias +0.0008 noto; usare soglia 0.9135-0.9143, non 0.90 |
| Posizione muro vicino a 6600 | MEDIA (±20v) | validata sulla ladder viva |
| Estrapolazioni lontane, altri casi, timing, positivi <0.001 | **BASSA** | fuori dominio di calibrazione |

**La regola d'oro (asimmetrica, ed è la sua forza):**
- **Un NO dello specchio è quasi definitivo** — scarta e passa oltre, gratis.
- **Un SÌ dello specchio è un candidato, non una vittoria** — un delta positivo ≥0.002 merita UNA
  submission S-read di conferma prima di costruirci sopra.

È il profilo giusto per la fase attuale: setacciare tante idee nuove cercando quella viva, con
costo degli errori asimmetrico (un falso-sì costa 1 submission di verifica; il design
"specchio-clemente + imbuto" rende raro il falso-no).

**Rafforzamento raccomandato** (gratis, 2 run): una seconda retrodizione di classe diversa — es.
l'aniso-quadric `G_ANISOQ` (judge-falsificata ×2: −2.6e-3 sub 20029030, −4e-3 sub 20029061): se lo
specchio la boccia con l'ordine di grandezza giusto, n=2 sulla validazione di meccanismo.
