"""Loader for OpenNeuro ds003838 (digit-span working-memory EEG), Stage 3B.

Source: https://openneuro.org/datasets/ds003838, DOI
10.18112/openneuro.ds003838.v1.0.6, CC0. 63-channel actiCHamp EEG at 1000 Hz,
FCz reference, Fpz ground, 50 Hz power line - all confirmed directly from a
real *_eeg.json sidecar (see results/ds003838_metadata_audit_stage1b.json).

Target: externally-imposed digit-sequence length (5/9/13), memory-condition
trials only, per the frozen protocol (results/ds003838_protocol_stage1b.json).
The label is parsed from the real BIDS `trial_type` column's human-readable
text (e.g. "memory 01/05 correct: memorize digit 1 (first) in 5 digit
sequence; correctly recalled") - never from the raw numeric trigger `value`
column, which is excluded from ever reaching the feature/label pipeline as
anything but this one parse step, per the leakage matrix
(results/dataset_expansion_leakage_matrix_stage1b.json:
"raw trigger-code string as a feature" -> EXCLUDE_LEAKAGE).

Each memory-condition digit-presentation event gets its own fixed-length
1.0 s epoch (matching the BIDS `duration` field exactly, itself matching the
2 s stimulus-onset-asynchrony protocol) - so epoch length never varies with
sequence length, which would otherwise trivially leak the label via epoch
duration.

This loader is intentionally NOT the full Stage-2 n=65 cohort - it operates
on whichever real, actually-downloaded subject .set files are present under
a given directory, for the bounded Stage-3B diagnostic
(docs/DS003838_STAGE3_BOUNDED_DIAGNOSTIC.md explains the scope).
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import mne
import numpy as np

SPARSE_CHANNELS = ["AF7", "AF8", "TP9", "TP10"]  # frozen, Muse-headband-matched (results/ds003838_protocol_stage1b.json)
EPOCH_TMIN = 0.0
EPOCH_TMAX = 1.0  # matches the real BIDS `duration` field for every event (verified, not assumed)

_LENGTH_RE = re.compile(r"in (\d+) digit sequence")


def parse_trial_type(trial_type: str) -> tuple[str, int] | None:
    """Return (condition, length) for a real memory/control trial_type string,
    or None for non-trial rows (e.g. 'STATUS'). Never touches the raw
    numeric `value` column."""
    if not trial_type.startswith("memory") and not trial_type.startswith("control"):
        return None
    m = _LENGTH_RE.search(trial_type)
    if not m:
        return None
    condition = "memory" if trial_type.startswith("memory") else "control"
    return condition, int(m.group(1))


def load_subject_epochs(set_path: Path, events_tsv_path: Path, memory_only: bool = True) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Return (epochs, labels, channel_names) for one real subject.

    `epochs`: float32, shape (n_epochs, n_channels, n_samples) - real raw EEG,
    no synthetic data.
    `labels`: int64, shape (n_epochs,) - digit-sequence length (5/9/13),
    memory-condition trials only if memory_only=True.
    """
    raw = mne.io.read_raw_eeglab(str(set_path), preload=True, verbose="ERROR")
    sfreq = raw.info["sfreq"]
    channel_names = raw.ch_names

    epochs: list[np.ndarray] = []
    labels: list[int] = []
    with open(events_tsv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            parsed = parse_trial_type(row["trial_type"])
            if parsed is None:
                continue
            condition, length = parsed
            if memory_only and condition != "memory":
                continue
            onset_s = float(row["onset"])
            start_sample = int(round(onset_s * sfreq))
            n_samples = int(round(EPOCH_TMAX * sfreq))
            end_sample = start_sample + n_samples
            if end_sample > raw.n_times:
                continue  # real edge case near recording end - skipped, not padded
            data = raw.get_data(start=start_sample, stop=end_sample)  # (n_channels, n_samples), real volts
            epochs.append(data.astype(np.float32))
            labels.append(length)

    return np.stack(epochs), np.array(labels, dtype=np.int64), channel_names


def select_channels(epochs: np.ndarray, channel_names: list[str], wanted: list[str]) -> np.ndarray:
    idx = [channel_names.index(ch) for ch in wanted]
    return epochs[:, idx, :]
