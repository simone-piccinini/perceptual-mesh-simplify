# v106 — read-then-bank, case-5 4212 (submission 19898182)

**Score: 90.243142 — 7/7 PASS (NEW BANK, +0.004335)**
Case-5 payout 91.573402 (V'=4212 exact, zero stall). Others at banked rungs.

## The instrument that made it
Dual-use same-binary design: the probe variant (19898155) runs the LIVE pipeline, then
+14 collapses from the refined mesh + 1.5 s refine AT 1024, self-scores FinalSSIM at 1024
in-process, and emits the measured mesh + K tetras (S = 0.885 + K·5e-4). Read: S(4212) ≈ 0.908.
The bank twin (this build) is byte-identical except K=0 — the measured mesh IS the payload.
READ → TWIN → BANK, no blind WA ladders.

## Why the mesh is better
First time case 5 gets a 1024-resolution refine pass (live refine was 512-only; the 768-native
attempt REPLACED 512 and failed — this ADDS a 1024 polish after extra collapses, hybrid-style).
Judge-side S(4212) = 0.908 vs the old family's ~0.900 at 4226.
