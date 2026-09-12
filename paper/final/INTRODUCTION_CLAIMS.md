# Introduction — Structured Claim Material

Source of truth: `results/final_claim_ledger.json`. Each bullet cites its `claim_id`.

## Motivation (context, not a validated claim)

Long-duration spaceflight requires continuous physiological monitoring, but
every additional sensor adds mass, power, contact points, and crew burden.
This motivates asking, per modality, whether it earns its burden budget with
measured evidence rather than assumption. `[claim_id: sensor_minimalism_framing]`

## Research question (methodological framing)

> Biological Minimalism evaluates whether sensing modalities provide measurable incremental value after controlling for model capacity, temporal correspondence, subject separation, heterogeneity, and physical burden.
`[claim_id: sensor_minimalism_framing]`

This is a methodology applied uniformly across candidate modalities, not a
target sensor count decided in advance.

## What this paper reports

- A capacity-controlled, externally-corroborated positive result for wrist PPG+IMU. `[claim_id: ppg_plus_imu, galaxy_replication]`
- A same-dataset controlled positive result for frontal EEG+EOG sleep staging, with a bounded (not yet full-cohort) external diagnostic. `[claim_id: eog_incremental_value, hmc]`
- Negative or mixed results for second-site PPG, leg BioZ, and thoracic EIS, preserved and reported alongside the positive results. `[claim_id: second_site_ppg, leg_bioz, thoracic_eis]`
- A final wearable architecture (CORE_PLUS_CONTEXT) selected from a Pareto-relevant, non-dominated set via evidence-driven, burden-aware Coordinator judgment — not a unique mathematical optimum. `[claim_id: final_architecture, pareto]`
- Explicit, bounded engineering burden estimates for that architecture. `[claim_id: engineering_burden]`

## What this paper does not claim

- That any sensor set is proven scientifically minimal or sufficient. `[claim_id: sensor_minimalism_framing]`
- That any result is validated on astronauts or in microgravity. `[claim_id: astronaut_microgravity_applicability]`
- That the Digital Twin is a trained or validated model. `[claim_id: digital_twin]`
