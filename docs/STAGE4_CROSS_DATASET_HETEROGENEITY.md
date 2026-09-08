# Stage 4 Cross-Dataset Heterogeneity

## HR external replication (PPG-DaLiA vs GalaxyPPG)

Cannot be compared this sprint — GalaxyPPG is blocked by data access. No
heterogeneity claim is made; the comparison remains for a future session.

## BioZ evidence heterogeneity

Two BioZ experiments now exist in this project, testing genuinely different
questions with different targets — they must not be pooled or compared as
if measuring the same thing:

- **Historical QDE (TBW)**: absolute total body water, InBody-derived
  target — acknowledged circular (BIA-features predicting a BIA-derived
  target).
- **QDE V2 (this sprint)**: baseline-relative body-mass change, Kern-scale
  (mechanically independent) target — less circular, negative-leaning,
  single-subject-dominated result.
- **LBNP thoracic EIS**: not yet trained (blocked). A fundamentally
  different physiological challenge (central hypovolemic stress via
  externally-applied negative pressure) from QDE's voluntary-exercise
  dehydration — even a future positive LBNP result would not corroborate or
  contradict QDE's finding, since the underlying physiological mechanism
  and measurement site (thorax vs. limbs) differ.

## EEG evidence heterogeneity

- **Sleep-EDF EEG+EOG**: sleep-staging target, inherited, reconfirmed under
  H1-corrected seeding.
- **ds003838 sparse-vs-full EEG**: cognitive/working-memory-load target,
  entirely different task, different montage, different subject population,
  different frequency content of interest. **A finding in one has no
  bearing on the other** — they are not treated as corroborating or
  conflicting evidence for "how much EEG minimalism is possible" in
  general.

## General heterogeneity discipline maintained this sprint

No result from one dataset was used to explain away, adjust, or reinterpret
a result from another. Each experiment's `safe_claim` in
`results/sensor_value_master_matrix_stage4.json` is scoped to its own
dataset, cohort, and protocol only.
