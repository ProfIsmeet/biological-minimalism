"""Loader for the BIDMC PPG and Respiration Dataset (PhysioNet).

Source: Pimentel, M. A. F., Johnson, A. E. W., Charlton, P. H., Birrenkott,
D., Watkinson, P. J., Tarassenko, L., & Clifton, D. A. (2017). Toward a
Robust Estimation of Respiratory Rate From Pulse Oximeters. IEEE
Transactions on Biomedical Engineering, 64(8), 1914-1923. A subset of the
MIMIC II matched waveform database (critically-ill adult ICU patients,
Beth Israel Deaconess Medical Center). Distributed via PhysioNet:
https://physionet.org/content/bidmc/1.0.0/ (Open Data Commons Attribution
License v1.0 - open access, no credentialing required).

Why this project uses it: this project's real, planned PPG dataset was
WESAD, whose two official distribution links were both confirmed dead (see
`ml/datasets/sleep_edf.py`'s docstring for the same finding, reused here).
BIDMC is a better fit for the PPG modality specifically than Sleep-EDF: real
125 Hz PLETH (PPG) waveform, paired with real per-second clinical-monitor
ground truth for HR, PULSE, RESP (respiration rate) and SpO2 - i.e. real
labels for two of this project's actual `OUTPUT_TARGETS`
(`heart_rate_bpm`, `respiration_rate_bpm`), not a proxy classification task.

53 subjects, 8-minute recordings each, `bidmc_csv/` distribution format
(`bidmc_XX_Signals.csv`: Time, RESP, PLETH, ECG leads; `bidmc_XX_Numerics.csv`:
per-second HR, PULSE, RESP, SpO2).
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

SAMPLE_RATE_HZ = 125.0
WINDOW_SECONDS = 8.0
WINDOW_SAMPLES = int(WINDOW_SECONDS * SAMPLE_RATE_HZ)


def _read_signals_csv(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return (time_seconds, pleth) from one `*_Signals.csv` file."""

    times, pleth = [], []
    with open(path, newline="", encoding="utf-8") as f:
        header = [h.strip() for h in next(f).split(",")]
        pleth_idx = header.index("PLETH")
        reader = csv.reader(f)
        for row in reader:
            times.append(float(row[0]))
            pleth.append(float(row[pleth_idx]))
    return np.array(times, dtype=np.float64), np.array(pleth, dtype=np.float32)


def _read_numerics_csv(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (time_seconds, hr, resp) from one `*_Numerics.csv` file, real
    per-second clinical-monitor values. Rows with a missing/blank HR or RESP
    reading are dropped rather than imputed."""

    times, hr, resp = [], [], []
    with open(path, newline="", encoding="utf-8") as f:
        header = [h.strip() for h in next(f).split(",")]
        t_idx, hr_idx, resp_idx = header.index("Time [s]"), header.index("HR"), header.index("RESP")
        reader = csv.reader(f)
        for row in reader:
            hr_val, resp_val = row[hr_idx].strip(), row[resp_idx].strip()
            if not hr_val or not resp_val or hr_val.lower() == "nan" or resp_val.lower() == "nan":
                continue
            hr_f, resp_f = float(hr_val), float(resp_val)
            if not (np.isfinite(hr_f) and np.isfinite(resp_f)):
                continue  # a real missing/invalid clinical-monitor reading - skipped, not imputed
            times.append(float(row[t_idx]))
            hr.append(hr_f)
            resp.append(resp_f)
    return np.array(times, dtype=np.float64), np.array(hr, dtype=np.float32), np.array(resp, dtype=np.float32)


def load_subject_windows(signals_path: Path, numerics_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Split one subject's real PLETH waveform into non-overlapping 8-second
    windows, each labeled with the real per-second HR/RESP averaged over
    that window.

    Returns (windows, hr_labels, resp_labels):
    `windows`: float32, shape (n_windows, 1, WINDOW_SAMPLES) - ready for
    `Conv1DEncoder` (backend/app/ml/models.py).
    """

    sig_times, pleth = _read_signals_csv(signals_path)
    num_times, hr, resp = _read_numerics_csv(numerics_path)

    n_windows = len(pleth) // WINDOW_SAMPLES
    windows, hr_labels, resp_labels = [], [], []
    for i in range(n_windows):
        start_sample = i * WINDOW_SAMPLES
        end_sample = start_sample + WINDOW_SAMPLES
        window_start_t, window_end_t = sig_times[start_sample], sig_times[end_sample - 1]

        in_window = (num_times >= window_start_t) & (num_times <= window_end_t)
        if not in_window.any():
            continue  # no real numerics label available for this window - skip, don't guess

        segment = pleth[start_sample:end_sample]
        std = segment.std()
        if std < 1e-6:
            continue  # flat/dropped-out signal segment, a real artifact - excluded rather than fabricated
        segment = (segment - segment.mean()) / std

        windows.append(segment)
        hr_labels.append(float(hr[in_window].mean()))
        resp_labels.append(float(resp[in_window].mean()))

    if not windows:
        return (
            np.empty((0, 1, WINDOW_SAMPLES), dtype=np.float32),
            np.empty((0,), dtype=np.float32),
            np.empty((0,), dtype=np.float32),
        )

    x = np.stack(windows).astype(np.float32)[:, None, :]
    return x, np.array(hr_labels, dtype=np.float32), np.array(resp_labels, dtype=np.float32)


def load_dataset_windows(dataset_dir: str | Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load every subject under `dataset_dir` and return
    (windows, hr_labels, resp_labels, subject_ids)."""

    dataset_dir = Path(dataset_dir)
    if not dataset_dir.exists():
        raise NotImplementedError(
            f"BIDMC PPG data not found at {dataset_dir}. See "
            "datasets/bidmc-ppg/README.md for the download command. This "
            "project does not ship or fabricate this data."
        )

    signal_files = sorted(dataset_dir.glob("bidmc_*_Signals.csv"))
    if not signal_files:
        raise NotImplementedError(f"No BIDMC subject files found under {dataset_dir}.")

    all_x, all_hr, all_resp, all_subject = [], [], [], []
    for subject_idx, signals_path in enumerate(signal_files):
        numerics_path = signals_path.with_name(signals_path.name.replace("_Signals.csv", "_Numerics.csv"))
        if not numerics_path.exists():
            continue
        x, hr, resp = load_subject_windows(signals_path, numerics_path)
        if len(hr) == 0:
            continue
        all_x.append(x)
        all_hr.append(hr)
        all_resp.append(resp)
        all_subject.append(np.full(len(hr), subject_idx, dtype=np.int64))

    return (
        np.concatenate(all_x),
        np.concatenate(all_hr),
        np.concatenate(all_resp),
        np.concatenate(all_subject),
    )
