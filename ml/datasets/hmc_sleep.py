"""Loader for the HMC Sleep Staging Database (PhysioNet v1.1).

Source: Alvarez-Estevez, D. & Rijsman, R.M. (2021/2022) Haaglanden Medisch
Centrum sleep staging database. PhysioNet. https://physionet.org/content/hmc-sleep-staging/1.1/

Independent-family external replication dataset for this project's
Sleep-EDF EEG-vs-EEG+EOG finding (Stage 3). Frozen protocol source:
results/hmc_protocol_stage1b.json (Stage 1B, commit fe32384, inspected
read-only from origin/stage1b-dataset-expansion-prep - NOT merged; see
docs/HMC_SLEEP_EXTERNAL_REPLICATION_PROTOCOL_STAGE1B.md).

Frozen, pre-registered choices (see results/hmc_protocol_stage1b.json,
NOT reconsidered after seeing any result):
  - EEG derivation: C4-M1 (channel label confirmed directly from the raw
    EDF header this session: "EEG C4-M1").
  - EOG derivation: E1-M2 minus E2-M2 (channel labels confirmed directly
    from the raw EDF header this session: "EOG E1-M2", "EOG E2-M2").
  - All channels (EEG/EOG/EMG/ECG) share one native 256 Hz rate for this
    dataset (confirmed by Stage 1B's actual-file audit) - unlike Sleep-EDF,
    there is no H2-style per-channel native-rate mismatch to reconcile here.
  - Recording == subject (1:1, confirmed by Stage 1B's actual-file audit;
    RECORDS index has no repeat-night suffixing).

Annotation format is a plain CSV-like text file
(`<recording>_sleepscoring.txt`), NOT an EDF+ annotations channel like
Sleep-EDF's Hypnogram.edf - columns are
`Date, Time, Recording onset, Duration, Annotation, Linked channel`,
confirmed directly from a real downloaded file this session.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

EPOCH_SECONDS = 30.0
EEG_CHANNEL = "EEG C4-M1"
EOG_CHANNEL_1 = "EOG E1-M2"
EOG_CHANNEL_2 = "EOG E2-M2"
EOG_DERIVED_HORIZONTAL = "EOG_DERIVED_HORIZONTAL"
NATIVE_SFREQ_HZ = 256.0  # uniform across all channels for this dataset (Stage 1B audit)

_STAGE_MAP = {
    "Sleep stage W": 0,
    "Sleep stage N1": 1,
    "Sleep stage N2": 2,
    "Sleep stage N3": 3,
    "Sleep stage R": 4,
}
STAGE_NAMES = ("Wake", "N1", "N2", "N3", "REM")


def find_recordings(dataset_dir: str | Path, subject_ids: list[str] | None = None) -> list[tuple[Path, Path]]:
    """Pairs each `SNxxx.edf` signal file with its `SNxxx_sleepscoring.txt`
    annotation file. `subject_ids` (e.g. ["SN001", "SN002"]) restricts to an
    explicit, pre-frozen list (results/hmc_split_stage2.json) - same
    frozen-subject-list convention as ml/datasets/sleep_edf.py's
    load_dataset_windows_multi(subject_ids=...)."""

    dataset_dir = Path(dataset_dir)
    edf_files = sorted(dataset_dir.glob("SN*.edf"))
    edf_files = [p for p in edf_files if "_sleepscoring" not in p.name]
    pairs: list[tuple[Path, Path]] = []
    for edf in edf_files:
        prefix = edf.stem  # "SN001"
        if subject_ids is not None and prefix not in subject_ids:
            continue
        scoring = dataset_dir / f"{prefix}_sleepscoring.txt"
        if scoring.exists():
            pairs.append((edf, scoring))
    if subject_ids is not None:
        found = {p.stem for p, _ in pairs}
        missing = set(subject_ids) - found
        if missing:
            raise FileNotFoundError(f"Requested HMC recordings not found under {dataset_dir}: {sorted(missing)}")
    return pairs


def parse_sleepscoring(scoring_path: Path) -> list[tuple[float, float, int]]:
    """Parses `<recording>_sleepscoring.txt` and returns a list of
    (onset_seconds, duration_seconds, stage_label) for every real
    "Sleep stage X" row. Non-stage rows ("Lights off", "Lights on", any
    other annotation) are skipped - not scored epochs, not guessed."""

    events: list[tuple[float, float, int]] = []
    with open(scoring_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert [c.strip() for c in header][:5] == ["Date", "Time", "Recording onset", "Duration", "Annotation"], (
            f"Unexpected sleepscoring.txt header in {scoring_path}: {header}"
        )
        for row in reader:
            if len(row) < 5:
                continue
            annotation = row[4].strip()
            stage = _STAGE_MAP.get(annotation)
            if stage is None:
                continue
            onset = float(row[2].strip())
            duration = float(row[3].strip())
            events.append((onset, duration, stage))
    return events


def load_recording_windows(edf_path: Path, scoring_path: Path, channels: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray]:
    """Loads one HMC recording, splits into 30s epochs aligned to the real
    technician-scored hypnogram (`_sleepscoring.txt`), and returns
    (windows, labels). Per-channel, per-window z-score normalization -
    same convention as ml/datasets/sleep_edf.py's load_subject_windows_multi().

    `windows`: float32 array, shape (n_epochs, len(channels), n_samples_per_epoch).
    `labels`: int64 array, shape (n_epochs,), values 0-4 per STAGE_NAMES.
    """

    import mne

    needed_raw_channels = sorted({
        raw_c
        for c in channels
        for raw_c in ((EOG_CHANNEL_1, EOG_CHANNEL_2) if c == EOG_DERIVED_HORIZONTAL else (c,))
        if raw_c in (EEG_CHANNEL, EOG_CHANNEL_1, EOG_CHANNEL_2)
    })
    raw = mne.io.read_raw_edf(edf_path, include=needed_raw_channels, preload=True, verbose="ERROR")
    sfreq = raw.info["sfreq"]
    assert abs(sfreq - NATIVE_SFREQ_HZ) < 1e-6, f"Unexpected sample rate {sfreq} Hz in {edf_path} (expected {NATIVE_SFREQ_HZ} Hz per Stage 1B audit)"
    samples_per_epoch = int(EPOCH_SECONDS * sfreq)

    raw_signals = {name: raw.get_data(picks=[name])[0] for name in needed_raw_channels}
    n_total_samples = len(next(iter(raw_signals.values())))

    # Build the requested channel stack, deriving horizontal EOG as
    # E1-M2 minus E2-M2 per the frozen protocol (results/hmc_protocol_stage1b.json).
    channel_signals = []
    for c in channels:
        if c == EOG_DERIVED_HORIZONTAL:
            channel_signals.append(raw_signals[EOG_CHANNEL_1] - raw_signals[EOG_CHANNEL_2])
        else:
            channel_signals.append(raw_signals[c])
    signals = np.stack(channel_signals)  # (len(channels), n_total_samples)

    events = parse_sleepscoring(scoring_path)

    windows: list[np.ndarray] = []
    labels: list[int] = []
    for onset, duration, stage in events:
        onset_sample = int(round(onset * sfreq))
        duration_epochs = max(1, int(round(duration / EPOCH_SECONDS)))
        for i in range(duration_epochs):
            start = onset_sample + i * samples_per_epoch
            end = start + samples_per_epoch
            if end > n_total_samples:
                break
            windows.append(signals[:, start:end])
            labels.append(stage)

    if not windows:
        return np.empty((0, len(channels), samples_per_epoch), dtype=np.float32), np.empty((0,), dtype=np.int64)

    x = np.stack(windows).astype(np.float32)
    means = x.mean(axis=2, keepdims=True)
    stds = x.std(axis=2, keepdims=True) + 1e-8
    x = (x - means) / stds
    y = np.array(labels, dtype=np.int64)
    return x, y


def load_dataset_windows(dataset_dir: str | Path, channels: tuple[str, ...], subject_ids: list[str] | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """Loads every requested recording under `dataset_dir` (or only
    `subject_ids`, e.g. results/hmc_split_stage2.json's frozen lists) and
    concatenates. Returns (windows, labels, subject_index_per_epoch,
    recording_ids_in_order) - same interface convention as
    ml/datasets/sleep_edf.py's load_dataset_windows_multi()."""

    pairs = find_recordings(dataset_dir, subject_ids=subject_ids)
    all_x, all_y, all_subject, prefixes = [], [], [], []
    for subject_idx, (edf, scoring) in enumerate(pairs):
        x, y = load_recording_windows(edf, scoring, channels)
        all_x.append(x)
        all_y.append(y)
        all_subject.append(np.full(len(y), subject_idx, dtype=np.int64))
        prefixes.append(edf.stem)
    return np.concatenate(all_x), np.concatenate(all_y), np.concatenate(all_subject), prefixes


def shuffle_eog_within_subject(x: np.ndarray, subject_idx: np.ndarray, eog_channel_index: int, seed: int) -> np.ndarray:
    """Negative control (C): permutes the derived-EOG channel's epochs
    among THAT SUBJECT'S OWN epochs only, breaking true EEG<->EOG temporal
    correspondence while preserving the real EOG signal distribution.
    Identical algorithm to ml/datasets/sleep_edf.py's
    shuffle_eog_within_subject() - same frozen control design
    (results/hmc_protocol_stage1b.json::control_C), applied to the new
    dataset. Never mixes epochs across subjects or partitions."""

    rng = np.random.default_rng(seed)
    shuffled = x.copy()
    for s in sorted(set(subject_idx.tolist())):
        idx = np.where(subject_idx == s)[0]
        permuted = rng.permutation(idx)
        shuffled[idx, eog_channel_index, :] = x[permuted, eog_channel_index, :]
    return shuffled
