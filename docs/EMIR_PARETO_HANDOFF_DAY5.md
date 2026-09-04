# Emir / Pareto Handoff — Day 5 Scientific Marginal Value Contract

**Source of truth:** `results/sensor_marginal_value_contract.json` (machine-readable),
built by `ml/build_sensor_marginal_value_contract.py` from frozen result
artifacts. Full rationale: `docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md`.

This document is implementation-ready for whoever builds the operational-cost
and Pareto layers next (Emir/Claude Code). It does not itself compute any
cost, weighting, or ranking — those remain a separate, later track.

## What you may safely consume

- `experiments.<id>.absolute_benefit.{mae_bpm,rmse_bpm}` and
  `relative_improvement.{mae_fraction,rmse_fraction}` — **within that one
  experiment only**.
- `experiments.<id>.marginal_status.overall_direction` — one of `POSITIVE`,
  `NEGATIVE`, `MIXED`, `NEUTRAL`, `INSUFFICIENT` (only `POSITIVE`/`NEGATIVE`
  are populated so far).
- `experiments.<id>.marginal_status.evidence_strength` — one of
  `preliminary`, `replicated-within-dataset`, `mixed`, `insufficient`.
- `experiments.<id>.evidence_scope.*` — held-out subject/seed/dataset counts,
  whether a negative control and subject-disjoint split were used.
- `evidence_matrix.<target>.<candidate_component_id>.status` — quick lookup
  of what's validated per target; anything not listed, or listed as
  `UNVALIDATED`, has no evidence and must not be treated as neutral/zero.
- `candidate_component_id` strings (e.g. `wrist_imu_accelerometer`,
  `second_physical_ppg_site_proximal_phalanx`) — stable identifiers you can
  map to your own physical-architecture/cost schema.

## Exact units and sign conventions

- All accuracy figures are **bpm** (heart rate is the only validated target
  so far).
- `absolute_benefit`: `baseline_metric - candidate_metric`. **Positive =
  candidate is better** (lower error). Never inverted between experiments.
- `relative_improvement`: `(baseline - candidate) / baseline`, a fraction
  (multiply by 100 for a percentage). Same sign convention.
- RMSE fields follow the identical convention as MAE, always reported
  alongside it, never combined into it.

## Null / unavailable semantics

- `null` (e.g. `synchronization_decomposition: null` for Experiment B,
  `negative_control: null`) means **that analysis does not apply to this
  experiment** — not zero, not "no effect."
- `"UNVALIDATED"` in `evidence_matrix` means **no experiment exists for
  this target/component pair** — not "neutral" or "assumed negative."
- `"SOURCE_ARTIFACT_NOT_FOUND"` (currently `ppg_dalia_fault_robustness`)
  means the cited source file could not be located in this repository —
  **do not treat this record's absence as a robustness finding of any
  kind** (positive or negative) until it is resolved.

## Cross-dataset comparison — hard prohibition

Do **not** rank or combine `baseline_metrics`/`candidate_metrics` raw MAE
or RMSE values across different `dataset_id`s. `7.03 bpm` (PPG-DaLiA) and
`17.54 bpm` (PTT) are not measuring comparable populations, activities, or
model families — see methodology doc SS10. You may compare `marginal_status.
overall_direction` and evidence-scope fields descriptively (e.g. "one
experiment is positive, the other negative"), but never as a numeric
ranking.

## Robustness is a separate axis

`ppg_dalia_fault_robustness` in this contract is currently unpopulated
(see above). Once resolved, robustness evidence (accuracy-under-corruption,
availability-under-corruption) must remain in its own record structure,
never merged into a `marginal_status` field. Methodology doc SS13.

## What may be combined with operational cost (later track, not built here)

- `candidate_component_id` → map to your hardware/contact/power/compute
  schema.
- `marginal_status.overall_direction` + `evidence_strength` as one input
  dimension to a future multi-objective decision, alongside your
  independently-owned cost dimension.

## What must NOT be averaged or summed

- Raw MAE/RMSE across experiments/datasets (SS10).
- `interaction_effects.interaction_evidence` is `"unavailable"` — do not
  assume `Value(A+B) = Value(A) + Value(B)` for any two candidate
  components; no experiment has measured this.
- Do not average `relative_improvement` fractions across experiments into
  a single "average sensor value" — each fraction is relative to a
  different baseline and population.

## What remains unvalidated (do not estimate)

Every target in `evidence_matrix` other than `heart_rate_bpm`: workload,
fatigue, blood_pressure, fluid_shift, circadian_stability. Any candidate
component's value for these targets is currently unknown, not zero.

## No universal sensor score exists

`universal_sensor_score.recommendation` is `"AGAINST"` — do not compute one
independently from this contract's fields. See methodology doc SS9.
