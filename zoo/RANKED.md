# Zoo ranking — mesh happy_qem.obj, base rung 6610
base S2 = 0.952397 (n=3) | trajectory sigma = 0.00e+00 | NOISE FLOOR = 1.50e-03

| variant | family | dS2 | dS2n | verdict | expected | note |
|---|---|---|---|---|---|---|
| pool_2500 | tail | +0.0040 | +0.0068 | ** WIN ** | ? | pool 2500: offline-depth probe - how much does an unaffordable tail bu |
| pool_1200 | tail | +0.0017 | +0.0029 | ** WIN ** | ? | pool 700->1200 (deeper candidate set; judge-time irrelevant locally) |
| stage2_30 | schedule | +0.0015 | +0.0025 | ** WIN ** | ? | bulk to 3x then ordered finish |
| mini_16 | polish | +0.0014 | +0.0032 | flat | ? | mini_refine iteration cap 8->16 (c3-determinism cap was chosen for TIM |
| mini_64 | polish | +0.0014 | +0.0032 | flat | ? | cap 8->64: how much of the +4.3e-3 M0 headroom does the in-pipeline po |
| sil2_400 | schedule | +0.0012 | +0.0019 | flat | ? | silhouette pass 200->400 evals (judge-costed +1.8s; local quality read |
| mini_32 | polish | +0.0011 | +0.0026 | flat | ? | cap 8->32: the c5-POLISH transplant, step 2 |
| zpen_3 | ordering | +0.0011 | +0.0006 | flat | ? | depth-steepness collapse deferral (c4-inert; organic re-screen) |
| lac_05 | polish | +0.0007 | +0.0009 | flat | ? | AC-seed: laplacian-of-residual guided zigzag (exploratory, env semanti |
| alloc_05 | ordering | +0.0005 | +0.0012 | flat | ? | Z-saliency quadric scaling on ORGANIC (was c4-inert/noise; c3 is a dif |
| lam_8 | ordering | +0.0000 | -0.0012 | flat | ? | Pivot-A lambda 16->8 (deficit-steering strength down) |
| traj_a | control | +0.0000 | +0.0000 | DUPE(base)=env inert? | 0 | tail box -0.05s: pure trajectory re-roll -> measures the local draw si |
| traj_b | control | +0.0000 | +0.0000 | DUPE(base)=env inert? | 0 | tail box +0.05s: second trajectory re-roll |
| subset_c3 | kernel | +0.0000 | +0.0000 | DUPE(base)=env inert? | 0 | DEAD KNOB (found by zoo DUPE-detection): mein.cpp:1984 'g_subset_place |
| deteps_8 | kernel | +0.0000 | +0.0000 | DUPE(base)=env inert? | ? | QEM solve regularization looser (more midpoint fallbacks on near-singu |
| deteps_12 | kernel | +0.0000 | +0.0000 | DUPE(base)=env inert? | ? | QEM solve regularization tighter (trust the solve on flatter quadrics) |
| ctb_50 | tail | +0.0000 | +0.0000 | DUPE(base)=env inert? | ? | tail box 6.5->5.0s (starved tail: measures the convergence margin) |
| ctb_85 | tail | +0.0000 | +0.0000 | DUPE(base)=env inert? | ? | tail box 6.5->8.5s (deeper converge) |
| rb_48 | tail | +0.0000 | +0.0000 | DUPE(base)=env inert? | ? | tail re-render burst 24->48 (fresher scores between renders) |
| rb_96 | tail | +0.0000 | +0.0000 | DUPE(base)=env inert? | ? | burst 96 (staler scores, more commits per render) |
| mpc_classic | tail | +0.0000 | +0.0000 | DUPE(base)=env inert? | ? | MPC classic only (no continuous line-search): is the line-search the a |
| repair_20 | polish | +0.0000 | +0.0000 | DUPE(base)=env inert? | ? | repair-burst budget 1.2->2.0s (c5-polish analog on c3, budget axis) |
| repair_30 | polish | +0.0000 | +0.0000 | DUPE(base)=env inert? | ? | repair burst 3.0s |
| budget_30 | polish | +0.0000 | +0.0000 | DUPE(base)=env inert? | ? | refine wall-clock 16->30s: the in-pipeline convergence ceiling (TLE-ir |
| tail_off | control | -0.0001 | -0.0001 | flat | 0 | MEASURED DUPE(base) on this fork: Decimate already reaches c3t so the  |
| mpc_off | tail | -0.0001 | -0.0001 | flat | - | multi-placement OFF (judge-validated +: 6710 crossed with it) - semi-c |
| pool_400 | tail | -0.0001 | -0.0001 | flat | ? | lazy tail pool 700->400 (cheaper, earlier commit) |
| lsiter_2 | polish | -0.0002 | +0.0003 | flat | ? | guided-seed->refine cycles x2 (family read +1.35e-4 at 1 iter) |
| lsiter_3 | polish | -0.0004 | +0.0021 | flat | ? | seed cycles x3 |
| rim_off | control | -0.0004 | +0.0007 | flat | - | RIM-BUDGET off. Judge-VALIDATED positive (c3 wall 6700->6610) => faith |
| lam_24 | ordering | -0.0009 | -0.0011 | flat | ? | Pivot-A lambda 16->24 (steering up; 24 WA'd once at an old rung - re-s |
| flip_m02 | kernel | -0.0011 | -0.0009 | flat | ? | relax the normal-flip gate slightly on c3 (default 0.0 = strict) |
| areaq | control | -0.0013 | +0.0042 | flat | - | area-weighted quadrics: HURT c4/c6 on the judge => expect <=0 here |
| alloc_10 | ordering | -0.0015 | -0.0002 | flat | ? | Z-saliency quadric scaling, full strength |
| nplace_off | control | -0.0017 | -0.0027 | NEG | - | normal-optimal placement off (+0.0006 c3 when shipped) => must read NE |
| redecim | schedule | -0.0018 | -0.0030 | NEG | ? | decimate->refine->RE-decimate lite (Road B item 2: ordering re-run on  |
| rim_035 | control | -0.0021 | -0.0029 | NEG | - | half rim strength: must sit between rim_off and base (monotonicity anc |
| aniso_on | kernel | -0.0023 | -0.0001 | NEG | ? | curvature-aligned placement candidates (banked on c4 CAD; 'dead on org |
| qw_005 | control | -0.0024 | -0.0032 | NEG | - | qweight 0.05: judge-WA'd #19885312 => must read NEGATIVE |
| stage2_15 | schedule | -0.0025 | -0.0045 | NEG | ? | bulk-QEM to 1.5x target then VSA-lite ordering (c7's speed trick, qual |
| salcost_05 | kernel | -0.0029 | -0.0045 | NEG | ? | NEW: steepness-saliency as rim-style COST multiplier (allocation via o |
| rim_100 | ordering | -0.0029 | -0.0044 | NEG | ? | rim-budget stronger than banked 0.7 (allocation-strength curve, judge- |
| rim_200 | ordering | -0.0030 | -0.0033 | NEG | ? | rim-budget ~3x: where does over-allocation start hurting? |
| rim_140 | ordering | -0.0030 | -0.0023 | NEG | ? | rim-budget 2x banked |
| salcost_10 | kernel | -0.0030 | -0.0022 | NEG | ? | same binary as salcost_05, strength 1.0 |
| hid_deep | ordering | -0.0043 | -0.0064 | NEG | ? | hidden-pair collapses even earlier (frees budget for visible verts) |
| lsres_768 | polish | -0.0096 | -0.0058 | NEG | ? | guided-seed at 768 instead of 1024 (cheaper seed -> budget freed downs |

## Controls acceptance (instrument sign-fidelity)
- rim_035: expected -, read -0.0021 -> OK
- rim_off: expected -, read -0.0004 -> OK
- qw_005: expected -, read -0.0024 -> OK
- nplace_off: expected -, read -0.0017 -> OK
- areaq: expected -, read -0.0013 -> OK
- mpc_off: expected -, read -0.0001 -> OK

controls: 6 OK / 0 MISS  (MISSes above the floor = instrument doubt; investigate before trusting WINs)
