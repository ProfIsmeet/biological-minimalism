# Methods Contract

Source of truth for every field below: `results/final_tables/table_a_modality_evidence.json`, `results/final_reproduction_manifest.json`, `docs/HASH_PROVENANCE_POLICY.md`. Do not restate numbers here that are not already in those artifacts.

## Datasets

| Dataset | Role | External? |
|---|---|---|
| PPG-DaLiA | Wrist PPG+IMU HR ablation, capacity control, fault robustness, PTT | No (primary) |
| GalaxyPPG (corrected cohort) | External corroboration of wrist IMU HR benefit | Yes |
| Sleep-EDF Expanded | Frontal EEG+EOG sleep-staging ablation (primary, shuffled control, secondary holdout, interaction) | No (primary) |
| HMC (Haaglanden Medisch Centrum) | Bounded n=7 external diagnostic for EOG | Yes (bounded) |
| ds003838 (OpenNeuro) | Bounded n=3 external diagnostic for sparse EEG | Yes (bounded) |
| QDE V2 | Leg BioZ ablation | No (primary) |
| LBNP protocol | Thoracic EIS ablation (terrestrial hypovolemia protocol-analog) | No (primary) |

Full per-experiment n, seeds, and data-availability are in
`results/final_reproduction_manifest.json`.

## Splits and subject separation

All governing results use held-out subject splits (not window-level
splits) — see each experiment's `biological_n_subjects` /
`held_out_n` in `results/final_tables/table_a_modality_evidence.json`.
Window-level and subject-level agreement is explicitly reported where
tested (e.g. GalaxyPPG participant-level vs window-level, <0.02 bpm
agreement).

## Model-capacity controls

The historical PPG-DaLiA IMU result compared models of different
parameter counts (Model A 8,065 vs Model B ~29,000); the governing
capacity-controlled comparison (`A_cap`) matches architecture/capacity
before testing the IMU channel's marginal contribution. `[claim_id: old_ppg_imu_headline_20_6_23_percent, ppg_plus_imu]`

## Shuffled / deranged controls

Sleep-EDF's Condition C shuffles the EOG channel's temporal alignment
(deranged, not simply removed) to control for the possibility that any
extra channel — regardless of temporal correspondence to the label —
improves the model. `[claim_id: eog_incremental_value]`

## Seed handling

Each governing training result reports the number of independent seeds and
how many of them favor the candidate condition (never a single-seed point
estimate) — see `seeds` and effect-direction counts throughout Table A and
Table B.

## External replication

GalaxyPPG (corrected cohort), HMC (bounded n=7), and ds003838 (bounded n=3)
are the three external-dataset checks in this project, explicitly classed
as full replication / bounded diagnostic / pending — see
`results/final_tables/table_c_external_replication.json`. An earlier
GalaxyPPG analysis was invalidated after discovering a reference-ECG
signal-quality defect in 6/24 subjects; only the corrected 18-subject
analysis is current governing evidence
(`results/galaxyppg_invalidated_evidence_registry.json`).

## Engineering burden methodology

Burden (power, mass, data rate, contacts) is estimated per candidate
architecture class from component-datasheet or class-level references
(Tier 0-2, not measured/vendor-sourced), covering body region, module
count, contact/electrode count, and attachment burden — not chip count
alone. See `results/final_tables/table_f_engineering_burden.json` and
`[claim_id: engineering_burden]`.

## Hash / provenance discipline

All committed text/JSON artifacts are hashed with the canonical
(LF-normalized) method; binary artifacts (checkpoints, datasets) are
hashed raw. See `docs/HASH_PROVENANCE_POLICY.md`.
