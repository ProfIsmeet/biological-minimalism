# HMC Sleep Staging External Replication Protocol (Stage 1B)

**Classification: GO_WITH_DEPENDENCY**

Full machine-readable facts: `results/hmc_actual_file_audit_stage1b.json`,
`results/hmc_protocol_stage1b.json`.

## Scientific purpose

Independent-family replication of EEG-only vs EEG+aligned-EOG vs
EEG+shuffled-EOG, using the H1-corrected seed-before-model-init protocol
from the start (not retrofitted). This is a new dataset family, not a
continuation of Sleep-EDF training.

## Actual-file verification summary

Directly fetched the PhysioNet v1.1 page and the RECORDS index. **151
recordings, confirmed one recording per unique subject** (RECORDS shows
sequential SN001–SN154 minus two gaps, no repeat-night suffixing) — this
explicitly checks and clears the master prompt's warning not to assume
"151 recordings = 151 unique subjects." All channels (EEG/EOG/EMG/ECG) share
one native 256 Hz rate, confirmed directly rather than assumed given the H2
lesson about per-channel native-rate mismatches.

## Frozen EEG derivation: C4/M1

Chosen over F4/M1, O2/M1, and C3/M2 as the closest anatomical analog to
Sleep-EDF's central placement, before any training. Not reconsidered after
results.

## Frozen EOG: E1/M2 minus E2/M2

Fixed polarity, no per-subject sign flipping; missing-channel recordings are
excluded (data-integrity rule).

## Split

Recording-wise k-fold (== subject-wise, since the two are 1:1 for this
dataset — no repeat-night grouping logic needed).

## Why GO_WITH_DEPENDENCY, not plain GO

The dataset and design have no scientific blocker. The dependency is
workflow-only: full HMC training should wait until Claude/Emir's Stage 1A
Sleep V2 protocol is frozen (Section 29), so this replication is built on a
stable Sleep protocol rather than one still in flux under parallel
integration work.

## Metric

Primary: Macro-F1. Secondary: balanced accuracy, per-class F1.

## Negative-result and forbidden-claim policy

See `results/hmc_protocol_stage1b.json` and
`docs/STAGE1B_EXPANSION_FORBIDDEN_CLAIMS.md`.
