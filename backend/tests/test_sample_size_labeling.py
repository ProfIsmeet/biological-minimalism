"""Phase-4 close-out: adversarial tests proving biological_subject_n and
optimization_seed_n are surfaced through the guarded display projection with
distinct semantic labels, never conflated, never fabricated as 0 when
missing, and never presented as an achieved result for an unexecuted
(BLOCKED/PENDING) entry. Closes the disclosed limitation from
docs/CLAUDE_PHASE4_DRY_RUN_HOSTILE_REVIEW_REPORT.md §13.

All fixtures are synthetic, TEST-ONLY, sentinel-prefixed; none touch
`results/` or any science value."""

from __future__ import annotations

import json
from pathlib import Path

from app.research.future_science_ingestion import FutureScienceManifestReader, project_for_display
from app.schemas.experiment_manifest import ExperimentManifestEntry

SENTINEL = "phase4-closeout-sample-size"


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
        "biological_subject_n": 3,
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


# --- Requirement 6, bullet 1: subject n and seed n remain distinct ---------

def test_subject_n_and_seed_n_are_independently_labeled_and_never_merged() -> None:
    projection = project_for_display(_built(biological_subject_n=3, optimization_seed_n=5))
    assert projection.biological_subject_n == 3
    assert projection.optimization_seed_n == 5
    assert projection.biological_subject_n_display == "Biological subjects: 3"
    assert projection.optimization_seed_n_display == "Training seeds: 5"
    # Never merged into one shared field or string.
    assert projection.biological_subject_n_display != projection.optimization_seed_n_display
    assert "seed" not in projection.biological_subject_n_display.lower()
    assert "subject" not in projection.optimization_seed_n_display.lower()


# --- Requirement 6, bullet 2: a 5-seed/3-subject experiment cannot display n=5

def test_five_seed_three_subject_experiment_cannot_display_bare_n_equals_5() -> None:
    projection = project_for_display(_built(biological_subject_n=3, optimization_seed_n=5))
    # The literal ambiguous "n=5" (implying 5 biological subjects) must never
    # appear as the biological-subject label.
    assert projection.biological_subject_n_display != "n=5"
    assert projection.biological_subject_n_display != "5"
    assert "3" in projection.biological_subject_n_display
    assert "5" not in projection.biological_subject_n_display
    # The seed count, correctly labeled, does say 5 — but always qualified as seeds.
    assert projection.optimization_seed_n_display == "Training seeds: 5"
    # Requirement 3: never implies seeds are biological replication.
    assert "biological" not in projection.optimization_seed_n_display.lower()
    assert "subject" not in projection.optimization_seed_n_display.lower()


# --- Requirement 4/6 bullet 3: missing subject n -> unavailable, never 0 ---

def test_missing_biological_subject_n_is_unavailable_never_zero() -> None:
    projection = project_for_display(_built(biological_subject_n=None))
    assert projection.biological_subject_n is None
    assert projection.biological_subject_n_display == "Biological subjects: unavailable"
    assert "0" not in projection.biological_subject_n_display


def test_missing_optimization_seed_n_is_unavailable_never_zero() -> None:
    projection = project_for_display(_built(optimization_seed_n=None))
    assert projection.optimization_seed_n is None
    assert projection.optimization_seed_n_display == "Training seeds: unavailable"
    assert "0" not in projection.optimization_seed_n_display


def test_both_missing_does_not_backfill_one_from_the_other() -> None:
    projection = project_for_display(_built(biological_subject_n=None, optimization_seed_n=None))
    assert projection.biological_subject_n is None
    assert projection.optimization_seed_n is None
    assert projection.biological_subject_n_display == "Biological subjects: unavailable"
    assert projection.optimization_seed_n_display == "Training seeds: unavailable"


# --- Requirement 5: BOUNDED_DIAGNOSTIC / BLOCKED / PENDING never fabricate --

def test_bounded_diagnostic_shows_real_achieved_counts_unqualified() -> None:
    """BOUNDED_DIAGNOSTIC DID execute (just not the full protocol), so a real
    present count is an achieved fact, not a fabrication or a plan."""
    projection = project_for_display(_built(completion_state="BOUNDED_DIAGNOSTIC", biological_subject_n=2))
    assert projection.biological_subject_n_display == "Biological subjects: 2"
    assert "planned" not in projection.biological_subject_n_display


def test_blocked_entry_with_a_real_count_is_labeled_as_planned_not_achieved() -> None:
    """BLOCKED_BY_DATA_ACCESS never executed; any count present describes the
    design target, not an achieved sample — must be labeled as such, never
    presented as if the experiment actually ran with that many subjects."""
    projection = project_for_display(_built(completion_state="BLOCKED_BY_DATA_ACCESS", biological_subject_n=8))
    assert projection.biological_subject_n == 8
    assert projection.biological_subject_n_display == "Biological subjects: 8 (planned; not yet executed)"


def test_pending_entry_with_missing_counts_is_unavailable_not_a_fabricated_plan() -> None:
    projection = project_for_display(_built(
        completion_state="PENDING", biological_subject_n=None, optimization_seed_n=None,
    ))
    assert projection.biological_subject_n_display == "Biological subjects: unavailable"
    assert projection.optimization_seed_n_display == "Training seeds: unavailable"


def test_pending_entry_with_a_real_planned_count_is_labeled_planned() -> None:
    projection = project_for_display(_built(
        completion_state="PENDING", biological_subject_n=6, optimization_seed_n=None,
    ))
    assert projection.biological_subject_n_display == "Biological subjects: 6 (planned; not yet executed)"
    assert projection.optimization_seed_n_display == "Training seeds: unavailable"


# --- Requirement 6, bullet 4: survives manifest -> validator -> projection -

def test_sample_sizes_survive_the_full_file_based_pipeline(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "results"
    manifest_dir.mkdir()
    manifest = {
        "schema_version": "1.0.0",
        "manifest_id": f"{SENTINEL}-pipeline-manifest",
        "generated_by": "pytest",
        "generated_at": None,
        "entries": [
            _entry(experiment_id=f"{SENTINEL}-complete", biological_subject_n=3, optimization_seed_n=5),
            _entry(
                experiment_id=f"{SENTINEL}-blocked-with-plan",
                completion_state="BLOCKED_BY_DATA_ACCESS",
                biological_subject_n=8,
                optimization_seed_n=None,
            ),
        ],
    }
    (manifest_dir / "stage2_4_science_completion_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    envelope = FutureScienceManifestReader(repository_root=tmp_path).status()
    assert envelope.status == "INGESTED"
    by_id = {p.experiment_id: p for p in envelope.display_projections}

    complete = by_id[f"{SENTINEL}-complete"]
    assert complete.biological_subject_n == 3
    assert complete.optimization_seed_n == 5
    assert complete.biological_subject_n_display == "Biological subjects: 3"
    assert complete.optimization_seed_n_display == "Training seeds: 5"

    blocked = by_id[f"{SENTINEL}-blocked-with-plan"]
    assert blocked.biological_subject_n == 8
    assert blocked.biological_subject_n_display == "Biological subjects: 8 (planned; not yet executed)"
    assert blocked.optimization_seed_n is None
    assert blocked.optimization_seed_n_display == "Training seeds: unavailable"
