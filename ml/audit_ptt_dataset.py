#!/usr/bin/env python
"""Full 66-record integrity + structural audit for the PhysioNet Pulse
Transit Time PPG Dataset, run once after the complete dataset is downloaded
(see datasets/PTT_DATASET_AUDIT_DAY3.md for the Day 3 representative-sample
audit this extends to all 66 records before the overnight full ablation).

Produces two machine-readable artifacts:
- datasets/pulse-transit-time-ppg/download_log/checksum_report.json
- datasets/pulse-transit-time-ppg/download_log/full_audit_report.json

Never deletes or "fixes" a record automatically - only reports.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from ml.datasets.pulse_transit_time_ppg import (  # noqa: E402
    ACTIVITIES,
    ALL_SUBJECTS,
    MODEL_B_CHANNELS,
    SIGNAL_FS,
    load_record_raw,
    record_name,
)

RAW_DIR = REPO_ROOT / "datasets" / "pulse-transit-time-ppg" / "raw"
LOG_DIR = REPO_ROOT / "datasets" / "pulse-transit-time-ppg" / "download_log"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_sha256sums(path: Path) -> dict[str, str]:
    expected = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        digest, filename = line.split(None, 1)
        expected[filename.strip()] = digest.strip()
    return expected


def run_checksum_audit() -> dict:
    sums_path = RAW_DIR / "SHA256SUMS.txt"
    expected = parse_sha256sums(sums_path)

    results = {}
    for subject_id in ALL_SUBJECTS:
        for activity in ACTIVITIES:
            name = record_name(subject_id, activity)
            for ext in (".hea", ".dat", ".atr"):
                filename = f"{name}{ext}"
                local_path = RAW_DIR / filename
                entry = {"expected_sha256": expected.get(filename)}
                if not local_path.exists():
                    entry["status"] = "MISSING"
                elif entry["expected_sha256"] is None:
                    entry["status"] = "NO_EXPECTED_HASH"
                    entry["actual_sha256"] = sha256_of(local_path)
                    entry["size_bytes"] = local_path.stat().st_size
                else:
                    actual = sha256_of(local_path)
                    entry["actual_sha256"] = actual
                    entry["size_bytes"] = local_path.stat().st_size
                    entry["status"] = "OK" if actual == entry["expected_sha256"] else "MISMATCH"
                results[filename] = entry

    statuses = [v["status"] for v in results.values()]
    summary = {
        "total_files_expected": len(results),
        "ok": statuses.count("OK"),
        "missing": statuses.count("MISSING"),
        "mismatch": statuses.count("MISMATCH"),
        "no_expected_hash": statuses.count("NO_EXPECTED_HASH"),
    }
    return {"summary": summary, "files": results}


def run_structural_audit() -> dict:
    per_record = {}
    anomalies = []

    for subject_id in ALL_SUBJECTS:
        for activity in ACTIVITIES:
            name = record_name(subject_id, activity)
            entry: dict = {"subject_id": subject_id, "activity": activity}
            try:
                raw = load_record_raw(RAW_DIR, subject_id, activity)
            except Exception as exc:  # noqa: BLE001 - report, never silently skip
                entry["status"] = "LOAD_FAILED"
                entry["error"] = f"{type(exc).__name__}: {exc}"
                per_record[name] = entry
                anomalies.append({"record": name, "issue": entry["error"]})
                continue

            checks = {}
            checks["fs_500"] = raw.fs == SIGNAL_FS
            checks["18_channels"] = len(raw.sig_name) == 18
            checks["channel_order_matches_known"] = raw.sig_name == [
                "ecg", "pleth_1", "pleth_2", "pleth_3", "pleth_4", "pleth_5", "pleth_6",
                "lc_1", "lc_2", "temp_1", "temp_2", "temp_3",
                "a_x", "a_y", "a_z", "g_x", "g_y", "g_z",
            ]
            checks["required_ppg_channels_present"] = all(c in raw.sig_name for c in MODEL_B_CHANNELS)
            checks["ecg_present"] = "ecg" in raw.sig_name
            checks["positive_duration"] = raw.signals.shape[1] > 0
            checks["subject_matches_filename"] = raw.subject_id == subject_id
            checks["activity_matches_filename"] = raw.activity == activity

            n_rpeaks = len(raw.rpeak_samples)
            checks["annotation_count_plausible"] = n_rpeaks > 30  # ~500s recording, even a slow HR gives well over this
            checks["rpeaks_monotonic_increasing"] = bool(np.all(np.diff(raw.rpeak_samples) > 0)) if n_rpeaks > 1 else False
            checks["rpeaks_within_signal_bounds"] = bool(raw.rpeak_samples.max() < raw.signals.shape[1]) if n_rpeaks > 0 else False

            entry["fs"] = raw.fs
            entry["n_channels"] = len(raw.sig_name)
            entry["n_samples"] = int(raw.signals.shape[1])
            entry["duration_seconds"] = raw.signals.shape[1] / raw.fs
            entry["n_rpeaks"] = n_rpeaks
            entry["checks"] = checks
            entry["status"] = "OK" if all(checks.values()) else "ANOMALY"

            if entry["status"] == "ANOMALY":
                failed = [k for k, v in checks.items() if not v]
                anomalies.append({"record": name, "issue": f"failed checks: {failed}"})

            per_record[name] = entry

    summary = {
        "total_records": len(per_record),
        "ok": sum(1 for v in per_record.values() if v["status"] == "OK"),
        "anomaly": sum(1 for v in per_record.values() if v["status"] == "ANOMALY"),
        "load_failed": sum(1 for v in per_record.values() if v["status"] == "LOAD_FAILED"),
    }
    return {"summary": summary, "records": per_record, "anomalies": anomalies}


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    print("Running checksum audit...")
    checksum_report = run_checksum_audit()
    print("Checksum summary:", json.dumps(checksum_report["summary"], indent=2))
    (LOG_DIR / "checksum_report.json").write_text(json.dumps(checksum_report, indent=2))

    print("Running structural audit (this loads every record via wfdb)...")
    structural_report = run_structural_audit()
    print("Structural summary:", json.dumps(structural_report["summary"], indent=2))
    if structural_report["anomalies"]:
        print("ANOMALIES FOUND:")
        for a in structural_report["anomalies"]:
            print(" -", a)
    (LOG_DIR / "full_audit_report.json").write_text(json.dumps(structural_report, indent=2))

    print("\nDone. See:")
    print(" -", LOG_DIR / "checksum_report.json")
    print(" -", LOG_DIR / "full_audit_report.json")


if __name__ == "__main__":
    main()
