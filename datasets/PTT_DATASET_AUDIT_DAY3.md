# Pulse Transit Time PPG Dataset — Day 3 Real-File Audit (2026-09-03)

**Verdict: APPROVED** (single-site vs. two-site PPG heart-rate experiment,
with the target reframed exactly as Day 2 proposed and now confirmed
against real downloaded files, not just documentation).

This audit re-verifies Day 2's `datasets/CARDIO_DATASET_DECISION_DAY2.md`
selection against actual downloaded WFDB files (headers, binary signal
data, and annotation files for subjects s1 — all 3 activities — and
s13_walk, the subject flagged by the original authors as ECG-noisy). Day 2
verified access and file *existence*; Day 3 verifies file *content*.

---

## 1–3. Identity

- **Exact name/version:** Pulse Transit Time PPG Dataset, PhysioNet page
  version "1.1.0", but the dataset's own `README.txt` (verified, downloaded
  today) titles itself "Version 1.0.0" internally — a real, harmless
  inconsistency in the source's own metadata, noted for completeness, not
  a data-quality issue.
- **Official source:** https://physionet.org/content/pulse-transit-time-ppg/1.1.0/
  (DOI 10.13026/jpan-6n92). Authors: Mehrgardt, Khushi, Poon, Withana
  (University of Sydney).
- **License:** Open Data Commons Open Database License (ODbL) v1.0 —
  confirmed by downloading and reading the real `LICENSE.txt`.
- **Access mechanism:** open, unauthenticated `curl`/HTTP download, no
  credentials required — confirmed by direct download today.
- **File structure:** root directory has one WFDB triplet per record
  (`sXX_activity.hea` / `.dat` / `.atr`) plus a `RECORDS` index,
  `README.txt`, `LICENSE.txt`, `ANNOTATORS`; a `csv/` subdirectory has an
  equivalent CSV per record plus `subjects_info.csv`. All confirmed by
  directory listing and direct file download.
- **Total size:** WFDB `.dat` files alone ≈ 452 MB for all 66 records
  (measured: one real file = 6,858,702 bytes × 66); the CSV equivalent is
  far larger (one real file ≈ 40 MB × 66 ≈ 2.6 GB). **Decision: use WFDB,
  not CSV**, both for size and because `wfdb.rdrecord`/`rdann` give
  correct, tested parsing without hand-rolling a CSV parser.
- **Exact subject IDs / count:** `s1`..`s22` (verified from the real
  `RECORDS` file, 22 unique subject prefixes, no gaps, no duplicates).
- **Exact record naming:** `sXX_activity` where activity ∈
  `{sit, walk, run}` — verified against the real `RECORDS` file (66 lines,
  22 × 3 exactly) and `SHA256SUMS.txt` (66 `.hea` + 66 `.dat` + 66 `.atr`
  + 67 CSV entries [66 activity CSVs + `subjects_info.csv`] — a complete,
  non-missing file set for every one of the 66 records).

## 4. Activities

Exact official activity names, verified directly from `README.txt` and
`RECORDS`: **sit**, **walk** (README: "stationary walking"), **run**.
Performed "in random order" per subject (per `README.txt` Methods). No
renaming applied anywhere in this project's loader — `ACTIVITIES` constant
uses these exact strings.

## 5. Signal inventory (verified against a real downloaded `.hea` and
   cross-checked with `wfdb.rdrecord`)

| Channel | Meaning | Site | Wavelength | Rate | Units |
|---|---|---|---|---|---|
| `ecg` | 3-lead ECG | chest/torso (per device schematic) | — | 500 Hz | mV |
| `pleth_1` | PPG | distal phalanx (site 1) | red (~660nm) | 500 Hz | NU (arbitrary) |
| `pleth_2` | PPG | distal phalanx (site 1) | infrared (~880nm) | 500 Hz | NU |
| `pleth_3` | PPG | distal phalanx (site 1) | green (~537nm) | 500 Hz | NU |
| `pleth_4` | PPG | proximal phalanx (site 2) | red | 500 Hz | NU |
| `pleth_5` | PPG | proximal phalanx (site 2) | infrared | 500 Hz | NU |
| `pleth_6` | PPG | proximal phalanx (site 2) | green | 500 Hz | NU |
| `lc_1`, `lc_2` | attachment-pressure load cells | site 1 / site 2 | — | 500 Hz (per header; README's "80Hz" is the sensor's native rate before common resampling — see §7) | NU |
| `temp_1`, `temp_2` | PPG sensor temperature | site 1 / site 2 | — | 500 Hz | °C |
| `temp_3` | IMU temperature | wrist/hand unit | — | 500 Hz | °C |
| `a_x`,`a_y`,`a_z` | accelerometer | hand/wrist unit | — | 500 Hz | g |
| `g_x`,`g_y`,`g_z` | gyroscope | hand/wrist unit | — | 500 Hz | °/s |

18 `.dat` channels total — matches `rec.n_sig == 18` verified directly.
`peaks` (R-peak flag, 1/0) is the 19th channel the README describes, but it
is **not** a `.dat` signal — it is stored as a separate WFDB *annotation*
file (`.atr`), and only appears as an explicit CSV column in the CSV
format. This project uses the WFDB `.atr` file via `wfdb.rdann`, not the
CSV `peaks` column.

**Missingness/coverage:** no missing records (66/66 complete, confirmed via
`SHA256SUMS.txt` counts, §1–3 above). No systematic per-subject or
per-activity channel gaps were found in the two real subjects inspected
(s1, s13) — all 18 channels present with real, non-placeholder values in
every record inspected.

**Real discrepancy found and corrected:** `README.txt`'s "Methods" section
says the PPG sensors were "configured to measure... at 1000Hz (multi-LED
mode)" — but the actual `.hea` files and the actual CSV `time` column both
confirm a single, shared **500 Hz** acquisition rate for all 18 channels
(verified directly: `s1_sit.hea` header line `s1_sit 18 500 254026`, and
CSV timestamps 2ms apart). The 1000Hz figure appears to describe the
sensor chip's internal multi-LED sampling capability, not the rate at
which samples were actually written to these files. **This project's
`SIGNAL_FS` constant is 500.0, taken from the real files, not the README
prose.**

**Real discrepancy found, not corrected (informational only, does not
affect this experiment):** `README.txt` states "6 participants were
female," but the actual downloaded `subjects_info.csv` shows 7 female
subjects (s1, s10, s15, s17, s18, s21, s22) and 15 male. Noted for honesty;
gender is not part of this project's ablation design and this discrepancy
has no bearing on the frozen protocol below.

## 6. Synchronization

**Verified directly, not assumed:** every one of the 18 `.dat` channels in
a given record shares one `fs` field in the `.hea` header (500 for every
channel, every record inspected) and — per the README's own hardware
description, corroborated by the single shared sample count in the
header — all 18 channels were read from a common ARM Cortex-M4
microcontroller "within a 2ms window (500Hz)." There is a single sample
index shared by ECG and all six PPG channels: **no resampling or
timestamp-alignment step is needed** to line up ECG with either PPG site —
this is a stronger synchronization guarantee than PPG-DaLiA had (which
needed cross-device alignment between chest ECG at 700Hz and wrist BVP at
64Hz). `.atr` R-peak sample indices are given in this same shared sample
index, confirmed by direct inspection (peak indices fall strictly within
`[0, sig_len)` in every record checked).

Known acquisition-quality caveat (from the dataset authors themselves,
`README.txt` "Limitations"): "for subject 13 the ECG data is particularly
noisy during the walking exercise," and the IMU "occasionally showed
single-sample artifacts, including for temperature." **Directly checked**:
`s13_walk`'s `.atr` R-peak annotations (which the `ANNOTATORS` file states
are "manually verified," i.e. a human corrected any automatic
mis-detections) show no physiologically implausible beat-to-beat jumps
(max consecutive-beat change 13.9 bpm, mean HR 85.0±7.3 bpm) — the raw ECG
waveform noise the authors warn about does not appear to have corrupted
the annotation itself. `s13` is retained in the frozen split (placed in
`train` by the seeded, pre-registered split — see §25) rather than
excluded, since the ground-truth annotation passed this direct check; if a
future full run's per-subject results flag `s13` as anomalous, that would
be a legitimate post-hoc finding, not a preemptive exclusion.

## 7. Missing/corrupt/inconsistent data findings — summary

- 66/66 records present and complete (SHA256SUMS-verified file counts).
- Two real documentation-vs-file discrepancies found and disclosed (§5).
- No missing channels in any inspected record.
- `s13_walk`'s known noise caveat checked directly against its actual
  R-peak annotations — annotation quality looks sound; retained, flagged.
- `lc_1`/`lc_2` header rate reads 500Hz in the actual file even though the
  README's hardware description states the HX711 load-cell amplifier's
  native rate is 80Hz — the file itself is authoritative for this
  project's purposes (all channels are already common-clock-resampled to
  500Hz by the time they reach the distributed `.dat` file); this channel
  pair is not used in the primary contract regardless (see §18–19).

---

## Ground truth

## 11–13. ECG reference / R-peak derivation / temporal alignment

- **Reference:** the dataset's own `.atr` annotation file per record,
  described in `ANNOTATORS` as "manually verified beat annotations" — a
  human-reviewed, independent R-peak reference, not an unverified
  automatic detector output.
- **Derivation method (this project's, frozen):** for a window
  `[t0, t0+8s)` (in the record's native 500Hz sample index), collect all
  annotated R-peak sample indices falling in that half-open interval,
  compute consecutive R-R intervals in seconds, and take
  `HR = 60 / mean(RR_seconds)`. If fewer than `MIN_RPEAKS_IN_WINDOW = 3`
  peaks fall in the window (i.e. fewer than 2 real RR intervals), the
  window is **dropped**, not assigned an interpolated/fabricated HR. See
  `compute_window_hr()` in `ml/datasets/pulse_transit_time_ppg.py`.
- **Real yield check:** across the 4 records smoke-tested (s1 × 3
  activities, s13_walk), average 9.7–12.5 R-peaks per 8-second window —
  comfortably above the 3-peak floor in every activity, including running.
  Zero windows were dropped for insufficient peaks in any of the 4 records
  tested.
- **Temporal alignment:** R-peak sample indices and PPG sample indices
  share the exact same sample clock (§6) — a window's PPG samples
  `[t0, t0+8s)` and its HR label (from R-peaks in that same interval) are
  drawn from literally the same underlying acquisition, no cross-device
  alignment or resampling involved.

## 14. Confirmation ECG never enters model input

Verified in code and by test (`ml/tests/test_pulse_transit_time_ppg.py::
test_ecg_and_peaks_never_in_model_channel_lists`): `MODEL_A_CHANNELS` and
`MODEL_B_CHANNELS` are built exclusively from `pleth_*` names; `windowize_
record()` extracts the ECG/R-peak data only to compute the scalar `hr`
label, never into the `ppg_a`/`ppg_b` tensors returned to the model.

## 15. Why sparse HR/BP/SpO2 metadata are NOT used

Confirmed directly in a real `.hea` comment line (e.g. `s1_sit.hea`:
`<bp_sys_start>: 87 <bp_sys_end>: 87 ... <hr_1_start>: 74 ... <spo2_start>: 98`)
and in `subjects_info.csv`: these are exactly **2 values per ~500-second
recording** (start/end only), sourced from separate consumer devices (an
OMRON cuff monitor and an iHealth pulse oximeter), not from the continuous
ECG. Interpolating or otherwise fabricating a continuous label from 2
points, or using a PPG-adjacent device's own HR reading as ground truth for
a PPG-input model, would both violate this project's no-circular-target
and no-fabricated-label rules. **Not used anywhere in this experiment's
primary target.** (Per the Day 3 master prompt §6, this dataset's sparse BP
values are also explicitly not converted into a continuous BP claim here or
elsewhere in this project.)

---

## Experiment decision

## 16–21.

**Decision: APPROVED.**

**Final research question (unchanged from Day 2, now file-verified):**
*Does a second physical PPG sensor site (proximal phalanx, in addition to
the distal phalanx) provide measurable value for heart-rate estimation
from PPG alone, evaluated across sitting, walking, and running?*

- **Model A (single-site PPG):** channels `pleth_1, pleth_2, pleth_3`
  (all 3 wavelengths — red/infrared/green — from the distal-phalanx site
  only).
- **Model B (two-site PPG):** channels `pleth_1..pleth_6` (all 3
  wavelengths from both the distal and proximal phalanx sites).
- **Wavelength handling:** all 3 available wavelengths are used at every
  site included in a model — no wavelength is cherry-picked, dropped, or
  chosen based on any observed performance (none has been observed as of
  Day 3). Model B's extra 3 channels are exactly the same 3 wavelengths as
  Model A's, from the second physical location — this isolates the
  physical-site variable as cleanly as the real channel topology allows,
  since the alternative (e.g. one wavelength × 2 sites) would have thrown
  away 2 real, physiologically distinct channels for no principled reason.
- **Scientific rationale:** identical to Day 2's, now grounded in real
  files: the dataset offers genuinely synchronized (§6), genuinely
  multi-site (§5) PPG with an independent, high-quality ECG ground truth
  (§11–13), across a real running condition PPG-DaLiA never had.

**Confounders/limitations (disclosed up front, not discovered later):**
- Model B has strictly more input channels (6 vs. 3) than Model A by
  construction — the "marginal value of a second site" and "marginal value
  of more channels" are not perfectly separable from PPG channel count
  alone in this design. This is the same structural situation Priority 2
  faced (PPG+IMU vs. PPG-only differ in channel count too) and is
  disclosed rather than hidden; see `docs/MODEL_CONTRACT_PTT_HR.md`
  "Fairness/Capacity Policy" for how model capacity (not input channel
  count) is held fixed.
- 22 subjects is a moderate sample; per-subject-per-activity held-out
  estimates in the eventual full run will have real, honestly-reported
  uncertainty, not treated as definitive.
- `s13`'s known ECG-noise caveat (§6) — retained, flagged, not excluded.
- IMU/pressure/temperature channels exist in this dataset and are
  deliberately excluded from the primary Model A/B contract (Day 3 master
  prompt §8) to keep the comparison about the second PPG site specifically,
  not a bigger multimodal model.

---

## Frozen protocol

## 22–28.

- **Window duration:** 8.0 seconds (`WINDOW_SECONDS = 8.0`) — same
  convention as the accepted PPG-DaLiA Priority 2 experiment. Justified
  independently for this dataset too: real R-peak density (§13) gives
  9–13 beats per 8s window even during running, well above the 3-peak
  floor for a stable mean-HR label.
- **Stride:** 2.0 seconds (`STEP_SECONDS = 2.0`), matching Priority 2.
- **Sample rate:** 500.0 Hz native, no resampling (§6).
- **Window samples:** 4000 (`WINDOW_SAMPLES = int(8.0 * 500.0)`).
- **Preprocessing:** per-channel, per-window z-score
  (`zscore_channels_window()`), self-contained (no stored/train-derived
  statistics — matches the PPG-DaLiA convention exactly), applied
  identically to all of Model A's 3 channels and Model B's 6 channels — no
  extra smoothing, filtering, or interpolation is applied by default (the
  dataset's own README suggests an optional DC-removal + 0.75–5Hz bandpass
  for those who want filtered-looking data; **not applied here**, to avoid
  introducing a preprocessing step chosen after seeing results, and to
  keep Model A/B preprocessing exactly symmetric).
- **Subject-wise split (frozen, seed=42):** see
  `ml/experiments/ptt_ppg_site_ablation/subject_split.json` — 15 train /
  3 val / 4 test subjects, disjoint, covering all 22 real subject IDs.
  Every subject has all 3 activities recorded, so sit/walk/run coverage is
  automatically present in every split partition — no additional
  stratification was necessary or performed.
- **Activity-stratified evaluation plan (for the future full run, NOT run
  today):** overall held-out MAE/RMSE, per-subject MAE/RMSE, and
  sit/walk/run MAE/RMSE for both Model A and Model B. No assumption is
  made in advance about whether the second-site benefit increases with
  motion — a null or non-monotonic result is an acceptable, reportable
  outcome.
- **Model architecture/interface:** `PPGSiteHRModel` (one
  `Conv1DEncoder(in_channels=N)` + `Linear(embedding_dim, 1)`), identical
  for A/B except `in_channels` (3 vs. 6). No Transformer/fusion module —
  not justified for two channel-groups of the same modality. See
  `docs/MODEL_CONTRACT_PTT_HR.md` for the full interface and fairness
  policy.

---

## What Day 3 has validated vs. left unvalidated

**Validated today, against real files:** dataset identity/access/license,
complete 66/66 record integrity, real channel topology and site/wavelength
mapping, real shared 500Hz synchronization (no resampling needed), real
manually-verified R-peak annotations with physiologically plausible
per-window HR yield across sit/walk/run for 2 subjects (s1, s13), a working
loader with passing data-integrity tests, a frozen subject-wise split, and
an end-to-end smoke test (data → tensors → model forward/backward pass)
for both Model A and Model B.

**Left unvalidated (explicitly out of Day 3 scope):** the actual scientific
question (whether the second site helps) — no full train/held-out-eval run
has been executed; only 2 of 22 subjects' raw files have been downloaded
and inspected in this pass (the remaining 20 are expected, given the
verified-complete `SHA256SUMS.txt` listing and identical `.hea` structure
observed, but not yet individually downloaded/parsed); per-subject/
per-activity signal-quality variation beyond s1/s13 is unknown; no
hyperparameter or architecture-size search has been done or is planned to
favor either model.

**Ready for the full PTT sensor-site ablation:** yes, pending explicit
authorization per the Day 3 master prompt's own gate (§19, §21) — the
protocol above is frozen and, in this auditor's assessment, does not
require further design changes before that authorized run, though
downloading and spot-checking a few more of the remaining 20 subjects
before the full run would further de-risk it (recommended, not required).
