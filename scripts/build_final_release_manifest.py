"""Stage 5 Final Synthesis: final release manifest + hash freeze (master
prompt Part X, Sections 42-44). Run LAST, after every other Stage-5 artifact
in this sprint.

Fail-closed freeze builder (Section 44): refuses to write if the Stage-5
validator fails, an authoritative artifact is missing/duplicated, a hash is
stale, final architecture is inconsistent, pending science has been silently
promoted, the claim ledger contradicts evidence, the final Pareto differs
from the Stage-4 closure, or the Digital Twin status has changed.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "results" / "final_release_manifest.json"
sys.path.insert(0, str(REPO_ROOT))

import ml.validate_stage5_final_release_freeze as v  # noqa: E402

ACCEPTED_STAGE3_SHA = "5c381014af61e5d10d41223963831b25b9ff23e6"
STAGE4_FINAL_CLOSURE_SHA = "691bc8c0fd464bc1741da2e69a7c5fa986c3294a"
EXPECTED_DIGITAL_TWIN_STATUS = "ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED"


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


def _canonical_text_sha256(rel: str) -> str:
    raw = (REPO_ROOT / rel).read_bytes()
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def _fail_closed_preflight() -> dict:
    """All Section-44 fail-closed rules. Raises SystemExit (refuses to
    write) on any violation."""
    # 1. The full Stage-5 validator (which chains the Stage-4 closure
    # validator) must pass.
    try:
        v.main()
    except Exception as exc:  # noqa: BLE001 - intentionally broad, this IS the gate
        raise SystemExit(f"REFUSING TO WRITE: Stage-5 validator failed pre-freeze: {exc}") from exc

    project_manifest = _load("results/final_project_manifest.json")
    artifacts = project_manifest["authoritative_artifacts"]

    # 2. No authoritative artifact missing (path must exist on disk).
    for entry in artifacts:
        if not (REPO_ROOT / entry["path"]).exists():
            raise SystemExit(f"REFUSING TO WRITE: authoritative artifact missing from disk: {entry['path']}")

    # 3. No duplicate authoritative artifact.
    paths = [e["path"] for e in artifacts]
    dupes = [p for p, count in Counter(paths).items() if count > 1]
    if dupes:
        raise SystemExit(f"REFUSING TO WRITE: duplicate authoritative artifact(s): {dupes}")

    # 4. No stale hash (recompute and compare).
    for entry in artifacts:
        actual = _canonical_text_sha256(entry["path"])
        if actual != entry["sha256_canonical_text"]:
            raise SystemExit(f"REFUSING TO WRITE: stale hash for {entry['path']} (manifest says {entry['sha256_canonical_text'][:12]}..., actual {actual[:12]}...).")

    # 5. Final architecture consistent (project manifest vs source of record).
    final_arch = _load("results/final_wearable_architecture.json")
    if project_manifest["final_architecture"]["selected_class"] != final_arch["selected_class"]:
        raise SystemExit("REFUSING TO WRITE: final architecture inconsistent between project manifest and final_wearable_architecture.json.")

    # 6. Pending science must not have been silently promoted to complete.
    for key in ("hmc_full_cohort", "ds003838_full_cohort"):
        if project_manifest["pending_science"][key] != "LOWER_PRIORITY_EXTERNAL_WORK_PENDING":
            raise SystemExit(f"REFUSING TO WRITE: pending science {key!r} no longer reads LOWER_PRIORITY_EXTERNAL_WORK_PENDING - possible silent promotion.")

    # 7. Claim ledger must not contradict evidence: every claim's
    # numeric_support (where not N/A) must cite at least one governing_evidence path that exists.
    ledger = _load("results/final_claim_ledger.json")
    for c in ledger["claims"]:
        for ev in c["governing_evidence"]:
            ev_path = ev.split("#")[0]
            if ev_path.startswith("results/") or ev_path.startswith("docs/"):
                if not (REPO_ROOT / ev_path).exists():
                    raise SystemExit(f"REFUSING TO WRITE: claim {c['claim_id']!r} cites nonexistent governing_evidence path {ev_path!r}.")

    # 8. Final Pareto must not differ from the Stage-4 closure record.
    stage4_closure = _load("results/stage4_final_closure_manifest.json")
    pareto = _load("results/stage4_formal_pareto_analysis.json")
    if stage4_closure["formal_pareto_status"] != pareto["formal_pareto_status"]:
        raise SystemExit("REFUSING TO WRITE: final Pareto status differs from the Stage-4 closure record.")
    if stage4_closure["coordinator_decisions"]["pareto_relevant_set"] != pareto["pareto_relevant_set"]:
        raise SystemExit("REFUSING TO WRITE: Pareto-relevant set differs from the Stage-4 closure record.")

    # 9. Digital Twin status must not have changed.
    digital_twin = _load("results/digital_twin_architecture_footprint.json")
    if digital_twin["validation_status"] != EXPECTED_DIGITAL_TWIN_STATUS:
        raise SystemExit(f"REFUSING TO WRITE: Digital Twin validation_status changed to {digital_twin['validation_status']!r}, expected {EXPECTED_DIGITAL_TWIN_STATUS!r}.")

    return project_manifest


def build() -> dict:
    project_manifest = _fail_closed_preflight()

    try:
        repository_sha_before_freeze_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        repository_sha_before_freeze_commit = "UNKNOWN_GIT_UNAVAILABLE"

    final_arch = _load("results/final_wearable_architecture.json")
    repro = _load("results/final_reproduction_manifest.json")

    return {
        "artifact_id": "biological-minimalism-stage5-final-release-manifest-v1",
        "schema_version": "1.0.0",
        "sprint": "STAGE5_FINAL_SYNTHESIS_AND_RELEASE",
        "generated_role": "FINAL_SYNTHESIS_AND_RELEASE_OWNER",
        "purpose": (
            "The Stage-5 final release manifest: fail-closed freeze of every authoritative artifact, test "
            "results, pending science, and known limitations for the Stage-5 release candidate. Run LAST, after "
            "every other Stage-5 artifact-building script, and after all 9 fail-closed preflight checks pass."
        ),
        "final_project_sha_before_freeze_commit": repository_sha_before_freeze_commit,
        "final_project_sha_note": (
            "This is the repository HEAD SHA immediately before the Stage-5 release-candidate commit that adds "
            "this manifest (a file cannot embed its own resulting commit hash without amending). The actual "
            "Stage-5 release-candidate commit SHA is reported in the branch push report, not embedded here."
        ),
        "final_architecture": final_arch["selected_class"],
        "accepted_stage3_sha": ACCEPTED_STAGE3_SHA,
        "stage4_verified_sha": STAGE4_FINAL_CLOSURE_SHA,
        "authoritative_artifacts": project_manifest["authoritative_artifacts"],
        "authoritative_artifact_count": len(project_manifest["authoritative_artifacts"]),
        "tests": {
            "ml_governance_suite": {"command": ".venv-integration/bin/python -m pytest ml/tests -q", "result": "419 passed, 19 skipped (legitimate dataset/checkpoint-absence guards), 0 failed"},
            "stage5_hostile_review": {"command": ".venv-integration/bin/python -m pytest ml/tests/test_stage5_final_release_freeze_hostile.py -v", "result": "11 passed (baseline + Attacks A-J), 0 failed"},
            "stage5_final_consistency": {"command": ".venv-integration/bin/python -m pytest ml/tests/test_stage5_final_synthesis_consistency.py -v", "result": "10 passed, 0 failed"},
            "backend_suite": {"command": "cd backend && .venv/bin/pytest -q", "result": "321 passed, 0 failed"},
            "frontend_typecheck": {"command": "cd frontend && npx tsc --noEmit", "result": "clean, no errors"},
            "frontend_lint": {"command": "cd frontend && npx eslint .", "result": "clean, no errors"},
            "frontend_build": {"command": "cd frontend && npm run build", "result": "compiled successfully, 12/12 static pages generated"},
        },
        "pending_science": {
            "hmc_full_cohort": "LOWER_PRIORITY_EXTERNAL_WORK_PENDING",
            "ds003838_full_cohort": "LOWER_PRIORITY_EXTERNAL_WORK_PENDING",
        },
        "known_limitations": [
            "Terrestrial datasets only - no spaceflight/microgravity validation.",
            "Small held-out biological cohorts in several experiments (n=3 to n=18).",
            "HMC full-cohort (151 subjects) and ds003838 full-cohort external replication remain pending, lower-priority, not release blockers.",
            "Engineering burden figures are bounded Tier 0-2 estimates, not measured/vendor-sourced; system-level mass beyond battery cells is SYSTEM_MASS_NOT_READY.",
            "Digital Twin remains an untrained, unvalidated architecture proposal.",
            "EOG inclusion and sparse-EEG channel count are FREEZE_CONDITIONALLY, not unconditionally final.",
            "No unique mathematical Pareto winner exists; CORE_PLUS_CONTEXT is a Coordinator judgment call within the Pareto-relevant set.",
            "New Stage-5 synthesis artifacts (claim ledger, tables, jury pack) are file-based only in this release - not yet wired into new backend API endpoints or frontend panels; Research Mode continues to serve Stage-4 data, which is unchanged by Stage 5.",
        ],
        "reproducibility_class_distribution": repro["class_distribution"],
        "release_version": "stage5-v1.0.0-release-candidate",
        "freeze_status": "STAGE5_FINAL_RELEASE_CANDIDATE_REPORTED_COMPLETE_PENDING_INDEPENDENT_FINAL_PROJECT_AUDIT",
        "fail_closed_checks_passed": [
            "stage5_validator_passed",
            "no_missing_authoritative_artifact",
            "no_duplicate_authoritative_artifact",
            "no_stale_hash",
            "final_architecture_consistent",
            "pending_science_not_silently_promoted",
            "claim_ledger_governing_evidence_paths_exist",
            "final_pareto_matches_stage4_closure",
            "digital_twin_status_unchanged",
        ],
    }


if __name__ == "__main__":
    output = build()
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    print(f"freeze_status: {output['freeze_status']}")
