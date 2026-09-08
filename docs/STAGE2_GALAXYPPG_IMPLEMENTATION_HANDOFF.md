# Stage 2 GalaxyPPG Implementation Handoff

- **Data path expectation**: `datasets/galaxyppg/raw/` (download from
  Zenodo 10.5281/zenodo.14635823; gitignored, same convention as every other
  dataset in this project).
- **Loader required**: new `ml/datasets/galaxyppg.py` (does not exist yet),
  modeled on `ml/datasets/ppg_dalia.py`'s interface (per-subject
  BVP/ACC/reference arrays + windowing), but must independently re-verify
  synchronization/session-duration facts against real files before windowing
  (see open items in the protocol doc).
- **Split artifact**: `results/galaxyppg_split_stage2.json` (grouped subject
  CV fold assignments, frozen before training).
- **Exact protocol artifact**: `results/galaxyppg_protocol_stage1b.json`
  (this sprint) — do not redesign A/B/C/split/metric at Stage-2 time.
- **Target**: HR (bpm), Polar H10 raw-ECG R-peak derived.
- **Features**: A = E4 BVP; B/C = E4 BVP + E4 ACC (aligned/deranged per C).
- **Excluded fields**: Polar/Galaxy Watch device-derived HR, Galaxy Watch ACC
  (out of scope).
- **Model/capacity design**: architecture-matched dual 1D-CNN encoder,
  parameter counts disclosed in the result artifact.
- **Seeds**: derive `model_init_seed` / `data_order_seed` / `control_shuffle_seed`
  from one run seed, following `ml/sleep_seed_utils.py`'s pattern (H1-corrected
  order: seed before model construction).
- **Primary metric**: MAE (bpm). Secondary: RMSE (bpm).
- **Output filenames**: `results/galaxyppg_hr_external_replication_stage2.json`.
- **Checkpoint naming**: `galaxyppg_hr_a_cap_seedXX.pt`,
  `galaxyppg_hr_b_imu_seedXX.pt`, `galaxyppg_hr_c_shuffled_imu_seedXX.pt`.
- **Tests to run**: `ml/tests/test_stage1b_galaxyppg.py` (contract tests,
  this sprint) plus new Stage-2 performance-adjacent tests (subject-disjoint
  folds actually enforced by the real loader, etc. — no performance-threshold
  tests, per Section 38).
- **Stop conditions**: if actual file inspection contradicts any fact in
  `results/galaxyppg_actual_file_audit_stage1b.json` (e.g. a signal is not
  actually complete for all 24 subjects, or cross-device sync is not
  recoverable), stop and re-open this protocol rather than silently adapting
  around it.
