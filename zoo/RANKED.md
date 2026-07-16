# Zoo ranking — mesh dragon_unit.obj, base rung 6610
base S2 = 0.824325 (n=1) | trajectory sigma = 0.00e+00 | NOISE FLOOR = 1.50e-03

| variant | family | dS2 | dS2n | verdict | expected | note |
|---|---|---|---|---|---|---|
| rim_035 | control | -0.0002 | +0.0007 | flat | - | half rim strength: must sit between rim_off and base (monotonicity anc |
| rim_off | control | -0.0007 | -0.0010 | flat | - | RIM-BUDGET off. Judge-VALIDATED positive (c3 wall 6700->6610) => faith |
| nplace_off | control | -0.0043 | -0.0077 | NEG | - | normal-optimal placement off (+0.0006 c3 when shipped) => must read NE |
| qw_005 | control | -0.0055 | -0.0103 | NEG | - | qweight 0.05: judge-WA'd #19885312 => must read NEGATIVE |
| areaq | control | -0.0057 | -0.0088 | NEG | - | area-weighted quadrics: HURT c4/c6 on the judge => expect <=0 here |

## Controls acceptance (instrument sign-fidelity)
- rim_off: expected -, read -0.0007 -> OK
- rim_035: expected -, read -0.0002 -> OK
- qw_005: expected -, read -0.0055 -> OK
- areaq: expected -, read -0.0057 -> OK
- nplace_off: expected -, read -0.0043 -> OK

controls: 5 OK / 0 MISS  (MISSes above the floor = instrument doubt; investigate before trusting WINs)
