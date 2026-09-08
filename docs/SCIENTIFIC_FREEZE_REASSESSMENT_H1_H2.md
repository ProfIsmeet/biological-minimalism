# Scientific Freeze Reassessment — H1/H2 (Day 12)

At the start of this sprint, scientific freeze status was set internally
to `SCIENTIFIC_FREEZE_CANDIDATE = HOLD_PENDING_H1_H2`, per instruction, so
that the prior `SCIENTIFIC_FREEZE_CANDIDATE_READY_WITH_LIMITATIONS` status
(Day 14) was not silently retained while H1/H2 were unresolved.

## H2 — closed, metadata-only, no data/retraining impact

Confirmed via EDF header inspection and MNE source-code review: Resp
oro-nasal is natively 1 Hz, resampled to the 100 Hz common grid via MNE's
FFT-based resampling. The training loader (`preload=True` throughout) has
always produced this exact resampled representation — the interaction
experiment's `results/sleep_edf_interaction_resp_day10.json` numbers are
unchanged and remain valid. Fixed: code comments/constants in
`ml/datasets/sleep_edf.py`, the Day-10 feasibility audit (struck-through
correction, not silently edited), and the interaction results doc (new
bandwidth-caveat section). **Status: `H2_CLOSED_METADATA_ONLY`.**

## H1 — real bug, confirmed by reproduction probe; retraining diagnosis in progress

Confirmed via a real reproduction probe (constructing the actual
`SleepStageClassifier` and reading its actual weights,
`results/sleep_seed_initialization_audit_day12.json`,
`overall_h1_confirmed: true`) that the current trainer order does not let
the recorded seed control model initialization. A corrected protocol
(`ml/sleep_seed_utils.py`, `docs/SLEEP_SEEDING_PROTOCOL_V2.md`) is
defined, tested (15 new tests, all passing), and used for a bounded
retraining diagnostic (`ml/train_sleep_edf_primary_seedfix_v2.py`,
primary A/B, 5 seeds each, same split/architecture/preprocessing/epochs/
hyperparameters as the original — only seeding order differs).

This document's final status depends on that diagnostic's outcome, which
is recorded in `results/sleep_scientific_remediation_day12.json` — see
that artifact and the final H1/H2 remediation report for the concrete
determination.

## Freeze status determination

**`FREEZE_RESTORED_WITH_VERSIONED_SLEEP_RESULTS`**

H2 closed with zero data/retraining impact (metadata-only). H1's bounded
retraining diagnostic (Primary A/B, 5 seeds each, corrected seeding
protocol) confirms the same qualitative conclusions as the historical
result — same direction, same 4/5 seed-favor count, same SC4011-dominated
subject pattern, same REM-driven class pattern (see
`results/sleep_scientific_remediation_day12.json` for the full
comparison). The canonical numerical reference
(`results/sleep_edf_eeg_eog_ablation.json`) is **not** replaced or
deprecated — `results/sleep_edf_primary_seedfix_v2.json` is added as a
versioned, fully-seed-controlled confirmatory result, recommended (not
mandated) as the preferred citation going forward.

Scope note: the shuffled-EOG control (C) and the interaction experiment
(M_B/M_AB) were **not** re-diagnosed under the corrected protocol this
sprint (time-bounded diagnostic scope, disclosed explicitly, not a silent
gap) — flagged `PENDING_FOLLOWUP` in
`results/scientific_freeze_candidate_post_audit_day12.json`. Reference
below for the three possible outcomes considered before reaching this
determination:

- **`FREEZE_RESTORED`**: both H1 and H2 fully closed, no canonical
  numbers need to change, freeze status reverts to
  `READY_WITH_LIMITATIONS` unchanged.
- **`FREEZE_RESTORED_WITH_VERSIONED_SLEEP_RESULTS`**: H2 closed
  (metadata-only); H1's corrected-seed diagnostic confirms the same
  qualitative conclusions but the canonical numerical reference should
  migrate to (or be supplemented by) the seed-corrected version for any
  new citation going forward, while historical numbers remain valid and
  are not deleted.
- **`FREEZE_REMAINS_ON_HOLD`**: H1's corrected-seed diagnostic reveals a
  material change to effect direction, control interpretation, subject
  pattern, or a major limitation — Sleep science would need to reopen
  before freeze can be restored.

No canonical scientific artifact (`sleep_edf_eeg_eog_ablation.json`,
`sleep_edf_eeg_eog_control_analysis.json`,
`sleep_edf_secondary_holdout_evaluation.json`,
`sleep_edf_interaction_resp_day10.json`,
`sensor_marginal_value_contract.json`) was modified by this sprint
regardless of outcome — only new, versioned, additive artifacts were
created.
