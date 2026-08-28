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

import mne
import numpy as np

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
