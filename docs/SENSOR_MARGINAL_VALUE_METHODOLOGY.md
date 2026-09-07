# Sensor Marginal Value Methodology (Day 5)

**Version 1.0.0.** Machine-readable implementation:
`results/sensor_marginal_value_contract.json`, generated deterministically
from frozen source artifacts by `ml/build_sensor_marginal_value_contract.py`
(no training, no source-artifact edits).

This document is the scientific source of truth for how Biological
Minimalism represents the marginal predictive value of a candidate sensing
component. It intentionally stops short of assigning operational cost or
building a Pareto frontier — that is a separate, later track.

---

## 1. Purpose

Convert already-completed, frozen experiments into a rigorous, consistent
representation of "did adding this sensing component measurably help this
target, in this experiment" — without collapsing distinct experiments into
one number that hides what they don't actually have in common.

## 2. Definitions

- **Target**: the physiological quantity being estimated (e.g. heart rate).
- **Baseline configuration**: the sensor input set evaluated *without* the
  candidate component.
- **Candidate component**: the single sensing element being tested for
  marginal value (a modality, a physical site, etc.).
- **Candidate configuration**: baseline + candidate component, evaluated
  under otherwise identical target, dataset, split, windows, preprocessing,
  and evaluation protocol.
- **Marginal value**: the measured difference in a chosen metric between
  candidate and baseline configurations, for one target, on one dataset,
  under one frozen protocol. Marginal value is never a property of a
  sensor in isolation.

## 3. Baseline / candidate semantics

Every experiment record stores baseline and candidate as full,
human-readable configurations (description + channel list), never just a
component name. Marginal value is only meaningful relative to its stated
baseline — a different baseline could yield a different result for the
same candidate component. Context is mandatory; see the contract's
`baseline_configuration`/`candidate_configuration` fields.

## 4. Accuracy metrics

- **MAE** is the primary accuracy metric for marginal-value comparison.
- **RMSE** is a secondary, outlier-sensitive severity metric, always
  reported alongside MAE, never combined with it into one score. No
  defensible MAE/RMSE weighting has been frozen (`metric_policy.
  combined_mae_rmse_score: null` in the contract).

## 5. Sign convention (frozen, applied identically everywhere)

```
absolute_benefit   = baseline_metric - candidate_metric
relative_improvement = (baseline_metric - candidate_metric) / baseline_metric
```

Positive = candidate improves (lower error). Negative = candidate worsens.
This sign convention is never inverted per-experiment, so a reader can
compare *direction* across experiments without re-deriving the sign each
time (see SS10 for what may and may not be compared).

## 6. Availability

`availability = valid_predictions / eligible_windows`, always a dimension
separate from MAE/RMSE. An unavailable prediction is never assigned a
fabricated MAE (zero, infinite, or otherwise) inside this contract — that
would require a decision-theoretic framework this project has not built.
Ordinary sensor-value ablations (Experiments A and B) had full availability
in both configurations, so availability does not distinguish them; it
becomes central for robustness/fault experiments (SS13).

## 7. Variability taxonomy

Different experiments have structurally different sources of uncertainty.
This project keeps them named and separate rather than collapsing them
into one "confidence" number:

| Source | Meaning | Present in Exp. A (PPG-DaLiA) | Present in Exp. B (PTT) |
|---|---|---|---|
| Training-seed variability | SD of a metric across independently-initialized/trained models, same split | No (1 seed) | Yes (5 seeds) |
| Subject heterogeneity | Different held-out subjects improve/worsen | Yes (3 subjects) | Yes (4 subjects) |
| Activity/condition heterogeneity | Effect differs by activity/motion level | Yes (9 activities + 4 motion quartiles) | Yes (3 activities) |
| Dataset uncertainty | Would the effect replicate on a different population/dataset? | Not estimated (1 dataset) | Not estimated (1 dataset) |

None of these is called "predictive uncertainty" — that term is reserved
for a calibrated per-prediction model output, which does not exist for
any model in this project.

## 8. Evidence-strength policy

A categorical, transparent descriptor — not a numeric confidence — built
from: held-out subject count, subject-disjoint evaluation, independence of
ground truth, seed replication, direction consistency, negative-control
presence, and known caveats. Categories used in the contract:

- `preliminary` — direction consistent within its scope, but no multi-seed
  replication and/or only one dataset/population (Experiment A's status).
- `replicated-within-dataset` — the same direction holds across multiple
  independent training seeds on one dataset (Experiment B's status).
- `replicated-with-control` (added Day 8) — `replicated-within-dataset`,
  PLUS a matched negative control (e.g. a shuffled/scrambled version of
  the candidate component) that shows the effect specifically depends on
  the property the control removes (e.g. temporal alignment), not merely
  on the candidate's presence. Strictly stronger than
  `replicated-within-dataset` alone, but still scoped to one dataset/
  population — see the Sleep-EDF EOG experiment for the first use of
  this category.
- `mixed` — direction itself is inconsistent across a primary evidence axis.
- `insufficient` — too little evidence to assign a direction at all.

These carry no clinical, regulatory, or population-generalization meaning.

## 9. Why there is no universal sensor score

**Recommendation: against.** A bounded 0–1 (or similar) score would require
weighting decisions this project cannot currently defend: how much a
+22.6% relative HR-MAE improvement on 15 free-living subjects should count
against a −8.3% relative HR-MAE effect on 22 different subjects performing
different activities, evaluated with a different model family. Any such
weighting is an operational/design choice belonging to a later, explicitly
authorized Pareto stage — not a scientific fact this contract can assert.
`results/sensor_marginal_value_contract.json`'s
`universal_sensor_score.recommendation` is `"AGAINST"`.

## 10. Cross-dataset comparability rules

**Prohibited**: comparing raw MAE/RMSE between experiments on different
datasets (e.g. "7.03 bpm < 17.54 bpm ⇒ the PPG-DaLiA architecture is
better") — the populations, HR distributions, activities, model families,
and baseline difficulty all differ, so the comparison is not measuring the
same thing.

**Allowed, descriptively**: comparing *direction* of marginal value,
*evidence scope* (held-out subject count, seed count, dataset count), and
*consistency descriptors* across experiments. Relative improvement is a
useful within-experiment normalization but does not make two experiments'
percentages equivalent to each other — a percentage of a different
baseline is still a different baseline.

## 11. Positive-result interpretation

`positive_for_target ≠ automatic_inclusion_in_final_architecture.` A
positive marginal-value result (Experiment A: wrist IMU improves HR
estimation) is evidence for one target, on one dataset, under one frozen
protocol. Final sensor-suite decisions must also weigh other targets,
operational cost, robustness role, and redundancy — none of which this
contract evaluates.

## 12. Negative-result interpretation

`negative_for_target ≠ global_removal_of_component.` A negative result
(Experiment B: second PPG site does not improve HR estimation here) means
exactly that: under this frozen experiment, the candidate did not
demonstrate sufficient predictive improvement over baseline for this
target. It says nothing about the same component's value for a different
target, and is not itself grounds to remove the component from a
final design. A negative result is treated as scientifically useful
evidence for the Biological Minimalism hypothesis, not a failed experiment.

## 13. Relationship to robustness

Sensor marginal-value experiments ask: *does adding this component improve
the target under clean conditions?* Robustness/fault experiments ask:
*what happens to accuracy and availability when an existing input is
degraded or unavailable?* These are related but distinct questions and
are kept as separate evidence structures — a robustness result must never
be silently folded into a sensor marginal-value score, and vice versa.
(This methodology anticipates a future `robustness_records` structure
alongside `experiments` in the contract once
`results/ppg_dalia_fault_robustness.json` is located/verified — see
Appendix A below for the current gap.)

## 14. Interaction effects

`Value(component_A + component_B)` is not assumed equal to
`Value(A) + Value(B)`. No experiment in this project has measured a
genuine interaction between two candidate components added together, so
the contract records `interaction_evidence: "unavailable"` rather than
inventing an additive or synergistic assumption.

## 15. Current experiment applications

See `results/sensor_marginal_value_contract.json` → `experiments` for the
full machine-readable records. Summary:

- `ppg_dalia_imu_hr`: wrist IMU → heart rate, PPG-DaLiA. **POSITIVE**,
  evidence strength `preliminary`.
- `ptt_second_ppg_site_hr`: second PPG site → heart rate, PTT dataset.
  **NEGATIVE**, evidence strength `replicated-within-dataset`, with
  subject/activity-level heterogeneity disclosed.
- `ppg_dalia_fault_robustness`: **not populated** — source artifact not
  found in this repository (see Appendix A).

## 16. Limitations of this methodology itself

- Only two sensor-value experiments exist; the framework has not yet been
  stress-tested against a genuinely conflicting or ambiguous third case.
- Evidence-strength categories are qualitative by design; they are not a
  substitute for statistical power analysis, which this project has not
  performed given small held-out-subject counts (see the master prompt's
  own SS16: window-level pseudo-replication is explicitly avoided, so no
  window-level significance claims exist here either).
- The methodology assumes MAE/RMSE are the correct metrics for all future
  targets; a differently-distributed target (e.g. a classification target)
  will need an explicit metric-policy extension, not silent reuse of this one.

## 17. Rules for future experiments

To be added to this contract, a new experiment must supply: an explicit
baseline/candidate configuration pair evaluated under the definition in
SS3, a subject-disjoint (or otherwise justified) split, MAE and RMSE (or a
documented reason another metric applies), and honest heterogeneity
reporting (subject/activity/seed, as available) — not just an aggregate.
Missing evidence for a target must be recorded as `UNVALIDATED`, never
estimated from literature or intuition (see `evidence_matrix` in the
contract).

## 18. Contract for Pareto integration (forward-looking, not built here)

A later, explicitly authorized Pareto track may combine this contract's
`marginal_status`/`relative_improvement`/`evidence_scope` fields with a
separate operational-cost contract (owned by the integration track, not
this one). This document does not define how that combination should be
weighted — see SS9 on why no such weighting is frozen yet.

---

## Appendix A — Fault robustness artifact discrepancy

The Day 5 master prompt describes `results/ppg_dalia_fault_robustness.json`
as an already-complete, frozen "Experiment C" with specific figures. That
file was searched for and **not found**: not in the working tree, not via
`git log --all -- results/ppg_dalia_fault_robustness.json`, and not on any
local or remote branch (`day2-ml`, `day3-ml`, `day5-ml`, `main`, and their
`origin` counterparts) as of this document's writing. Per this project's
standing rule against citing unverified numbers, none of the prompt's
cited fault-robustness figures were copied into this methodology or into
`results/sensor_marginal_value_contract.json`. The contract's
`ppg_dalia_fault_robustness` record instead carries a
`SOURCE_ARTIFACT_NOT_FOUND` status and an explicit `action_required` note.
This is reported for team review, not silently resolved. Still absent as
of Day 7 (`day7-accelerated-ml`); re-confirmed, not fabricated.

## Appendix B — Day 7 revisions (methodology v1.2.0)

- **PPG-DaLiA capacity confound repaired**: a capacity-matched PPG-only
  control (Model A_cap) showed that ~68% of the originally-reported
  wrist-IMU benefit was attributable to model capacity/architecture, not
  IMU sensing information. The contract's `ppg_dalia_imu_hr` record now
  carries a `capacity_confound_status` field with the full revised
  decomposition. The direction remains POSITIVE, but at materially
  reduced magnitude (~0.6 bpm, still 5/5-seed-consistent, vs. the
  originally reported ~1.9 bpm). See
  `docs/PPG_DALIA_CAPACITY_CONTROL_RESULTS.md`.
- **PTT subject-heterogeneity/sensitivity added**: the aggregate negative
  result is driven almost entirely by held-out subject s2; excluding s2
  (descriptively, not as a re-run) flips the aggregate direction. s2 is
  never removed from the frozen primary result. See
  `docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md` SS "cross-dataset
  comparability" (unchanged) and `results/ptt_sensitivity_analysis.json`.
- **New target added**: `sleep_stage_5class` (Sleep-EDF, EOG added to
  EEG) — the methodology's first non-HR, non-regression application,
  confirming the marginal-value framework (baseline/candidate,
  subject-disjoint split, seed replication, evidence-strength
  categorization) transfers to a classification task and a different
  modality family. See `docs/SLEEP_EDF_EEG_EOG_RESULTS.md`.
- **Statistical reporting**: all multi-seed SD figures going forward
  report sample SD (`ddof=1`) as primary; historical `ddof=0` figures in
  frozen artifacts are preserved unchanged, with a side-by-side audit in
  `results/sd_convention_audit.json`. See
  `docs/STATISTICAL_REPORTING_AUDIT.md`.
- **Interaction limitation formalized**: `docs/SENSOR_INTERACTION_LIMITATION.md`
  — one-at-a-time marginal-value evidence does not establish a globally
  minimal sensor subset; referenced from the contract's
  `interaction_effects` block.
