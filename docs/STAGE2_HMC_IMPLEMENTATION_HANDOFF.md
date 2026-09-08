# Stage 2 HMC Implementation Handoff

- **Data path expectation**: `datasets/hmc-sleep-staging/raw/` (download from
  PhysioNet v1.1; 15.7 GB uncompressed — gitignored).
- **Loader required**: new `ml/datasets/hmc_sleep.py` (does not exist yet),
  modeled on `ml/datasets/sleep_edf.py`'s multi-channel windowed-loader
  interface, but simpler (no per-channel native-rate reconciliation needed —
  confirmed uniform 256 Hz).
- **Split artifact**: `results/hmc_split_stage2.json` (recording-wise folds,
  frozen before training).
- **Exact protocol artifact**: `results/hmc_protocol_stage1b.json` — do not
  reselect the EEG derivation or EOG polarity after seeing results.
- **Target**: 5-class sleep stage (W/N1/N2/N3/REM), technician hypnogram.
- **Features**: A = C4/M1; B/C = C4/M1 + (E1/M2 − E2/M2).
- **Excluded fields**: chin EMG, ECG lead II, F4/O2/C3 (unused derivations).
- **Model/capacity design**: architecture-matched dual-channel Conv1D encoder
  adapted from the existing `SleepStageClassifier` convention for 256 Hz
  input.
- **Seeds**: H1-corrected order from the start
  (`ml/sleep_seed_utils.py` pattern) — model_init_seed / data_order_seed /
  control_shuffle_seed.
- **Primary metric**: Macro-F1. Secondary: balanced accuracy, per-class F1.
- **Output filenames**: `results/hmc_sleep_external_replication_stage2.json`.
- **Checkpoint naming**: `hmc_sleep_a_eeg_seedfix_v2_seedXX.pt`,
  `hmc_sleep_b_eeg_eog_seedfix_v2_seedXX.pt`,
  `hmc_sleep_c_shuffled_eog_seedfix_v2_seedXX.pt`.
- **Tests to run**: `ml/tests/test_stage1b_hmc.py` (this sprint) plus new
  Stage-2 recording-disjoint-fold enforcement tests once the real loader
  exists.
- **Stop conditions**: (1) do not start full training until Claude/Emir's
  Stage 1A Sleep V2 protocol is frozen (workflow dependency, Section 29);
  (2) if per-file inspection finds any recording missing C4/M1, E1/M2, or
  E2/M2, exclude that recording via the data-integrity rule rather than
  substituting another derivation ad hoc.
