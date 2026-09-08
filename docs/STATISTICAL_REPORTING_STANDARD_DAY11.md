# Statistical Reporting Standard (Day 11)

Canonical, project-wide statistical language. Supersedes ad hoc per-
experiment reporting choices going forward; does not rewrite any legacy
artifact. See `docs/STATISTICAL_REPORTING_AUDIT.md` for the prior SD-
convention-specific audit this document generalizes.

## 1. Replication units — not interchangeable

This project's experiments mix several distinct kinds of repetition. They
must never be conflated into one "n" or one confidence interval:

| Unit | What varies | What it tells you | What it does NOT tell you |
|---|---|---|---|
| **Training seed** | Random weight init + data-loader shuffle order, same data/split | Whether an effect survives independent optimization trajectories on the SAME data | Anything about population variability, generalization to new subjects, or "statistical significance" in the classical sense |
| **Held-out subject** | Which real individual's data was excluded from training | Whether an effect generalizes across the (small) population actually sampled | Generalization beyond that population/dataset |
| **Dataset** | Entirely different data source/population/recording protocol | Cross-population/cross-protocol replication | N/A - this project has never varied this axis for any target (single dataset per target throughout) |
| **Condition** (robustness) | An injected perturbation scenario (dropout, noise, frozen sensor, etc.) | How a fixed, already-trained model degrades under a specific fault | Anything about sensor value/marginal benefit - a separate axis (see `SENSOR_MARGINAL_VALUE_METHODOLOGY.md` SS13) |
| **Class** (sleep stage) | Which of 5 sleep stages is being scored | Per-class error structure | Overall/macro accuracy - classes are not independent samples of "the same effect," they are different sub-tasks with very different base rates |

**Hard rule: 5 training seeds is never "n=5 subjects."** Every artifact and
every paper-facing sentence in this project must say which unit a given
"n" refers to.

## 2. Sample SD convention

- **Sample SD (`ddof=1`)** is the standard for any *new* multi-seed
  aggregate produced from this document forward. It is the correct
  small-sample variability estimator when treating the 5 seeds as a
  sample from a (hypothetical) larger population of possible
  initializations.
- **Legacy artifacts** that originally reported population SD (`ddof=0`)
  are **preserved unchanged** - never rewritten retroactively merely to
  switch convention. `results/sd_convention_audit.json` provides the
  `ddof=1` recomputation for the two affected legacy artifacts
  (PPG-DaLiA multiseed, PTT) side-by-side with the original, without
  altering the originals.
- **Paper tables use sample SD (`ddof=1`)** unless a specific table is
  explicitly reproducing a legacy figure verbatim, in which case it must
  say so.

## 3. Confidence interval policy

**No project artifact computes a seed-based interval and presents it as a
population confidence interval.** The following distinctions are frozen:

| Label | What it is | Valid uses in this project |
|---|---|---|
| `SEED_VARIABILITY` | Mean ± sample SD across training seeds | Communicating optimization-trajectory sensitivity. Never described as "95% CI" or population uncertainty. |
| `DESCRIPTIVE_SUBJECT_BOOTSTRAP` | Percentile interval from resampling held-out subjects with replacement | Purely descriptive summary of the small observed subject sample's spread. Explicitly labeled `DESCRIPTIVE_SUBJECT_BOOTSTRAP` wherever computed (see `results/sleep_edf_sensitivity_day11.json`). Never a population-generalization proof. |
| `NO_DEFENSIBLE_POPULATION_CI` | n too small (e.g. PTT n=4) for any inferential interval to mean anything | Applied explicitly to PTT subject-level reporting - report descriptive per-subject values and direction counts only, never a computed interval. |

No p-values are computed anywhere in this project's statistical artifacts.
Training seeds are never treated as independent biological replicates for
the purpose of any inferential test - see SS5.

## 4. Statistical unit audit

`results/statistical_unit_audit_day11.json` records, per experiment, the
true optimization-replication-n, held-out-subject-n, dataset-n, and
class-n, plus an explicit list of interpretations that would be
inappropriate given those numbers (e.g., "PTT n=4 subjects is not evidence
of population-level negative effect").

## 5. Multiple-comparison caution

Where many class/activity/subject comparisons are reported (e.g. Sleep's
5-class per-class F1, PPG-DaLiA's 9-activity breakdown), this project
reports **direction counts and effect sizes**, never significance testing
across many comparisons. No result in this project has ever been selected
or highlighted because it crossed a p<0.05 threshold - none is computed.

## 6. What this standard does NOT do

- Does not change any canonical mean, delta, or evidence-strength
  classification.
- Does not retroactively edit any legacy `ddof=0` artifact.
- Does not introduce inferential statistics (p-values, hypothesis tests)
  anywhere in this project.
