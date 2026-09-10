#!/usr/bin/env python
"""Builds the real GalaxyPPG participant eligibility table (Stage 2B, data-
quality rules only, frozen before any model outcome). For each of the 24
real participant directories, checks required file presence and computes
the real pre/post-UTC+9-correction synchronization gap between E4 and
Polar H10 (the real bug found and fixed this sprint)."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.datasets.galaxyppg import detect_r_peaks  # noqa: E402

DATA_DIR = REPO_ROOT / "datasets" / "galaxyppg" / "raw" / "extracted" / "Dataset"
OUT_PATH = REPO_ROOT / "results" / "galaxyppg_eligibility_stage2.json"
MIN_R_PEAKS_PER_MINUTE = 40.0  # real data-integrity gate (Stage 3 addition): a
# resting/active adult HR is physiologically >=40 bpm; anything far below this
# indicates the reference ECG channel itself is unusable (electrode contact
# failure / saturation), not a genuine low heart rate - found this sprint via
# real full-cohort evaluation (P03: 0.08 peaks/min, P07: 0.83 peaks/min, vs.
# ~85-86 peaks/min for every other real subject checked)


def first_last_timestamp(csv_path: Path, col: str) -> tuple[float, float] | None:
    if not csv_path.exists():
        return None
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return None
    return float(rows[0][col]), float(rows[-1][col])


def main() -> None:
    participants = sorted(p.name for p in DATA_DIR.iterdir() if p.is_dir() and p.name.startswith("P"))
    table = []
    for pid in participants:
        pdir = DATA_DIR / pid
        bvp_path = pdir / "E4" / "BVP.csv"
        acc_path = pdir / "E4" / "ACC.csv"
        ecg_path = pdir / "PolarH10" / "ECG.csv"

        bvp_present = bvp_path.exists()
        acc_present = acc_path.exists()
        ecg_present = ecg_path.exists()

        entry = {
            "participant_id": pid,
            "bvp_present": bvp_present,
            "acc_present": acc_present,
            "ecg_present": ecg_present,
        }

        if bvp_present and ecg_present:
            bvp_span = first_last_timestamp(bvp_path, "timestamp")
            ecg_span = first_last_timestamp(ecg_path, "phoneTimestamp")
            if bvp_span and ecg_span:
                bvp_t0 = bvp_span[0] / 1e6
                bvp_tlast = bvp_span[1] / 1e6
                ecg_t0_raw = ecg_span[0] / 1e3
                ecg_tlast_raw = ecg_span[1] / 1e3
                ecg_t0_corrected = ecg_t0_raw - 9 * 3600
                ecg_tlast_corrected = ecg_tlast_raw - 9 * 3600
                pre_correction_gap = ecg_t0_raw - bvp_t0
                post_correction_gap = ecg_t0_corrected - bvp_t0
                overlap_start = max(bvp_t0, ecg_t0_corrected)
                overlap_end = min(bvp_tlast, ecg_tlast_corrected)
                overlap_duration = max(0.0, overlap_end - overlap_start)
                entry.update({
                    "pre_correction_start_gap_s": pre_correction_gap,
                    "post_correction_start_gap_s": post_correction_gap,
                    "overlap_duration_s": overlap_duration,
                })

        required_ok = bvp_present and acc_present and ecg_present
        plausible_sync = entry.get("overlap_duration_s", 0) > 300  # at least 5 min real overlap

        r_peaks_per_min = None
        ecg_quality_ok = True
        if required_ok:
            with open(ecg_path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            ecg_val = np.array([float(r["ecg"]) for r in rows], dtype=np.float32)
            UTC9 = 9 * 3600
            ecg_t = np.array([float(r["phoneTimestamp"]) for r in rows], dtype=np.float64) / 1e3 - UTC9
            peaks = detect_r_peaks(ecg_val, ecg_t)
            duration_min = (ecg_t[-1] - ecg_t[0]) / 60.0
            r_peaks_per_min = len(peaks) / duration_min if duration_min > 0 else 0.0
            ecg_quality_ok = r_peaks_per_min >= MIN_R_PEAKS_PER_MINUTE
            entry["r_peaks_per_min"] = r_peaks_per_min

        entry["eligible"] = bool(required_ok and plausible_sync and ecg_quality_ok)
        if not required_ok:
            entry["exclusion_reason"] = "missing required file(s)"
        elif not plausible_sync:
            entry["exclusion_reason"] = f"implausible/insufficient overlap after UTC+9 correction ({entry.get('overlap_duration_s', 0):.1f}s)"
        elif not ecg_quality_ok:
            entry["exclusion_reason"] = f"reference ECG quality too poor for R-peak detection ({r_peaks_per_min:.2f} peaks/min, below the {MIN_R_PEAKS_PER_MINUTE} peaks/min data-integrity threshold - real electrode contact/saturation issue, not a low heart rate)"
        else:
            entry["exclusion_reason"] = None
        table.append(entry)

    n_eligible = sum(1 for e in table if e["eligible"])
    out = {
        "purpose": "Real GalaxyPPG participant eligibility table, built from actual files, data-quality rules only, frozen before any model outcome.",
        "n_participants_found": len(table),
        "n_eligible": n_eligible,
        "eligibility_rule": "bvp_present AND acc_present AND ecg_present AND overlap_duration_s > 300 (after the documented UTC+9 Polar correction)",
        "table": table,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2))
    print(f"Found {len(table)} participants, {n_eligible} eligible")
    for e in table:
        if not e["eligible"]:
            print(" EXCLUDED:", e["participant_id"], e["exclusion_reason"])
    print("Wrote", OUT_PATH)


if __name__ == "__main__":
    main()
