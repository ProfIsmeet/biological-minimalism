"""Loader for the PhysioNet "Quantitative Dehydration Estimation" (QDE) dataset.

Source: PhysioNet, Quantitative Dehydration Estimation, v1.0.0 (published
2017-08-10). Open Data Commons Attribution License v1.0.
https://physionet.org/content/qde/1.0.0/

10 subjects ran on a treadmill for 120 minutes without fluid intake, in 8
15-minute intervals (9 measurement points per subject, including the
baseline before interval 1). At each point, real segmental bio-impedance
(right arm, left arm, trunk, right leg, left leg, at 1000 kHz) and real skin
temperature (11 sites) were measured alongside total body water (TBW, via
InBody 720 bioelectrical impedance analysis) as fluid loss accumulated.

Why this project uses it: this project's real, planned bio-impedance/fluid
target dataset was NASA OSDR (head-down-tilt bed rest / dry immersion) — but
OSDR's public search API (`https://osdr.nasa.gov/osdr/data/search`) was
queried directly for "bioimpedance", "impedance", "fluid shift", "dry
immersion", and "head-down tilt" while building this loader, and returned
only 'omics studies (transcriptomics, proteomics, gene expression) — OSDR is
GeneLab-derived and is a molecular-biology repository, not a repository of
raw physiological sensor time series. No downloadable real bio-impedance
sensor dataset was found there. QDE is a real substitute: real segmental
bio-impedance and real skin temperature, from a real (if not spaceflight-
specific) body-fluid-loss protocol — dehydration rather than microgravity-
induced fluid shift, but the same underlying measurement technique (Section 8
of the PDD) applied to a genuinely real fluid-status change.

This is small, tabular, per-interval data (9 points x 10 subjects = 90 rows)
— not a high-sample-rate waveform like the EEG/PPG data this project's other
loaders handle, so it is not windowed for Conv1DEncoder; see
`ml/train_bioimpedance.py` for the small MLP this shape actually calls for.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

IMPEDANCE_COLUMNS = [
    "impedance right arm at 1000kHz [Ohm]",
    "impedance left arm at 1000kHz [Ohm]",
    "impedance trunk at 1000kHz [Ohm]",
    "impedance right leg at 1000kHz [Ohm]",
    "impedance left leg at 1000kHz [Ohm]",
]

TEMPERATURE_COLUMNS = [
    "temperature ear [degree C]",
    "temperature left hand [degree C]",
    "temperature right hand [degree C]",
    "temperature left foot [degree C]",
    "temperature right foot [degree C]",
    "temperature chest [degree C]",
    "temperature back [degree C]",
    "temperature upper arm [degree C]",
    "temperature lower arm [degree C]",
    "temperature upper leg [degree C]",
    "temperature lower leg [degree C]",
]

TARGET_COLUMN = "total body water using InBody 720 [l]"
FEATURE_COLUMNS = IMPEDANCE_COLUMNS + TEMPERATURE_COLUMNS


def load_dataset(csv_path: str | Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (features, target, subject_ids) - one row per real measurement
    point (baseline + 8 running intervals, per subject).

    `features`: float32, shape (n_rows, 16) - 5 real segmental bio-impedance
    readings + 11 real skin temperature readings, both real project sensor
    modalities.
    `target`: float32, shape (n_rows,) - real total body water in liters.
    `subject_ids`: int64, shape (n_rows,) - for a subject-level held-out
    split, the only honest way to evaluate generalization with 10 subjects.

    Rows with any missing feature/target value (a handful exist in the raw
    CSV, e.g. an occasional un-recorded temperature sensor) are dropped
    rather than imputed - this is real, incomplete real-world data, and this
    loader does not fabricate values for it.
    """

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise NotImplementedError(
            f"QDE dataset not found at {csv_path}. See "
            "datasets/qde-bioimpedance/README.md for the download command. "
            "This project does not ship or fabricate this data."
        )

    features: list[list[float]] = []
    targets: list[float] = []
    subjects: list[int] = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                feature_row = [float(row[col]) for col in FEATURE_COLUMNS]
                target = float(row[TARGET_COLUMN])
            except ValueError:
                continue  # a real missing value in the raw CSV - skipped, not imputed
            features.append(feature_row)
            targets.append(target)
            subjects.append(int(row["id"]))

    return (
        np.array(features, dtype=np.float32),
        np.array(targets, dtype=np.float32),
        np.array(subjects, dtype=np.int64),
    )
