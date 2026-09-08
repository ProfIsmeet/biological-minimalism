# Sleep-EDF Respiration Native Sampling Rate — Provenance Correction (Day 12, H2)

## What was wrong

`docs/INTERACTION_EXPERIMENT_FEASIBILITY_DAY10.md` and a code comment in
`ml/datasets/sleep_edf.py` stated that Resp oro-nasal has "the same 100 Hz
sample rate as EEG/EOG." This is **incorrect**. Both have now been
corrected (with the original doc text struck through, not silently
deleted, to preserve what the feasibility audit actually said at the
time).

## Verified facts

Verified directly from the EDF file's own header fields
(`n_samps_per_record` / `record_length`), read via MNE's internal
`raw._raw_extras[0]` — **not** via `raw.info['sfreq']`, which reports one
global rate for the whole file and is what caused the original error:

| Channel | Samples per 30s record | Native rate |
|---|---|---|
| EEG Fpz-Cz | 3000 | **100 Hz** |
| EEG Pz-Oz | 3000 | **100 Hz** |
| EOG horizontal | 3000 | **100 Hz** |
| Resp oro-nasal | 30 | **1 Hz** |
| EMG submental | 30 | 1 Hz |
| Temp rectal | 30 | 1 Hz |

`raw.info['sfreq']` reports `100.0` for the file regardless of which
channels are selected — this is `LOADED_COMMON_GRID_RATE`, not
`NATIVE_SIGNAL_RATE`. The two must never be conflated; they were, in the
original feasibility audit.

## MNE's actual resampling behavior (verified from source, not assumed)

`mne.io.edf.edf._read_segment_file` (installed MNE 1.12.1, per
`results/environment_manifest.json`): when channels with different native
sample counts are loaded together, MNE reads each channel at its own
native rate, then — **after all chunks are loaded, to avoid edge
artifacts** — calls `resample(ones[i, :smp_read], smp_exp, smp_read,
npad=0, axis=-1)` for any channel whose sample count is below the file's
maximum. This is `mne.filter.resample`, an **FFT-based** resampling
(zero-padded, no `preload=False`-specific edge-artifact risk since this
project's loader always uses `preload=True` — verified via `grep -n
preload ml/datasets/sleep_edf.py`, both call sites use `preload=True`).

This is **not** simple sample-and-hold repetition and **not** naive linear
interpolation. It is a legitimate signal-processing technique, but it
cannot manufacture information above the Nyquist frequency of the
original 1 Hz signal (~0.5 Hz) — the FFT-resampled 100 Hz array is a
smooth reconstruction of a low-bandwidth signal, not a genuine 100 Hz
physiological measurement.

## Three distinct rates, now explicit

Recorded as new constants in `ml/datasets/sleep_edf.py`:

- `NATIVE_SIGNAL_RATE`: `RESP_NATIVE_SFREQ_HZ = 1.0` Hz (what the sensor
  actually sampled at) vs. `EEG_EOG_NATIVE_SFREQ_HZ = 100.0` Hz.
- `LOADED_COMMON_GRID_RATE`: `RESP_LOADED_SFREQ_HZ = 100.0` Hz (what MNE's
  `raw.get_data()` returns for Resp after FFT-based upsampling).
- `MODEL_INPUT_RATE`: 100 Hz — identical to the loaded common grid, since
  `load_dataset_windows_multi` windows all requested channels together at
  whatever MNE returns, with no further resampling of its own.

## Does this require retraining?

**No.** The interaction training script
(`ml/train_sleep_edf_interaction_resp.py`) has always called
`load_dataset_windows_multi(..., preload=True)`, which has always produced
exactly this FFT-upsampled 100 Hz Resp array — the same array the M_B and
M_AB models in `results/sleep_edf_interaction_resp_day10.json` were
trained on. The corrected metadata constants added to
`ml/datasets/sleep_edf.py` are purely additive (new module-level
constants and comments only) — no function body in the loader
(`load_subject_windows_multi`, `load_dataset_windows_multi`) was touched,
confirmed by direct code review of the diff. The loader was re-run after
the edit (`load_dataset_windows_multi(channels=(EEG_CHANNEL, RESP_CHANNEL),
subject_ids=['SC4001'])`) and produces a real, correctly-shaped array
((2650, 2, 3000)) with no errors, confirming the change did not break or
alter the loading path (see `results/sleep_scientific_remediation_day12.json`,
H2 section).

**H2 is a provenance/wording bug, not a data bug.**

## Information-bandwidth caveat (now made explicit)

A 1 Hz-sampled signal cannot represent frequency content above ~0.5 Hz
regardless of what grid it is later resampled onto. The interaction
model's `M_B`/`M_AB` configurations see a 100-Hz-length tensor for the Resp
channel, but that tensor's actual information content is bounded by the
original 1 Hz acquisition — **not** equivalent in bandwidth to the
genuinely-100-Hz EEG/EOG channels it is concatenated with, despite having
equal tensor length. This is now stated explicitly wherever the
interaction result is described (see
`docs/INTERACTION_EXPERIMENT_RESULTS_DAY10.md` amendment and the Furkan
source package).

## Impact on the interaction result's interpretation

The already-cautious `approximately_additive_or_unresolved` classification
is **not** strengthened by this correction — if anything, it gains an
additional, previously-unstated reason for caution: Resp's low native
bandwidth is a plausible *contributing explanation* for why Candidate B
(Resp alone) showed no clear benefit in
`results/sleep_interaction_sensitivity_day11.json` (mean −0.014, only 2/5
seeds favorable) — the channel may simply carry less exploitable
high-frequency information than EEG/EOG, independent of any interaction
question. This is offered as a plausible explanation, not a proven
mechanism.
