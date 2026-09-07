# Sleep-EDF Prospective Secondary Holdout — Predeclaration

**Frozen BEFORE any evaluation, prediction, or content inspection of the
secondary-holdout subjects. Frozen before the corresponding raw files for
these subjects were even downloaded to this machine.**

This document exists to prevent outcome-driven cohort selection. Do not edit
the cohort list after evaluation results are known.

## 1. Why this cohort is needed

The primary frozen Sleep-EDF experiment (`ml/experiments/sleep_edf_eeg_eog_ablation/subject_split.json`)
has only 3 held-out test subjects (SC4011, SC4081, SC4131), and the Day-8
per-subject analysis (`results/sleep_edf_per_subject_analysis.json`) already
disclosed that the aggregate aligned-EOG benefit is concentrated in one of
those three (SC4011). n=3 is too small to assess whether the effect
generalizes. This holdout adds independent subject evidence **without**
touching the original n=3 test set.

## 2. Subject eligibility audit (performed before touching content)

Local `datasets/sleep-edfx/raw/` was audited by filename only (no signal or
label content read) against the PhysioNet Sleep-EDFx "sleep-cassette" file
index (`SHA256SUMS.txt`, fetched fresh from
`https://physionet.org/files/sleep-edfx/1.0.0/SHA256SUMS.txt`).

Sleep-Cassette filenames follow `SC4ssNEO-PSG.edf`, where `ss` is the
**subject index** and `N` is the **night number** (1 or 2) for that same
subject. This matters: `SC4002` is subject `00`'s **second night**, i.e. the
same individual as `SC4001` (already in the primary **train** set) — not an
independent subject. It is therefore excluded from consideration, not
included as "untouched."

| Category | Subject indices | Filenames |
|---|---|---|
| Primary train | 00,03,05,06,07,09,10,11,12,14,16,17 | SC4001,4031,4051,4061,4071,4091,4101,4111,4121,4141,4161,4171 |
| Primary val | 02,04,15 | SC4021,4041,4151 |
| Primary test (frozen, never touched again) | 01,08,13 | SC4011,4081,4131 |
| Excluded — same person as a used subject | 00 (night 2) | SC4002 |
| **Untouched candidates found locally** | none | (all locally downloaded PSGs map to subjects 00-17, all already used above) |

Because zero eligible untouched subjects existed on this machine, the
PhysioNet Sleep-EDFx **sleep-cassette** file index (same dataset, same
distribution point already used and cited by this project — not a new
dataset) was queried for additional subject indices. Selection criterion,
fixed **before** inspecting any signal/label content:

- Same recording-code family as every subject in the primary split (`...E0`
  PSG / `E?`-suffixed hypnogram — the "study E" cassette batch). Subjects
  encoded `F0`/`G0` (batch F/G, a later recording round) are excluded to
  avoid introducing an unrelated equipment/protocol shift as a confound.
- First night only (`N=1`), consistent with every primary-split subject.
- Subject index not in {00,01,02,03,04,05,06,07,08,09,10,11,12,13,14,15,16,17}
  (i.e., strictly outside the primary train/val/test index range).
- File exists and downloads with a byte-exact `Content-Length` match (a
  metadata/integrity check, not an outcome check).

This produced subject indices **18–25** (8 subjects) as the full contiguous
block of untouched, same-protocol, first-night subjects immediately
following the primary split's index range. All 8 were included — no
subsetting by any criterion that could be outcome-related.

## 3. Frozen cohort (exact IDs)

| Subject prefix | PSG file | Hypnogram file |
|---|---|---|
| SC4181 | SC4181E0-PSG.edf | SC4181EC-Hypnogram.edf |
| SC4191 | SC4191E0-PSG.edf | SC4191EP-Hypnogram.edf |
| SC4201 | SC4201E0-PSG.edf | SC4201EC-Hypnogram.edf |
| SC4211 | SC4211E0-PSG.edf | SC4211EC-Hypnogram.edf |
| SC4221 | SC4221E0-PSG.edf | SC4221EJ-Hypnogram.edf |
| SC4231 | SC4231E0-PSG.edf | SC4231EJ-Hypnogram.edf |
| SC4241 | SC4241E0-PSG.edf | SC4241EC-Hypnogram.edf |
| SC4251 | SC4251E0-PSG.edf | SC4251EP-Hypnogram.edf |

Cohort size: **n = 8** subjects.

## 4. Inclusion / exclusion criteria (restated, frozen)

**Inclusion:** subject index 18–25 inclusive; `E`-batch, first-night
recording; PSG + hypnogram both present on PhysioNet; downloaded file size
matches the server's `Content-Length` exactly.

**Exclusion:** any subject index already used in primary train/val/test
(00–17, all excluded); any subject who is the same *person* as an already-used
subject even under a different filename (night-2 recordings of subjects
00–17); `F`/`G`-batch subjects (different recording round); any subject whose
download fails integrity verification (to be checked before evaluation, not
after seeing results — if a file fails, it is dropped and the reduced cohort
size is reported honestly, never backfilled with a different subject chosen
after peeking at results).

**No outcome-based selection occurred or will occur.** No prediction, macro-F1,
or per-class metric was computed for any of these 8 subjects before this
document was written.

## 5. Models — evaluation only, no retraining

Reuse the existing frozen checkpoints, unmodified:

- `ml/checkpoints/sleep_edf_baseline_eeg_only_seed{42..46}.pt` (Model A)
- `ml/checkpoints/sleep_edf_candidate_eeg_plus_eog_seed{42..46}.pt` (Model B)
- `ml/checkpoints/sleep_edf_model_c_shuffled_eog_seed{42..46}.pt` (Model C)

All 5 seeds (42–46) are used. No seed is dropped after viewing results. No
hyperparameter is tuned. No retraining occurs on secondary-holdout data.

The shuffled-EOG logic for Model C reuses `shuffle_eog_within_subject()` from
`ml/datasets/sleep_edf.py` unmodified, applied per-subject exactly as in the
primary control (`docs/SLEEP_EDF_SHUFFLED_EOG_PREDECLARATION.md`), seeded
identically per training seed.

## 6. Metrics

Primary: macro-F1.
Secondary: balanced accuracy, accuracy, per-class F1 (Wake/N1/N2/N3/REM),
confusion matrix. Subject-level reporting is mandatory for every subject in
this cohort — no subject's result may be omitted regardless of direction.

## 7. Predeclared outcome interpretation (frozen)

- **Outcome 1 — B > A and B > C broadly:** the aligned-EOG effect generalizes
  beyond the original 3 primary-test subjects under the same frozen
  model/protocol. Still single-dataset, terrestrial, n=8.
- **Outcome 2 — B > C but B ≈ A:** temporal alignment remains informative
  relative to the shuffled control, but incremental value over EEG-only is
  weak in this cohort.
- **Outcome 3 — B > A but B ≈ C:** the added channel may help, but temporal
  alignment specifically is not clearly responsible in this cohort.
- **Outcome 4 — B ≈ A ≈ C:** the original positive result does not generalize
  strongly to this cohort.
- **Outcome 5 — B < A or B < C:** the original positive result is
  cohort-sensitive and must be reported as weakened. This is a scientifically
  acceptable outcome. No retuning follows from it.

## 8. Primary/secondary separation rule

The primary frozen test (n=3) and this secondary holdout (n=8) are reported
**separately** in all artifacts. They are never merged into a single
"n=11 test set" headline result. A pooled descriptive summary, if produced,
must be labeled explicitly `post-hoc pooled descriptive analysis` and never
substitutes for the primary/secondary distinction.
