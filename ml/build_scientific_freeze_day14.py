#!/usr/bin/env python
"""Day 14: scientific freeze manifest + freeze-candidate artifact.
Deterministic - hashes a fixed list of canonical science artifacts. No
training, no modification of any hashed file."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

MANIFEST_OUT = REPO_ROOT / "results" / "scientific_freeze_manifest_day14.json"
CANDIDATE_OUT = REPO_ROOT / "results" / "scientific_freeze_candidate_day14.json"

CANONICAL_FILES = [
    "results/sensor_marginal_value_contract.json",
    "results/ppg_dalia_capacity_control.json",
    "results/ppg_dalia_imu_multiseed_replication.json",
    "results/ptt_ppg_site_ablation.json",
    "results/ptt_sensitivity_analysis.json",
    "results/sleep_edf_eeg_eog_ablation.json",
    "results/sleep_edf_eeg_eog_control_analysis.json",
    "results/sleep_edf_per_subject_analysis.json",
    "results/sleep_edf_secondary_holdout_evaluation.json",
    "results/sleep_edf_secondary_n3_diagnostic.json",
    "results/sleep_n3_extended_diagnostic_day11.json",
    "results/day10_ppg_dalia_fault_robustness_reproduction.json",
    "results/sleep_edf_interaction_resp_day10.json",
    "results/sleep_interaction_sensitivity_day11.json",
    "results/ppg_dalia_sensitivity_day11.json",
    "results/ptt_sensitivity_day11.json",
    "results/sleep_edf_sensitivity_day11.json",
    "results/statistical_unit_audit_day11.json",
    "results/scientific_master_table_day11.json",
    "results/day10_frozen_environment_verification.json",
    "results/dataset_fingerprint_manifest_day10.json",
    "results/final_checkpoint_inventory_day14.json",
    "results/clean_clone_reproduction_day13.json",
    "results/paper_tables/table1_experimental_protocols.json",
    "results/paper_tables/table2_main_marginal_value_results.json",
    "results/paper_tables/table3_subject_heterogeneity.json",
    "results/paper_tables/table4_reproducibility_provenance.json",
    "results/paper_tables/table5_interaction_experiment.json",
    "results/figure_sources/figure_A_ppg_capacity_control.json",
    "results/figure_sources/figure_B_ppg_subject_activity_heterogeneity.json",
    "results/figure_sources/figure_C_ptt_subject_heterogeneity.json",
    "results/figure_sources/figure_D_sleep_primary_abc.json",
    "results/figure_sources/figure_E_sleep_secondary_abc.json",
    "results/figure_sources/figure_F_sleep_subject_level_b_minus_a.json",
    "results/figure_sources/figure_G_sleep_class_level_b_minus_a.json",
    "results/figure_sources/figure_H_robustness.json",
    "results/figure_sources/figure_I_interaction.json",
]


def sha256_of(path: Path) -> str:
    # Hash line-ending-normalized content (CRLF -> LF) so the manifest's
    # hashes are stable across Windows/Linux/macOS checkouts of the same
    # git-tracked text content, rather than reflecting incidental
    # CRLF-vs-LF byte differences that carry no scientific meaning.
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    entries = []
    all_exist = True
    for rel in CANONICAL_FILES:
        path = REPO_ROOT / rel
        exists = path.exists()
        all_exist = all_exist and exists
        entries.append({
            "path": rel,
            "exists": exists,
            "sha256": sha256_of(path) if exists else None,
        })

    manifest = {
        "purpose": "Scientific freeze manifest (Day 14) - the science source-of-truth hash chain. Any future change to a hashed file must be intentional and re-run this builder.",
        "n_files": len(entries),
        "all_files_exist": all_exist,
        "entries": entries,
    }
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2))
    print("Wrote", MANIFEST_OUT, "-", len(entries), "files, all_exist:", all_exist)

    day10_repro = json.loads((REPO_ROOT / "results" / "day10_scientific_reproduction.json").read_text())
    clean_clone = json.loads((REPO_ROOT / "results" / "clean_clone_reproduction_day13.json").read_text())
    checkpoint_inv = json.loads((REPO_ROOT / "results" / "final_checkpoint_inventory_day14.json").read_text())

    open_limitations = [
        "Interaction evidence covers exactly one candidate pair (Sleep EOGxResp); two other audited candidates remain deferred.",
        "PTT evidence is n=4 subjects, s2-sensitive - the most fragile subject-level result in the project.",
        "Sleep primary/secondary/interaction all use the same single dataset/recording protocol - no cross-dataset replication anywhere.",
        "Robustness testing covers a single subject (S14) and 114 specific fault conditions - not a general robustness claim.",
        "Clean-clone raw-dataset acquisition was verified via hash-matched file copy, not a second live network re-download in this session.",
        "N3 regression's underlying cause is undiagnosed (descriptive confusion-matrix account only, by design).",
    ]

    freeze_candidate = {
        "canonical_source_commit": "e414ef5c0c2b00f7d80b681848d37d7c59e523b5",
        "canonical_source_branch": "origin/day10-canonical-integration",
        "scientific_branch": "day11-14-scientific-parallel",
        "environment": {"status": "EXACT_FROZEN_ENVIRONMENT", "source": "results/day10_frozen_environment_verification.json"},
        "dataset_fingerprints": {"n_records": 266, "n_present": 266, "n_committed_to_git": 0, "source": "results/dataset_fingerprint_manifest_day10.json"},
        "checkpoint_archive": {
            "n_total": checkpoint_inv["summary"]["n_total_referenced"],
            "n_externally_archived": checkpoint_inv["summary"]["n_with_external_archival"],
            "archives": checkpoint_inv["archives"],
        },
        "canonical_experiments": ["ppg_dalia_imu_hr", "ptt_second_ppg_site_hr", "sleep_edf_eeg_eog_sleep_stage_primary", "sleep_edf_eeg_eog_shuffled_control", "sleep_edf_secondary_holdout", "ppg_dalia_fault_robustness", "sleep_edf_interaction_eeg_eog_resp"],
        "reproduction_status": day10_repro["overall"],
        "table_package": "results/paper_tables/ (5 tables, CSV+JSON)",
        "figure_sources": "results/figure_sources/ (9 figures)",
        "sensitivity_package": ["results/ppg_dalia_sensitivity_day11.json", "results/ptt_sensitivity_day11.json", "results/sleep_edf_sensitivity_day11.json", "results/sleep_n3_extended_diagnostic_day11.json", "results/sleep_interaction_sensitivity_day11.json"],
        "interaction_status": "approximately_additive_or_unresolved (one candidate pair run, two deferred)",
        "clean_clone_result": clean_clone["overall_status"],
        "open_scientific_limitations": open_limitations,
        "freeze_candidate_status": "SCIENTIFIC_FREEZE_CANDIDATE_READY_WITH_LIMITATIONS",
    }
    CANDIDATE_OUT.write_text(json.dumps(freeze_candidate, indent=2))
    print("Wrote", CANDIDATE_OUT)
    print("Status:", freeze_candidate["freeze_candidate_status"])


if __name__ == "__main__":
    main()
