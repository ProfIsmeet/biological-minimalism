"""Regression test for Codex finding H-02: the old ~20.6%/23% PPG-only->
PPG+IMU headline (capacity-confounded, Model A 8,065 params vs Model B
28,865/29,089 params) must always be labeled HISTORICAL_CAPACITY_CONFOUNDED
wherever it appears, never presented as capacity-controlled evidence."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load(name):
    return json.loads((REPO_ROOT / "results" / name).read_text())


def test_sensor_value_matrices_label_confounded_result():
    for fname in (
        "sensor_value_master_matrix_stage4.json",
        "sensor_value_master_matrix_post_stage2_4.json",
        "sensor_value_master_matrix_stage3_complete.json",
    ):
        d = _load(fname)
        row = next(r for r in d["rows"] if r["experiment"].startswith("PPG-DaLiA"))
        assert "HISTORICAL_CAPACITY_CONFOUNDED" in row["exact_result"]
        assert "capacity-controlled" in row["safe_claim"]
        assert "0.605" in row["safe_claim"] or "A_cap" in row["safe_claim"]


def test_safe_claim_never_cites_bare_percentage_as_capacity_controlled():
    for fname in (
        "sensor_value_master_matrix_stage4.json",
        "sensor_value_master_matrix_post_stage2_4.json",
        "sensor_value_master_matrix_stage3_complete.json",
    ):
        d = _load(fname)
        row = next(r for r in d["rows"] if r["experiment"].startswith("PPG-DaLiA"))
        # the percentage may appear ONLY inside an explicit warning not to cite it
        for bad in ("~23%", "20.6%"):
            if bad in row["safe_claim"]:
                assert "historical" in row["safe_claim"].lower() or "never cite" in row["safe_claim"].lower()


def test_architecture_evidence_handoff_labels_confounded_result():
    d = _load("architecture_evidence_handoff_stage4.json")
    candidate = next(c for c in d["candidates"] if "wrist PPG" in c["sensor_site"])
    joined = " ".join(candidate["positive_evidence"])
    assert "HISTORICAL_CAPACITY_CONFOUNDED" in joined
    assert "0.605" in joined
