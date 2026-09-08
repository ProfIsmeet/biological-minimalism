# Stage 2 ds003838 Implementation Handoff

- **Data path expectation**: `datasets/ds003838/raw/` (DataLad/git-annex
  clone from OpenNeuro; memory-task EEG only needed, ~96-99 GB for 65
  subjects — plan disk/bandwidth accordingly; gitignored).
- **Loader required**: new `ml/datasets/ds003838_eeg.py` (does not exist
  yet) — must read the real per-digit-position trigger codes from
  `events.tsv`, derive the 5/9/13-length label, and never pass the raw
  trigger string as a feature.
- **Split artifact**: `results/ds003838_split_stage2.json` (subject-wise
  folds over the 65 eligible subjects).
- **Exact protocol artifact**: `results/ds003838_protocol_stage1b.json` — do
  not reselect the sparse channel set after seeing results.
- **Target**: 3-class digit-span length (5/9/13), memory-condition trials.
- **Features**: A = AF7/AF8/TP9/TP10; B/C = full 63-channel montage.
- **Excluded fields**: raw trigger-code string, behavioral recall
  correctness, NASA-TLX scores.
- **Model/capacity design**: channel-wise shared 1D-CNN encoder + fixed-width
  aggregation (mean/attention pooling), so A and B have near-identical
  parameter counts.
- **Seeds**: `ml/sleep_seed_utils.py` sub-seed pattern.
- **Primary metric**: Macro-F1 (3-class). Secondary: balanced accuracy,
  ordinal error.
- **Output filenames**: `results/ds003838_eeg_minimalism_stage2.json`.
- **Checkpoint naming**: `ds003838_a_sparse4_seedXX.pt`,
  `ds003838_b_full63_seedXX.pt`, `ds003838_c_deranged_extra_seedXX.pt`.
- **Tests to run**: `ml/tests/test_stage1b_ds003838.py` (this sprint) plus
  new Stage-2 tests once the real loader exists (frozen channels present
  across all 65 subjects, subject-disjoint folds, control shuffles only the
  non-A channels).
- **Stop conditions**: (1) if AF7/AF8/TP9/TP10 is missing for ANY of the 65
  eligible subjects, stop and resolve before training (do not silently drop
  or substitute channels); (2) if the full download proves impractical,
  apply the frozen neutral-rule subject-subset fallback documented in the
  protocol — never an outcome-driven convenience subset.
