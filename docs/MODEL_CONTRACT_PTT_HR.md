# Model Contract — PTT PPG Site-Value HR Experiment (Day 3, FROZEN)

**Status: contract/loader/split frozen. No trained checkpoint exists yet —
this is the Day 3 preparation deliverable, not a Day 4 trained-model
contract.** See `datasets/PTT_DATASET_AUDIT_DAY3.md` for the full dataset
audit this contract is built on.

## 1. Research question

Does a second physical PPG sensor site provide measurable value for
heart-rate estimation over a single PPG site, evaluated across sitting,
walking, and running? (PhysioNet Pulse Transit Time PPG Dataset v1.1.0.)

## 2. Dataset location

- **Expected local raw path:** `datasets/pulse-transit-time-ppg/raw/`
  (WFDB `.hea`/`.dat`/`.atr` triplets, e.g. `s14_run.hea`). As of Day 3,
  only `s1_sit`, `s1_walk`, `s1_run`, `s13_walk` are downloaded locally
  (used for the smoke test and audit). The remaining 18 subjects' files
  are NOT yet downloaded — see §11 "What Emir/Claude may safely consume."
- **Expected local cache path:** `datasets/pulse-transit-time-ppg/processed/`
  (per-record `.npz`, produced by `preprocess_record()`).
- Both directories are gitignored (matches the existing `datasets/*/*` +
  `!datasets/*/README.md` pattern) — never commit raw or cached PTT data.
- No `BIOMIN_*`-style environment variable exists for this dataset (same
  finding as the PPG-DaLiA handoff) — paths are explicit function
  arguments, not env vars.

## 3. Loader module

`ml/datasets/pulse_transit_time_ppg.py` — the single source of truth for
loading, windowing, and normalizing this dataset. Key entry points:

- `load_record_raw(raw_dir, subject_id, activity) -> RawRecord` — real WFDB
  parse via the `wfdb` package (added to `ml/requirements.txt`).
- `windowize_record(raw: RawRecord) -> RecordWindows` — produces Model A/B
  tensors + HR labels for one record.
- `preprocess_record(raw_dir, cache_dir, subject_id, activity) -> Path` —
  caches one record's windows to `.npz`.
- `load_cached_record(cache_dir, subject_id, activity) -> RecordWindows`.
- `zscore_channels_window(window) -> np.ndarray` — the frozen normalization
  function; do not reimplement.
- `compute_window_hr(rpeak_samples, start, end, fs, min_rpeaks=3)` — the
  frozen ground-truth derivation function; do not reimplement.

## 4. Subject IDs

`s1`..`s22` (22 total, lowercase, no zero-padding — `ALL_SUBJECTS` in the
loader module). This differs from PPG-DaLiA's `S1`..`S15` (uppercase) —
**do not assume the same casing convention across datasets.**

## 5. Activity IDs

`sit`, `walk`, `run` (`ACTIVITIES` in the loader module) — exact official
names, every subject has all three.

## 6. Model A input channels (single-site PPG)

`pleth_1, pleth_2, pleth_3` — red, infrared, green wavelengths, distal
phalanx of the left index finger. Tensor shape per window:
`(3, 4000)` — `(channels, samples)`. Batched: `(batch, 3, 4000)`.

## 7. Model B input channels (two-site PPG)

`pleth_1, pleth_2, pleth_3, pleth_4, pleth_5, pleth_6` — same 3
wavelengths as Model A, plus the same 3 wavelengths from the proximal
phalanx (second physical site). Tensor shape per window: `(6, 4000)`.
Batched: `(batch, 6, 4000)`. **Model A's channels are always the first 3
of Model B's 6, in the same order** (`MODEL_B_CHANNELS[:3] ==
MODEL_A_CHANNELS`, enforced by test).

## 8. Sampling rate

500.0 Hz, shared by every channel and the ECG/R-peak reference — no
resampling anywhere in this pipeline (verified against real files, see
audit §6).

## 9. Window duration / stride

8.0 seconds / 2.0 seconds → 4000 / 1000 samples at 500Hz
(`WINDOW_SECONDS`, `STEP_SECONDS`, `WINDOW_SAMPLES`, `STEP_SAMPLES` in the
loader module). A window is dropped, never padded, if it would run past
the end of the real recording.

## 10. Synchronization semantics

ECG and all 6 PPG channels share one sample index (one 500Hz clock, one
acquisition device) — a window's PPG samples `[t0, t0+8s)` and its HR
label (from R-peaks in the same interval) come from the literal same
underlying recording, no cross-device timestamp alignment needed or
performed.

## 11. Preprocessing function

`zscore_channels_window(window)`: per-channel, per-window z-score
(subtract window mean, divide by window std), self-contained — no
train-set statistics are stored or required at inference time. Applied
identically to Model A's 3 channels and Model B's 6 channels. Raises
`FlatSignalError` if any channel in the window has near-zero variance —
callers must handle this (the loader itself drops such windows during
`windowize_record`, never fabricates a value).

## 12. Ground-truth construction

`compute_window_hr(rpeak_samples, window_start_sample, window_end_sample,
fs, min_rpeaks=3)`: mean instantaneous HR = `60 / mean(RR_intervals_sec)`
over real, manually-verified R-peak annotations (`.atr` files) falling
inside the window. Raises `InsufficientRPeaksError` (window dropped, never
interpolated) if fewer than 3 peaks (2 RR intervals) fall in the window —
did not occur in any of the 4 smoke-tested records across sit/walk/run.
**ECG is used only to compute this scalar label — it is never a tensor fed
to any model.**

## 13. Model interface (Day 3: architecture only, no trained weights)

`ml/train_ptt_ppg_site_ablation.py`:

```python
class PPGSiteHRModel(nn.Module):
    def __init__(self, in_channels: int, embedding_dim: int = 32): ...
    def forward(self, ppg: torch.Tensor) -> torch.Tensor:  # (batch, in_channels, 4000) -> (batch,)
```

Model A = `PPGSiteHRModel(in_channels=3)`. Model B =
`PPGSiteHRModel(in_channels=6)`. Identical `embedding_dim` and all other
hyperparameters for both — the only difference is `in_channels`. No
trained checkpoint exists for either as of Day 3.

### Fairness / capacity policy

Both models use exactly one `Conv1DEncoder` (the project's existing,
unmodified `backend/app/ml/models.py` class) + one `nn.Linear(embedding_dim,
1)` head — no Transformer, no extra layers for Model B, no depth/width
difference. The one acknowledged, disclosed confound: Model B necessarily
has more first-layer input weights than Model A because it has more input
channels — this is the variable under test (the second PPG site), not an
unfair architecture advantage layered on top of it. `embedding_dim` (and
any future hyperparameter) must be set identically for both models in the
eventual full run; do not tune Model B more aggressively than Model A.

## 14. Missing/invalid-input semantics

- Wrong window shape → `ValueError`, immediately.
- Flat/dead channel in a window → `FlatSignalError`, immediately (during
  windowing, such windows are silently dropped from the dataset, not fed
  forward — this is a data-cleaning step, not a runtime API contract for a
  live predictor, since no live inference adapter exists yet for this
  dataset).
- Fewer than 3 R-peaks in a window → `InsufficientRPeaksError`, window
  dropped, never assigned a fabricated HR.
- Missing/incomplete WFDB triplet for a requested record → `wfdb`'s own
  `FileNotFoundError`, not caught or masked.

## 15. Source-of-truth files

- `ml/datasets/pulse_transit_time_ppg.py` — loader, preprocessing,
  normalization, ground-truth derivation (all frozen constants/functions).
- `ml/train_ptt_ppg_site_ablation.py` — model interface + smoke test only.
- `ml/experiments/ptt_ppg_site_ablation/config.json` — frozen experiment
  configuration.
- `ml/experiments/ptt_ppg_site_ablation/subject_split.json` — frozen
  subject-wise train/val/test partition (seed 42, 15/3/4 subjects).
- `ml/tests/test_pulse_transit_time_ppg.py` — 25 passing data-integrity
  and channel-contract tests.
- `datasets/PTT_DATASET_AUDIT_DAY3.md` — the real-file audit this contract
  is built on.

## 16. What Emir/Claude Code may safely consume

- The loader module's public functions (§3) and constants
  (`MODEL_A_CHANNELS`, `MODEL_B_CHANNELS`, `WINDOW_SAMPLES`, `SIGNAL_FS`,
  etc.) — call them directly, do not reimplement.
- The frozen `config.json`/`subject_split.json` as configuration inputs to
  any future training/integration code.
- `PPGSiteHRModel`'s interface (§13) as the model class to instantiate
  once real trained weights exist (they do not yet).

## 17. What Emir/Claude Code must NOT reinterpret or duplicate

- Must not recompute the subject-wise split independently, even with the
  same seed — read `subject_split.json`, the committed file is the source
  of truth.
- Must not reimplement `zscore_channels_window` or `compute_window_hr` —
  import and call them.
- Must not add BP/HR-device/SpO2 sparse metadata as a continuous training
  target for this experiment (see audit §15) — that would require a
  separate, differently-scoped experiment and explicit new authorization.
- Must not use the CSV format as an alternative data source for this
  experiment — the WFDB format is the frozen source (§2, audit §1–3).
- Must not run the full Model A vs. Model B training/evaluation — that
  requires explicit authorization after this Day 3 gate is reviewed (per
  the Day 3 master prompt §19/§21). The smoke test in
  `ml/train_ptt_ppg_site_ablation.py` is not a substitute and its output
  is explicitly labeled "NOT a scientific result."
- Must not modify frontend/backend/replay/WebSocket/dashboard/Digital
  Twin/fault-injection code as part of consuming this contract — if
  integrating this into the live system requires such a change, stop and
  report it rather than making an uncoordinated edit (Day 3 master prompt
  §18).
