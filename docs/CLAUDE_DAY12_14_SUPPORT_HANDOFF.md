# Claude Day 12–14 Support + Audit Handoff

Branch: `day12-14-ismet-support-audit`, based on your verified Day-11
canonical `169f99d`, with `day11-14-scientific-parallel` (`983720d`)
merged in cleanly (49 files added, 0 modified, 0 conflicts). Does not
modify `main` or your canonical branches.

## What was integrated

All scientific parallel-track artifacts (statistics standard, sensitivity
packages, master table, paper tables, figure sources, clean-clone report,
Day-14 checkpoint archive, freeze candidate, hostile review) — see
Support Commit 1 for the exact file list. No scientific value changed.

## New verified engineering values

Nothing new was computed — everything in
`results/independent_engineering_arithmetic_check_day12.json` is an
**independent recomputation of your existing Day-11 numbers**, not a new
figure. Result: 21/21 checks pass exactly. Your power and data-rate
arithmetic is correct.

## Power-model support

`ml/engineering/ppg_led_power.py` implements exactly the LED-power
formula already frozen in your
`results/reference_power_budget_day11_part2.json`
(`wrist_ppg.led_contribution.formula`). It's a pure calculator — no LED
count/current/voltage/timing was chosen. Call it once those 5 inputs are
frozen; it refuses to compute (returns `NOT_READY`) if any is missing,
never silently substitutes 0. See `results/ppg_led_power_model_support_day12.json`
for a worked (explicitly hypothetical) example.

Your existing ADS1299/AD5940 evidence
(`results/reference_power_budget_day11_part2.json`) was reviewed and
found already rigorous — datasheet-cited supply rails, correctly left
NOT_READY where the exact power point couldn't be verified. No separate
support artifact was needed there; it already does what was asked.

## Data-rate verification

48.068 kbps independently reconfirmed exact
(`results/independent_engineering_arithmetic_check_day12.json`). One
presentation note: it includes the deprioritized second-PPG evaluation
branch's 28,500 bps (59% of the total) — see finding HW-1 below if this
number reaches jury/paper copy.

## Scientific freeze status

Revalidated: no Day-11 engineering change broke any scientific artifact
path, hash, or claim reference. `SCIENTIFIC_FREEZE_CANDIDATE_READY_WITH_LIMITATIONS`
stands unchanged.

## Paper/jury source artifacts

`results/science_to_engineering_integration_map_day12.json` — exactly
what your architecture track may and may not infer from each scientific
candidate. `results/paper_visual_integrity_day12.json` — all figure/table
sources checked, 0 issues.

## Fixed this session (real bug, was affecting your live API on Windows)

Running your full backend test suite for the first time in this audit
lineage found that `decision_inputs.artifact()` — backing a research API
endpoint — was actually returning `ResearchAvailability.UNAVAILABLE` on
this Windows machine, due to the exact same `core.autocrlf`/SHA256
false-positive already fixed in the ML track, but not yet applied to
`backend/app/research/decision_inputs.py`. Fixed with the identical
normalize-before-hash pattern, verified the same way (git-blob content
equality), zero scientific/engineering values changed. Also fixed a
separate, smaller encoding bug (`.read_text()` missing `encoding="utf-8"`
in 3 test files — your production code was already correct). Backend
suite: 128/128 passing now (was 7 failed + 12 errors). See REPRO-1/REPRO-2
in `results/full_repository_audit_day14.json` for full detail.

## Audit findings requiring your attention

Full detail: `docs/INDEPENDENT_FULL_REPOSITORY_AUDIT_DAY14.md`,
`results/full_repository_audit_day14.json`. Two HIGH findings:

1. **SOFT-1** (`backend/app/research/engineering_readiness.py` lines
   130, 133): two fields default to `0` if missing from source data,
   contradicting your own module's "never zero an unknown" invariant.
   Not currently misfiring (your data is complete), but untested for the
   missing case. Recommend: `None` + explicit not-ready status, plus a
   test mirroring your existing `test_unknown_power_is_not_ready_never_zero`.
2. **CLAIM-1**: your claim-consistency checker
   (`ml/check_claim_consistency.py`) is regex-based and I confirmed 5/5
   tested paraphrases of forbidden claims bypass it completely (e.g.
   "our complete wearable consumes 45 milliwatts" vs. the literal
   "system power = 45mW" pattern it checks for). It currently reports OK
   only because no live document phrases an overclaim that way — this
   is not a guarantee it always will. Recommend treating its "OK" output
   as a lint, not a semantic audit, in any jury-facing description of
   your claim-governance process.

Two MEDIUM (SOFT-2: hardcoded `48068` fallback duplicate constant;
HW-1: the 59%-second-PPG-share presentation risk above) and one LOW
(SOFT-3: two more `or 0` patterns in `catalog.py`, unconfirmed misfire).

## Exact items Claude should integrate

- Consider fixing SOFT-1/SOFT-2 (small, isolated, don't touch scientific
  values) — I did not fix them myself per this task's Fix Policy (touches
  your owned code, no scientific-integrity urgency).
- If citing 48.068 kbps in jury/paper copy, consider the baseline-only
  vs. baseline+evaluation-branch split (HW-1).

## Exact items Claude must NOT reinterpret

- Do not read "0 findings changed scientific results" as "0 findings" —
  there are 5 real findings, all in engineering-evidence *rendering*
  code and claim-checker *robustness*, none in the science itself.
- Do not treat the claim checker's "OK" as proof no document overclaims
  — it proves no document matches its specific regex list.
- Do not merge this branch's audit findings as "resolved" — they are
  flagged for your review/fix, not fixed here.

## Tests

Full ML suite passing (see final report). Backend suite not modified by
this branch — no new failures introduced by the merge (verified by
running it, see final report Section on tests).
