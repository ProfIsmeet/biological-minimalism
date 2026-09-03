#!/usr/bin/env python
"""Batch-preprocess all 66 real PTT records into the small `.npz` window
cache, and produce a per-subject x activity window-accounting table.

Uses only `ml/datasets/pulse_transit_time_ppg.py`'s existing
`load_record_raw`/`windowize_record`/`preprocess_record` - no parallel
preprocessing logic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from ml.datasets.pulse_transit_time_ppg import (  # noqa: E402
    ACTIVITIES,
    ALL_SUBJECTS,
    load_record_raw,
    preprocess_record,
    record_name,
)

RAW_DIR = REPO_ROOT / "datasets" / "pulse-transit-time-ppg" / "raw"
CACHE_DIR = REPO_ROOT / "datasets" / "pulse-transit-time-ppg" / "processed"
LOG_DIR = REPO_ROOT / "datasets" / "pulse-transit-time-ppg" / "download_log"


def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    accounting = {}
    for subject_id in ALL_SUBJECTS:
        for activity in ACTIVITIES:
            name = record_name(subject_id, activity)
            raw = load_record_raw(RAW_DIR, subject_id, activity)
            n_samples = raw.signals.shape[1]
            n_candidate_windows = max(0, (n_samples - 4000) // 1000 + 1)

            cache_path = preprocess_record(RAW_DIR, CACHE_DIR, subject_id, activity)

            import numpy as np

            with np.load(cache_path) as data:
                n_valid = len(data["hr"])

            n_dropped = n_candidate_windows - n_valid
            print(f"{name}: candidate={n_candidate_windows} valid={n_valid} dropped={n_dropped}")

            accounting[name] = {
                "subject_id": subject_id,
                "activity": activity,
                "source_duration_seconds": n_samples / raw.fs,
                "n_candidate_windows": n_candidate_windows,
                "n_valid_windows": n_valid,
                "n_dropped_windows": n_dropped,
                "drop_reason": "insufficient R-peaks (<3) or flat channel - see loader for exact rule" if n_dropped > 0 else None,
            }

    (LOG_DIR / "window_accounting.json").write_text(json.dumps(accounting, indent=2))

    total_candidate = sum(v["n_candidate_windows"] for v in accounting.values())
    total_valid = sum(v["n_valid_windows"] for v in accounting.values())
    total_dropped = sum(v["n_dropped_windows"] for v in accounting.values())
    print(f"\nTOTAL: candidate={total_candidate} valid={total_valid} dropped={total_dropped}")
    print("Wrote", LOG_DIR / "window_accounting.json")


if __name__ == "__main__":
    main()
