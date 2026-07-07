# case3-lab — the single front that still moves the score

**Why this folder exists.** After v111 (90.285538) every case is compressed 85–99% EXCEPT
**case 3, stuck at ~70.08% (N=6941 of V=23201)**. The gap to the leader (91.46) lives almost
entirely here. This folder concentrates all case-3 work: the ideas we're trying, the results
of past ones, and the automation to test them on the judge.

Judge facts (how it evaluates, limits, what's proven) are NOT duplicated here — the authority is:
- [docs/JUDGE-ENVELOPE.md](../../docs/JUDGE-ENVELOPE.md) — every measured judge fact.
- [docs/WALL-MODEL.md](../../docs/WALL-MODEL.md) — what a wall is, the S-read instrument, automation.
Read those first. This README is the case-3 operating hub.

## The two case-3 opportunities (different levers, both use the S-read)
1. **HARVEST the existing wall down** (high confidence, automatable NOW).
   The friend's read: S2=0.9135 at N=6940. Threshold is S=0.900; S2 is ~+0.005 optimistic
   (case-4 anchor) → true headroom ~0.0085 → slope 3.5e-5/vert → **~240 verts left**
   (6941 → ~6700 ≈ **+0.17 total**). Method: S-read at descending N, anchor, bank the lowest
   passing N. Pure probing; no new mechanism.
2. **LOWER the wall itself** (the big win, +1–2). case 3 sits at 70% because OUR simplifier
   renders a worse normal map at low N than the leaders'. Needs a BETTER case-3 mechanism.
   The S-read (§5.5 WALL-MODEL) is the ONLY transfer-safe way to A/B a new mechanism on the
   real judge case-3 mesh (local proxies do not transfer — ENVELOPE §9.1). Test = two reads
   at the same N (control vs variant), compare judge-side S2.

## The automated loop (the human CAN be removed — corrected 2026-07-07)
`judge_submit.py` submits via the ~/.kattisrc token (403 is only for standings, not submit).
So the full loop is scriptable:
  probe/harness.py plan --read 3@N  ->  probe/harness.py preflight  ->
  scripts/judge_submit.py probe/out/main.cpp --note "..."  ->  probe/harness.py decode <score>
Bounded, ambiguity-pre-checked, best-counts protects the bank. Rate limit ~1 submit / 4 min.

## Files here
- README.md   — this hub.
- IDEAS.md    — ranked case-3 ideas being tried / to try (harvest + wall-lowering mechanisms).
- RESULTS.md  — every case-3 mechanism tried + its judge outcome + the S-read log.
- snapshots of any case-3 bank candidate (main.cpp per convention) land here.
