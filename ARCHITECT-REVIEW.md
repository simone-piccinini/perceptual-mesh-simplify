# ARCHITECT REVIEW — la strada verso 91+ (e oltre)

*Revisione esterna, indipendente, con occhio critico. Autore: analisi architetturale su richiesta di
Emanuel, 2026-07-08. Non ho accesso al giudice: tutto ciò che segue è ragionamento sui vostri dati
misurati, letti con la regola che avete dato voi — «non è detto che ciò che c'è scritto sia vero al
100%». Dove sfido i vostri doc lo dico esplicitamente.*

---

## ⚑ UPDATE 2026-07-09 — piano eseguito, UNA correzione, e la NUOVA strada (3.C.2)

L'agente ha eseguito tutto il piano §7. Riepilogo + le due cose che contano ora.

| item §7 | esito reale | giudizio dell'architetto |
|---|---|---|
| 1. bonifica main.cpp | ✅ −19.3 KiB, ~109 MB cc1plus recuperati, judge-validata, byte-identica | **vittoria vera.** Tenere. |
| 2. reorg repo | ✅ STATUS/CLAUDE/ROADS/nav | fatto; README ora corretto (il "problema enorme": diceva Hausdorff p2s "matching the judge" — falso, è v2v). |
| 3. adotta CLAUDE.md | ✅ | ok |
| 4. Hoppe placement (§3.B.1) | ⚠ "neutro", NON pulitamente attribuito | chiuso su evidenza debole (proxy non-de-biasato). Priorità bassa, non sepolto. |
| 5. re-roll coin | giorno freddo (c4 perde), rimandato | ok |
| 6. **de-bias proxy (§3.C.1)** | ⚠ dichiarato "FALSIFICATO" a iter 2/10 | **correzione sotto.** |
| 7. domanda giudice | ✅ bozza pronta | mandarla — gratis |

**Correzione (§3.C.1).** L'agente ha dichiarato morto il lever #1 all'**iterazione 2 di 10**, con **il
modello di rumore sbagliato sul caso sbagliato** — il vizio che il §4 predice. Non è falsificato il
*programma*, solo una forma ingenua. Tre difetti (due scoperti da lui stesso senza trarne la conseguenza):
(1) **rumore sbagliato** — white-noise-along-normal per-vertice è *refine-recuperabile* (lui lo scrive!);
serve rumore **correlato / band-limited** sotto la frequenza rappresentabile, o cotto nei normali di
FACCIA. (2) **caso sbagliato** — ha calibrato su **c3 (box-cut = moneta)** mentre il segnale pulito era
su **c5 deterministico** (R1 ha WA'd c5 in modo deterministico, 19897122). (3) **campione debole** —
Hoppe non discrimina; resta un segnale, una forma di rumore. È 2/10, non 10/10.

**⚑ La scoperta nuova (Road 3.C.2 — DATA SOURCING, vedi §3.C).** Analizzando i mesh locali: avete **un
solo** mesh organico hi-res (armadillo pulito), e il proxy di case-3 ne è una **decimazione** →
doppiamente liscio (la decimazione è un passa-basso: toglie esattamente la struttura sub-triangolo che
lo scan vero conserva). **Ma il giudice usa modelli STANDARD:** case-5 = 49.987 ≈ armadillo Stanford
(49.990). Quindi il de-bias migliore **non è rumore sintetico — è procurarsi i mesh GIUSTI** (scan grezzi
Stanford, modelli-sorgente identificati per risoluzione). Questo può dissolvere il transfer-problem su
c5/c6/c7 e dare un proxy c3 fedele. È più importante del de-bias sintetico. Dettaglio in §3.C.

*Il resto del documento è invariato rispetto al 2026-07-08 e resta valido.*

---

## 0. TL;DR per chi ha 30 secondi

1. **Il premio è quasi tutto in case-3.** Ogni punto di compressione su case-3 vale **0.167 sul
   totale**. Portare case-3 da 70% a ~76% chiude **da solo** quasi tutto il gap col leader
   (91.46 − 90.286 = 1.174). Non serve spingere altrove: le altre 5 cases sono già a 85–99% e i
   loro muri sono misurati duri. **Il 91 si vince o si perde su case-3.**

2. **La conclusione "siamo vicini al ceiling" è un'IPOTESI, non un fatto.** È stata costruita
   chiudendo porte con un proxy locale che voi stessi avete DIMOSTRATO non trasferire (§9.1). Il
   leader a 91.46 è la prova vivente che una mesh migliore esiste. Non siete al ceiling: siete al
   **limite di quanto potete MISURARE** con il budget di submission che avete.

3. **Il vero collo di bottiglia non è l'algoritmo, è lo STRUMENTO DI MISURA.** Il file singolo da
   113 KiB al bordo del compile-cliff, il proxy che non trasferisce, il coin box-cut, ~1 submit/4min:
   questo è ciò che vi tiene fermi. La strada verso 91 passa da **industrializzare il test judge-side**,
   non dal trovare un trucco.

4. **Le tre strade** (dettaglio in §3): PICCOLA = gestione lotteria + harvest residui (+0.01–0.05,
   non basta). GRANDE = nuovo meccanismo di placement/ricostruzione nella famiglia smooth, A/B via
   S-read (potenziale +0.1–0.6). ENORME = de-bias del proxy per riaprire l'iterazione offline +
   co-ottimizzazione differenziabile sul metrica vero (potenziale +0.5–1.2, è qui che vive il 91).

5. **Il repo va ripulito prima di ripartire.** Doc-drift reale (SOLVER_STATE.md dichiara se stesso
   obsoleto; docs/README punta a 3 file inesistenti; 4 numeri di "bank" diversi in giro). Un agente
   brucia token a disambiguare. Serve UNA fonte di verità e un archivio. Dettaglio in §5.

---

## 1. Dove sono davvero i punti (l'aritmetica che decide tutto)

Bank attuale **90.285538**, decomposto (JUDGE-ENVELOPE §6, residuo +0.000000):

| case | V input | N banked | compressione | **valore di 1 vertice sul TOTALE** | spazio fino a 100% | tipo di muro |
|---|---|---|---|---|---|---|
| 2 | 4.098 | 28 | 99.32% | 0.00407 | **0.11** | SSIM wall @28 (27 WA) |
| **3** | **23.201** | **6.941** | **70.08%** | **0.00072** | **5.0** | **SSIM struttura — mechanism-limited** |
| 4 | 35.292 | ~5.044 | 85.71% | 0.00047 | 2.38 | box-cut coin, genus-0 |
| 5 | 49.987 | 4.212 | 91.55% | 0.00033 | 1.41 | wall deterministico |
| 6 | 377.084 | ~8.705 | 97.69% | 0.000044 | 0.38 | box-cut razor |
| 7 | 1.009.118 | ~28.822 | 97.14% | 0.000017 | 0.48 | deterministico, no refine |

**Lettura numero uno.** La colonna "spazio fino a 100%" dice dove ci sono punti da prendere in
teoria: c3 (5.0) ≫ c4 (2.38) ≫ c5 (1.41). Ma c4 è genus-0 con muro misurato, c5 è deterministico e
chiuso 0/12. Restano **realisticamente solo c3** come fronte con premio grande e muro *pipeline-relative*
(cioè che si muove se il simplificatore migliora — la storia lo prova, §3.B).

**Lettura numero due (la sfida al vostro doc).** ROADS.md dice: «il gap 7.05 è probabilmente SPARSO,
quindi leader_c3 ~72–77%, premio modesto». **Questa è una congettura travestita da fatto.** Non potete
vedere il profilo per-caso del leader (Kattis 403). Le altre 5 cases vostre sono già 85–99%: se il
leader fosse molto più avanti lì, dovrebbe avere c5/c6/c7 quasi a 99–100%, il che è implausibile
(sono muri fisici anche per lui). **La spiegazione più semplice del gap 7.05 è che sia concentrato
dove VOI siete anomali: case-3.** Quindi non escludete lo scenario leader_c3 ≈ 80–85%. Il "right-sizing
del premio" a ≤7 pt è prudente per non fare over-engineering, ma **non usatelo come scusa per non
attaccare case-3** — è l'unico posto dove il 91 è raggiungibile.

---

## 2. Cosa fa `main.cpp` oggi (la pipeline, letta dal codice, non dai doc)

Un solo file, ~1869 righe, C++17 + Eigen, single-thread, dispatch per numero di vertici. Le fasi:

1. **Load + Initialize** — half-edge implicito (`vfaces`), quadriche per-vertice (Garland-Heckbert).
2. **Visibility culling** (c3+c4, V∈(7k,40k]) — libera le facce mai viste dalle 6 camere.
3. **Ordinamento dei collassi = VSA-lite** (`g_ndecim`, `ndecim_for`>7000) — heap ordinato per
   **distorsione del normale** `area·(1−cosθ)`, NON per errore di posizione QEM. È il singolo lever
   più grande della storia (66%→69% su c3, THEORY §6).
4. **Placement** — QEM free-optimum (LDLT 4×4) + `g_nplace` (candidato che minimizza la distorsione
   normale) + `g_aniso` (candidati anisotropi curvature-aligned, solo c4).
5. **Steering metric-in-the-loop = Pivot-A / s-def** (`g_lambda`, `lambda_for`) — il solver
   RENDERIZZA se stesso durante la decimazione con un rasterizer flat-shaded judge-matched, e
   moltiplica il costo di collasso per il deficit di STRUTTURA SSIM locale (8 passi, re-render della
   mesh corrente, main.cpp:~1715).
6. **Refine post-decimazione** — ascesa sul **gradiente analitico della SSIM vera** attraverso
   rasterizzazione + box-filter + formula SSIM. Monotono, box su CPU-getrusage. Per c3/c5 finisce con
   una fase "hybrid" a 1024 nativi (+0.0013, ha rotto il muro c3).
7. **Per c7**: 2-stage (QEM bulk fino a 5× target, poi VSA) per stare nel budget CPU.
8. **Output** + (nei read) K tetraedri invisibili che codificano il self-score S nel conteggio V'.

**Il giudizio da architetto sul codice.** È un solo file mostruoso ma *coerente*: ogni lever è
judge-calibrato e c'è un env-gate per ogni esperimento. Il problema non è la qualità algoritmica —
è **ottima**. Il problema è **strutturale e riguarda la capacità di continuare a sperimentare**:

- **Compile-cliff.** Il file è a ~629 MB di RSS in `cc1plus` (gcc:14), ~110 MB di margine. Ogni
  nuova istanziazione Eigen pesante fa OOM. `Eigen/Sparse` è ancora `#include`-ato ma serve solo a
  codice morto (`g_lapl`/Sobolev). **Questo è debito tecnico che BLOCCA le strade grandi:** non
  potete aggiungere la co-ottimizzazione differenziabile se non compila.
- **128 KiB source-limit**, ~15 KiB di margine. Codice env-gated morto (G_ADAM, G_SHARP, G_HOP,
  G_LAPL, G_LLOYD, G_VSAC, tcand, nplace2, mask…) occupa spazio che servirà.
- **Single-file** = ogni modifica ricompila tutto e ridisegna il "binary family" → **ridisegna il
  coin box-cut di OGNI caso**, non solo quello che tocchi (è il motivo per cui una modifica isolata
  a c3 fa WA c4). Questo accoppiamento è il nemico numero uno della sperimentazione.

**Prima raccomandazione architetturale, prerequisito a tutto il resto:** fate una PASSATA DI
BONIFICA del `main.cpp` — rimuovete tutto il codice env-gated giudicato-morto e `Eigen/Sparse`,
verificando byte-identità dell'output sul proxy (solo rumore FP ammesso). Obiettivo: **≥250 MB di
compile-headroom e ≥40 KiB di source-headroom** PRIMA di provare qualsiasi meccanismo nuovo. Senza
questo, le strade grandi/enormi sono fisicamente non compilabili. È noioso ma è il gate.

---

## 3. LE STRADE verso 91 (piccole, grandi, enormi — con odds onesti)

### 3.A — PICCOLE (costanti, harvest, gestione della lotteria) — atteso +0.01…+0.05

Queste NON portano a 91 da sole, ma sono gratis (best-counts protegge il bank) e vanno fatte in
parallelo, non al posto delle altre.

1. **Re-roll dei coin box-cut nei giorni "caldi".** ROADS.md 2026-07-08: 8 draw hanno tutti WA'd
   c4@4970 (giudice "freddo"). Il bank 90.285538 è un joint-draw fortunato. Ri-tirare c4/c6 quando
   la macchina è scarica può riprodurre o battere di poco quel draw. Puro management. **Odds alti,
   premio ~0.**
2. **Ladder a conteggio-fisso da 1 vertice su c6/c7** (JUDGE-ENVELOPE: 41+32 rung, ≤+0.0023 totale).
   Micro.
3. **Anchoring S-read su ogni famiglia** — non è un guadagno di score ma di INFORMAZIONE: ogni
   bank-attempt vi regala un pass/fail che àncora il self-score. Fatelo sistematicamente (oggi è
   sporadico). Rende le strade grandi molto più economiche da testare.

Verdetto: fatele, ma sappiate che **il tetto di questa classe è ~90.32**. Non è il 91.

### 3.B — GRANDI (nuovo meccanismo nella famiglia smooth-QEM, A/B via S-read) — atteso +0.1…+0.6

Qui c'è il vero campo di gioco a rischio medio. **La lezione VSA è corretta e va rispettata: la mesh
vincente per c3 è smooth+densa+adattiva. Niente facet piatti.** Ma dentro quella famiglia, il vostro
stesso doc chiude porte con test LOCALI che avete dimostrato non trasferire — quindi quelle porte
NON sono chiuse davvero. Le tre che rimetterei sul tavolo, **testate SOLO judge-side**:

1. **Quadrica di attributo (Hoppe Vis'99) per il PLACEMENT, non solo l'ordering.** Oggi VSA-lite
   ordina i collassi per distorsione normale ma PIAZZA il vertice con la quadrica di posizione
   (`g_qweight=0`). Hoppe estende la quadrica con i termini di attributo (normale) così il vertice
   piazzato minimizza anche l'errore di normale. ROADS.md la dichiara "already maxed" — ma l'evidenza
   è un'ablazione LOCALE di `nplace` (neutra) su un proxy che over-premia il position-space. **Non è
   la stessa cosa della quadrica-attributo completa, e non è mai stata testata sul giudice.** Costo:
   piccolo (riusa heap/quadriche), rischio family-re-roll (calibrare). **A/B = due read @6941,
   confronto S2. Un solo submission-pair. Fatelo.**

2. **Ciclo completo decimate→refine→RE-decimate (Road B item 1), non i burst R1.** R1 (refine-burst
   in mezzo alla decimazione) è judge-negativo ×2 perché i proxy lo over-premiano. Ma un ciclo
   *completo* — decima, porta i vertici alle posizioni SSIM-ottimali col refine, poi ri-esegui
   l'ordering VSA su QUELLA geometria — esplora un **bacino diverso** per ciclo. È strutturalmente
   diverso da R1. Odds medio-bassi ma il codice esiste quasi tutto. A/B via S-read.

3. **Basin-diversity deliberato (Road B item 3).** N ordini di decimazione perturbati, refine 16/N
   secondi ciascuno a 512, tieni il migliore per self-score, poi polish a 1024. Sfrutta lo spread
   misurato ±0.013 SSIM a conteggio fisso *di proposito* invece che per lotteria. Pura riallocazione
   di compute, zero teoria nuova. Il rischio: il self-score che seleziona è lo stesso strumento
   ~+0.010 ottimista — ma qui lo usate RELATIVAMENTE (scegli il migliore tra N), dove è più affidabile.

Verdetto: **la #1 è il primo esperimento che farei domani.** È a un submission-pair, è nella famiglia
giusta, e attacca esattamente il termine che vincola (struttura del normale via miglior placement).

### 3.C — ENORMI (riaprire l'iterazione offline + rebuild) — atteso +0.5…+1.2, è qui che vive il 91

Le strade grandi migliorano il meccanismo di poco per tentativo. Il **91 richiede o molta più
larghezza di banda di misura, o un salto di meccanismo.** Due mosse enormi, la prima è la più
importante e nessuno l'ha ancora fatta:

1. **DE-BIAS del proxy per riaprire l'iterazione offline. ⚑ La mia raccomandazione forte.**
   Voi avete dimostrato PERCHÉ il proxy non trasferisce (§9.1): i proxy sono prodotti di decimazione
   dell'armadillo → campo di normali *troppo liscio* rispetto agli scan grezzi del giudice → il
   position-space optimizer trova struttura recuperabile che sul giudice non c'è. **Questa diagnosi è
   una ricetta per la cura.** Aggiungete al proxy c3 un rumore scan-like (displacement ad alta
   frequenza lungo la normale, ampiezza calibrata) finché **una** differenza A/B già misurata sul
   giudice (es. R1 judge-negativo, o SIL ratio 0.3) si riproduce localmente con il segno e l'ordine
   di grandezza giusti. A quel punto avete un proxy che TRASFERISCE, e potete tornare a iterare
   offline a costo zero submission invece di 1-submit-per-idea. **Questo attacca direttamente il vero
   collo di bottiglia (§0.3).** È lavoro di giorni, non di ore, ma moltiplica per 10–100 la vostra
   velocità di ricerca — che è l'unica cosa che vi separa dal ceiling vero. Nessun doc lo propone;
   lo considero il singolo investimento a più alto rendimento del progetto.

2. **Co-ottimizzazione differenziabile DURANTE la riduzione, sul metrica VERO (non sul proxy).**
   nvdiffmodeling-style ma CPU e — cruciale — validata judge-side col S-read. Il gradiente analitico
   della SSIM (`refine_score_grad`) esiste già; manca l'interleaving decimazione↔co-opt come
   ottimizzatore congiunto. R1 (la sua forma "burst") è morto sui PROXY; ma se la #1 vi dà un proxy
   che trasferisce, R1/co-opt vanno RI-testati lì, e la conclusione "morto" potrebbe ribaltarsi.
   Prerequisito assoluto: il compile-headroom di §2 (la co-opt aggiunge codice pesante).

3. **(Speculativo, ma è "occhio intelligente")** Il termine che vincola è σxy, la *correlazione*
   spaziale del campo di normali dentro finestre 11×11. La superficie 3D vince sul mosaico libero
   (THEORY §4) proprio perché i normali delle facce sono spazialmente correlati. Domanda che nessun
   doc si pone fino in fondo: **esiste una triangolazione che massimizza σxy per vertice invece di
   minimizzare l'errore L2,1?** VSA-lite minimizza `area·(1−cosθ)` (errore di normale). Ma il giudice
   non premia l'accuratezza del normale in sé — premia la sua **correlazione con l'originale dentro
   la finestra box**. Sono obiettivi *diversi*. Una selezione di collasso guidata dal delta-σxy vero
   renderizzato (R-ζ nel vostro registro) ha dato +0.0022 su cow ma ~0 su bunny organico — MA è stata
   testata solo LOCALMENTE, sul proxy over-liscio, dove σxy è già saturo. Su uno scan grezzo (proxy
   de-biasato della #1) il segnale potrebbe riemergere. **Le strade #1 e #3 si abilitano a vicenda.**

Verdetto: la **#1 è la vera leva architetturale.** Tutto il resto del progetto è stato limitato dal
non poter iterare offline in modo affidabile. Risolvete QUELLO e le strade grandi diventano
economiche, la co-opt torna testabile, e il ceiling "misurato" si rivela per quello che è — un
artefatto dello strumento, non una legge fisica.

### 3.C.2 — DATA SOURCING: la forma VERA del de-bias (aggiunta 2026-07-09) ⚑ NUOVA, priorità alta

Il de-bias sintetico (3.C.1) cerca di *simulare* uno scan grezzo aggiungendo rumore a un mesh pulito.
Ma l'analisi dei dati locali dice che si può fare di meglio, andando alla radice. Fatti misurati:

- **Avete UN solo mesh organico hi-res: armadillo (49.990 V), già "watertight" = ripulito/denoised.**
  Tutto l'organico (c3/c5/c6/c7) è proxato da lì. Il proxy di **case-3 è armadillo decimato a ~25k** →
  doppiamente liscio. Rugosità misurata (dihedral medio): armadillo 10.2°, bunny/cow 13–17°, fandisk
  (CAD) 3.9°. La decimazione è un **filtro passa-basso**: rimuove la struttura ad alta frequenza che è
  proprio il segnale che il giudice paga (σxy) e che lo scan vero a 23k conserva. **Questo È il bias
  §9.1, alla sorgente.**
- **Il giudice usa modelli STANDARD di ricerca.** Prova: `case-5 = 49.987 V ≈ armadillo Stanford
  (49.990)`, differ. di 3 vertici = stesso modello, processing diverso (infatti "+0.055 SSIM più
  clemente" del vostro proxy). I conteggi esatti (c3=23.201, c4=35.292, c6=377.084, c7=1.009.118) sono
  impronte di post-processing. `[INFERRED]`

**Il piano (in ordine di valore):**
1. **Identificare i modelli-sorgente per famiglia + risoluzione** (web research, DATA-side). Candidati
   per taglia: c6≈377k → Stanford dragon (~437–566k) decimato; c7≈1M → dragon/buddha/lucy/thai decimati
   a 1M; c3≈23k organico → un modello organico decimato *poco*; c4 CAD → classe ABC/fandisk. Se
   identificati e riprocessati alla risoluzione giusta, **c5/c6/c7 diventano riproducibili offline** →
   i loro muri sono misurabili offline, il coin e il transfer-problem spariscono per quei casi.
2. **Scaricare gli scan GREZZI** (Stanford 3D Scanning Repo ha i range data con rumore sensore reale).
   Un armadillo grezzo È letteralmente il proxy de-biasato di 3.C.1, **senza sintesi**. Test decisivo:
   R1 legge negativo su un proxy grezzo/nativo *out-of-the-box*? Se sì, "troppo liscio" è confermato e
   avete uno strumento che trasferisce, gratis.
3. **Un mesh organico NATIVO ~23k** (non decimato-da-50k) per uno screen SSIM di case-3 fedele.

**Caveat onesto:** non conoscerete il processing ESATTO del giudice (watertight-repair, metodo di
decimazione, rumore), quindi la riproduzione esatta è improbabile. Ma un proxy con **il modello giusto,
la risoluzione giusta e rugosità realistica** trasferisce incomparabilmente meglio di un
armadillo-pulito-decimato — ed è l'unica via per riavere l'iterazione offline, che è il vero collo di
bottiglia (§0.3). **Questa è la 3.C rivista: fatela PRIMA del rumore sintetico.**

*(Nota di igiene emersa dall'analisi: la harness usa `probe/cache/c3band.obj`/`c4band.obj` =
**fandisk (CAD) suddiviso** — corretto SOLO per preflight validità/conteggio-vertici, MAI per un A/B
di SSIM organica. E c6/c7 non hanno alcun proxy locale: ciechi offline su quei due, accettabile perché
saturi al 97%.)*

**Convergenza dalla letteratura recente (web 2026):** la SOTA appearance-driven (MeshSplatting, CVPR
2026; nvdiffmodeling) fa co-opt geometria+apparenza con perdite percettive (DSSIM) e — dettaglio che
NON avete — **densify/prune adattivo guidato dal contenuto renderizzato** (suddividi i triangoli ad
alto contenuto, pota quelli sotto-contribuenti). Il vostro pipeline solo *decima poi* sposta i vertici;
non *aggiunge* triangoli dove il deficit SSIM è alto. È un lever nuovo-per-voi dentro la famiglia smooth
(una R-δ arricchita), pesante e transfer-rischioso, ma è l'unica idea algoritmica fresca che la
letteratura offre — e diventa testabile solo DOPO 3.C.2 (serve un proxy che trasferisce).

---

## 4. La sfida critica ai vostri doc (dove "non è tutto vero al 100%")

Come richiesto, ecco dove leggerei i doc con sospetto:

1. **«Case-3 mechanism front near practical ceiling» (LIMITS.md Front B).** Difeso principalmente da
   test locali su un proxy che NON trasferisce + una manciata di A/B judge. Epistemicamente debole:
   avete chiuso porte con uno strumento rotto. Il leader a 91.46 falsifica il "ceiling". **Non è
   chiuso; è non-misurato.**

2. **«leader_c3 ~72–77%, premio modesto» (ROADS.md/IDEAS.md).** Inferenza da un gap totale spalmato
   su ipotesi non verificabili. Plausibile ma non un fatto. Vedi §1 lettura due. Non lasciate che
   ridimensioni l'unico fronte vincente.

3. **docs/README.md** rimanda a `problem-statement-summary.md`, `judge-map.md`,
   `architecture-roadmap.md` — **nessuno dei tre esiste.** Il "read in this order" per un nuovo
   agente è rotto. Doc-drift puro.

4. **handoff/SOLVER_STATE.md** si auto-dichiara «OLD FILE, IT MUST BE UPDATED... TOO VAGUE» e riporta
   bank 90.099634 e 89.8247 e 89.49 in tre punti diversi. **Un agente che lo legge per primo parte
   con lo stato sbagliato.** Va cancellato o riscritto, non lasciato lì.

5. **README.md (root)** dice «`solver/main.cpp` is currently an empty scaffold». È FALSO da ~100
   submission. Il README di primo livello mente sullo stato del progetto.

6. Il numero di "bank" corretto (**90.285538**) convive con 90.276093, 90.276200, 90.238542,
   90.099634 sparsi nei doc a seconda della data. Solo `handoff/submissions.jsonl` + Kattis sono
   affidabili, e submissions.jsonl è **incompleto** (non logga le submission da web UI, incluso il
   bank). **Nessuna fonte locale singola conosce il bank vero.** Questo è un problema serio: §5.

**Regola generale che ne ricavo:** i vostri doc TECNICI (THEORY, JUDGE-ENVELOPE, WALL-MODEL) sono
eccellenti e affidabili. I vostri doc di STATO (README, SOLVER_STATE, docs/README) sono andati in
drift. Il fix è strutturale (§5): separare "verità durevole" (raramente cambia) da "stato corrente"
(cambia ogni submission) e avere UNA sola fonte per lo stato.

---

## 5. Riorganizzazione del repo per un agente AI (token-efficiency)

Il problema concreto: un agente che apre questo repo trova 6 doc top-level + 5 in case3-lab + 5 in
Future + 10 postmortem + 3 in handoff + **102 cartelle di submission (5.5 MB)** + doc di stato in
contraddizione. Deve leggere metà repo per capire dove siamo, e rischia di credere a un numero
sbagliato. Ecco il ridisegno.

### 5.1 Una sola fonte di verità per lo STATO — `STATUS.md` (root)

Un unico file, ≤1 schermata, aggiornato a OGNI submission, che contiene SOLO ciò che cambia:

```
BANK: 90.285538 (7/7)  — verificato su Kattis 2026-07-08, non da submissions.jsonl
LEADER: 91.46 (manuale, browser)
PER-CASE:  c2 99.32 (N=28) | c3 70.08 (N=6941) | c4 85.71 (~5044) | c5 91.55 (4212) | c6 97.69 (~8705) | c7 97.14 (~28822)
LIVE main.cpp = <sha256 corto> <banner> <data>
FRONTE ATTIVO: case-3, meccanismo di placement (Road 3.B.1)
PROSSIMA AZIONE: A/B Hoppe-placement, 2 read @6941
```

Tutto il resto (perché, storia, teoria) sta altrove e NON si ripete qui.

### 5.2 Gerarchia canonica (cosa tiene, cosa si legge quando)

| livello | file | ruolo | cadenza di aggiornamento |
|---|---|---|---|
| **STATO** | `STATUS.md` | dove siamo ORA, cosa fare dopo | ogni submission |
| **CONTRATTO** | `CLAUDE.md` | come lavorare senza allucinare (vedi file allegato) | raro |
| **VERITÀ GIUDICE** | `docs/JUDGE-ENVELOPE.md` | ogni fatto misurato sul giudice | ogni probe |
| **VERITÀ METRICA** | `docs/THEORY.md` | la matematica, cosa è provato | raro |
| **MODELLO MURI** | `docs/WALL-MODEL.md` | cos'è un muro, S-read, automazione | raro |
| **CODICE** | `docs/SOLVER-INTERNALS.md` | mappa riga-per-riga di main.cpp | quando cambia il codice |
| **REGISTRO STRADE** | `docs/ROADS.md` (promosso da case3-lab) | strade queued/active/dead con provenance | ogni idea/verdetto |
| **STORIA** | `handoff/ATTEMPT_LOG.md` | narrativa cronologica | ogni submission |
| **DATI** | `handoff/submissions.jsonl` | ledger machine-readable | ogni submit script |

### 5.3 Cosa ARCHIVIARE (togliere dal cammino dell'agente)

- **`submissions/` → `archive/submissions/`** e aggiungere a `.gitignore` dell'attenzione dell'agente
  (o un `archive/README.md` che dice "non leggere qui salvo caccia storica"). 102 cartelle, 5.5 MB,
  quasi tutte snapshot morti. Tenere SOLO l'ultimo bank e gli ultimi 2-3 esperimenti vivi come
  `submissions/current/`. **Regola: la cartella `submissions/` attiva contiene ≤5 elementi.**
- **`handoff/SOLVER_STATE.md` → cancellare** (rimpiazzato da STATUS.md). Si auto-dichiara morto.
- **`docs/README.md` → riscrivere** con i link ai file che ESISTONO davvero (togliere i 3 fantasma).
- **`README.md` (root) → correggere** la frase "empty scaffold".
- **`docs/Future/` → fondere in `docs/ROADS.md`.** Idee forward-looking e registro strade sono la
  stessa cosa; averle in due posti crea drift (già successo: c4-harvest-ladder vs WALL-MODEL).
- **case3-lab: fondere README+LIMITS+IDEAS+ROADS+RESULTS in DUE file:** `docs/ROADS.md` (strade) e
  `case3/RESULTS.md` (log dei read c3). 5 file → 2. Oggi si sovrappongono pesantemente.

### 5.4 Convenzioni che fanno risparmiare token all'agente

- **Ogni doc inizia con un blocco `STATE:` di 3 righe** (bank, fronte, ultima azione) così l'agente
  sa in 1 read se il doc è fresco, senza leggerlo tutto.
- **Un solo numero di bank in tutto il repo**, e sta in STATUS.md. Ogni altro doc che nomina il bank
  scrive «bank (vedi STATUS.md)», mai il numero. Elimina il drift a 5 numeri.
- **Provenance tag obbligatorio** su ogni claim quantitativo (`[JUDGE]`/`[LOCAL]`/`[INFERRED]`/
  `[UNTESTED]`) — lo fate già in LIMITS.md/ROADS.md, estendetelo ovunque. È la difesa numero uno
  contro l'allucinazione: un agente vede subito se un "fatto" è judge-provato o proxy-debole.
- **Naming submission**: oggi `v106-readbank-4212-90243142` è ottimo (versione-cosa-caso-score).
  Tenetelo, ma spostate tutto in archive.

---

## 6. La domanda al giudice (una sola)

Regole che mi do: (a) non deve chiedere la soluzione; (b) la risposta deve poter cambiare la
strategia in modo materiale; (c) deve essere ancora GENUINAMENTE aperta — cioè non già risolta dalla
vostra calibrazione. Il punto (c) è sottile: la vostra calibrazione §7.1 (self-score di una mesh
semplificata = pass/fail del giudice) ha di fatto chiuso normal-space, depth-scaling e la finestra
box, perché sono *systematics condivisi* solo per l'identità, ma la mesh semplificata li mette alla
prova. Quindi la maggior parte delle domande metriche NON è più utile.

Quello che la calibrazione **NON** ha davvero pinnato, perché richiede una mesh con silhouette molto
diverse dall'originale (e voi testate vicino al muro dove le silhouette combaciano), è il
**trattamento dei pixel di background DENTRO una finestra contata**. È l'analogo esatto della
clarification Hausdorff che vi ha aperto una porta: una definizione di dettaglio che, se più lasca di
come l'assumete, sposta dove vive il deficit.

> **DOMANDA (tipo: definizione della metrica, alto-leverage, ancora aperta):**
> «Per la SSIM: una finestra 11×11 è conteggiata quando il suo pixel centrale è foreground
> nell'originale o nella semplificata (unione). All'interno di una finestra così contata, le
> statistiche SSIM (medie μ, varianze σ², covarianza σxy) sono calcolate su **tutti i 121 pixel**
> della finestra (inclusi i pixel di background con il loro valore costante), oppure **solo sui pixel
> foreground** presenti nella finestra?»

Perché è la domanda giusta:
- **Alto leverage.** Il termine che vi vincola è σxy sul normale, e voi misurate che «~90% del
  deficit è nelle finestre interne». Ma se il giudice INCLUDE i pixel di background nelle statistiche
  (come assumete), le finestre a cavallo della silhouette sono dominate dalla costante di sfondo →
  il deficit di struttura è calcolato in modo diverso rispetto a un giudice che MASCHERA il
  background. Le due ipotesi implicano strategie di steering **opposte** sulle finestre di bordo.
- **Ancora aperta.** La vostra calibrazione l'ha toccata solo tangenzialmente (una singola mesh, un
  singolo pass/fail vicino al muro dove le silhouette combaciano). Non è pinnata come lo sono
  normal-space o depth.
- **Non è "dammi la soluzione".** È una definizione di rendering/scoring, esattamente come la
  domanda Hausdorff che vi hanno risposto il 2026-06-18.

**Runner-up (se preferite una porta di compressione anziché di metrica):** «Un output può contenere
vertici isolati (referenziati da nessuna faccia) restando valido, dato 1 ≤ V′ ≤ V?». Perché conta:
se un meccanismo migliore spinge c3 verso 76%+, la direzione *forward* dell'Hausdorff v2v (ogni
vertice ORIGINALE deve avere un vertice output vicino) può iniziare a vincolare; vertici isolati
sparsi sui cluster originali scoperti la soddisfano a **costo SSIM zero** (un vertice isolato non
renderizza nulla). È una valvola di sfogo che sblocca la compressione aggressiva proprio nello
scenario in cui vincete. Voi lo segnate come OPEN/IDLE (§8) — diventa non-idle appena la strada 3.B/3.C
funziona. Ma la domanda primaria sulla finestra SSIM ha leverage più immediato sul fronte che vi
vincola OGGI.

---

## 7. Piano operativo consigliato (ordine di esecuzione)

1. **Bonifica compile/source headroom** (§2) — prerequisito, ~1 sessione. Verifica byte-identità.
2. **Riorganizza il repo** (§5) — STATUS.md, archivia submissions, cancella SOLVER_STATE, fondi i
   doc. ~1 sessione. Fa risparmiare token a ogni sessione futura.
3. **Adotta CLAUDE.md** (file allegato) come contratto operativo.
4. **Road 3.B.1 (Hoppe-placement A/B via S-read)** — il primo esperimento a premio, 1 submission-pair.
5. **In parallelo, gratis:** re-roll dei coin nei giorni caldi (3.A).
6. **Investimento grosso: de-bias del proxy (3.C.1)** — la leva vera. Se riesce, riapre R1/co-opt/R-ζ
   offline e cambia il gioco.
7. **Manda la domanda sulla finestra SSIM** (§6) — è gratis e può riaprire il fronte struttura.

---

## 8. PERCHÉ SIAMO FERMI: il processo, non le idee (analisi 2026-07-09)

Il punteggio ha fatto 88.67 → 89.5 → 89.8 → 90.0 → 90.24 → **90.28** e poi si è appiattito. Dopo aver
letto anche l'oracolo e l'ultimo giro dell'agente, la mia diagnosi è che **il plateau è del METODO, non
delle idee.** Sette patologie di processo, in ordine di quanto spiegano lo stallo:

1. **Il processo ottimizza per la CHIUSURA difendibile, non per il punteggio.** Il segnale di reward
   che l'agente si dà è "ho ucciso una strada con rigore". Il cimitero (ROADS §2) cresce ogni sessione,
   il numero no. La sua frase di chiusura — *"non brucerò submission su idee morte. Quale direzione?"* —
   è orgoglio nel **non** fare. Rigore vero, puntato sull'obiettivo sbagliato. **Questa è la falla
   madre; le altre sono sintomi.**

2. **Settimane di misura con un righello rotto.** §9.1 (i proxy non trasferiscono) è nei doc da tanto,
   eppure l'agente ha continuato a fare A/B locali (inutili) e a **chiudere strade su quelli**. La cosa
   che riaprirebbe l'iterazione — un proxy che trasferisce — non è mai stata costruita davvero (§3.C.2).
   Non si scala fidandosi di un altimetro rotto e registrando i suoi errori come fatti sulla montagna.

3. **Ridimensionamento motivato del bersaglio.** "leader_c3 77% non 85%": comodo, fa sembrare il plateau
   un soffitto. Adottato *mentre* si è bloccati = motivated stopping. Forse vero, ma abbassa l'urgenza
   proprio quando non dovrebbe.

4. **Hoarding delle submission — l'errore strategico.** **432 tentativi contro gli 800–6.640 dei
   leader.** Le submission fallite sono GRATIS (best-counts), il rate limit consente centinaia/giorno.
   L'agente è *orgoglioso* della frugalità e la razionalizza. I leader hanno scalato probando 2–15× di
   più. La risorsa scarsa è il **tempo alla deadline**, non gli slot. Stanno conservando l'unica cosa
   gratis. (Ho corretto il CLAUDE.md §5 di conseguenza.)

5. **Monocultura mono-file, mono-famiglia.** Una pipeline rifinita all'osso; l'alternativa (main_v2)
   abbandonata al 64%. Nessun secondo approccio vero in parallelo. Il compile-cliff trattato come legge
   di natura (finché la bonifica — solo dopo spinta esterna).

6. **"In-family esaurito" poggia INTERAMENTE sul righello rotto.** Non c'è quasi evidenza judge-side che
   la pipeline attuale sia ben tarata sui mesh VERI. Uno schedule di keep / λ / allocazione-refine
   diverso potrebbe essere molto meglio sugli input reali, e non lo vedono. Il soffitto potrebbe essere
   un artefatto dello strumento.

7. **Auto-arbitraggio senza red-team.** L'agente valuta i propri esperimenti e ha liquidato il report
   esterno come "0 lever". La prima lettura esterna (questa) ha trovato una chiusura prematura in un
   giorno. Le chiusure non sono mai state contestate.

### 8.1 Due mosse ingegneristiche che nessuno ha messo in discussione

- **Il "coin" box-cut è auto-inflitto.** Esiste perché il refine è boxato a tempo (wall/CPU) → il taglio
  cade a un'iterazione non deterministica. **Refine a NUMERO FISSO di iterazioni** dimensionato al budget
  con margine → output deterministico per binario → il bank si riproduce ogni volta e il rumore degli
  A/B crolla. Hanno speso mesi a *gestire* una moneta che potevano *cancellare*. Prerequisito insieme al
  proxy (§3.C.2) per riavere l'iterazione offline.
- **L'oracolo ha una cucitura non verificata sul termine che vincola.** `ssim.py` include i pixel di
  background (grigio 127.5 / depth 255) nelle statistiche μ/σ/σxy delle finestre a cavallo della
  silhouette. Se il giudice li MASCHERA, l'oracolo è sbagliato esattamente dove vive il deficit di
  struttura di case-3, e la calibrazione §7.1 non lo coglierebbe. È il motivo per cui la domanda al
  giudice sulla finestra SSIM (§6) conta davvero.

### 8.2 Onestà: cosa io NON ho ancora verificato

Perché il review sia affidabile deve dire anche i suoi buchi. Non ho ancora: (a) letto il codice del
**refine/gradiente** in main.cpp — l'unica cosa che trasferisce è throughput/traiettoria, e un bug o
un'inefficienza lì sarebbe invisibile a ogni A/B locale; (b) letto **main_v2** per giudicare un ibrido
costruzione+decimazione; (c) **scaricato i mesh-sorgente candidati** del giudice e provato a matcharli
per conteggio (il compito concreto a più alto valore, ancora da fare). Questi sono i prossimi passi.

### 8.3 La prescrizione in una riga

**Smettere di chiudere strade, iniziare ad aprire lo strumento.** Sistema il righello (proxy
matched/grezzi + refine deterministico), poi spendi le submission come se fossero gratis (lo sono),
mieti in parallelo le monete facili su c4/c6, e smetti di rimpicciolire il bersaglio. Le idee non sono
il collo di bottiglia — il **metodo** lo è.

---

*Fine. I due deliverable operativi — questo review e il `CLAUDE.md` — sono pensati per stare
insieme: questo dice DOVE andare e perché; il CLAUDE.md dice COME lavorarci senza allucinare. §8 dice
perché finora NON ci siamo riusciti.*
