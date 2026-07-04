# IMC 2026 — Problem B: Perception-Aware Mesh Simplification

Solver per il contest Kattis/Huawei (`imc2.kattis.com`, deadline 2026-07-18): comprimere mesh 3D
al minor numero di vertici possibile mantenendo `FinalSSIM ≥ 0.9` su 6 viste renderizzate
(normal map + depth map, flat shading) e la validità della mesh.

**Stato: bank 90.238542 (7/7).** Per caso: c2 99.298 | c3 70.031 | c4 85.719 | c5 91.547 |
c6 97.695 | c7 97.145.

## Layout

```
solver/main.cpp     IL file che si sottomette (C++17, Eigen fornito dal giudice).
                    Pipeline: dispatch per-caso → decimazione greedy edge-collapse ordinata
                    per distorsione dei normali (VSA-lite) + steering dal deficit renderizzato
                    (Pivot-A/s-def) + piazzamento aniso (c4) + visibility culling (c3/c4)
                    + 2-stage (c7) → ottimizzatore inverse-rendering sul metrica esatto
                    (refine, hybrid 512→1024) → output. Esperimenti falliti restano nel file,
                    disattivati dietro variabili d'ambiente (il giudice non ne setta).
src/imc_eval/       Oracolo Python: replica bit-exact del giudice (render+SSIM). ATTENZIONE:
                    il suo Hausdorff è punto-a-superficie, il giudice vero usa vertice-a-vertice
                    (più permissivo) — vedi docs/PROBLEM-AND-JUDGE.md.
scripts/            judge_submit.py (submission autonoma + verdetto), utilità di calibrazione.
docs/               PROBLEM-AND-JUDGE.md (regole + scoperte chiave) · THEORY.md (matematica,
                    cosa funziona, cimitero) · research/ (fonti esterne).
handoff/            ATTEMPT_LOG.md (storia round-per-round, VERITÀ operativa) · SOLVER_STATE.md.
submissions/        Snapshot congelati per submission: main.cpp + RESULT.md.
                    Convenzione RESULT.md: SEMPRE punteggio % e casi passati; poi il resto.
tests/data/         Mesh proxy locali (armadillo/bunny/cow/fandisk).
```

## Comandi essenziali

```bash
# build
g++ -O2 -std=c++17 -Isolver solver/main.cpp -o solver/main   # solver/Eigen -> brew eigen

# rigenerare i proxy (armadillo decimato al 50% / 70%)
G_NDECIM=0 G_NOLAMBDA=1 ./solver/main k 0.045 0.5 < tests/data/armadillo_watertight.obj > proxy25k.obj
G_NDECIM=0 G_NOLAMBDA=1 ./solver/main k 0.045 0.7 < tests/data/armadillo_watertight.obj > proxy35k.obj

# oracolo locale (SSIM fedele; Hausdorff più severo del giudice)
PYTHONPATH=src python3 -m imc_eval.cli --input orig.obj --output simp.obj

# submission autonoma (richiede ~/.kattisrc)
python3 scripts/judge_submit.py solver/main.cpp   # stampa VERDICT / SCORE / CASES
```

## Regole operative (imparate a caro prezzo)

1. Il giudice è l'unico test: i proxy locali sottostimano gli effetti veri anche >10×.
2. Best-counts definitivo (niente rejudging): ogni probe è gratis; una domanda per submission.
3. Il runtime giudice è deterministico dato il binario; i muri vicini sono distribuzioni tra
   binari (σ≈0.0002): ritentare un rung con un binario diverso è un'estrazione legittima.
4. Mai aggiungere meccanismi "migliorativi" a un rung già confermato senza rivalidarlo:
   due volte un extra ha rotto il caso che voleva proteggere.
5. CPU ~16.5s/caso, sommata sui thread: single-thread, box wall-clock su ogni loop aperto.
