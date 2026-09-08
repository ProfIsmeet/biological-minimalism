# Stage 2 QDE V2 Implementation Handoff

- **Data path expectation**: `datasets/qde-bioimpedance/raw/dehydration_estimation.csv`
  (already present).
- **Loader required**: extend `ml/datasets/qde_bioimpedance.py` with a new
  function (e.g. `load_dataset_v2_leg_bioz`) returning baseline-relative
  deltas and the new target — do not modify `load_dataset`'s existing
  behavior (used by the historical trainer).
- **Split artifact**: `results/qde_v2_loso_folds_stage2.json`.
- **Exact protocol artifact**: `results/qde_v2_protocol_stage1b.json`.
- **Target**: baseline-relative Kern-scale delta_weight_kg.
- **Features**: A = arm+trunk impedance delta; B/C = + leg impedance delta.
- **Excluded fields**: Kern weight (target), InBody weight, InBody TBW,
  running interval, running speed.
- **Model/capacity design**: ridge regression, nested-LOSO alpha selection,
  identical model class for A/B/C.
- **Seeds**: N/A for the primary ridge model (deterministic fit); if a
  stochastic model is later substituted, seed via the same
  `ml/sleep_seed_utils.py`-style sub-seed convention.
- **Primary metric**: MAE (kg). Secondary: RMSE (kg).
- **Output filenames**: `results/qde_v2_leg_bioz_stage2.json`.
- **Checkpoint naming**: N/A for ridge regression — explicitly state in the
  Stage-2 result artifact that no checkpoint files are scientifically
  necessary for a linear model (avoid creating meaningless serialized
  artifacts), per Section 46.
- **Tests to run**: `ml/tests/test_stage1b_qde_v2.py` (this sprint).
- **Stop conditions**: if any subject's leg-impedance channel is found
  missing/corrupted at Stage-2 load time (not observed this sprint), exclude
  that subject via the eligibility rule rather than imputing.
