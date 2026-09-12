# Results Contract

Distinguishes positive / replicated / mixed / negative / pending results.
Do not cherry-pick only the positive rows — every row below has a governing
artifact in `results/final_tables/`.

## Positive, externally corroborated

- **Wrist PPG+IMU → HR.** Capacity-controlled A_cap→B +0.605 bpm (PPG-DaLiA, 5/5 seeds); externally corroborated on GalaxyPPG corrected cohort, A_cap→B +0.834 bpm (12/18 participants favor B). `[claim_id: ppg_plus_imu, galaxy_replication]`

## Positive, same-dataset controlled, bounded external diagnostic only

- **Frontal EEG+EOG → sleep stage.** B−A +0.028 macro-F1 (4/5 seeds), B−C (shuffled control) +0.032 (4/5 seeds); prospective n=8 secondary holdout supports the primary direction but N3 regresses while REM gains strongly — disclosed, not smoothed. HMC bounded n=7 diagnostic does not itself establish external replication (B−A −0.031, 2/5 seeds favor B). `[claim_id: eog_incremental_value, hmc]`

## Mixed / negative

- **Second-site PPG → HR/PTT.** B−A +1.462 MAE (worse), n=4, subject-fragile (excluding s2 flips the aggregate sign). `[claim_id: second_site_ppg]`
- **Leg BioZ (QDE V2).** Aggregate-negative (A−B −0.052, C−B −0.060, n=10) but heterogeneous (7/10 subjects individually favor the candidate). `[claim_id: leg_bioz]`
- **Thoracic EIS (LBNP, corrected protocol).** COMPLETE_MIXED: A−B −0.452 mmHg MAE (n=12), sign-reverses without subject 9. `[claim_id: thoracic_eis]`
- **EEG×Respiration interaction.** Mixed-sign (interaction_mean −0.0078 ± 0.0363, 3/5 seeds positive, 2/5 negative) — "approximately additive or unresolved," not evidence of synergy or antagonism. `[claim_id: sleep_interaction]`

## Descriptive (not a marginal-value claim)

- **Fault-injection robustness.** 114 perturbation conditions on a single held-out subject (S14); zero/frozen IMU diagnostic +0.95 bpm MAE vs clean; reproduced 114/114 within 1e-4 bpm tolerance from a frozen checkpoint. Descriptive per-condition, not a hypothesis test. `[claim_id: robustness_fault_injection]`

## Pending (not run, not a negative result)

- **HMC full cohort** (151 subjects; 59 downloaded, 52 SHA-verified). `[claim_id: hmc]`
- **ds003838 full cohort** (~93GB additional download required, not attempted). `[claim_id: ds003838]`

## Architecture decision outcome

CORE_PLUS_CONTEXT was selected from a Pareto-relevant, non-dominated set
(alongside MINIMAL_CORE) via Coordinator judgment, not mathematical
dominance. `[claim_id: final_architecture, pareto]`
