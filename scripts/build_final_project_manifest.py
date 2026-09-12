"""Stage 5 Final Synthesis: final project manifest + authoritative artifact
registry (master prompt Part I, Sections 10-12).

The Stage-5 project-level source of truth: every authoritative artifact
required for paper/jury/demo/reproduction (Stage-3/4 carryover + new Stage-5
artifacts), each with SHA256 (canonical text hash per docs/HASH_PROVENANCE_POLICY.md),
owner, source-stage, and required-for flags. Downstream surfaces (backend,
frontend, paper exports, jury exports, docs) must point back to these
artifacts rather than reconstructing state independently (Section 12).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "results" / "final_project_manifest.json"

ACCEPTED_STAGE3_SHA = "5c381014af61e5d10d41223963831b25b9ff23e6"
STAGE4_FINAL_CLOSURE_SHA = "691bc8c0fd464bc1741da2e69a7c5fa986c3294a"


def _canonical_text_sha256(rel: str) -> str:
    """LF-normalized hash per docs/HASH_PROVENANCE_POLICY.md - stable across
    platforms for committed text/JSON artifacts."""
    raw = (REPO_ROOT / rel).read_bytes()
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


# Carried forward from Stage 4 (results/stage4_final_closure_manifest.json
# authoritative_artifacts) - NOT rebuilt, referenced as historical/frozen.
STAGE4_CARRYOVER_ARTIFACTS = [
    ("results/stage4_architecture_acceptance_gates.json", "STAGE4", "Acceptance gates A-H"),
    ("results/stage4_gate_d_burden_completeness.json", "STAGE4", "Gate D burden-completeness, CONDITIONALLY_READY"),
    ("results/stage4_gate_e_coordinator_decisions.json", "STAGE4", "Gate E decisions, FREEZE_CONDITIONALLY x2"),
    ("results/stage4_formal_pareto_analysis.json", "STAGE4", "Formal Pareto dominance analysis - COMPLETE"),
    ("results/final_wearable_architecture.json", "STAGE4", "THE canonical final architecture decision - CORE_PLUS_CONTEXT"),
    ("results/stage4_science_claim_ledger.json", "STAGE4", "Science Owner claim ledger (base, superseded partially by closure updates)"),
    ("results/stage4_final_closure_claim_updates.json", "STAGE4", "Integration Owner claim updates (final_architecture, pareto only)"),
    ("results/stage4_final_closure_manifest.json", "STAGE4", "Stage-4 final closure manifest of record"),
    ("results/digital_twin_architecture_footprint.json", "STAGE3", "Digital Twin status: ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED"),
]

# New Stage-5 artifacts (this sprint).
STAGE5_ARTIFACTS = [
    ("results/final_claim_ledger.json", "The final project claim contract - all required claim areas.", "required_for_paper_jury_release"),
    ("results/final_tables/table_a_modality_evidence.json", "Table A - modality evidence.", "required_for_paper"),
    ("results/final_tables/table_b_controlled_ablations.json", "Table B - controlled ablations.", "required_for_paper"),
    ("results/final_tables/table_c_external_replication.json", "Table C - external replication.", "required_for_paper"),
    ("results/final_tables/table_d_negative_mixed_results.json", "Table D - negative/mixed results.", "required_for_paper"),
    ("results/final_tables/table_e_final_architecture_rationale.json", "Table E - final architecture rationale.", "required_for_paper_jury"),
    ("results/final_tables/table_f_engineering_burden.json", "Table F - engineering burden.", "required_for_paper_jury"),
    ("results/final_figure_manifest.json", "Catalog of all 14 final figure-data exports with provenance.", "required_for_paper_demo"),
    ("presentation/final_jury_evidence_pack.json", "Jury Q&A evidence pack, traced to the claim ledger.", "required_for_jury"),
    ("results/final_reproduction_manifest.json", "Per-experiment reproducibility classification.", "required_for_release_reproduction"),
]


def build() -> dict:
    try:
        repository_sha_at_manifest_time = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        repository_sha_at_manifest_time = "UNKNOWN_GIT_UNAVAILABLE"

    ledger = _load("results/final_claim_ledger.json")
    final_arch = _load("results/final_wearable_architecture.json")
    pareto = _load("results/stage4_formal_pareto_analysis.json")
    gate_d = _load("results/stage4_gate_d_burden_completeness.json")
    gate_e = _load("results/stage4_gate_e_coordinator_decisions.json")
    repro = _load("results/final_reproduction_manifest.json")
    digital_twin = _load("results/digital_twin_architecture_footprint.json")

    authoritative_artifacts = []
    for path, source_stage, description in STAGE4_CARRYOVER_ARTIFACTS:
        authoritative_artifacts.append(
            {
                "artifact_id": Path(path).stem,
                "path": path,
                "purpose": description,
                "owner": "INTEGRATION_OWNER" if source_stage == "STAGE4" else "SCIENCE_OWNER",
                "current_or_historical": "CURRENT",
                "sha256_canonical_text": _canonical_text_sha256(path),
                "source_stage": source_stage,
                "required_for_release": True,
                "required_for_paper": path.endswith(("claim_ledger.json", "claim_updates.json", "architecture.json")) or "pareto" in path,
                "required_for_jury_demo": True,
            }
        )
    for path, purpose, required_for in STAGE5_ARTIFACTS:
        authoritative_artifacts.append(
            {
                "artifact_id": Path(path).stem,
                "path": path,
                "purpose": purpose,
                "owner": "FINAL_SYNTHESIS_AND_RELEASE_OWNER",
                "current_or_historical": "CURRENT",
                "sha256_canonical_text": _canonical_text_sha256(path),
                "source_stage": "STAGE5",
                "required_for_release": "release" in required_for,
                "required_for_paper": "paper" in required_for,
                "required_for_jury_demo": "jury" in required_for or "demo" in required_for,
            }
        )

    return {
        "artifact_id": "biological-minimalism-stage5-final-project-manifest-v1",
        "schema_version": "1.0.0",
        "sprint": "STAGE5_FINAL_SYNTHESIS_AND_RELEASE",
        "generated_role": "FINAL_SYNTHESIS_AND_RELEASE_OWNER",
        "purpose": (
            "The Stage-5 project-level source of truth: title, IAC paper ID, final architecture, accepted "
            "Stage-3/4 SHAs, current Stage-5 SHA, authoritative artifacts, final claims, Pareto state, Gate D/E "
            "state, pending science, Digital Twin status, reproducibility status, and release status. All "
            "downstream surfaces (backend, frontend, paper exports, jury exports, docs) must point back to these "
            "canonical artifacts rather than reconstructing state independently."
        ),
        "project_title": "Biological Minimalism",
        "iac_paper_id": "IAC-2026 (submission ID not yet assigned)",
        "final_architecture": {
            "selected_class": final_arch["selected_class"],
            "module_topology": final_arch["module_topology"]["topology_class"],
            "gate_d_burden_completeness": gate_d["gate_d_burden_completeness"],
            "gate_e_decisions": [{"item": d["item"], "decision": d["decision"]} for d in gate_e["decisions"]],
        },
        "pareto_state": {
            "formal_pareto_status": pareto["formal_pareto_status"],
            "pareto_relevant_set": pareto["pareto_relevant_set"],
            "no_unique_pareto_winner": pareto["no_unique_pareto_winner"],
            "coordinator_selected_architecture": pareto["coordinator_selected_architecture"],
        },
        "final_claims": {
            "central_scientific_message": ledger["central_scientific_message"],
            "claim_ledger_path": "results/final_claim_ledger.json",
            "claim_count": len(ledger["claims"]),
        },
        "pending_science": {
            "hmc_full_cohort": "LOWER_PRIORITY_EXTERNAL_WORK_PENDING",
            "ds003838_full_cohort": "LOWER_PRIORITY_EXTERNAL_WORK_PENDING",
        },
        "digital_twin_status": digital_twin["validation_status"],
        "reproducibility_status": {
            "manifest_path": "results/final_reproduction_manifest.json",
            "class_distribution": repro["class_distribution"],
            "clean_clone_verdict": repro["clean_clone_drill"]["verdict"],
        },
        "release_status": "PENDING - see results/final_release_manifest.json (built after this manifest)",
        "accepted_stage3_sha": ACCEPTED_STAGE3_SHA,
        "stage4_final_closure_sha": STAGE4_FINAL_CLOSURE_SHA,
        "stage5_repository_sha_at_manifest_time": repository_sha_at_manifest_time,
        "stage5_repository_sha_note": (
            "This is the repository HEAD SHA at manifest-generation time (a file cannot embed its own resulting "
            "commit hash without amending). The actual Stage-5 release-candidate commit SHA is reported in the "
            "branch push report, not embedded here."
        ),
        "authoritative_artifacts": authoritative_artifacts,
        "authoritative_artifact_count": len(authoritative_artifacts),
        "one_current_truth_policy": (
            "Current final project state must not be reconstructed independently in backend, frontend, paper "
            "exports, jury exports, or documentation. All must cite the authoritative_artifacts listed above."
        ),
        "status": "STAGE5_FINAL_PROJECT_MANIFEST_REPORTED_COMPLETE_PENDING_INDEPENDENT_AUDIT",
    }


if __name__ == "__main__":
    output = build()
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({output['authoritative_artifact_count']} authoritative artifacts)")
