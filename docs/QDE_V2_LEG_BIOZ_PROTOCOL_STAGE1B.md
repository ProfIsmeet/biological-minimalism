# QDE V2 (Leg BioZ) Protocol (Stage 1B)

**Classification: GO_WITH_LIMITATIONS**

Full machine-readable facts: `results/qde_v2_actual_file_audit_stage1b.json`,
`results/qde_v2_protocol_stage1b.json`.

## Historical reconciliation

QDE is **not new** to this project — `ml/datasets/qde_bioimpedance.py` and
`ml/train_bioimpedance.py` already exist from an earlier sprint. The old
experiment predicted **InBody TBW (liters)** from 5 impedance + 11
temperature features via LOSO with a small MLP; no archived
`results/*.json` exists for that run (documented narratively in the trainer's
own docstring and the dataset README instead — reconstructed from source
this sprint, not overwritten or reinterpreted).

## New scientific question

Does bilateral leg segment impedance add predictive information beyond
arm+trunk impedance for **baseline-relative Kern-scale body-mass change**
(a body-mass-loss/dehydration proxy under this specific protocol — not TBW,
not general hydration).

## Why the new target is less circular

InBody TBW is computed by the InBody 720 device using its own internal
bio-impedance measurement — training on BIA features to predict a
BIA-derived target is close to definitionally circular. The Kern scale is a
mechanical/strain-gauge instrument, a physically independent measurement
principle. Some residual correlation is still expected (both share the
common cause of dehydration) — stated explicitly, not claimed as zero
dependence.

## Actual-file verification

Direct CSV read confirms: 10 subjects, 9 rows each (90 total), 0 missing
Kern-weight or TBW values, exact column names verified (impedance is at
1000 kHz — single-frequency BIA, not a spectroscopy sweep like LBNP). No
literal "elapsed time" column exists; `running interval` and
`running speed [km/h]` are the real protocol-progression fields, excluded
per the master prompt's rule.

## Frozen A/B/C

- **A**: right/left arm + trunk impedance (baseline-relative delta).
- **B**: A + right/left leg impedance (delta).
- **C**: B-dimensional, with leg-impedance-delta correspondence destroyed
  within subject — **both legs deranged jointly** (same donor interval for
  both), preserving plausible bilateral structure.

## Model class: ridge regression (frozen)

Given n=90 rows / 10 subjects, a small MLP is explicitly ruled out (matching
this project's own prior QDE trainer's reasoning). LOSO outer, nested LOSO
inner for hyperparameter selection.

## Metric

Primary: MAE (kg). Secondary: RMSE (kg).

## Negative-result and forbidden-claim policy

See `results/qde_v2_protocol_stage1b.json` and
`docs/STAGE1B_EXPANSION_FORBIDDEN_CLAIMS.md`.
