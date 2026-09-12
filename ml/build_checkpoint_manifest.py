#!/usr/bin/env python
"""Canonical, machine-readable checkpoint manifest across every ML
experiment in this project (Reviewer B, master review: checkpoint
archival provenance weaknesses; Day 8: full reconciliation of the
43-hashes-vs-1-present-on-Mac discrepancy).

This is a READ-ONLY consolidation - it computes SHA256/size for whichever
checkpoint files actually exist on THIS machine right now and honestly
reports any expected checkpoint that is missing, rather than regenerating
or fabricating it. `ml/checkpoints/` remains gitignored; only this small
JSON index is committed.

Reconciliation note (Day 8): the "43 hashes recorded, only 1 checkpoint
present on Emir's Mac" discrepancy is explained by design, not a bug -
`ml/checkpoints/` has always been gitignored throughout this project
(see .gitignore's `ml/checkpoints/*` pattern). Every training run in this
project's history was executed on this Windows machine; the resulting
.pt files were never pushed to git (by design - large binaries). Emir's
Mac clone therefore has whatever he happens to have trained/copied
locally himself (evidently 1 file), not the full set this machine holds.
The "40 missing" figure cited in the Day-8 prompt could not be exactly
reproduced from this side (this machine reports 0 missing, since it is
the machine that trained everything) - see the discrepancy note in the
final report rather than a fabricated number-for-number reconciliation.
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

EXPECTED: list[dict] = []


def add(dataset: str, target: str, experiment: str, role: str, seed: int, architecture_id: str, path: str) -> None:
    EXPECTED.append({
        "checkpoint_id": f"{experiment}::{role}::seed{seed}",
        "dataset": dataset,
        "target": target,
        "experiment_id": experiment,
        "model_role": role,
        "seed": seed,
        "architecture_id": architecture_id,
        "path": path,
    })


# Original PPG-DaLiA single-seed experiment (Day 1/2)
for role, fname in [
    ("model_a_ppg_only", "model_a_ppg_only_ppg_dalia.pt"),
    ("model_b_ppg_plus_imu", "model_b_ppg_plus_imu_ppg_dalia.pt"),
    ("model_c_ppg_plus_shuffled_imu", "model_c_ppg_plus_shuffled_imu_ppg_dalia.pt"),
]:
    add("ppg_dalia", "heart_rate_bpm", "ppg_dalia_imu_ablation", role, 42, role, fname)

# Day 6 multi-seed replication
for role in ("a", "b", "c"):
    role_name = {"a": "model_a_ppg_only", "b": "model_b_ppg_plus_imu", "c": "model_c_ppg_plus_shuffled_imu"}[role]
    for seed in (42, 43, 44, 45, 46):
        add("ppg_dalia", "heart_rate_bpm", "ppg_dalia_imu_multiseed_replication", role_name, seed, role_name, f"ppg_dalia_multiseed_{role_name}_seed{seed}.pt")

# Day 7 capacity control
for seed in (42, 43, 44, 45, 46):
    add("ppg_dalia", "heart_rate_bpm", "ppg_dalia_capacity_control", "model_a_cap", seed, "PPGCapacityMatchedModel", f"ppg_dalia_model_a_cap_seed{seed}.pt")

# PTT second-site ablation (Day 3/4)
for role in ("a", "b"):
    for seed in (42, 43, 44, 45, 46):
        add("pulse_transit_time_ppg", "heart_rate_bpm", "ptt_ppg_site_ablation", f"model_{role}", seed, "PPGSiteHRModel", f"ptt_model_{role}_seed{seed}.pt")

# Day 7 Sleep-EDF EEG/EOG ablation
for config in ("baseline_eeg_only", "candidate_eeg_plus_eog"):
    for seed in (42, 43, 44, 45, 46):
        add("sleep_edf_cassette", "sleep_stage_5class", "sleep_edf_eeg_eog_ablation", config, seed, "SleepStageClassifier", f"sleep_edf_{config}_seed{seed}.pt")

# Day 8 Sleep-EDF shuffled-EOG negative control
for seed in (42, 43, 44, 45, 46):
    add("sleep_edf_cassette", "sleep_stage_5class", "sleep_edf_shuffled_eog_control", "model_c_shuffled_eog", seed, "SleepStageClassifier", f"sleep_edf_model_c_shuffled_eog_seed{seed}.pt")

# Legacy pre-manifest checkpoints (earlier Priority-1 single-modality training passes,
# predating the per-experiment manifest convention - included here for completeness)
add("sleep_edf_cassette", "sleep_stage_5class", "sleep_edf_single_channel_baseline_priority1", "eeg_encoder", "n/a", "Conv1DEncoder+head (original single-channel script)", "eeg_encoder_sleep_edf.pt")
add("bidmc_ppg", "heart_rate_bpm_and_respiration_rate", "bidmc_ppg_training_priority1", "ppg_encoder", "n/a", "Conv1DEncoder+heads (original BIDMC script)", "ppg_encoder_bidmc.pt")


def main() -> None:
    entries = []
    n_present, n_missing = 0, 0
    seen_paths: dict[str, str] = {}

    for exp in EXPECTED:
        ckpt_path = CKPT_DIR / exp["path"]
        entry = dict(exp)
        entry["file_path"] = f"ml/checkpoints/{exp['path']}"

        if exp["path"] in seen_paths:
            entry["unique_file"] = False
            entry["duplicate_reference_of"] = seen_paths[exp["path"]]
        else:
            entry["unique_file"] = True
            entry["duplicate_reference_of"] = None
            seen_paths[exp["path"]] = entry["checkpoint_id"]

        if ckpt_path.exists():
            data = ckpt_path.read_bytes()
            entry["current_machine_present"] = True
            entry["file_size"] = len(data)
            entry["sha256"] = hashlib.sha256(data).hexdigest()
            entry["archival_status"] = "PENDING_ARCHIVAL"
            entry["regeneration_status"] = "NOT_NEEDED_FILE_PRESENT"
            n_present += 1
        else:
            entry["current_machine_present"] = False
            entry["file_size"] = None
            entry["sha256"] = None
            entry["archival_status"] = "CANNOT_ARCHIVE_FILE_MISSING"
            entry["regeneration_status"] = "WOULD_REQUIRE_RETRAINING_NOT_PERFORMED"
            entry["note"] = "Expected checkpoint file not found on this machine - reported honestly, not regenerated or fabricated."
            n_missing += 1

        entries.append(entry)

    n_unique = sum(1 for e in entries if e["unique_file"])
    n_duplicate_refs = len(entries) - n_unique

    manifest = {
        "purpose": "Canonical checkpoint index across all ML experiments, for Emir/Claude's later archival step (e.g. GitHub Release/LFS). Computed from whatever exists on THIS machine right now.",
        "checkpoint_directory": "ml/checkpoints/ (gitignored - never committed to git, on any machine)",
        "reconciliation_note": (
            "This machine (the one that ran every training script in this project) reports "
            f"{n_present} present / {n_missing} missing of {len(EXPECTED)} total references, all unique files "
            f"({n_unique} unique, {n_duplicate_refs} duplicate references). A different machine's clone "
            "(e.g. Emir's Mac) would show far fewer PRESENT, because ml/checkpoints/ was never pushed to git - "
            "this explains a low present-count on another machine without implying data loss on THIS one."
        ),
        "summary": {
            "total_references": len(EXPECTED),
            "unique_files": n_unique,
            "duplicate_references": n_duplicate_refs,
            "present_on_this_machine": n_present,
            "missing_on_this_machine": n_missing,
        },
        "entries": entries,
    }

    OUT_PATH.write_text(json.dumps(manifest, indent=2))
    print(f"Wrote {OUT_PATH}: {n_present} present, {n_missing} missing (of {len(EXPECTED)} total, {n_unique} unique)")
    if n_missing:
        print("MISSING:")
        for e in entries:
            if not e["current_machine_present"]:
                print(" -", e["path"])


if __name__ == "__main__":
    main()
