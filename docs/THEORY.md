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

- ✗ **Vertex-removal endgame contro i floor** — costruito e giudicato (19888881): localmente
  sfonda ogni inceppamento geometrico (bunny→3 verts, il minimo assoluto; trefoil→13 = bound
  del suo genus 1), ma sul giudice c2/c4 non cede NULLA → i loro floor sono GENUS VERO
  (c2 ≈ 2–4 manici, c4 ≈ centinaia di fori CAD). Ultima porta per quei casi: chiudere i fori
  (surgery) — ma i fori c4 sono 3–7px visibili nelle foto = costo SSIM, giorni di lavoro.
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

## 8. THE ROADS FROM HERE (2026-07-05, post-envelope-completion; in English by request)

Everything incremental inside the current pipeline family is judged-closed (§6b/§7 + the
2026-07-05 closures in ATTEMPT_LOG: keep/λ/res/hybrid ladders on case 5, case-3 push, 768).
The bank is 90.238542; the leader ~91.6. What remains, ranked by expected value:

### Road A — ✗ Topology surgery — DEAD 2026-07-05 (genus probes: BOTH candidate cases are genus-0 spheres)
**Verdict [MEASURED 19895596 + 19895626]: case 2 AND case 4 (the CAD) are 1-component,
genus 0. There are no handles to remove; the "topological floors" were wrong-size arithmetic
plus geometric gate jams. Surgery has zero prize on this test set. Road closed for the cost
of two probe submissions — the paper list below is kept only as a record of what NOT to read
now.** Original plan follows for the archive:
**Why:** the judge requires closed-2-manifoldness but NOT genus preservation (ENVELOPE §6.1).
Our greedy manifold-PRESERVING collapse jams at "topological floors" on the CAD case (4,570
verts) — if that floor is a genus jam, an algorithm allowed to close handles/holes goes far
below it, paying only SSIM. Case-4 vertices are worth 5.2e-4 total each: 2,000 verts below
the floor ≈ **+1.0 on the total**. That is leader-gap material.
**Status:** genus probe on case 2 answered (sphere, genus 0 — c2 prize void, its 28-floor is
an SSIM wall, mislabelled). Case-4 genus probe = next submission after its size probe.
**How to build (if genus > 0):**
1. cheapest first: Garland-Heckbert **vertex-PAIR contraction** (the original QSlim paper
   supports non-edge pairs!) — add distance-threshold virtual pairs to the heap; the existing
   quadric/heap machinery is reused verbatim; the link-condition gate is replaced for virtual
   pairs by a component-merge/handle-pinch validity check;
2. hole filling on the INPUT before decimation (CAD holes → disks), giving the decimator a
   lower-genus surface to chew;
3. explicit handle removal (localized genus surgery).
**Test path:** local first on any genus>0 proxy (fandisk? torus subdivisions) — verify the
manifold checker accepts pinched results; judge A/B at the confirmed case-4 keep, then push
the keep down in fixed-count steps.
**Papers to pull (and why):**
- Garland & Heckbert, *Surface Simplification Using Quadric Error Metrics* (SIGGRAPH 97) —
  §"aggregation": virtual pairs = topology-modifying contraction; exactly our machinery.
- Popović & Hoppe, *Progressive Simplicial Complexes* (97) — principled non-manifold-safe
  contraction lattice, the theory behind "collapse anything".
- El-Sana & Varshney, *Topology Simplification for Polygonal Virtual Environments* (TVCG 98)
  — α-hull based hole/handle elimination with error control.
- Wood, Hoppe, Desbrun, Schröder, *Removing Excess Topology from Isosurfaces* (TOG 2004) —
  handle detection + localized surgery on scanned surfaces (case 6/7 class inputs).
- Guskov & Wood, *Topological Noise Removal* (GI 2001) — cheap handle detection via local
  wavefront growth; good fit for a 21 s CPU budget.

### Road B — A better refine optimum for the SSIM-walled organics (cases 5, 3, 6)
**Why:** the case-5 wall is the LOCAL OPTIMUM of monotone gradient ascent from the greedy
mesh; probes showed structurally different meshes at the same count spread ±0.013 SSIM —
the wall is family-relative, and ~0.007 of spread sits above our converged point.
**What to try (in local-A/B order on the faithful case-3 proxy):**
1. joint decimate+optimize loops (decimate → refine → RE-decimate the refined mesh → refine):
   the refine moves vertices to SSIM-optimal positions; re-running VSA ordering on THAT
   geometry explores a different basin per cycle at ~zero new code;
2. appearance-driven simplification à la nvdiffmodeling: differentiable-renderer
   co-optimization of positions during (not after) reduction — heavy, but the analytic
   gradient machinery is already written; the missing piece is interleaving;
3. basin diversity harvesting: N seeded decimation orders (perturbed VSA costs), refine each
   16/N seconds at 512, keep the best by self-score, polish. Pure compute reallocation —
   no new theory, exploits the measured ±0.013 spread deliberately instead of by lottery.
**Papers:**
- Hasselgren, Munkberg et al., *Appearance-Driven Automatic 3D Model Simplification*
  (EGSR 2021, "nvdiffmodeling") — THE reference for optimizing simplified meshes against
  rendered-image losses; our refine is a special case with a hand-derived gradient.
- Hoppe, *New Quadric Metric for Simplifying Meshes with Appearance Attributes* (Vis 99) —
  quadrics extended with attribute (normal) terms: a principled replacement for our
  area·(1−cos) ordering that also fixes placement, not just order.
- Cohen-Steiner, Alliez, Desbrun, *Variational Shape Approximation* (SIGGRAPH 04) — the L2,1
  theory our VSA-lite approximates; the full alternating optimization could beat greedy
  ordering (B2 tested only a *static* partition penalty — the judged-dead form; the live
  alternation was never built).
- Lindstrom & Turk, *Image-Driven Simplification* (TOG 2000) — collapse costs from rendered
  images directly; historical validation of the metric-in-the-loop idea, with sampling tricks.

### Road C — Squeeze the measured envelope (small, safe, additive)
1-vertex rung ladders on cases 6/7 via fixed-count outputs (≤ +0.0023 total, per-run coins);
CPU-clock boxes already shipped; re-roll coin cases at low-load hours. Pure lottery
management — do it alongside A/B, not instead.

### How to search the literature (we have seen ~0.1% of it)
Venues: SIGGRAPH/TOG, Eurographics/CGF, TVCG, SGP. Query stems, each tied to a road:
- A: "topology simplification mesh", "handle removal", "genus reduction simplification",
  "vertex pair contraction aggregation", "mesh repair hole filling CAD".
- B: "appearance driven simplification", "image driven simplification", "perceptual mesh
  simplification SSIM", "differentiable rendering mesh optimization", "normal field
  approximation L2,1", "variational shape approximation".
- Filters: prefer methods with per-operation validity gates (we must stay closed-manifold
  every step) and CPU budgets (no GPU on the judge). Anything requiring global remeshing
  from scratch must fit ~10 s on 1M vertices to be usable on cases 6/7.

## 9. Session 2026-07-05/06 additions — proxy-transfer theory + the coverage channel

### 9.1 ✗ R1 (interleaved decimate↔refine) — judge-negative, and WHY it matters theoretically
Mid-decimation refine bursts (so collapse ordering/placement/importance act on SSIM-optimized
geometry) gain +0.0015-0.002 on BOTH proxies at equal count — and THREE live families out of
three failed their own BANKED razors on the judge (cases 3 and 5). Combined with the earlier
768-native inversion, this establishes a THEORY-LEVEL fact:

**The armadillo-derived proxies systematically over-reward fine geometric optimization.**
Plausible mechanism: the proxies are themselves DECIMATION PRODUCTS of armadillo (25k/35k
proxies) or armadillo itself (case-5 proxy) — their normal fields are smoother/more coherent
than the judges' raw scans, so position-space micro-optimization finds more recoverable
structure locally than on the true inputs. Consequences:
- local RELATIVE gains ≤ +0.002 from position-space optimizers DO NOT transfer (measured
  transfer ratio ≈ 0 to negative, three mechanisms);
- the float32/speed class of change (more iterations of the SAME trajectory) DID transfer —
  throughput is proxy-neutral, trajectories are not;
- every new mechanism must pass a judge family test AT ITS BANKED RUNG before any descent
  (one submission; the per-case verdict is the read).

### 9.2 The coverage/silhouette channel (SIL) — OPEN, first mechanism through the judge gate
The analytic refine gradient is coverage-blind (pixel-to-face assignment frozen) and Sd-blind
(accept metric was normal-SSIM only). SIL adds: (a) accept on Final = 0.5·Sn+0.5·Sd (depth
scorer from the probe line), (b) per-view coverage-DIFFERENCE map — original foreground the
current mesh misses votes its nearest rim vertex OUTWARD, excess coverage votes INWARD —
(c) one line-searched global step along per-vertex signed rim directions, (d) alternation with
the Sn-ascent which repairs interior damage.
- UNIFORM (unsigned) rim displacement is exactly zero-sum (half the chords are inside, half
  outside the true arcs) — consistent with the old global-scale sweep peaking at 1.0. The SIGN
  per vertex is the whole content of the mechanism.
- Measured: case-5 proxy +0.0019 internal (one-shot, then converged) → +0.000735 on the TRUE
  1024 evaluator at equal count; judge: PASSES the banked case-5 razor (19897967) — but
  descent rungs −7 and −14 vertices both WA → current judge-side gain < 7·3.5e-5 ≈ 0.0002.
  Transfer ratio ≈ 0.3 (vs ≈ 0 for position-space mechanisms) — the first channel where local
  and judge agree on the SIGN.
- ✗ v3 (vote-magnitude-scaled steps, radius 14, double round, in-flow with the c3 hybrid) —
  JUDGED 2026-07-06: local true-metric +0.00104 on case 5 (double of v2) and NEUTRAL on case 3
  (−0.00007: hybrid phase B already owns that margin) — but the v3 family **WA'd the banked
  case-5 razor (19898073)** that v2 passed. Refined conclusion: ONLY the soft one-shot
  correction of the systematic chord bias transfers (~0.3×); any intensification (more rounds,
  scaled steps, finer attribution) re-enters the proxy-specific position-space regime and
  inverts, exactly like R1. The SIL channel stays in the base as v2 (razor margin on case 5);
  further investment requires a judge-side S-read instrument on the SIL family, not more local
  tuning.

### 9.3 ✗ bbox-crop on the 377k case — trajectory sensitivity of box-cut razors
The exact-math crop (R3b) is bit-identical at convergence (case 5 verified to 9 decimals) but
1-ulp border differences reshuffle CUT trajectories. On the only case that is both box-cut and
razor-tuned (case 6), five consecutive crop-family draws failed rungs up to SAFER than banked
(8720 > 8711) — the crop family's mean is genuinely lower there. Healed by gating the crop to
V ≤ 100000. Lesson: throughput changes are trajectory re-rolls on box-cut cases; their sign is
a family draw, not a free lunch.

### 9.4 The READ→TWIN→BANK instrument, and the c5 endpoint
Dual-use single binary: run the live pipeline, apply the candidate variation IN-PROCESS (extra
collapses + 1024 mini-refine), self-score FinalSSIM at 1024, emit the measured mesh + K tetras
(S = 0.885 + K·5e-4). If the read says ≥ 0.9005, submit the byte-identical pads-stripped twin —
same mesh, banks immediately. Judged results (2026-07-06): S(4212) ≈ 0.908 read → twin BANKED
90.243142 first try; 4190/4170/4130/4050 all < 0.9 even with doubled repair budget. The cliff
(> 0.008 SSIM in ≤ 22 vertices) is structural: post-refine collapses run on STALE quadrics
(accumulated on original geometry, evaluated at refined positions) — small damage (≈14
collapses) is repairable by a short 1024 ascent, larger is not. The instrument, not the rung,
is the asset: it converts any pipeline experiment into ONE zero-risk judge reading, which is
the only unbiased signal available (§9.1).

### 9.5 Night-of-07-06 outcome: the 1024-polish family and the instrument's regime rule
The recipe "banked-target − extra collapses + a FIRST 1024-resolution mini-refine" (cases 4/5
never had one: case-5 refine was 512-only, case-4's box was too tight before the crop/f32
speedups) moved the bank four times in one night: 90.238542 → 90.266754 (+0.0282; case 5
4226→4212, case 6 8711→8705, case 4 5044→5034→4990). Reads before every descent; zero blind
ladders. Floors (probe-family): case 5 at 4212 (three-leg evidence: repair time ✗, fresh
quadrics ✗), case 4 in (4970, 4990]. Instrument regime rule: on CONVERGED-refine cases the
pads-stripped twin reproduces the read mesh exactly; on BOX-CUT cases (4, 6) any binary change
re-rolls the family — the twin inherits the read's family MEAN and may need per-run --force
re-rolls (case-4 @4990: WA then bank). Case 6 cannot afford the recipe (orig 1024 render of
754k faces ≈ 4 s > its budget).


### 9.6 ✗ VSA-full construction (contract-to-anchors) — closed LOCALLY, 2026-07-06, zero submissions
The first genuinely out-of-family constructor since the image-fit test: connectivity built FROM
an L2,1 Lloyd partition of the original normal field (anchors = triple points, manifold-safe
contraction into them, greedy trim, standard refine). Result on the faithful case-3 proxy at the
banked count: **S = 0.8535 vs 0.8989 for the current family — −0.045, i.e. 20-30× every proxy
bias ever measured**, insensitive to refine budget ×3 (converged), Lloyd iterations ×2.5, and a
post-trim flip pass. Mechanism: the same static-partition disease as the judged-dead B2/C
families — a partition computed once on the original cannot adapt as geometry coarsens, while
the greedy heap re-equalizes marginal cost on fresh geometry after every collapse. The day's
real finding: **greedy collapse connectivity is a much stronger constructor than naive
region-based remeshing** — any future out-of-family attempt must beat a −0.045 head start, so
it needs the FULL alternating machinery (partition ↔ proxy ↔ anchor placement ↔ anisotropic
triangulation) or a rendered-metric-in-the-loop constructor, not a static skeleton.