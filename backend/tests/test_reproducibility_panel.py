"""Adversarial tests for the artifact-driven reproducibility panel (audit H3).

These prove the panel NEVER emits a positive verification (PASS) from missing,
empty, malformed, or failed reproduction evidence (§5), that every displayed
number is derived from the artifact (§6), and that malformed input is normalized
to a typed status rather than raising an uncaught TypeError (§10)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.research.catalog import ResearchCatalog
from app.schemas.research import ReproComponentStatus


def _valid_artifact() -> dict:
    """A complete, internally-consistent reproduction artifact -> full PASS."""
    return {
        "environment": {"frozen_stack_verified": True, "status": "recorded", "source": "results/env.json"},
        "dataset_fingerprints": {"n_records_total": 266, "n_present": 266, "n_missing": 0},
        "ppg_dalia": {"checkpoints_verified": 20, "all_metrics_match": True, "max_abs_difference": 0.0},
        "robustness": {
            "n_conditions_canonical": 114,
            "n_conditions_reproduced": 114,
            "all_metrics_match": True,
            "max_abs_difference_bpm": 7.6e-06,
            "tolerance_bpm": 1e-4,
            "n_mismatches_beyond_tolerance": 0,
        },
        "n3_diagnostic": {"verified": True},
        "interaction_experiment": {
            "status": "RUN",
            "interaction_term_mean": 0.00306,
            "interaction_term_sd_sample_ddof1": 0.0434,
            "classification": "approximately_additive_or_unresolved",
        },
        "overall": "SCIENTIFIC_REPRODUCTION_PASS",
    }


def _write(root: Path, artifact, *, with_inventory: bool = True) -> ResearchCatalog:
    results = root / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / "day10_scientific_reproduction.json").write_text(
        json.dumps(artifact), encoding="utf-8"
    )
    if with_inventory:
        (results / "final_checkpoint_inventory_day14.json").write_text(
            json.dumps({"summary": {"n_total_referenced": 60, "n_with_external_archival": 60}}),
            encoding="utf-8",
        )
    return ResearchCatalog(repository_root=root)


def _status(summary, key) -> ReproComponentStatus:
    return next(c.status for c in summary.components if c.key == key)


def test_missing_artifact_omits_panel_never_pass(tmp_path):
    """No artifact at all -> panel omitted (None), i.e. no claim, never PASS."""
    (tmp_path / "results").mkdir()
    catalog = ResearchCatalog(repository_root=tmp_path)
    assert catalog._reproducibility() is None


def test_empty_object_is_partial_not_pass(tmp_path):
    catalog = _write(tmp_path, {}, with_inventory=False)
    summary = catalog._reproducibility()
    assert summary is not None
    assert summary.overall_status != "SCIENTIFIC_REPRODUCTION_PASS"
    assert summary.overall_status == "SCIENTIFIC_REPRODUCTION_PARTIAL"
    # An empty object declares no overall, so declared cross-check is False.
    assert summary.overall_matches_declared is False
    assert _status(summary, "environment") is ReproComponentStatus.UNAVAILABLE


def test_artifact_not_object_omits_panel_never_pass(tmp_path):
    """A non-object top-level artifact cannot be parsed into components, so the
    loader (`_read_json`) rejects it and the panel is omitted (None) — a safe
    no-claim state, never a false PASS."""
    catalog = _write(tmp_path, ["not", "an", "object"])
    assert catalog._reproducibility() is None


def test_malformed_field_does_not_raise_and_is_malformed(tmp_path):
    artifact = _valid_artifact()
    artifact["dataset_fingerprints"]["n_present"] = "two hundred"  # wrong type
    catalog = _write(tmp_path, artifact)
    summary = catalog._reproducibility()  # must not raise TypeError
    assert _status(summary, "datasets") is ReproComponentStatus.MALFORMED
    assert summary.overall_status == "SCIENTIFIC_REPRODUCTION_MALFORMED"


def test_failed_subresult_is_fail_not_pass(tmp_path):
    artifact = _valid_artifact()
    artifact["ppg_dalia"]["all_metrics_match"] = False
    catalog = _write(tmp_path, artifact)
    summary = catalog._reproducibility()
    assert _status(summary, "canonical") is ReproComponentStatus.FAIL
    assert summary.overall_status == "SCIENTIFIC_REPRODUCTION_FAIL"


def test_robustness_mismatch_is_fail(tmp_path):
    artifact = _valid_artifact()
    artifact["robustness"]["n_mismatches_beyond_tolerance"] = 3
    artifact["robustness"]["all_metrics_match"] = False
    catalog = _write(tmp_path, artifact)
    summary = catalog._reproducibility()
    assert _status(summary, "robustness") is ReproComponentStatus.FAIL
    assert summary.overall_status == "SCIENTIFIC_REPRODUCTION_FAIL"


def test_partial_dataset_is_partial(tmp_path):
    artifact = _valid_artifact()
    artifact["dataset_fingerprints"]["n_present"] = 260
    artifact["dataset_fingerprints"]["n_missing"] = 6
    catalog = _write(tmp_path, artifact)
    summary = catalog._reproducibility()
    assert _status(summary, "datasets") is ReproComponentStatus.PARTIAL
    assert summary.overall_status == "SCIENTIFIC_REPRODUCTION_PARTIAL"


def test_missing_inventory_makes_durability_unavailable_not_pass(tmp_path):
    catalog = _write(tmp_path, _valid_artifact(), with_inventory=False)
    summary = catalog._reproducibility()
    assert _status(summary, "checkpoint_durability") is ReproComponentStatus.UNAVAILABLE
    assert summary.overall_status != "SCIENTIFIC_REPRODUCTION_PASS"


def test_valid_artifact_is_pass_with_derived_numbers(tmp_path):
    catalog = _write(tmp_path, _valid_artifact())
    summary = catalog._reproducibility()
    assert summary.overall_status == "SCIENTIFIC_REPRODUCTION_PASS"
    assert summary.overall_matches_declared is True
    disp = {c.key: c.value_display for c in summary.components}
    assert disp["checkpoint_durability"] == "60/60 externally archived"
    assert disp["canonical"].startswith("20 checkpoints")
    assert "266/266" in disp["datasets"]


def test_derived_numbers_track_the_artifact(tmp_path):
    artifact = _valid_artifact()
    artifact["ppg_dalia"]["checkpoints_verified"] = 25  # not the canonical 20
    catalog = _write(tmp_path, artifact)
    summary = catalog._reproducibility()
    disp = {c.key: c.value_display for c in summary.components}
    assert disp["canonical"].startswith("25 checkpoints")  # tracks artifact, not a constant


def test_interaction_excluded_from_overall(tmp_path):
    """A missing interaction block must not drag overall below PASS (it is new
    evidence, not a reproduction of a prior claim)."""
    artifact = _valid_artifact()
    del artifact["interaction_experiment"]
    catalog = _write(tmp_path, artifact)
    summary = catalog._reproducibility()
    assert summary.overall_status == "SCIENTIFIC_REPRODUCTION_PASS"
    assert _status(summary, "interaction") is ReproComponentStatus.UNAVAILABLE


def test_environment_failure_is_fail(tmp_path):
    artifact = _valid_artifact()
    artifact["environment"]["frozen_stack_verified"] = False
    catalog = _write(tmp_path, artifact)
    summary = catalog._reproducibility()
    assert _status(summary, "environment") is ReproComponentStatus.FAIL
    assert summary.overall_status == "SCIENTIFIC_REPRODUCTION_FAIL"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
