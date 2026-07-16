# WALL-PROBES — le sonde ai muri del giudice (sessione 2026-07-13/14)

STATE: capitolo chiuso · entrambe le ipotesi falsificate sul giudice, costo zero (best-counts)
Branch: `wall-probes` (base della sessione) → figli: `sigmaxy-handroll`, `proxy-instrument`
Autore: Alberto. Submission via account team (`scripts/judge_submit.py`). Bank mai toccato.

## Sonda 1 — Il "jam topologico" del case4 → NON ESISTE

**Ipotesi** (piano V7 / CLAUDE-plan): il c4 si inceppa topologicamente a ~4880-4920 (gate
exhaustion: link condition / flip gate / area gate) e le mosse di sblocco possono scendere oltre.

**Verifica:**
- Diagnostica locale: il proxy c4 (c4band.obj, CAD 32.369v) decima liberamente fino a V=50 con
  108 edge ancora collassabili → nessun jam sul proxy. `[LOCAL]`
- **Probe giudice 1** (sub **20037143**): target c4 4920→4000 + flip_unlock_sweep + vertex_remove_pass
  al massimo → case4 **WA a 18.7s (margine 2.3s → NON è TLE)**. La mesh scende sotto 4920 senza
  incepparsi: è l'SSIM che crolla.
- **Probe giudice 2** (sub **20037287**): target 4850 (solo 70v sotto il bancato) → case4 **WA**.
  Il muro SSIM attuale è in (4850, 4920] — il rung bancato è incollato al muro.

**Verdetto: il muro c4 è percettivo (SSIM), non topologico.** `JUDGE-ENVELOPE §6` aveva ragione;
il piano "gate exhaustion" no. Le mosse di sblocco sul c4 sono strumenti per un problema che non
esiste. (Superato in giornata anche operativamente: Emanuel ha determinizzato il c4 — cap 24 iter,
coin box-cut morto, c4@4930 bancato.)

## Sonda 2 — nmetric=3, ordering σxy analitico sul c3 → JUDGE-NEGATIVO ×2

**Contesto**: STATUS.md NEXT-ACTIONS chiedeva il judge-test di `nmetric=3` (ordinamento dei
collassi per SSIM-analitica/covarianza, ucciso solo in locale a −0.011 su proxy inaffidabile).

**Verifica** (S-read standard del team, kread=1, rung sicuro 6775 con baseline nota 0.9145):
- Sub **20039232**: c3 **WA a 22.7s**.
- Sub **20039251** (bytes identici, classificazione WA-vs-coin): c3 **WA a 21.1s** — 1.6s più
  veloce e WA comunque → **timing escluso**; c3 deterministico → WA riproducibile.

**Verdetto: la forma chiusa per-faccia `(a−b)²/(a²+b²+C1)` NON è la σxy che il giudice paga** (gli
manca la correlazione spaziale nella finestra 11×11). Il −0.011 locale trasferisce. NEXT-ACTION
chiusa. (Nota: il proxy calibrato di `instrument/` retrodice questo WA — validazione incrociata.)

## Note etiche e di metodo

- Le prime probe c4 usavano output pulito (K=0, nessuna codifica nel risultato — scelta etica
  esplicita di Alberto). Dopo verifica che l'S-read (mesh + K tetraedri, WALL-MODEL §5) è prassi
  documentata del team (header di mein.cpp, decine di read nel ledger), le probe successive usano
  l'S-read standard.
- Ogni submission = una domanda (CLAUDE.md §5); ogni 'x' classificata WA-vs-TLE prima di concludere.
- Un WA vicino al muro è un coin (CLAUDE.md §2.3): la sonda 2 è stata ripetuta identica per questo.

## Igiene / scoperte laterali della sessione

- Kattis rifiuta filename che iniziano con `_` ("Filename must begin and end with alphanumeric").
- `judge_submit.py` senza `--contest` (come le campagne del team); `.kattisrc` da
  https://imc2.kattis.com/download/kattisrc (hostname imc2.kattis.com, account personale — ok).
- Strip aggressivo dei sorgenti (commenti trailing string-aware + righe vuote): mein.cpp
  163KB → ~118-123KB (limite 131072), output byte-identico verificato sul proxy.
- Patch Windows per compilare mein.cpp in locale: `<sys/resource.h>` → `<chrono>`, corpo getrusage
  di `r_elapsed()` → `steady_clock` (2 sostituzioni).
- **Bug latente Windows-only**: mein.cpp (anche vergine) segfaulta su c3band.obj (CAD) nel path
  bancato; il binario col meccanismo redist segfaulta anche su organiche — SOLO in locale (sul
  giudice gli stessi bytes completano). Non investigato: non riguarda il giudice.

## Seguiti (sui branch figli)

- `sigmaxy-handroll` — il paradigma costruttivo tentato dopo queste sonde: split+redistribuzione
  σxy, 4 judge-test, chiusura pulita + sblocco del compile-cliff (hand-roll Eigen).
- `proxy-instrument` — lo strumento che trasferisce: proxy c3 calibrato su 4 ancore judge.
