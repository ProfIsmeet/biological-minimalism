# Stage 4 Paper Science Handoff (Expansion Science)

This is a Methods/Results handoff for new Stage 2–4 experiments, **not the
final paper** — it does not overwrite any canonical paper source on
Claude/Furkan's branch.

## Methods added this sprint

- **QDE V2** (`ml/train_qde_v2_leg_bioz.py`): baseline-relative Kern-scale
  body-mass-change regression, ridge regression, LOSO outer / nested-LOSO
  inner alpha selection, jointly-deranged bilateral-leg control.
- **ds003838 bounded diagnostic** (`ml/train_ds003838_eeg_minimalism.py`):
  channel-wise mean-pooled fixed-width features (mean abs amplitude, std, 3
  FFT band powers), logistic regression, subject-wise LOSO across a small
  real-file subset.

## Results

- QDE V2: negative-leaning, single-subject-dominated (see
  `docs/QDE_V2_STAGE2_RESULTS_AND_INTERPRETATION.md`).
- GalaxyPPG, LBNP: blocked by data access (Zenodo unreachable both this and
  the prior sprint) — not a negative result, a genuine access gap.
- ds003838: bounded diagnostic only, real access confirmed working,
  full-cohort scientific result not yet available.

## Negative results preserved

QDE V2's negative-leaning finding is reported at full detail (aggregate,
per-subject, dominance) in `results/qde_v2_leg_bioz_stage2.json` and its
interpretation doc — no subject was excluded, no metric was switched, no
result was hidden.

## Limitations

n=10 (QDE), blocked access (GalaxyPPG/LBNP), bounded-diagnostic-only scale
(ds003838). See `results/sensor_value_master_matrix_stage4.json` for the
full per-experiment limitation list.

## Dataset lineage

See `results/dataset_lineage_stage1b.json` (Stage 1B, unchanged this
sprint) for full lineage/independent-family status of all five candidates.

## Terrestrial/spaceflight boundaries

None of this sprint's experiments (QDE, GalaxyPPG, LBNP, ds003838) involve
spaceflight, microgravity, or astronaut subjects. Every finding is bounded
to its own terrestrial population and protocol — see
`docs/STAGE1B_EXPANSION_FORBIDDEN_CLAIMS.md` for the exact list of claims
this project will not make from this evidence.
