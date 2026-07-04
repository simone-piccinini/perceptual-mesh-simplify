# Teoria consolidata — la matematica del metrica e cosa abbiamo dimostrato

Tutto ciò che serve sapere per ragionare sul punteggio, in un file solo. Ogni affermazione
quantitativa qui è MISURATA (oracolo locale bit-exact o giudice vero), non congetturata.
Le regole/scoperte sul giudice stanno in PROBLEM-AND-JUDGE.md; qui c'è il perché matematico.

## 1. La formula SSIM e la sua decomposizione

Per due immagini X, Y su finestra 11×11:

    SSIM = [(2μxμy + C1)(2σxy + C2)] / [(μx² + μy² + C1)(σx² + σy² + C2)]
    C1 = (0.01·255)² = 6.5025      C2 = (0.03·255)² = 58.5225

Decomposizione classica in tre fattori (luminanza · contrasto · struttura):

    l = (2μxμy + C1)/(μx² + μy² + C1)     c = (2σxσy + C2)/(σx² + σy² + C2)
    s = (σxy + C2/2)/(σxσy + C2/2)

**Misura chiave (2026-07-02, tutti i casi con proxy):** sul canale normale, al muro:
l ≈ 0.999, c ≈ 0.98, **s ≈ 0.74–0.82, con σy ≈ σx (21 vs 21 encoded)**. Tradotto: la mesh
semplificata ha la giusta QUANTITÀ di variazione ma il disegno è nel posto sbagliato dentro le
finestre. Il deficit è correlazione (σxy), non contrasto. Inoltre ~90% del deficit sta nelle
finestre interne, non sulle silhouette.

## 2. Forma chiusa per finestre piatte, e perché il costo VSA è "giusto"

Finestra interamente dentro una faccia originale (valore encoded a) e una semplificata (b):
varianze nulle → SSIM collassa alla sola luminanza:

    SSIM_flat = (2ab + C1)/(a² + b² + C1)     ⇒     1 − SSIM_flat = (a−b)²/(a² + b² + C1)

Identità utile: con encoding a=(n+1)·127.5, per due normali unitarie n̂₁, n̂₂:

    Σ_canali (a_c − b_c)² = 127.5²·|n̂₁ − n̂₂|² = 2·127.5²·(1 − cosθ)

Cioè: **il costo di collasso `area·(1−cosθ)` (VSA-lite) È la somma dei quadrati delle
differenze nello spazio encoded** — il modello simmetrico corretto. Le varianti asimmetriche
(pesare col denominatore a²+b²+C1, che renderebbe i normali encoded≈0 fino a 20.000× più
sensibili) sono state testate a piena e mezza forza: SEMPRE peggio (fino a −0.016). Il metrica
reale è dominato dai termini di contrasto/struttura (scala C2), non dalla luminanza pura.

## 3. L'asimmetria di sensibilità normale/depth (misurata: ~6.850×)

Stesso spostamento fisico Δz=0.012 di un vertice, valori REALI del caso 5 (w faccia=0.0322,
z̄ foreground=2.199, σ²depth finestra=0.0021 ≪ C2 → contrasto/struttura depth saturi):

    costo depth  ≈ Δz²/(2z̄² + C1) = 0.000144/16.17 ≈ 8.9·10⁻⁶   per finestra
    effetto normale: tiltθ = atan(Δz/w) = 20.4° → Δa = 127.5·sinθ ≈ 44.5
                     ≈ Δa²/(2·127.5² + C1) ≈ 0.061                 per finestra
    rapporto ≈ 6.850 : 1   (lower bound: il termine s del normale è ancora più sensibile)

Conseguenza: il metrica "fattorizza" — la forma (depth) costa quasi nulla, l'orientamento
(normale) è tutto. Sfruttamenti falsificati: ottimizzazione nel sottospazio dei tilt (il
gradiente all'ottimo è zero, e la proiezione di zero è zero); tilt costruttivi con proxy
economici (−0.007: i proxy locali non sanno scegliere i tilt giusti per l'immagine).
Sfruttamento superstite: scelte costruttive guidate dalle immagini vere.

## 4. Perché la superficie batte il mosaico libero (test del 2026-07-04)

Fit 2D a layout libero dell'immagine normale (+X, budget = 2.738 vertici come la mesh, colori
liberi unit-norm, silhouette perfetta): **0.689 contro 0.810 della mesh 3D**. Con budget 7×
(20.000 punti): satura a 0.911. Meccanismo: i normali delle facce 3D sono spazialmente
CORRELATI per continuità geometrica — è esattamente la σxy che il termine di struttura premia;
un mosaico di costanti indipendenti non la replica a nessun budget sensato. Corollario: la
superficie originale è la migliore "guida di layout" possibile; la famiglia image-fit
construction è chiusa per misura, non per pigrizia.

## 5. Il limite informativo e dove sono i muri

A budget V fisso, la mesh dipinge ~2V facce piatte; una finestra 11×11 a 1024² copre ~2–4
facce nostre contro ~20–40 originali. La σxy raggiungibile = frazione della varianza del
disegno che vive a scala ≥ della faccia. I muri per caso (tutti respinti con 3–6 meccanismi):

    c2 99.298 | c3 70.03125 | c4 85.71875 | c5 91.546875 | c6 97.6953125 | c7 97.145

Slope tipico vicino al muro: ~0.0013 SSIM per 0.5% di compressione (c3). I rung distano
0.0002–0.0004 SSIM: per questo il rumore FP tra binari (σ≈0.0002) li fa "estrarre".

## 6. Cosa ha funzionato (giudice-confermato) e il suo perché

- **VSA-lite** (ordine di collasso per distorsione del normale, non per errore di posizione):
  il giudice guarda normali; l'ordinamento greedy col heap fa equalizzazione globale del costo
  marginale su geometria fresca — batte ogni partizione statica (Lloyd testato ×6: sempre peggio).
- **Pivot-A / s-def steering** (mappa del deficit renderizzato → protezione): il segnale di
  struttura (s-def) ha rotto muri che quello di contrasto non rompeva — coerente con §1.
- **nplace/aniso**: candidati di piazzamento che esplorano la direzione piatta del tangente;
  su oggetti CAD (c4) l'anisotropia vale +0.25 di compressione (teoria: errore O(N⁻²) vs
  O(N⁻¹) su regioni anisotrope). Su organici: nulla (misurato, giudice).
- **Refine inverse-rendering**: ascesa sul gradiente ANALITICO della SSIM vera (bit-exact),
  monotona, box 16s. Convergiuto (8s=16s=64s). La fase finale a 1024 esatti (hybrid) vale
  +0.0013 e ha rotto il muro c3.
- **2-stage per c7**: sgrossatura QEM fino a 5× target poi VSA — 8.0s→3.9s a qualità pari
  (i collassi precoci sono a basso errore sotto qualsiasi ordinamento).
- **Tail-harvest**: vedi PROBLEM-AND-JUDGE.md §4 (determinismo per binario, estrazioni).

## 6b. ✗ Strade chiuse DAL GIUDICE il 2026-07-04 (con il perché)

- ✗ **Flip-to-unlock del floor topologico** — 3 submission (gate rilassato, flip valence≥7,
  valence-somma≥12): output c2/c4 SEMPRE identico. Il floor non è geometrico ma di GENUS
  (vedi PROBLEM-AND-JUDGE §5b) — i flip non cambiano la topologia. Codice resta (innocuo,
  scatta solo se alive>target).

- ✗ **Masking-prior (divisive normalization)** — giudicato WA su c3/c4/c5 ai rung (3 submission).
  Perché non funziona: il masking vale per distorsioni ADDITIVE (rumore di quantizzazione);
  la nostra è STRUTTURALE — nelle zone lisce l'errore va a zero da solo con poche facce, e il
  greedy le demolisce già per prime. Proteggerle affama il dettaglio.
- ✗ **Tilt costruttivo (candidati fuori-superficie in nplace)** — giudicato WA su c3. Perché:
  i proxy economici del costo (vicinato o nref) non sanno scegliere i tilt giusti per
  l'immagine; solo il metrica renderizzato vero li sceglierebbe, ma a decimation-time costa
  troppo. (Il tubo Hausdorff v2v resta legale e inutilizzato.)
- ✗ **Sigillatura zone nascoste** — misurato PRIMA di costruire: 0 vertici mai-visti negli
  output attuali (culling+decimazione li eliminano già). Valore zero.
- ✗ **Pannelli-rilievo per vista (imposter geometrici)** — legali (output disconnesso accettato,
  v96) ma il flat-test dice che la specializzazione per-vista perde 0.12 SSIM contro la
  continuità della superficie, e i pannelli costano ~2.4× in vertici (niente condivisione
  multi-vista). EV negativo.

## 7. ✗ Cimitero (mai rifare senza un meccanismo DIVERSO)

Steering: varianti raggio/potenza/view-max/qweight del s-def (5 config giudicate). Partizioni:
Lloyd ×6. Connettività: splits (un inserimento = un un-collapse; il migliore è l'ultimo
collasso del greedy), flips (oggettivo-smoothing = anti-struttura, −0.016). Ottimizzatore:
Adam/momentum (crash: paesaggio a lama), basin-hop (0 hop nel budget), Sobolev/Laplaciano
(λ↑ → peggio: liscia proprio le mosse ad alta frequenza che il metrica paga), budget 4×
(convergiuto), jitter esplicito (costo medio 10× la varianza aggiunta). Geometrico: unsharp
(σ già a posto), scala globale (picco esatto a 1.0 = sag già bilanciato), subdivide-then-
decimate (diluisce la discriminazione greedy). Multistart su c2 (il seed migliore per il
Final-512 non è migliore a 1024; ha rotto il rung bancato — pattern "miglioria al rung
confermato rompe il caso", visto 2 volte). Depth: gradiente interno inutile (deficit interior
≈ 10⁻⁴/finestra; il 73% del deficit depth è silhouette = coverage discreta, invisibile al
gradiente). Letteratura SSIM-ottimale (Brunet/Vrscay/Wang): coefficienti SSIM-ottimali =
riscalatura dei coefficienti L2 — dominata dal nostro ottimizzatore diretto.
