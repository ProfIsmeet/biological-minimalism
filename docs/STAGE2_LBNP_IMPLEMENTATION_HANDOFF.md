# Stage 2 LBNP Implementation Handoff

- **Data path expectation**: `datasets/lbnp-impedance/raw/` (download from
  Zenodo 10.5281/zenodo.10119427 once direct access is confirmed — blocked
  in this sandbox this sprint).
- **Loader required**: new `ml/datasets/lbnp_impedance.py` (does not exist
  yet). First task: confirm actual file structure/naming and the true
  16-vs-18-subject file count before writing the loader.
- **Split artifact**: `results/lbnp_loso_folds_stage2.json`.
- **Exact protocol artifact**: `results/lbnp_protocol_stage1b.json` — do not
  reselect EIS representation or target framing (ordinal MAE, not F1) after
  seeing results.
- **Target**: LBNP pressure stage (mmHg), 0–60 mmHg focus.
- **Features**: A = ECG + pleth; B/C = + thoracic EIS full spectrum (100
  points, 100 Hz–1 MHz).
- **Excluded fields**: elapsed_time, stage_sequence_index, trial_order,
  filename/timestamp fields, abdominal/arm EIS, EIT, MAP (primary run).
- **Model/capacity design**: shared ECG+pleth backbone; small fixed-width
  MLP branch over the 100-point EIS spectrum for B/C.
- **Seeds**: derive via the `ml/sleep_seed_utils.py` sub-seed pattern.
- **Primary metric**: MAE (mmHg). Secondary: macro-F1 (5-class, diagnostic
  only).
- **Output filenames**: `results/lbnp_bioz_stage2.json`.
- **Checkpoint naming**: `lbnp_a_ecg_pleth_seedXX.pt`,
  `lbnp_b_thoracic_eis_seedXX.pt`, `lbnp_c_shuffled_eis_seedXX.pt`.
- **Tests to run**: `ml/tests/test_stage1b_lbnp.py` (this sprint) plus new
  Stage-2 leakage-barrier enforcement tests once real files/loader exist.
- **Stop conditions**: (1) if the actual Zenodo file count does not match
  16 (or 18-with-2-flagged) usable subjects, stop and reconcile before
  training; (2) if any timestamp/sequence-index field cannot be safely
  removed from a provided file format, stop — do not train on a dataset
  where the leakage barrier cannot be enforced.
