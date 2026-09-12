"""Loader for PhysioNet Sleep-EDF Database Expanded (sleep-cassette study).

Source: Kemp, B., Zwinderman, A. H., Tuk, B., Kamphuisen, H. A. C., & Oberye,
J. J. L. (2000). Analysis of a sleep-dependent neuronal feedback loop: the
slow-wave microcontinuity of the EEG. IEEE Transactions on Biomedical
Engineering, 47(9), 1185-1194. Distributed via PhysioNet:
Goldberger et al. (2000), PhysioBank, PhysioToolkit, and PhysioNet.
https://physionet.org/content/sleep-edfx/1.0.0/

Substituted for WESAD in this project's first real-data training pass: WESAD's
two official distribution points (uni-siegen.sciebo.de share link and the
ubi29.informatik.uni-siegen.de mirror) both returned 404/dead at the time this
was written, and re-verified as such directly (not assumed) before switching.
Sleep-EDF is fully open (no login wall, no application/approval process),
already discussed in this project's PDD (Dataset Research, Section 7) for
respiration/circadian structure, and — usefully — several of its recordings
include real 'Resp oro-nasal' and 'Temp rectal' channels alongside EEG, so it
also gives this project real (if not spaceflight-relevant) respiration and
temperature signal, not just EEG.

Downloaded to `datasets/sleep-edfx/raw/` in this repository (gitignored, not
committed) via `datasets/sleep-edfx/README.md`'s documented curl commands.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# NOTE: `mne` is imported lazily inside the two EDF-reading functions below. It is a
# heavy, optional dependency needed only to parse raw Sleep-EDF PSG/hypnogram files
# (which are gitignored and not present on every machine). Keeping the import lazy
# lets the frozen-artifact / architecture tests run without it.

EPOCH_SECONDS = 30.0
EEG_CHANNEL = "EEG Fpz-Cz"

# Sleep-EDF hypnogram annotation descriptions -> 5-class label used for training.
_STAGE_MAP = {
    "Sleep stage W": 0,
    "Sleep stage 1": 1,
    "Sleep stage 2": 2,
    "Sleep stage 3": 3,
    "Sleep stage 4": 3,  # merged with stage 3 per the standard AASM-era convention
    "Sleep stage R": 4,
}
STAGE_NAMES = ("Wake", "N1", "N2", "N3", "REM")


def find_subject_pairs(dataset_dir: str | Path) -> list[tuple[Path, Path]]:
    """Pair each `*-PSG.edf` file with its matching `*-Hypnogram.edf` file by
    the shared subject/night prefix (e.g. `SC4001`)."""

    dataset_dir = Path(dataset_dir)
    psg_files = sorted(dataset_dir.glob("*-PSG.edf"))
    pairs: list[tuple[Path, Path]] = []
    for psg in psg_files:
        prefix = psg.name.split("E")[0]  # "SC4001E0-PSG.edf" -> "SC4001"
        hyp_matches = list(dataset_dir.glob(f"{prefix}*-Hypnogram.edf"))
        if hyp_matches:
            pairs.append((psg, hyp_matches[0]))
    return pairs


def load_subject_windows(psg_path: Path, hypnogram_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load one subject's EEG, split into 30s epochs aligned to the real
    hypnogram, and return (windows, labels).

    `windows`: float32 array, shape (n_epochs, 1, n_samples_per_epoch) - ready
    for `Conv1DEncoder` (backend/app/ml/models.py), which expects
    (batch, in_channels, sequence_length).
    `labels`: int64 array, shape (n_epochs,), values 0-4 per `STAGE_NAMES`.

    Only real, actually-recorded samples and real hypnogram-scored epochs are
    included; epochs during unscored ("Sleep stage ?") or movement-artifact
    periods are dropped rather than labeled with a guess.
    """

    import mne

    raw = mne.io.read_raw_edf(psg_path, include=[EEG_CHANNEL], preload=True, verbose="ERROR")
    annotations = mne.read_annotations(hypnogram_path)
    raw.set_annotations(annotations, emit_warning=False)

    sfreq = raw.info["sfreq"]
    samples_per_epoch = int(EPOCH_SECONDS * sfreq)
    signal = raw.get_data(picks=[EEG_CHANNEL])[0]  # (n_total_samples,)

    windows: list[np.ndarray] = []
    labels: list[int] = []
    for annot in annotations:
        stage = _STAGE_MAP.get(annot["description"])
        if stage is None:
            continue  # "Sleep stage ?" / movement - real data, deliberately excluded, not guessed
        onset_sample = int(annot["onset"] * sfreq)
        duration_epochs = max(1, int(round(annot["duration"] / EPOCH_SECONDS)))
        for i in range(duration_epochs):
            start = onset_sample + i * samples_per_epoch
            end = start + samples_per_epoch
            if end > len(signal):
                break
            windows.append(signal[start:end])
            labels.append(stage)

    if not windows:
        return np.empty((0, 1, samples_per_epoch), dtype=np.float32), np.empty((0,), dtype=np.int64)

    x = np.stack(windows).astype(np.float32)
    x = (x - x.mean()) / (x.std() + 1e-8)  # per-subject z-score, real signal, no synthetic fill
    x = x[:, None, :]  # (n_epochs, 1, samples_per_epoch)
    y = np.array(labels, dtype=np.int64)
    return x, y


def load_dataset_windows(dataset_dir: str | Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load every subject pair under `dataset_dir` and return
    (windows, labels, subject_ids) - `subject_ids` (one int per epoch,
    matching each epoch to the subject index it came from) is what lets the
    caller do a real subject-level (not epoch-level) train/test split, which
    is the only honest way to estimate generalization for this task."""

    dataset_dir = Path(dataset_dir)
    if not dataset_dir.exists():
        raise NotImplementedError(
            f"Sleep-EDF raw data not found at {dataset_dir}. See "
            "datasets/sleep-edfx/README.md for the download commands. This "
            "project does not ship or fabricate this data."
        )

    pairs = find_subject_pairs(dataset_dir)
    if not pairs:
        raise NotImplementedError(f"No PSG/Hypnogram pairs found under {dataset_dir}.")

    all_x, all_y, all_subject = [], [], []
    for subject_idx, (psg, hyp) in enumerate(pairs):
        x, y = load_subject_windows(psg, hyp)
        all_x.append(x)
        all_y.append(y)
        all_subject.append(np.full(len(y), subject_idx, dtype=np.int64))

    return np.concatenate(all_x), np.concatenate(all_y), np.concatenate(all_subject)


# --- Day 7: multi-channel (EEG+EOG) loader, for the EEG-vs-EEG+EOG marginal-
# value experiment. Additive - does not change load_subject_windows() above,
# which remains exactly as used by the original single-channel training run
# (ml/train_sleep_edf.py, checkpoint ml/checkpoints/eeg_encoder_sleep_edf.pt).

EOG_CHANNEL = "EOG horizontal"

# Day 10: interaction-experiment candidate channel. Real, genuinely measured,
# present in the same PSG files. Not one of the official AASM/R&K sleep-staging
# scoring channels (those are EEG+EOG+chin EMG) - a genuinely independent
# information source relative to how the hypnogram ground truth was
# originally produced. See docs/INTERACTION_EXPERIMENT_FEASIBILITY_DAY10.md.
#
# H2 CORRECTION (Day 12, see docs/SLEEP_RESPIRATION_RATE_PROVENANCE_DAY12.md):
# Resp oro-nasal is NOT natively 100 Hz. Verified directly from the EDF file
# header (n_samps_per_record / record_length, not MNE's raw.info['sfreq']
# which reports one global rate for all channels): EEG/EOG are natively
# 100 Hz (3000 samples/30s record); Resp oro-nasal is natively 1 Hz (30
# samples/30s record). When this loader's mne.io.read_raw_edf() call reads
# multiple channels with different native rates together, MNE upsamples the
# lower-rate channel(s) to the highest native rate present (100 Hz) via
# mne.io.edf.edf._read_segment_file()'s FFT-based `resample()` call - not a
# simple repeat/sample-and-hold, not true 100 Hz acquisition. A 1 Hz-sampled
# signal cannot carry information above ~0.5 Hz (Nyquist) regardless of the
# grid it is later represented on. RESP_NATIVE_SFREQ_HZ / RESP_LOADED_SFREQ_HZ
# below record this explicitly; the training arrays themselves are UNCHANGED
# by this correction (this loader has always called read_raw_edf with
# preload=True, so the FFT-resampled values it has always produced are
# exactly what results/sleep_edf_interaction_resp_day10.json's models were
# trained on - this is a provenance/wording fix, not a data fix).
RESP_CHANNEL = "Resp oro-nasal"
RESP_NATIVE_SFREQ_HZ = 1.0
RESP_LOADED_SFREQ_HZ = 100.0  # common grid after MNE's FFT-based upsampling
RESP_RESAMPLING_METHOD = "FFT-based (mne.io.edf.edf._read_segment_file -> mne.filter.resample, npad=0)"
EEG_EOG_NATIVE_SFREQ_HZ = 100.0


def load_subject_windows_multi(psg_path: Path, hypnogram_path: Path, channels: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray]:
    """Same real epoch/label construction as `load_subject_windows()`
    (identical hypnogram-driven windowing, identical dropped-epoch rule for
    unscored/movement periods), but returns multiple channels and uses
    PER-CHANNEL, PER-WINDOW z-score (this project's standard normalization
    convention - see ml/datasets/ppg_dalia.py, ml/datasets/pulse_transit_time_ppg.py)
    rather than the single-channel loader's per-subject-global normalization.
    This is a deliberate, disclosed choice for this new experiment - it does
    not change the original single-channel training run's preprocessing.

    `windows`: float32 array, shape (n_epochs, len(channels), n_samples_per_epoch).
    `labels`: int64 array, shape (n_epochs,), values 0-4 per STAGE_NAMES.
    """

    import mne

    raw = mne.io.read_raw_edf(psg_path, include=list(channels), preload=True, verbose="ERROR")
    annotations = mne.read_annotations(hypnogram_path)
    raw.set_annotations(annotations, emit_warning=False)

    sfreq = raw.info["sfreq"]
    samples_per_epoch = int(EPOCH_SECONDS * sfreq)
    signals = raw.get_data(picks=list(channels))  # (len(channels), n_total_samples)

    windows: list[np.ndarray] = []
    labels: list[int] = []
    for annot in annotations:
        stage = _STAGE_MAP.get(annot["description"])
        if stage is None:
            continue
        onset_sample = int(annot["onset"] * sfreq)
        duration_epochs = max(1, int(round(annot["duration"] / EPOCH_SECONDS)))
        for i in range(duration_epochs):
            start = onset_sample + i * samples_per_epoch
            end = start + samples_per_epoch
            if end > signals.shape[1]:
                break
            windows.append(signals[:, start:end])
            labels.append(stage)

    if not windows:
        return np.empty((0, len(channels), samples_per_epoch), dtype=np.float32), np.empty((0,), dtype=np.int64)

    x = np.stack(windows).astype(np.float32)  # (n_epochs, len(channels), samples_per_epoch)
    means = x.mean(axis=2, keepdims=True)
    stds = x.std(axis=2, keepdims=True) + 1e-8
    x = (x - means) / stds
    y = np.array(labels, dtype=np.int64)
    return x, y


def load_dataset_windows_multi(dataset_dir: str | Path, channels: tuple[str, ...], subject_ids: list[str] | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """Same as load_dataset_windows() but multi-channel, and optionally
    restricted to an explicit, pre-frozen list of subject prefixes (e.g.
    ["SC4001", "SC4011", ...]) so the caller controls exactly which
    subjects participate (needed for a frozen, reproducible split) rather
    than picking up whatever happens to be in the raw/ directory.

    Returns (windows, labels, subject_index_per_epoch, subject_prefixes_in_order).
    """

    dataset_dir = Path(dataset_dir)
    if not dataset_dir.exists():
        raise NotImplementedError(f"Sleep-EDF raw data not found at {dataset_dir}.")

    pairs = find_subject_pairs(dataset_dir)
    if subject_ids is not None:
        pairs = [(psg, hyp) for psg, hyp in pairs if psg.name.split("E")[0] in subject_ids]
        found = {psg.name.split("E")[0] for psg, _ in pairs}
        missing = set(subject_ids) - found
        if missing:
            raise FileNotFoundError(f"Requested subjects not found under {dataset_dir}: {sorted(missing)}")

    if not pairs:
        raise NotImplementedError(f"No matching PSG/Hypnogram pairs found under {dataset_dir}.")

    all_x, all_y, all_subject, prefixes = [], [], [], []
    for subject_idx, (psg, hyp) in enumerate(pairs):
        prefix = psg.name.split("E")[0]
        x, y = load_subject_windows_multi(psg, hyp, channels)
        all_x.append(x)
        all_y.append(y)
        all_subject.append(np.full(len(y), subject_idx, dtype=np.int64))
        prefixes.append(prefix)

    return np.concatenate(all_x), np.concatenate(all_y), np.concatenate(all_subject), prefixes


def shuffle_eog_within_subject(x: np.ndarray, subject_idx: np.ndarray, eog_channel_index: int, seed: int) -> np.ndarray:
    """Negative control (Day 8): permutes the EOG channel's epochs among
    THAT SUBJECT'S OWN epochs only, breaking true EEG<->EOG temporal
    correspondence while preserving the real EOG signal distribution.
    Never mixes epochs across subjects or across partitions (the caller
    is expected to invoke this separately per-partition, matching the
    original PPG-DaLiA shuffle_imu_within_subject() convention).

    `x`: (n_epochs, n_channels, samples). `subject_idx`: (n_epochs,) int
    array matching each epoch to its real subject (as returned by
    load_dataset_windows_multi). Deterministic given `seed`; the EEG
    channel and the label array are never touched by this function.
    """

    rng = np.random.default_rng(seed)
    shuffled = x.copy()
    for s in sorted(set(subject_idx.tolist())):
        idx = np.where(subject_idx == s)[0]
        permuted = rng.permutation(idx)
        shuffled[idx, eog_channel_index, :] = x[permuted, eog_channel_index, :]
    return shuffled
