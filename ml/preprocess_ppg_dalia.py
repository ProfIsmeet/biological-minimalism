#!/usr/bin/env python
"""One-time preprocessing: extract every real subject from the downloaded
PPG-DaLiA archive and cache compact per-subject `.npz` windows.

Never writes the huge raw per-subject `.pkl` (~1.2-1.7 GB each) to disk -
streams each one directly out of the nested zip, windows it in memory, and
discards the raw arrays once the compact cache file is saved. Idempotent:
re-running skips subjects that are already cached.

Usage:
    python preprocess_ppg_dalia.py \
        --zip ../datasets/ppg-dalia/raw_uci/ppg_dalia_uci.zip \
        --cache-dir ../datasets/ppg-dalia/processed
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.datasets.ppg_dalia import list_available_raw_subjects, preprocess_subject  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=str, default=str(REPO_ROOT / "datasets" / "ppg-dalia" / "raw_uci" / "ppg_dalia_uci.zip"))
    parser.add_argument("--cache-dir", type=str, default=str(REPO_ROOT / "datasets" / "ppg-dalia" / "processed"))
    args = parser.parse_args()

    zip_path = Path(args.zip)
    subjects = list_available_raw_subjects(zip_path)
    print(f"Found {len(subjects)} real subjects in archive: {subjects}")

    for subject_id in subjects:
        start = time.time()
        cache_path = preprocess_subject(zip_path, subject_id, args.cache_dir)
        elapsed = time.time() - start
        size_mb = cache_path.stat().st_size / 1e6
        print(f"{subject_id}: cached to {cache_path.name} ({size_mb:.1f} MB) in {elapsed:.1f}s")

    print("Done.")


if __name__ == "__main__":
    main()
