# Il problema e il giudice — fatti verificati, nero su bianco

Fonte primaria: PDF ufficiale (`~/Downloads/Perception-Aware ... Huawei.pdf`, riletto parola per
parola il 2026-07-04) + clarification ufficiali del contest + 100+ submission di esperienza diretta.
Questo file è LA verità sul giudice. Se un'affermazione qui contraddice un altro doc, vale questa.

## Le regole del gioco (dal PDF, verbatim dove conta)

- **Input**: mesh pre-normalizzata (AABB centrato nell'origine, vertici nella sfera unitaria),
  formato "V F" + righe `v x y z` + righe `f i j k`. Watertight, connessa, senza duplicati.
- **Output**: stesso formato, su stdout, max 100 MiB.
- **Vincoli di validità (tutti e 4, testuali)**:
  1. Conteggio vertici: `1 ≤ V′ ≤ V`.
  2. Manifold: ogni edge condiviso da **esattamente due** facce (chiuso, watertight).
  3. Facce non degeneri (area positiva).
  4. Indici delle facce dentro il range dell'array vertici.
  Se violi uno di questi: Wrong Answer **e ti viene detto quale** hai violato.
- **Vincolo geometrico**: `d_H(M, M′) ≤ 5% × Diagonal` (diagonale AABB dell'originale).
- **Punteggio per caso** = tasso di compressione `100 − 100·(V′/V)`, valido solo se
  `FinalSSIM ≥ 0.9`. Punteggio finale = **media dei 6 casi** (il sample non conta).
- **Range dei casi**: c2 ≤5.000 V | c3 ≤25.000 | c4 ≤40.000 | c5 ≤50.000 | c6 ≤400.000 | c7 ≤1.100.000.

## Il rendering del giudice (esatto, verificato bit-a-bit dal nostro oracolo)

- 6 camere fisse sugli assi a distanza D=2.5, focale 800 px, immagini 1024×1024, principal point (512,512).
- **Normal map**: flat shading — ogni pixel prende il normale (costante) della faccia più vicina
  che ne copre il centro; encoding `(n+1)·127.5` per canale. Sfondo (0,0,0) → grigio 127.5.
- **Depth map**: z camera-space, interpolazione prospetticamente corretta (1/z lineare a schermo).
  Sfondo 255.
- **SSIM**: finestra scorrevole 11×11, C1=(0.01·255)², C2=(0.03·255)². Media SOLO sulle finestre
  il cui pixel CENTRALE è foreground **nell'originale E/O nella semplificata** (unione); per la
  normal map, SSIM per canale poi media dei 3 canali. FinalSSIM = media su 6 viste di
  0.5·SSIM_normal + 0.5·SSIM_depth.
- Finestra 11×11 = **box** (uniforme), NON gaussiana: stabilito dai dati giudice (la gaussiana
  leggerebbe 0.854 in un punto che il giudice passa a ≥0.90 — gap 0.047).

## LE SCOPERTE CHIAVE (in ordine di importanza)

### 1. Il guinzaglio Hausdorff è VERTICE-A-VERTICE, non punto-a-superficie ⚠ ENORME
Clarification ufficiale del contest (2026-06-18): *"In the formula, a and b vary across
**vertices** of their respective mesh. We do not iterate over interior or surface points."*
Quindi: ogni vertice originale deve avere un vertice semplificato entro 0.05·Diagonal, e
viceversa. **Le facce (la superficie) non hanno alcun vincolo geometrico.** Il nostro oracolo
locale calcola punto-a-superficie: è PIÙ SEVERO del giudice vero — abbiamo giocato con un
guinzaglio più corto del necessario. Con la spaziatura tipica dei nostri vertici tenuti
(~0.02–0.05), il vincolo vero è quasi sempre lontanissimo dall'attivo.

### 2. La connessione NON è richiesta per l'output — ⚠ PROVATO SUL GIUDICE
Il PDF garantisce l'input "connected" ma i 4 vincoli di output non menzionano mai la
connessione. **Probe del 2026-07-04: output di c2 + tetraedro disconnesso → Accepted 7/7
(90.222274).** Il giudice accetta componenti multiple, watertight per-componente. Porte
aperte: sigillatura delle zone mai fotografate (cancellare geometria nascosta e richiudere,
recupero stimato 0.5–0.8% dei vertici sui casi organici); componenti-rilievo per vista
(imposter geometrici — legali, EV incerto per la perdita di condivisione multi-vista).

### 3. Niente rejudging: "the current test cases are final"
Clarification ufficiale. Il best-counts è definitivo: ogni submission fallita è gratis per sempre.

### 4. Il runtime del giudice è DETERMINISTICO dato il binario
Misurato: 3 resubmission con soli commenti diversi → punteggi bit-identici. La varianza tra
submission viene SOLO dal riordino delle operazioni floating-point quando il codice cambia
davvero (σ≈0.0002–0.0003 SSIM vicino ai muri, costo medio zero). Vicino a un muro, ogni
binario nuovo è un'estrazione: i muri sono distribuzioni, non fatti binari.

### 5. Il giudice NOMINA i casi falliti e distingue WA da TLE — ⚠ e NOI non li distinguevamo
Fino al 2026-07-04 il nostro script mostrava solo pass/fail: **submission 19888628 rivelò che
c4@85.75 moriva di Time Limit Exceeded, NON di Wrong Answer** — un "muro SSIM" che era in
realtà un muro di TEMPO (rotto tagliando il box del refine 16→14s: 85.75 poi passato).
MORALE: ogni 'x' va classificato (WA = qualità; TLE = tempo; i rimedi sono opposti).
`scripts/judge_submit.py` ora stampa il verdetto per-caso (righe FAIL); `scripts/judge_audit.py`
riclassifica le submission passate.

### 5b. Alcuni "muri" sono FLOOR FISICI della decimazione, non muri SSIM
c2: keep 0.007 e 0.00725 producono lo STESSO output (28 vertici) — i collassi legali si
esauriscono. c4: keep 0.1425 produce ancora 4570 vertici (85.71875) — stesso fenomeno, i gate
di sicurezza (link condition, flip, area) bloccano gli ultimi collassi. Tre tipi di muro:
SSIM (c5, c6 — WA veri), TEMPO (c4@85.75 col box 16s), TOPOLOGICO (c2, c4 sotto 85.75).
Rimedi diversi: qualità / velocità / rilassare i gate.

### 6. Budget CPU: ~16.5s per caso, fatturato SOMMANDO i thread
Multithreading = suicidio (lezione v60/v63). Il box wall-clock a 16s del refine è provato al limite.

### 7. depthSSIM è quasi saturo; il campo di battaglia è la normal map
Misurato ovunque: depth 0.98–0.99, normale 0.72–0.84. E dentro la normale, il deficit è ~tutto
nel termine di **struttura** (correlazione σxy): vedi THEORY.md.

## Stato attuale (2026-07-04)

Bank **90.238542** (7/7). Per caso: c2 99.298 | c3 70.03125 | c4 85.71875 | c5 91.546875 |
c6 97.6953125 | c7 97.145. Ogni muro respinto con 3–6 meccanismi diversi. Leader ≈ 91.6+.
Deadline 2026-07-18. Storia completa round-per-round: `handoff/ATTEMPT_LOG.md`.
