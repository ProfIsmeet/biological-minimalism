"""Phase 4 integration dry-run (governing prompt §49-51 + explicit Phase-4
user stress-test list). Exercises the FULL pipeline — manifest dict/file ->
validator -> FutureScienceManifestReader -> display projections -> the
consumer-facing narrative/claim functions — for every representative and
adversarial case named for this phase. This complements (does not repeat)
Phase 2's `test_future_science_ingestion.py` and Phase 3's
`test_future_science_consumer_guards.py`, which test individual guards in
isolation; this file proves the whole pipeline behaves correctly together
and specifically stress-tests the 13 additional cases the user named.

All fixtures are synthetic, TEST-ONLY, and use the unmistakable sentinel
prefix "phase4-dry-run-". None are written into `results/` as real project
evidence — this is verified explicitly by this file's own leakage-guard test
(governing prompt §49)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.research.day6 import day6_research
from app.research.engineering_readiness import engineering_readiness
from app.research.future_science_ingestion import (
    FutureScienceManifestReader,
    ManifestErrorCode,
    ManifestValidationError,
    assert_replication_claim_is_plausible,
    build_two_arm_comparison_narrative,
    project_for_display,
    validate_claim_against_entry,
)
from app.schemas.experiment_manifest import ExperimentManifestEntry

REPO_ROOT = Path(__file__).resolve().parents[2]
SENTINEL = "phase4-dry-run"


def _entry(**overrides) -> dict:
    raw = {
        "experiment_id": f"{SENTINEL}-experiment",
        "experiment_version": "V1",
        "dataset": f"{SENTINEL}-dataset",
        "dataset_version": "v1",
        "target": f"{SENTINEL}-target-mae",
        "baseline_config": "A",
        "candidate_config": "B",
        "control_config": "C",
        "metric": {"name": f"{SENTINEL}-metric-mae", "kind": "regression", "directionality": "lower_is_better", "unit": "unit"},
        "biological_subject_n": 5,
        "optimization_seed_n": 5,
        "primary_result": {"mean": 0.60, "sd": 0.05, "n": 5, "display": "0.60 unit"},
        "control_result": {"mean": 1.00, "sd": 0.05, "n": 5, "display": "1.00 unit"},
        "subject_sensitivity": {"status": "available", "entries": [], "dominant_key": None, "note": None},
        "class_sensitivity": None,
        "replication_class": "SINGLE_RUN",
        "completion_state": "COMPLETE",
        "access_blocker": None,
        "provenance": {
            "source_artifact_path": f"results/{SENTINEL}_fixture_only.json",
            "source_sha256": None,
            "experiment_commit": None,
            "dataset_version": "v1",
            "protocol_version": f"{SENTINEL}-protocol-v1",
            "checkpoint_manifest_path": None,
            "subject_split_manifest_path": None,
        },
        "checkpoint_manifest": None,
        "safe_claims": [],
        "unsafe_claims": [],
        "limitations": [],
    }
    raw.update(overrides)
    return raw


def _built(**overrides) -> ExperimentManifestEntry:
    return ExperimentManifestEntry.model_validate(_entry(**overrides))


def _prov(dataset_version: str, protocol_version: str) -> dict:
    return {
        "source_artifact_path": f"results/{SENTINEL}_fixture_only.json", "source_sha256": None,
        "experiment_commit": None, "dataset_version": dataset_version, "protocol_version": protocol_version,
        "checkpoint_manifest_path": None, "subject_split_manifest_path": None,
    }


# --- §50 case 1: positive MAE candidate --------------------------------------

def test_case_positive_mae_candidate() -> None:
    entry = _built()  # primary 0.60 < control 1.00, lower_is_better
    projection = project_for_display(entry)
    assert projection.is_headline_eligible is True
    assert projection.benefit_value == pytest.approx(0.40)
    assert projection.benefit_value > 0


# --- §50 case 2: negative MAE candidate (candidate worse) -------------------

def test_case_negative_mae_candidate_is_shown_not_hidden() -> None:
    entry = _built(
        primary_result={"mean": 1.50, "sd": 0.05, "n": 5, "display": "1.50 unit"},
        control_result={"mean": 1.00, "sd": 0.05, "n": 5, "display": "1.00 unit"},
    )
    projection = project_for_display(entry)
    assert projection.is_headline_eligible is True  # COMPLETE, still shown
    assert projection.benefit_value == pytest.approx(-0.50)
    assert projection.benefit_value < 0
    assert "N/A" not in projection.benefit_display  # a real negative result, not suppressed


# --- §50 case 3: positive F1 candidate ---------------------------------------

def test_case_positive_f1_candidate() -> None:
    entry = _built(
        metric={"name": f"{SENTINEL}-metric-f1", "kind": "classification", "directionality": "higher_is_better", "unit": "f1"},
        primary_result={"mean": 0.85, "sd": None, "n": None, "display": "0.85"},
        control_result={"mean": 0.70, "sd": None, "n": None, "display": "0.70"},
    )
    projection = project_for_display(entry)
    assert projection.benefit_value == pytest.approx(0.15)
    assert projection.benefit_value > 0


# --- User stress-test: strong aggregate improvement + severe heterogeneity -

def test_case_heterogeneous_subject_effect_is_visible_despite_strong_aggregate() -> None:
    entry = _built(
        primary_result={"mean": 0.20, "sd": 0.02, "n": 5, "display": "0.20 unit"},
        control_result={"mean": 1.00, "sd": 0.02, "n": 5, "display": "1.00 unit"},  # huge +0.80 aggregate benefit
        subject_sensitivity={
            "status": "available",
            "entries": [
                {"key": "subj-01", "value": 3.90, "note": "drives nearly the entire aggregate effect"},
                {"key": "subj-02", "value": 0.02, "note": None},
                {"key": "subj-03", "value": -0.05, "note": "slightly negative"},
                {"key": "subj-04", "value": 0.01, "note": None},
                {"key": "subj-05", "value": 0.03, "note": None},
            ],
            "dominant_key": "subj-01",
            "note": "Aggregate benefit is single-subject-dominated; not uniform support.",
        },
    )
    projection = project_for_display(entry)
    assert projection.benefit_value == pytest.approx(0.80)  # strong aggregate
    # ...but the heterogeneity is NOT hidden: it survives all the way to the projection.
    assert projection.subject_sensitivity.status == "available"
    assert projection.subject_sensitivity.dominant_key == "subj-01"
    assert len(projection.subject_sensitivity.entries) == 5
    assert "single-subject-dominated" in (projection.subject_sensitivity.note or "")


# --- §50 case 5/6 + user stress-test: external replication, incl. failed ---

def test_case_external_replication_labeled_correctly_when_plausible() -> None:
    primary = _built(experiment_id=f"{SENTINEL}-primary", dataset=f"{SENTINEL}-dataset-A")
    replication = _built(
        experiment_id=f"{SENTINEL}-external-replication",
        dataset=f"{SENTINEL}-dataset-B",  # genuinely different dataset
        replication_class="EXTERNAL_REPLICATION",
    )
    assert_replication_claim_is_plausible(replication, primary)  # must not raise
    projection = project_for_display(replication)
    assert projection.replication_class_label == "Independent external replication"


def test_case_failed_negative_external_replication_is_shown_not_hidden() -> None:
    failed_replication = _built(
        experiment_id=f"{SENTINEL}-failed-replication",
        dataset=f"{SENTINEL}-dataset-B",
        replication_class="EXTERNAL_REPLICATION",
        primary_result={"mean": 1.80, "sd": 0.10, "n": 6, "display": "1.80 unit"},
        control_result={"mean": 1.00, "sd": 0.10, "n": 6, "display": "1.00 unit"},
    )
    projection = project_for_display(failed_replication)
    assert projection.is_headline_eligible is True
    assert projection.benefit_value == pytest.approx(-0.80)  # candidate clearly worse
    assert projection.replication_class == "EXTERNAL_REPLICATION"
    assert "N/A" not in projection.benefit_display  # a negative replication is a real, displayable result


# --- User stress-test: SAME_DATASET_HOLDOUT mislabeled as EXTERNAL_REPLICATION

def test_case_same_dataset_holdout_mislabeled_as_external_replication_is_caught() -> None:
    primary = _built(experiment_id=f"{SENTINEL}-primary", dataset=f"{SENTINEL}-dataset-A", dataset_version="v2")
    mislabeled = _built(
        experiment_id=f"{SENTINEL}-mislabeled-holdout",
        dataset=f"{SENTINEL}-dataset-A",       # SAME dataset as primary
        dataset_version="v2",                   # SAME dataset_version as primary
        replication_class="EXTERNAL_REPLICATION",  # but claims external replication
    )
    with pytest.raises(ManifestValidationError) as excinfo:
        assert_replication_claim_is_plausible(mislabeled, primary)
    assert excinfo.value.code == ManifestErrorCode.SUSPICIOUS_REPLICATION_CLAIM

    # The correctly-labeled version of the same scenario is fine.
    correctly_labeled = _built(
        experiment_id=f"{SENTINEL}-correct-holdout",
        dataset=f"{SENTINEL}-dataset-A", dataset_version="v2",
        replication_class="SAME_DATASET_HOLDOUT",
    )
    projection = project_for_display(correctly_labeled)
    assert projection.replication_class_label == "Same-dataset holdout (not independent replication)"


# --- §50 case 7 + user stress-test: BOUNDED_DIAGNOSTIC cannot become headline

def test_case_bounded_diagnostic_cannot_become_headline() -> None:
    entry = _built(completion_state="BOUNDED_DIAGNOSTIC")
    projection = project_for_display(entry)
    assert projection.is_headline_eligible is False
    assert projection.benefit_value is None
    with pytest.raises(ManifestValidationError) as excinfo:
        validate_claim_against_entry(entry, required_full_evidence=True)
    assert excinfo.value.code == ManifestErrorCode.CLAIM_EVIDENCE_INSUFFICIENT


# --- §50 case 8 + user stress-test: blocked dataset with stale numeric fields

def test_case_blocked_dataset_with_stale_numeric_fields_never_renders_a_number() -> None:
    entry = _built(
        completion_state="BLOCKED_BY_DATA_ACCESS",
        access_blocker="ZENODO_UNREACHABLE",
        # A real-looking, plausible-but-stale number left over from before access broke.
        primary_result={"mean": 0.42, "sd": 0.03, "n": 12, "display": "0.42 bpm (STALE pre-block estimate)"},
        control_result={"mean": 0.55, "sd": 0.03, "n": 12, "display": "0.55 bpm (STALE pre-block estimate)"},
    )
    projection = project_for_display(entry)
    assert projection.is_headline_eligible is False
    assert projection.benefit_value is None
    assert projection.benefit_display.startswith("N/A —")
    assert "0.42" not in projection.benefit_display  # the stale number must not leak into the display
    with pytest.raises(ManifestValidationError) as excinfo:
        validate_claim_against_entry(entry)
    assert excinfo.value.code == ManifestErrorCode.CLAIM_EVIDENCE_INSUFFICIENT


# --- §50 case 9 + user stress-test: HISTORICAL/SUPERSEDED vs preferred COMPLETE, mixed Sleep V1/V2 operands

def test_case_historical_and_superseded_vs_preferred_corrected_version() -> None:
    historical = _built(
        experiment_id=f"{SENTINEL}-sleep-v1-historical",
        dataset=f"{SENTINEL}-sleep-edf", dataset_version="V1_HISTORICAL",
        completion_state="HISTORICAL",
        provenance=_prov("V1_HISTORICAL", "V1_HISTORICAL"),
    )
    superseded = _built(
        experiment_id=f"{SENTINEL}-sleep-v1-superseded-draft",
        dataset=f"{SENTINEL}-sleep-edf", dataset_version="V1_HISTORICAL",
        completion_state="SUPERSEDED",
        provenance=_prov("V1_HISTORICAL", "V1_HISTORICAL"),
    )
    preferred = _built(
        experiment_id=f"{SENTINEL}-sleep-v2-preferred",
        dataset=f"{SENTINEL}-sleep-edf", dataset_version="V2_SEEDFIX_CORRECTED",
        completion_state="COMPLETE",
        provenance=_prov("V2_SEEDFIX_CORRECTED", "V2_SEEDFIX_CORRECTED"),
    )
    # HISTORICAL remains citable as historical...
    validate_claim_against_entry(historical)  # must not raise
    # ...but SUPERSEDED must never be citable, even though it looks structurally similar.
    with pytest.raises(ManifestValidationError):
        validate_claim_against_entry(superseded)
    # Neither historical leg is headline-eligible; only the corrected V2 is.
    assert project_for_display(historical).is_headline_eligible is False
    assert project_for_display(superseded).is_headline_eligible is False
    assert project_for_display(preferred).is_headline_eligible is True
    # A V1/V2 mixed-protocol narrative (the literal Sleep V1/V2 case) is blocked.
    with pytest.raises(ManifestValidationError) as excinfo:
        build_two_arm_comparison_narrative(historical, preferred)
    assert excinfo.value.code == ManifestErrorCode.MIXED_PROTOCOL_VERSION
    # Two same-version historical legs may be narrated together.
    build_two_arm_comparison_narrative(historical, superseded)  # must not raise


# --- User stress-test: subject_n accidentally copied from seed_n -----------

def test_case_subject_n_copied_from_seed_n_cannot_corrupt_the_benefit() -> None:
    """The bug this guards against: someone copy-pastes optimization_seed_n's
    value into biological_subject_n (or vice versa). Both fields are
    independently required by the schema (already enforced in Phase 2), but
    this test additionally proves the *computed benefit* is structurally
    independent of either field's value — a copy-paste bug there cannot
    silently corrupt the scientific number, even though (documented
    limitation, see Phase 4 report) neither field is currently surfaced on
    `ManifestEntryDisplayProjection` for a viewer to visually sanity-check."""
    plausible = _built(biological_subject_n=3, optimization_seed_n=5)
    suspicious_copy = _built(biological_subject_n=5, optimization_seed_n=5)  # n's coincide
    swapped = _built(biological_subject_n=5, optimization_seed_n=3)

    benefit_plausible = project_for_display(plausible).benefit_value
    benefit_copy = project_for_display(suspicious_copy).benefit_value
    benefit_swapped = project_for_display(swapped).benefit_value
    assert benefit_plausible == benefit_copy == benefit_swapped == pytest.approx(0.40)


# --- §50 + Phase 2 regression, run again in full-file dry-run form ---------

def test_case_incomplete_provenance_and_checkpoint_mapping_fail_closed_at_file_level(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "results"
    manifest_dir.mkdir()
    bad_manifest = {
        "schema_version": "1.0.0",
        "manifest_id": f"{SENTINEL}-bad-manifest",
        "generated_by": "pytest",
        "generated_at": None,
        "entries": [_entry(provenance={
            "source_artifact_path": "", "source_sha256": None, "experiment_commit": None,
            "dataset_version": "v1", "protocol_version": "p1",
            "checkpoint_manifest_path": None, "subject_split_manifest_path": None,
        })],
    }
    (manifest_dir / "stage2_4_science_completion_manifest.json").write_text(json.dumps(bad_manifest), encoding="utf-8")
    reader = FutureScienceManifestReader(repository_root=tmp_path)
    envelope = reader.status()
    assert envelope.status == "INGESTION_FAILED"
    assert envelope.error_code == ManifestErrorCode.MISSING_PROVENANCE.value
    assert envelope.display_projections == []


# --- User stress-test: missing control_result and benefit_value behavior ---

def test_case_missing_control_result_benefit_behavior() -> None:
    entry = _built(control_result=None)
    projection = project_for_display(entry)
    assert projection.is_headline_eligible is True  # still COMPLETE, still eligible
    assert projection.benefit_value is None          # no control to compare against -> no computed benefit
    assert projection.benefit_display == entry.primary_result.display  # raw value shown, not "N/A"
    assert not projection.benefit_display.startswith("N/A")


# --- User stress-test: synthetic fixtures must never leak into real results -

def test_case_synthetic_fixtures_never_leak_into_active_results() -> None:
    results_dir = REPO_ROOT / "results"
    offenders = []
    for path in results_dir.glob("*.json"):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if SENTINEL in text:
            offenders.append(str(path))
    assert offenders == [], f"Phase-4 dry-run test fixtures leaked into real results/: {offenders}"


# --- User stress-test: architecture/Pareto state cannot auto-upgrade -------

def test_case_ingestion_module_has_no_import_of_architecture_or_pareto_modules() -> None:
    ingestion_source = (REPO_ROOT / "backend" / "app" / "research" / "future_science_ingestion.py").read_text()
    assert "day6" not in ingestion_source
    assert "engineering_readiness" not in ingestion_source
    assert "decision_inputs" not in ingestion_source


def test_case_ingesting_a_strong_positive_manifest_does_not_change_architecture_or_pareto_state(
    tmp_path: Path,
) -> None:
    engineering_before = engineering_readiness.artifact().model_dump_json()
    day6_before = day6_research.readiness().model_dump_json()

    manifest_dir = tmp_path / "results"
    manifest_dir.mkdir()
    strong_positive_manifest = {
        "schema_version": "1.0.0",
        "manifest_id": f"{SENTINEL}-strong-positive-manifest",
        "generated_by": "pytest",
        "generated_at": None,
        "entries": [_entry(primary_result={"mean": 0.05, "sd": 0.01, "n": 20, "display": "0.05 unit"})],
    }
    (manifest_dir / "stage2_4_science_completion_manifest.json").write_text(
        json.dumps(strong_positive_manifest), encoding="utf-8"
    )
    reader = FutureScienceManifestReader(repository_root=tmp_path)
    envelope = reader.status()
    assert envelope.status == "INGESTED"
    assert envelope.display_projections[0].benefit_value == pytest.approx(0.95)  # very strong positive

    engineering_after = engineering_readiness.artifact().model_dump_json()
    day6_after = day6_research.readiness().model_dump_json()
    assert engineering_after == engineering_before
    assert day6_after == day6_before


# --- Full end-to-end dry run: one comprehensive multi-entry manifest file ---

def test_full_pipeline_dry_run_with_a_multi_state_manifest_file(tmp_path: Path) -> None:
    """The actual "dry-run architecture" proof: manifest file on disk ->
    FutureScienceManifestReader -> validated ExperimentManifestFile ->
    display_projections, for a manifest containing several different
    completion/replication states at once, exactly as a real Ismet handoff
    manifest would."""
    manifest_dir = tmp_path / "results"
    manifest_dir.mkdir()
    manifest = {
        "schema_version": "1.0.0",
        "manifest_id": f"{SENTINEL}-full-pipeline-manifest",
        "generated_by": "pytest",
        "generated_at": None,
        "entries": [
            _entry(experiment_id=f"{SENTINEL}-complete-positive", completion_state="COMPLETE"),
            _entry(
                experiment_id=f"{SENTINEL}-bounded-diagnostic",
                completion_state="BOUNDED_DIAGNOSTIC",
                primary_result={"mean": 0.9, "sd": None, "n": None, "display": "0.9 unit (diagnostic)"},
            ),
            _entry(
                experiment_id=f"{SENTINEL}-blocked",
                completion_state="BLOCKED_BY_DATA_ACCESS",
                access_blocker="ZENODO_UNREACHABLE",
            ),
            _entry(experiment_id=f"{SENTINEL}-historical", completion_state="HISTORICAL"),
        ],
    }
    (manifest_dir / "stage2_4_science_completion_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    envelope = FutureScienceManifestReader(repository_root=tmp_path).status()
    assert envelope.status == "INGESTED"
    assert envelope.availability == "available"
    assert len(envelope.display_projections) == 4

    by_id = {p.experiment_id: p for p in envelope.display_projections}
    assert by_id[f"{SENTINEL}-complete-positive"].is_headline_eligible is True
    assert by_id[f"{SENTINEL}-bounded-diagnostic"].is_headline_eligible is False
    assert by_id[f"{SENTINEL}-blocked"].is_headline_eligible is False
    assert by_id[f"{SENTINEL}-historical"].is_headline_eligible is False
    # Only the COMPLETE entry has a real numeric benefit; the other three do not.
    non_complete_ids = [f"{SENTINEL}-bounded-diagnostic", f"{SENTINEL}-blocked", f"{SENTINEL}-historical"]
    for exp_id in non_complete_ids:
        assert by_id[exp_id].benefit_value is None
