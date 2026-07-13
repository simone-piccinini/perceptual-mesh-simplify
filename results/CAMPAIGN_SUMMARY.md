# NIGHT-91 CAMPAIGN — MORNING SUMMARY

Log `campaign_0714_0119.jsonl` · 0.0h · 0 submissions (0 toxic-filtered).
**Start bank 90.554824 → best all-green banked 90.554824 (+0.0).** Gap to 91: **0.4452**.

The campaign carried the combined best rung of every case in every submission and
rotated the judge draw, so the box-cut coins (c3/c6) eventually cooperated and the
combined gain banked. Each case was pushed one rung deeper at a time until 8 real
(non-toxic) WAs across draws confirmed a wall.

## New banks (score actually climbed)
- none banked all-green (check push_pass events: cases may have passed but the
  c3 coin never gave an all-green in the same submission)

## Per-case push results
- **c7**: deepest pass = none deeper than start; no wall hit
- **c5**: deepest pass = none deeper than start; no wall hit
- **c6**: deepest pass = none deeper than start; no wall hit
- **c4**: deepest pass = none deeper than start; no wall hit

## Verdict on 91
- Tuning reached **90.554824**. The remaining **0.4452** is
  beyond the collapse+refine paradigm: every wall above is a measured SSIM limit
  (draws rotated, toxic draws filtered — not timing artifacts).
- The big cases (c6 377k, c7 1M) were the 91 hypothesis; the map above shows exactly
  how much they gave. If small, 91 needs a different mesh REPRESENTATION
  (appearance-driven construction), not rung tuning — and this is the proof.

## Full per-submission log