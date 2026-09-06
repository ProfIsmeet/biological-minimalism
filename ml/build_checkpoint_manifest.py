#!/usr/bin/env python
"""Consolidated machine-readable checkpoint manifest across every ML
experiment in this project (Reviewer B, master review: checkpoint
archival provenance weaknesses). This is a READ-ONLY consolidation - it
computes SHA256/size for whichever checkpoint files actually exist
locally right now and honestly reports any expected checkpoint that is
missing, rather than regenerating or fabricating it.

Does not commit large binaries - `ml/checkpoints/` remains gitignored.
This manifest (small JSON) is the source-of-truth index for Emir/Claude's
later archival step (e.g. GitHub Release/LFS), not a replacement for it.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"
OUT_PATH = REPO_ROOT / "results" / "checkpoint_manifest_consolidated.json"

# (relative path under ml/checkpoints/, dataset, experiment, model_role, seed, architecture_id)
EXPECTED: list[dict] = []

# Original PPG-DaLiA single-seed experiment (Day 1/2)
for role, fname in [
    ("model_a_ppg_only", "model_a_ppg_only_ppg_dalia.pt"),
    ("model_b_ppg_plus_imu", "model_b_ppg_plus_imu_ppg_dalia.pt"),
    ("model_c_ppg_plus_shuffled_imu", "model_c_ppg_plus_shuffled_imu_ppg_dalia.pt"),
]:
    EXPECTED.append({"dataset": "ppg_dalia", "experiment": "ppg_dalia_imu_ablation", "model_role": role, "seed": 42, "architecture_id": role, "path": fname})

# Day 6 multi-seed replication
for role in ("a", "b", "c"):
    role_name = {"a": "model_a_ppg_only", "b": "model_b_ppg_plus_imu", "c": "model_c_ppg_plus_shuffled_imu"}[role]
    for seed in (42, 43, 44, 45, 46):
        EXPECTED.append({"dataset": "ppg_dalia", "experiment": "ppg_dalia_imu_multiseed_replication", "model_role": role_name, "seed": seed, "architecture_id": role_name, "path": f"ppg_dalia_multiseed_{role_name}_seed{seed}.pt"})

# Day 7 capacity control
for seed in (42, 43, 44, 45, 46):
    EXPECTED.append({"dataset": "ppg_dalia", "experiment": "ppg_dalia_capacity_control", "model_role": "model_a_cap", "seed": seed, "architecture_id": "PPGCapacityMatchedModel", "path": f"ppg_dalia_model_a_cap_seed{seed}.pt"})

# PTT second-site ablation (Day 3/4)
for role in ("a", "b"):
    for seed in (42, 43, 44, 45, 46):
        EXPECTED.append({"dataset": "pulse_transit_time_ppg", "experiment": "ptt_ppg_site_ablation", "model_role": f"model_{role}", "seed": seed, "architecture_id": "PPGSiteHRModel", "path": f"ptt_model_{role}_seed{seed}.pt"})

# Day 7 Sleep-EDF EEG/EOG ablation
for config in ("baseline_eeg_only", "candidate_eeg_plus_eog"):
    for seed in (42, 43, 44, 45, 46):
        EXPECTED.append({"dataset": "sleep_edf_cassette", "experiment": "sleep_edf_eeg_eog_ablation", "model_role": config, "seed": seed, "architecture_id": "SleepStageClassifier", "path": f"sleep_edf_{config}_seed{seed}.pt"})


def main() -> None:
    entries = []
    n_present, n_missing = 0, 0
    for exp in EXPECTED:
        ckpt_path = CKPT_DIR / exp["path"]
        entry = dict(exp)
        if ckpt_path.exists():
            data = ckpt_path.read_bytes()
            entry["status"] = "PRESENT_LOCALLY"
            entry["size_bytes"] = len(data)
            entry["sha256"] = hashlib.sha256(data).hexdigest()
            n_present += 1
        else:
            entry["status"] = "MISSING_LOCALLY"
            entry["note"] = "Expected checkpoint file not found - reported honestly, not regenerated or fabricated."
            n_missing += 1
        entries.append(entry)

    manifest = {
        "purpose": "Consolidated checkpoint index across all ML experiments, for Emir/Claude's later archival step (e.g. GitHub Release/LFS). Read-only - computed from whatever exists locally right now.",
        "checkpoint_directory": "ml/checkpoints/ (gitignored - never committed to git)",
        "summary": {"total_expected": len(EXPECTED), "present_locally": n_present, "missing_locally": n_missing},
        "entries": entries,
    }

    OUT_PATH.write_text(json.dumps(manifest, indent=2))
    print(f"Wrote {OUT_PATH}: {n_present} present, {n_missing} missing (of {len(EXPECTED)} expected)")
    if n_missing:
        print("MISSING:")
        for e in entries:
            if e["status"] == "MISSING_LOCALLY":
                print(" -", e["path"])


if __name__ == "__main__":
    main()
