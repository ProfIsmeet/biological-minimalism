# HMC Bounded n=7 Diagnostic — Real Results

**NOT the canonical full-151 HMC replication result.** Trainer:
`ml/train_hmc_sleep_a_b_c_bounded_n7.py` (versioned from Claude's
full-cohort trainer). Split: `results/hmc_split_stage3_bounded_n7.json`
(train=5/val=1/test=1, the only complete recordings downloaded before
PhysioNet's TLS certificate expired mid-sprint —
`docs/HMC_FULL_COHORT_CERT_EXPIRY_BLOCKER.md`). Real bug found and fixed
before this run succeeded: `ml/datasets/hmc_sleep.py`'s derived-EOG
channel expansion (`docs/STAGE2_4_HOSTILE_REVIEW_ADDENDUM.md` finding #1).

## Exact results (macro-F1, 5 seeds, test = 1 recording, 1034 epochs)

| Model | Mean | SD (ddof=1) |
|---|---|---|
| A (EEG only) | 0.4562 | 0.0353 |
| B (EEG+EOG) | 0.4249 | 0.0774 |
| C (EEG+shuffled-EOG) | 0.4169 | 0.0489 |

- **B−A**: mean **−0.0313**, only **2/5 seeds favor B**.
- **B−C**: mean +0.0080, **2/5 seeds favor B** (essentially a coin flip).

Parameter counts confirmed capacity-matched (A=8197, B=C=8309 — B and C
identical, as required).

## Interpretation — negative-leaning, honestly reported

At this bounded n=7 (and critically, only **one test recording**, so all
seed-to-seed variance reflects one recording's own epoch-level noise, not
genuine between-subject variance), **the Sleep-EDF EOG benefit did not
reproduce.** Per the frozen protocol's own predeclared
`negative_result_policy` (`results/hmc_protocol_stage1b.json`):

> "the Sleep-EDF EOG benefit did not reproduce on HMC's clinical cohort" —
> a real, retained negative result, not discarded.

This is reported exactly as that predeclared outcome, not softened, not
retrained to chase a positive result, and explicitly not generalized to
the full 151-recording cohort. With n=7 (1 test recording), this is far
too small a sample to conclude anything about whether EOG genuinely fails
to help on HMC's clinical population — it only shows that at this
diagnostic scale, no positive effect appeared. The `interaction_term`-style
statistical caution that applies to Sleep-EDF's n=3 test subjects applies
here even more strongly (n=1 test recording).

## What this diagnostic does and does not establish

**Does establish**: the HMC loader (after the real bug fix), trainer,
capacity-matching, and control design all run correctly end-to-end on real
data, producing a real, deterministic, non-degenerate 5-class prediction
distribution.

**Does not establish**: whether EOG genuinely helps or doesn't help on
HMC's full clinical cohort — that requires the full 151-recording split
(`results/hmc_split_stage3_full_cohort.json`), which remains blocked by
the external PhysioNet certificate expiry, not by this project's design or
effort.

## Forbidden claims (unchanged, reaffirmed)

"HMC replicates Sleep-EDF" is never said (true here in either direction —
neither a positive nor negative bounded-n7 result is a "replication"
claim). "EOG is necessary for sleep staging" is never said. See
`results/hmc_protocol_stage1b.json`'s `forbidden_claims`.
