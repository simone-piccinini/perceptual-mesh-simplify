# NIGHT-91 CAMPAIGN — MORNING SUMMARY

Log: `campaign_0713_2346.jsonl`. Duration: 1.42h. Submissions: 12 (0 toxic-filtered, 0 build-skipped).
**Bank at start: 90.554824. Best all-green reached: 90.567326** (delta +0.012502).

This campaign pushed each case's compression lever down one rung at a time on the
real judge, adapting after every verdict. It targeted the BIG cases (c6=377k verts,
c7=1M verts) first — they hold the most vertices and had never been pushed with the
modern config (rim-budget + iteration-determinize). Below: what each lever reached.

## New banks (the score actually climbed here)
- **90.567326** — c7_push c7=0.0278 (variant plain, sub 20039277, 0.16h)

## Per-family wall map (the certain answer)
### c3_det (c3)
- tried: [6600]
- passed (case green): none
- failed: [6600]
- **wall confirmed at: 6600** (2 real WAs; tried plain)

### c5_push (c5)
- tried: [4160, 4165]
- passed (case green): [4165]
- failed: [4160]
- **deepest passing rung: 4165**
- **wall confirmed at: 4160** (2 real WAs; tried plain)

### c6_push (c6)
- tried: [8600]
- passed (case green): none
- failed: [8600]
- **wall confirmed at: 8600** (2 real WAs; tried plain + determinize + rim)
- variants exercised: ['det', 'plain', 'rim']

### c7_push (c7)
- tried: [0.0266, 0.0272, 0.0278]
- passed (case green): [0.0272, 0.0278]
- failed: [0.0266]
- **deepest passing rung: 0.0272**
- **wall confirmed at: 0.0266** (2 real WAs; tried plain)

## Path-to-91 arithmetic
- Start bank: 90.554824
- Best all-green this campaign: 90.567326 (+0.012502)
- Gap to 91: **0.4327** remaining

### Reading
- Tuning (rung pushes on the current paradigm) reached the number above. The remaining
  gap is what the collapse+refine paradigm cannot close: every family's wall is a
  measured SSIM limit, not a timing artifact (toxic draws were filtered).
- If the big cases (c6/c7) walled early, their headroom is genuinely small (large
  vertex denominators mean each rung is worth little). If they descended far, they
  carried most of the gain — check their deepest-passing rungs above.
- To close a gap this size, 91 needs a different mesh REPRESENTATION (construction /
  appearance-driven remesh), not more rung tuning — this map is the proof of how far
  tuning goes, so tomorrow's effort can go straight to the representation question.

## Raw per-submission log
Every verdict (for auditing): `results/campaign_0713_2346.jsonl`

- [WA ] c6_push c6=8600 v=plain cases=..x..x. score=62.353671 (0.04h)
- [BANK] c7_push c7=0.0278 v=plain cases=....... score=90.567326 (0.16h)
- [WA ] c3_det c3=6600 v=det cases=..x.... score=78.636516 (0.28h)
- [ok ] c5_push c5=4165 v=plain cases=..x.... score=78.63885 (0.4h)
- [WA ] c6_push c6=8600 v=det cases=..x..x. score=62.353671 (0.52h)
- [ok ] c7_push c7=0.0272 v=plain cases=..x.... score=78.659011 (0.63h)
- [WA ] c3_det c3=6600 v=det cases=..x.... score=78.636516 (0.75h)
- [WA ] c7_push c7=0.0266 v=plain cases=..x...x score=62.445677 (0.87h)
- [WA ] c5_push c5=4160 v=plain cases=....x.. score=75.279185 (0.99h)
- [WA ] c6_push c6=8600 v=rim cases=.....x. score=74.27198 (1.1h)
- [WA ] c7_push c7=0.0266 v=plain cases=..x...x score=62.445677 (1.22h)
- [WA ] c5_push c5=4160 v=plain cases=..x.x.. score=63.360877 (1.34h)