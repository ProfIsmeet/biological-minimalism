# Next Target-Specific Experiment — Predeclaration (Day 6)

**This document is written and frozen BEFORE any next-target training is
run.** No training for the recommended experiment below has been performed.
Its purpose is to prevent post-hoc protocol changes once results exist —
exactly the discipline this project applied to PPG-DaLiA and PTT.

---

## 1. Candidate dataset review

Reviewed against: scientific importance to Biological Minimalism, real
dataset availability, candidate-sensor availability, ground-truth quality,
subject identity, synchronization, ability to support a genuine baseline-
vs-candidate marginal-value experiment, feasibility within remaining
project time, and risk of overclaiming.

| Dataset | Target | Decision | Why |
|---|---|---|---|
| **Sleep-EDF (sleep-cassette)** | Sleep stage (5-class) | **ACCEPT FOR NEXT EXPERIMENT** | Already real, open, downloaded (3 subjects so far, ~150 available); already has a working single-channel-EEG baseline (72.6% held-out accuracy, `ml/train_sleep_edf.py`); a second synchronized channel (`EOG horizontal`) exists in the same files at the same 100Hz clock, unused so far — a clean, low-risk "add one channel" ablation, structurally identical to PPG-DaLiA/PTT's proven pattern. |
| **BIDMC PPG+Resp** | Respiration rate | DEFER | Real, open, already downloaded (53 subjects) and has a real per-second respiration-rate ground truth (bedside monitor) plus a real synchronized ECG channel in the same files (`*_Signals.csv`: PLETH + II/V/AVR) — a genuine PPG-only vs PPG+ECG ablation is possible. Deferred, not rejected, because the existing single-modality PPG-only respiration result was already found weak (did not beat a naive baseline per `datasets/DATASET_MATRIX.md`) — starting a new ablation on a baseline already known to be barely functional raises real risk-of-overclaiming/uninterpretable-result concerns that should be weighed by the team before committing scarce remaining time to it. |
| **STEW (EEG workload)** | Cognitive workload | DEFER | Real dataset exists (IEEE DataPort, labeled "Open Access"), checked directly today (`curl -I`/`curl` against the live page) - but IEEE DataPort gates actual file download behind an account/login, unlike PhysioNet's anonymous access. No account was created (out of scope for this pass). Would need genuine credentialed access verification before any further planning - same "do not assume access" standard as PulseDB. Also has no existing project loader/audit at all, unlike Sleep-EDF/BIDMC. |
| **QDE (bio-impedance + temperature)** | Fluid shift / hydration | ALREADY ADEQUATELY TESTED | Real training run already complete (`ml/train_bioimpedance.py`): small-N (10 subjects) null/negative result already reported honestly. Re-running would not be a new ablation (no untested candidate-component question remains) without a substantially different framing than this project has scoped time for. |
| **PulseDB** | Cuffless BP | REJECT (unchanged) | Confirmed technically reachable but impractical (~100GB+, credential-gated curated subset) per Day 2's `datasets/CARDIO_DATASET_DECISION_DAY2.md`; no new information since then. |
| **HeartCycle** | Cardiac timing (PEP/PAT) | REJECT (unchanged) | Frozen Day 1 verdict stands: only 4/17 subjects have PPG, records are short snippets, ground truth inconsistently populated. `datasets/HEARTCYCLE_AUDIT.md`. |

## 2. Recommended next target: sleep stage classification, single-channel EEG vs EEG+EOG (Sleep-EDF)

**Research question:** Does adding a synchronized EOG channel improve
5-class sleep-stage classification over single-channel EEG alone?

This mirrors the project's own proven structure (PPG-DaLiA: PPG vs
PPG+IMU; PTT: one PPG site vs two) applied to a genuinely different target
(sleep stage, not heart rate) and a genuinely different modality (EEG/EOG,
not PPG/IMU) — real target-portfolio diversification, not a fourth HR
experiment.

## 3. Frozen protocol (to be implemented, NOT executed, in this Day 6 pass)

- **Dataset**: PhysioNet Sleep-EDF (sleep-cassette), open access, no login.
- **Target**: 5-class sleep stage (Wake, N1, N2, N3, REM), from the real
  hypnogram annotation shipped with the dataset — never self-scored.
- **Baseline configuration**: single-channel `EEG Fpz-Cz`, 100 Hz.
- **Candidate component**: `EOG horizontal`, 100 Hz, same file, same clock.
- **Candidate configuration**: `EEG Fpz-Cz` + `EOG horizontal` (2 channels).
- **Channels excluded from both configurations** (kept out of the primary
  ablation, exactly as IMU/temperature/pressure were excluded from the PTT
  PPG-site ablation): `EEG Pz-Oz`, `Resp oro-nasal`, `EMG submental`,
  `Temp rectal`, `Event marker`.
- **Window**: 30 seconds (the dataset's own native epoch length — this is
  not a free parameter; PSG sleep staging is scored in fixed 30s epochs by
  convention and by the hypnogram file's own structure), no stride/overlap
  (non-overlapping 30s epochs, matching the annotation granularity exactly
  - unlike the continuous-signal HR experiments, there is no windowing
  choice to freeze here beyond "use the annotation's own epoch boundaries").
- **Sampling rate**: 100 Hz (native to both channels, shared clock —
  verified in `datasets/sleep-edfx/README.md`; no resampling needed).
- **Subjects**: expand beyond the current 3 downloaded subjects before
  training - a subject-wise train/val/held-out-test split requires more
  than 3 subjects to be defensible (3 subjects cannot support a train/val/
  test partition with the same rigor as PPG-DaLiA's 10/2/3 or PTT's
  15/3/4). Recommend downloading at minimum ~15-20 subjects from the
  ~150 available in sleep-cassette before this experiment begins - this is
  a data-acquisition step for a FUTURE authorized run, not performed here.
- **Split**: subject-disjoint, seeded (seed 42, matching project
  convention), exact partition to be frozen and recorded before training,
  not after.
- **Preprocessing**: per-epoch, per-channel z-score (matching this
  project's standing per-window normalization convention); no filtering
  beyond what `ml/datasets/sleep_edf.py`'s existing loader already does
  (reused, not reimplemented).
- **Model family**: `Conv1DEncoder` (unmodified, from
  `backend/app/ml/models.py`) + classification head - the same encoder
  class already used for the existing single-channel baseline, with
  `in_channels` = 1 (baseline) or 2 (candidate) - the same "vary only
  input channel count" pattern used for the PTT ablation's
  `PPGSiteHRModel`.
- **Training seeds**: 5 seeds (42, 43, 44, 45, 46), matching the Day 6
  replication convention - planned as multi-seed from the start this
  time, not retrofitted after a single-seed flagship result.
- **Optimizer/loss**: to be frozen identically to the existing
  `train_sleep_edf.py` script's choices (reused, not re-derived) once that
  script is extended - not a new arbitrary choice.
- **Primary metric**: macro-averaged F1 (or balanced accuracy) across the
  5 sleep-stage classes - NOT raw accuracy, because sleep-stage classes
  are naturally imbalanced (much more N2 than N1, for example) and raw
  accuracy would reward the majority class.
- **Secondary metric**: per-class F1/recall (analogous to this project's
  MAE-primary/RMSE-secondary convention, adapted for a classification
  target) and a confusion matrix.
- **Aggregation**: overall, per-subject, per-sleep-stage, mirroring the
  PPG-DaLiA/PTT stratification pattern exactly.
- **Success interpretation** (frozen now): candidate (EEG+EOG) improves
  macro-F1 over baseline (EEG-only) consistently across seeds and
  held-out subjects → positive marginal value for EOG, analogous to the
  PPG-DaLiA outcome. Consistent non-improvement or degradation → negative
  marginal value, exactly as valid and reportable as the PTT result.
- **Failure interpretation** (frozen now): mixed/seed-inconsistent
  direction → MIXED, not forced into positive or negative.
- **Claim boundary** (frozen now): this would establish EOG's marginal
  value for sleep-stage classification on Sleep-EDF only - not for any
  other target, not for astronaut/spaceflight sleep monitoring, not
  clinically validated, and (per the cross-dataset comparability rule)
  never numerically ranked against the PPG-DaLiA or PTT HR results.

## 4. Rejected/deferred alternatives (recap)

- BIDMC PPG+ECG→respiration: deferred, real risk that the already-weak
  PPG-only respiration baseline makes the marginal-value question hard to
  interpret cleanly; a legitimate candidate for a future pass if the team
  wants respiration coverage despite this risk.
- STEW: deferred pending credentialed IEEE DataPort access verification;
  no project loader/audit exists yet.
- QDE: already tested; a genuine new ablation question was not identified.
- PulseDB, HeartCycle: rejected, unchanged from prior audits.

## 5. Confirmation

**No training for this predeclared experiment was performed in Day 6.**
This document exists so that if/when it is authorized, the protocol above
is already frozen and cannot be quietly adjusted after results are seen.
