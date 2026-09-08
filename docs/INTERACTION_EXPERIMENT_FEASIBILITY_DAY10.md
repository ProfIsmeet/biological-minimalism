# Interaction Experiment Feasibility Audit (Day 10)

> **H2 CORRECTION (Day 12)**: the "same 100 Hz sample rate as EEG/EOG" claim
> in the Candidate B row below is **wrong**. Verified directly from the EDF
> file header: Resp oro-nasal is natively **1 Hz** (30 samples per 30s
> record), not 100 Hz (EEG/EOG are natively 100 Hz - 3000 samples per 30s
> record). MNE's `raw.info['sfreq']` reports a single common-grid rate for
> all channels in the file, which obscures this - it does not mean Resp was
> actually recorded at 100 Hz. See
> `docs/SLEEP_RESPIRATION_RATE_PROVENANCE_DAY12.md` for the full correction.
> The original (incorrect) sentence is left below, struck through, rather
> than silently edited, to preserve what this audit actually said at the
> time it gated the interaction experiment's design.

Formal audit of whether a scientifically legitimate interaction experiment
(baseline, Candidate A, Candidate B, Candidate A+B, same subjects/target/
split, no leakage, capacity-controllable, no new dataset) exists using data
already present in this project. Performed BEFORE any training or
predeclaration of a specific design.

## Hard prohibition check (target leakage)

For every HR target in this project, the ground truth is derived from a
reference channel that must never be reused as a candidate predictor:

- **PPG-DaLiA HR**: ground truth = `data['label']`, real ECG-derived HR from
  the **chest** RespiBAN device (`results/ppg_dalia_imu_ablation.json` →
  `ground_truth_source`). The **chest** ECG/EMG/Resp/Temp channels are
  therefore categorically rejected as candidates for this target - using
  them would make the task circular. Only **wrist**-side signals are
  eligible candidates.
- **PTT HR**: ground truth = ECG R-peak-derived HR from the `ecg` channel
  in each `.hea`/`.dat` record. The `ecg` channel is rejected as a
  candidate for the same reason.
- **Sleep-EDF sleep stage**: ground truth = human-expert hypnogram
  annotations (categorical labels), not a numeric transform of any single
  channel. No channel in this dataset IS the label; the leakage concern
  does not apply here the same way it does for the two HR targets. (A
  softer concern - whether a candidate channel was one of the official
  AASM/R&K scoring inputs - is addressed per-candidate below, since it
  affects interpretability, not leakage validity.)

## Candidate audit

### Candidate 1: PPG-DaLiA — baseline PPG, Candidate A = wrist IMU (ACC), Candidate B = wrist EDA/TEMP

| Field | Value |
|---|---|
| Dataset | PPG-DaLiA |
| Target | Heart rate (bpm), ECG-derived (chest, not a candidate) |
| Baseline | Wrist PPG (BVP), capacity-matched A_cap architecture (28,865 params) |
| Candidate A | Wrist 3-axis accelerometer (ACC) - already characterized (Model B/C, existing frozen checkpoints) |
| Candidate B | Wrist EDA + wrist TEMP (Empatica E4, **confirmed present** in the raw per-subject pickle: `raw['signal']['wrist']['EDA']`, `raw['signal']['wrist']['TEMP']`, both real, genuinely measured, synchronized, 4 Hz, never used by any script in this project to date) |
| A+B availability | Yes - all four signals co-exist in the same per-subject pickle for all 15 subjects |
| Same subjects? | Yes - same 15 subjects, same frozen 10/2/3 split |
| Same timing? | Yes - same recording session per subject |
| Same splits? | Yes - reuse `results/ppg_dalia_imu_ablation.json` train/val/test subject lists |
| Candidate target leakage? | No - EDA/TEMP are wrist sensor channels, not the chest-ECG ground truth |
| Preprocessing ready? | Partial - loader only extracts BVP/ACC today; EDA/TEMP extraction would be new code |
| Architecture capacity fairness achievable? | **Complicated.** EDA/TEMP are sampled at 4 Hz (32 samples per 8s window) vs. PPG's 64 Hz (512 samples) and IMU's 32 Hz (256 samples). The existing capacity-fair convention (one shared `Conv1DEncoder` class, differing only in `in_channels`) assumes all channels share one sequence length. A 4 Hz branch needs either a second, differently-shaped encoder (introducing exactly the kind of architecture-family asymmetry that caused the Day 7 PPG-DaLiA capacity confound) or upsampling EDA/TEMP to 64 Hz (a preprocessing decision with no existing precedent in this project, and defensible either way - not a decision to make casually under time pressure). |
| Checkpoint reuse possible? | Partial - M0 (`ppg_dalia_model_a_cap_seed*`) and M_A (`model_b_ppg_plus_imu_ppg_dalia`/multiseed) are already frozen and reusable; M_B and M_AB require new training AND new architecture design. |
| New training required? | Yes - 2 new configs x 5 seeds = 10 runs, PLUS new architecture design work (not just a config change). |
| Scientific interpretability | Good in principle (EDA is a plausible arousal/stress correlate, TEMP a plausible peripheral perfusion correlate) - but any result would be confounded with whichever ad hoc capacity/upsampling decision is made, undermining the "avoid the Day-7 mistake" mandate. |
| Estimated implementation complexity | **HIGH** - new loader code, new architecture branch, new capacity-fairness design under time pressure. |
| **Verdict** | **`FEASIBLE_BUT_NOT_WORTH_DAY10`** - technically possible, but the sample-rate mismatch makes honest capacity-fairness materially harder to guarantee than a "modest implementation burden" should require. Deferred, not rejected. |

### Candidate 2: PTT — baseline one PPG site, Candidate A = second PPG site (existing), Candidate B = wrist/sensor-site IMU (accelerometer + gyroscope)

| Field | Value |
|---|---|
| Dataset | PhysioNet Pulse Transit Time PPG Dataset v1.1.0 |
| Target | Heart rate (bpm), ECG R-peak-derived (the `ecg` channel - not a candidate) |
| Baseline | One PPG site, 3 wavelengths (`pleth_1..3`) - existing frozen Model A |
| Candidate A | Second PPG site, 3 wavelengths (`pleth_4..6`) - existing frozen Model B (already characterized: negative aggregate, s2-sensitive, heterogeneous 2/4 subjects) |
| Candidate B | 3-axis accelerometer + 3-axis gyroscope (`a_x,a_y,a_z,g_x,g_y,g_z`), **confirmed present** in every `.hea` header at the same 500 Hz sample rate as the PPG/ECG channels |
| A+B availability | Yes - all channels co-exist in the same multiplexed `.dat` file per subject/activity |
| Same subjects? | Yes - same 22 subjects, same frozen 15/3/4 split |
| Same timing? | Yes - same recording |
| Same splits? | Yes - reuse `results/ptt_ppg_site_ablation.json` `subject_split` |
| Candidate target leakage? | No - IMU is a motion channel, unrelated to the ECG ground truth |
| Preprocessing ready? | Mostly - same 500 Hz sample rate as existing PPG channels means the IMU channels can be added to the SAME `Conv1DEncoder`-based model class used for Model A/B (`in_channels` change only, the exact capacity-fair convention already used for this experiment) with no sample-rate mismatch. Loader would need a small extension to read the 6 additional channel names via `wfdb`. |
| Architecture capacity fairness achievable? | **Yes, cleanly** - same shared-encoder-class convention already in use for this experiment. |
| Checkpoint reuse possible? | Yes - M0 (existing Model A) and M_A (existing Model B, second site) are already frozen; only M_B and M_AB need new training. |
| New training required? | Yes - 2 new configs x 5 seeds = 10 runs, low architectural risk. |
| Scientific interpretability | Weaker than it looks: Candidate A (second PPG site) is itself a **heterogeneous, s2-sensitive, small-n(4) negative** result (`docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md` appendix / `results/ptt_sensitivity_analysis.json`). Any interaction term built on top of an already-unstable base effect inherits that instability - a positive or negative interaction reading here would be hard to trust given how easily the underlying A effect flips (excluding s2 alone flips its sign). |
| Estimated implementation complexity | LOW-MEDIUM (small loader extension, reuses existing model/training code). |
| **Verdict** | **`FEASIBLE_BUT_NOT_WORTH_DAY10`** - technically clean and low-complexity, but building on a known-unstable base effect undermines the trustworthiness goal this sprint is explicitly optimizing for. Deferred in favor of a design built on a more stable base effect. |

### Candidate 3: Sleep-EDF — baseline EEG, Candidate A = EOG (existing), Candidate B = Resp oro-nasal

| Field | Value |
|---|---|
| Dataset | PhysioNet Sleep-EDFx sleep-cassette |
| Target | 5-class sleep stage, human hypnogram-scored |
| Baseline | EEG Fpz-Cz only - **existing frozen Model A** (`sleep_edf_baseline_eeg_only_seed{42-46}.pt`) |
| Candidate A | EOG horizontal - **existing frozen Model B** (`sleep_edf_candidate_eeg_plus_eog_seed{42-46}.pt`), already validated with a matched shuffled-EOG negative control (Day 8) AND a prospective secondary holdout (Day 9) - the single most rigorously validated effect in this project |
| Candidate B | Resp oro-nasal - **confirmed present** in every Sleep-EDFx cassette recording used by this project, ~~same 100 Hz sample rate as EEG/EOG~~ **[H2 CORRECTION: natively 1 Hz, upsampled to the 100 Hz common grid by MNE's FFT-based resampling on load - see docs/SLEEP_RESPIRATION_RATE_PROVENANCE_DAY12.md]**, genuinely measured, never used by any script in this project to date |
| A+B availability | Yes - EEG, EOG, and Resp all co-exist in the same PSG file for every subject |
| Same subjects? | Yes - same frozen 12/3/3 primary split (`ml/experiments/sleep_edf_eeg_eog_ablation/subject_split.json`) |
| Same timing? | Yes - same recording, same 30s epoch windowing |
| Same splits? | Yes |
| Candidate target leakage? | No - the label is a categorical stage assigned by a human expert, not a transform of any one channel. Softer concern: Resp oro-nasal is **not** one of the official AASM/R&K sleep-staging scoring channels (those are EEG+EOG+chin EMG) - unlike EOG, which legitimately was part of the official scoring protocol, Resp is a genuinely orthogonal information source with respect to how the ground-truth labels were originally produced. This makes it, if anything, the more scientifically interesting and less "expected" candidate. |
| Preprocessing ready? | **Yes, fully** - `ml/datasets/sleep_edf.py`'s `load_dataset_windows_multi(channels=...)` already accepts an arbitrary channel tuple; passing `(EEG_CHANNEL, RESP_CHANNEL)` or `(EEG_CHANNEL, EOG_CHANNEL, RESP_CHANNEL)` requires zero loader changes. "Zero loader changes" is about code, not signal bandwidth - MNE's `read_raw_edf` transparently upsamples Resp's native 1 Hz to the 100 Hz common grid (see H2 correction above); this is what the interaction experiment's models were actually trained on. |
| Architecture capacity fairness achievable? | **Yes, cleanly** - identical `SleepStageClassifier(in_channels=N)` class already used for the 1-channel and 2-channel configs; a 3-channel config is the same class, same convention, already-established capacity-fairness discipline (`capacity_confound_status: AVOIDED_BY_DESIGN` for the existing EEG/EOG pair). |
| Checkpoint reuse possible? | **Yes, half the design is already frozen** - M0 and M_A require zero new training; only M_B (EEG+Resp) and M_AB (EEG+EOG+Resp) need new checkpoints. |
| New training required? | Yes - 2 new configs x 5 seeds = 10 runs, reusing `train_one`/`evaluate_full` from `ml/train_sleep_edf_eeg_eog_ablation.py` unmodified. |
| Scientific interpretability | Strong - tests whether a genuinely independent (non-scoring-protocol) respiratory signal adds information beyond the already-doubly-validated EEG+EOG effect, and whether combining it with EOG is additive, redundant, or super-additive. Builds on this project's single most stable, most-replicated effect rather than a known-unstable one. |
| Estimated implementation complexity | **LOW** - reuses existing loader, existing model class, existing training/eval functions verbatim; only 2 new training configs. |
| **Verdict** | **`CLEAN_AND_FEASIBLE`** |

## Final selection

Exactly one candidate satisfies every criterion (no leakage, same
subjects/target/split, genuinely measured non-leaking modalities,
cleanly-achievable capacity fairness reusing an already-proven convention,
no new dataset, modest implementation burden, and — the deciding factor
between the two technically-clean-and-cheap candidates — a scientifically
sound foundation rather than one built on an already-unstable base effect):

**Sleep-EDF — EEG (baseline) x EOG (Candidate A, existing) x Resp oro-nasal
(Candidate B, new).**

Proceeding to `docs/INTERACTION_EXPERIMENT_PREDECLARATION_DAY10.md` for this
design only. PPG-DaLiA (EDA/TEMP) and PTT (IMU) interaction designs are
explicitly deferred, not rejected - both remain valid candidates for a
future sprint with more design time.
