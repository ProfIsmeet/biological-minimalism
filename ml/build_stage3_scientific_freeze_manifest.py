#!/usr/bin/env python
"""Section 32 remediation: a NEW Stage-3 scientific freeze manifest,
covering the actual current Stage-3 science package (not a retrofit of
the historical Day-14 freeze manifest, which covers a different, earlier
package). Hashes line-ending-normalized content (CRLF->LF) so results are
stable across Windows/Linux/macOS checkouts, distinct from the raw-byte
checkpoint SHA256 hashes recorded elsewhere (checkpoints are binary and
must be hashed as raw bytes; this manifest's targets are all text/JSON)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

OUT_PATH = REPO_ROOT / "results" / "stage3_scientific_freeze_manifest.json"

CANONICAL_TEXT_FILES = [
    # GalaxyPPG
    "results/galaxyppg_reference_ecg_qc.json",
    "results/galaxyppg_corrected_eligibility.json",
    "results/galaxyppg_corrected_full_cv_folds.json",
    "results/galaxyppg_corrected_full_cv_result.json",
    "results/galaxyppg_hr_corrected_eligibility_stage3.json",
    "results/galaxyppg_hr_corrected_per_subject_stage3.json",
    "results/galaxyppg_high01_strong_consistency_check.json",
    "results/galaxyppg_invalidated_evidence_registry.json",
    "results/galaxyppg_correctedcv_v2_expected_membership.json",
    "results/stage3_galaxyppg_lbnp_consolidated_provenance.json",
    # LBNP
    "results/lbnp_target_stage_inventory.json",
    "results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json",
    "results/lbnp_thoracic_eis_stage3.json",
    "results/lbnp_protocol_stage1b.json",
    # Sleep V2 / checkpoint identity
    "results/sleep_v2_checkpoint_accepted_mapping.json",
    "results/sleep_edf_primary_seedfix_v2.json",
    # HMC
    "results/hmc_current_download_inventory.json",
    # Stage-3 completion / status
    "results/stage3_science_completion_manifest.json",
    "results/sensor_value_master_matrix_stage3_complete.json",
    "results/architecture_evidence_handoff_stage4.json",
    "results/stage3_environment_snapshot.json",
]


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    entries = []
    all_exist = True
    for rel in CANONICAL_TEXT_FILES:
        path = REPO_ROOT / rel
        exists = path.exists()
        all_exist = all_exist and exists
        entries.append({
            "path": rel,
            "exists": exists,
            "hash_kind": "line_ending_normalized_sha256_of_text_content",
            "sha256": sha256_of(path) if exists else None,
        })

    governing_artifacts = {
        "lbnp_eis_result": "results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json",
        "lbnp_eis_result_historical_superseded": "results/lbnp_thoracic_eis_stage3.json",
        "galaxyppg_full_cv_result": "results/galaxyppg_corrected_full_cv_result.json",
        "galaxyppg_bounded_diagnostic": "results/galaxyppg_hr_corrected_eligibility_stage3.json",
        "hmc_current_state": "results/hmc_current_download_inventory.json",
        "stage3_manifest": "results/stage3_science_completion_manifest.json",
    }

    manifest = {
        "governing_artifacts": governing_artifacts,
        "purpose": (
            "Stage 3 scientific freeze manifest (Codex fail remediation "
            "sprint) - the current Stage-3 science source-of-truth hash "
            "chain. This is a NEW manifest, distinct from and not a "
            "retrofit of results/scientific_freeze_manifest_day14.json "
            "(which covers a different, earlier science package)."
        ),
        "hash_semantics_note": (
            "All hashes here are computed on line-ending-normalized TEXT "
            "content (CRLF->LF), distinct from raw-byte SHA256 hashes used "
            "for binary checkpoint files (e.g. results/*_expected_membership.json "
            "entries) - text hashes and checkpoint hashes are never "
            "comparable to each other and are never conflated in this "
            "repository's convention."
        ),
        "n_files": len(entries),
        "all_files_exist": all_exist,
        "entries": entries,
    }
    OUT_PATH.write_text(json.dumps(manifest, indent=2))
    print("Wrote", OUT_PATH, "-", len(entries), "files, all_exist:", all_exist)


if __name__ == "__main__":
    main()
