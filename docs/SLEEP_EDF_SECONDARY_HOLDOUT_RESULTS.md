# Sleep-EDF Prospective Secondary Holdout — Results (Day 9)

Predeclaration: `docs/SLEEP_EDF_SECONDARY_HOLDOUT_PREDECLARATION.md` (frozen
before cohort download, before any prediction). Source artifact:
`results/sleep_edf_secondary_holdout_evaluation.json`. Reproducibility:
`results/sleep_edf_secondary_holdout_reproducibility.json` (5/5 seeds exact
macro-F1 match on reload + re-shuffle).

## 1. Cohort

n = 8 subjects, PhysioNet Sleep-EDFx sleep-cassette indices 18–25
(SC4181, SC4191, SC4201, SC4211, SC4221, SC4231, SC4241, SC4251) — first
night, same `E`-batch recording protocol as every primary-split subject.
Zero overlap with primary train (12), val (3), or test (3) subjects,
verified programmatically before evaluation. 22,041 total 30s epochs.
Evaluation only: the 15 existing frozen checkpoints (A/B/C × seeds 42–46)
were reloaded unmodified; nothing was retrained or tuned.

## 2. Aggregate result (5 seeds, sample SD)

| Model | Macro-F1 mean ± SD | Balanced accuracy mean ± SD |
|---|---|---|
| A — EEG only | 0.6530 ± 0.0154 | 0.7338 ± 0.0126 |
| B — EEG + aligned EOG | 0.6858 ± 0.0272 | 0.7611 ± 0.0211 |
| C — EEG + shuffled EOG | 0.6556 ± 0.0141 | 0.7397 ± 0.0152 |

| Comparison | Mean Δ | Seeds favoring B |
|---|---|---|
| A → B | +0.0328 | 5/5 |
| A → C | +0.0026 | 3/5 (~neutral) |
| C → B | +0.0302 | 5/5 |

**Outcome classification: Outcome 1** — B beats both A and C broadly (5/5
seeds each). The aligned-EOG effect, and specifically its dependence on
temporal alignment (not mere EOG presence), **generalizes to this
independent n=8 cohort** under the identical frozen model/protocol. Still
single-dataset (Sleep-EDF cassette) and terrestrial.

## 3. Subject-level results

| Subject | A | B | C | B−A | B−C | n epochs |
|---|---|---|---|---|---|---|
| SC4181 | 0.6677 | 0.6972 | 0.6841 | +0.0295 | +0.0131 | 2756 |
| SC4191 | 0.7730 | 0.7681 | 0.7760 | −0.0048 | −0.0079 | 2774 |
| SC4201 | 0.4818 | 0.5440 | 0.4816 | +0.0622 | +0.0624 | 2803 |
| SC4211 | 0.6599 | 0.6858 | 0.6667 | +0.0259 | +0.0192 | 2805 |
| SC4221 | 0.5088 | 0.6451 | 0.5257 | +0.1363 | +0.1194 | 2700 |
| SC4231 | 0.5599 | 0.6256 | 0.5728 | +0.0657 | +0.0529 | 2743 |
| SC4241 | 0.6361 | 0.6580 | 0.6327 | +0.0219 | +0.0253 | 2700 |
| SC4251 | 0.6515 | 0.6470 | 0.6432 | −0.0045 | +0.0038 | 2760 |

(Values are each model's mean macro-F1 across 5 seeds, per subject.)

**6/8 subjects favor B over A; 7/8 favor B over C; 6/8 win both
comparisons.** Two subjects (SC4191, SC4251) show a small negative or
near-zero B−A delta — disclosed, not hidden. The subject with the largest
absolute effect (SC4221, ΔB−A = +0.136) accounts for **41% of the summed
B−A effect across all 8 subjects** — a meaningful contributor, but **not a
single-subject-dominated result** the way the primary n=3 test was (where
SC4011 alone drove the aggregate). This is a genuine improvement in
robustness of the finding.

## 4. Class-level results (mean per-class F1 across 5 seeds, pooled cohort)

| Class | A | B | C | B−A | B−C |
|---|---|---|---|---|---|
| Wake | 0.9686 | 0.9753 | 0.9703 | +0.0067 | +0.0050 |
| N1 | 0.3774 | 0.4036 | 0.3829 | +0.0261 | +0.0207 |
| N2 | 0.7711 | 0.7958 | 0.7805 | +0.0247 | +0.0153 |
| N3 | 0.6312 | 0.5877 | 0.6040 | **−0.0435** | −0.0163 |
| REM | 0.5165 | 0.6665 | 0.5403 | **+0.1500** | +0.1261 |

The primary experiment's N1/REM pattern **generalizes**: REM shows by far
the largest gain (as in the primary cohort), consistent with the expected
relevance of ocular information to REM detection — not offered as causal
proof. N3 is the one class that **regresses** under the aligned-EOG model in
this cohort; this was not observed as a regression in the primary result and
is reported here without smoothing it away.

## 5. Primary vs. secondary interpretation

The secondary holdout **supports** the primary finding: the direction (B >
A, B > C), its consistency (5/5 seeds on both comparisons), and the
N1/REM class pattern all reproduce on an independent, previously-untouched
8-subject cohort using the exact same frozen checkpoints. It also
**meaningfully improves** the primary result's weakest point — subject-level
dominance — since the secondary cohort's effect is not carried by one
outlier subject the way the primary n=3 test was. It does **not** support
any claim of independent-dataset or population-level replication: this is
still the same Sleep-EDF cassette recording protocol, one dataset, 8
additional terrestrial adult subjects.

## 6. Revised Sleep-EDF claim

**Strongest defensible sentence:** "Under a frozen, capacity-matched
protocol, adding a synchronized EOG channel to single-channel EEG improved
5-class sleep-stage macro-F1 on both a primary 3-subject held-out test set
and an independent, prospectively-frozen 8-subject holdout cohort from the
same dataset; a shuffled-EOG negative control confirms the benefit
specifically depends on EEG-EOG temporal alignment rather than the mere
presence of an EOG-shaped input, and this alignment-dependence also
generalizes to the secondary cohort."

**Unsupported claims (still, after this holdout):**
- Independent-dataset or cross-population replication (this is still one
  dataset/recording protocol).
- Any claim of EOG necessity for the final architecture.
- Any claim of astronaut, spaceflight, or microgravity validation.
- Any claim of uniform per-subject benefit (2/8 secondary subjects show
  near-zero or slightly negative deltas; N3 regresses in the secondary
  cohort).
- Any pooled "n=11 test set" headline (primary and secondary are reported
  and must continue to be reported separately).

## 7. Evidence strength

Unchanged category: `replicated-with-control`. Appended qualifier:
`prospective_secondary_holdout_supported` (see
`docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md` SS8 and
`results/sensor_marginal_value_contract.json` →
`experiments.sleep_edf_eeg_eog_sleep_stage.prospective_secondary_holdout`).
The taxonomy category itself was deliberately **not** upgraded — a same-
dataset secondary holdout is stronger same-dataset evidence, not
independent replication, per the frozen methodology rule.
