"""Section 21 regression tests for the Stage 3 final source-of-truth
remediation sprint: LBNP resolver returns the corrected v2 result, the old
result fails as governing evidence, all current-evidence consumers cite
the corrected numbers/classification, and cross-cutting counts
(HMC/tests/Galaxy split) are internally consistent."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load(name):
    return json.loads((REPO_ROOT / "results" / name).read_text())


def test_current_lbnp_result_is_v2_protocol_compliant():
    d = _load("lbnp_thoracic_eis_stage3_v2_protocol_compliant.json")
    assert d["classification"] == "COMPLETE_MIXED"
    agg = d["aggregate"]
    assert abs(agg["A_minus_B_mean"] - (-0.452385)) < 1e-3
    assert abs(agg["C_minus_B_mean"] - (-1.293281)) < 1e-3
    assert agg["n_subjects_total"] == 12


def test_old_lbnp_result_marked_historical_and_not_governing():
    d = _load("lbnp_thoracic_eis_stage3.json")
    assert d["status"] == "HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL"
    assert "governing_evidence_note" in d
    assert "MUST NOT be consumed" in d["governing_evidence_note"]


def test_architecture_handoff_cites_corrected_lbnp_not_old():
    d = _load("architecture_evidence_handoff_stage4.json")
    c = next(c for c in d["candidates"] if c["sensor_site"] == "thoracic bio-impedance spectroscopy (EIS)")
    joined = " ".join(c["negative_evidence"])
    assert "-0.452" in joined or "COMPLETE_MIXED" in joined
    assert "COMPLETE_MIXED" in joined
    # old stale numbers must not appear as the current figure (only allowed
    # inside an explicit historical/superseded disclosure sentence)
    assert "-2.24" not in joined or "HISTORICAL_SUPERSEDED" in joined
    assert d["final_architecture_status"] == "UNRESOLVED"


def test_sensor_value_matrix_cites_corrected_lbnp():
    d = _load("sensor_value_master_matrix_stage3_complete.json")
    row = next(r for r in d["rows"] if "LBNP" in r.get("experiment", ""))
    assert row["replication_state"] == "COMPLETE_MIXED"
    assert "20.973" in row["exact_result"] or "-0.452" in row["exact_result"]
    assert "HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL" in row["exact_result"]


def test_consolidated_provenance_points_to_corrected_lbnp():
    d = _load("stage3_galaxyppg_lbnp_consolidated_provenance.json")
    eis = d["lbnp"]["eis_result"]
    assert "v2_protocol_compliant" in eis
    assert "CURRENT" in eis


def test_stage3_manifest_lbnp_is_complete_mixed():
    d = _load("stage3_science_completion_manifest.json")
    lbnp = next(x for x in d["datasets"] if x["dataset"] == "LBNP")
    assert lbnp["replication_class"] == "COMPLETE_MIXED"


def test_no_current_governing_artifact_cites_old_lbnp_numbers_uncontextualized():
    """Section 16/22: for every current (non-historical) artifact that
    mentions the old stale numbers, the mention must be inside an explicit
    historical/superseded disclosure - never presented bare as current."""
    current_files = [
        "architecture_evidence_handoff_stage4.json",
        "sensor_value_master_matrix_stage3_complete.json",
        "stage3_galaxyppg_lbnp_consolidated_provenance.json",
        "stage3_science_completion_manifest.json",
    ]
    stale_markers = ["27.62", "29.86", "29.83"]
    for fname in current_files:
        raw = json.dumps(_load(fname))
        for marker in stale_markers:
            if marker in raw:
                # must be near a historical/superseded disclosure
                idx = raw.index(marker)
                window = raw[max(0, idx - 300):idx + 300]
                assert "HISTORICAL" in window or "SUPERSEDED" in window or "OUT_OF_PROTOCOL" in window, (
                    f"stale marker {marker} found in {fname} without historical disclosure nearby"
                )


def test_hmc_current_state_internally_consistent():
    d = _load("hmc_current_download_inventory.json")
    state = d["current_authoritative_state"]
    assert state["n_complete_usable_recordings"] == state["n_sha256_verified"] + state["n_unverified_but_complete"]
    manifest = _load("stage3_science_completion_manifest.json")
    hmc = next(x for x in manifest["datasets"] if x["dataset"] == "HMC")
    assert hmc["actual_biological_n"] == state["n_complete_usable_recordings"]


def test_galaxy_bounded_split_description_is_12_3_3():
    d = _load("galaxyppg_hr_corrected_eligibility_stage3.json")
    assert "12/3/3" in d["scope_disclosure"]
    split = _load("galaxyppg_split_stage3_corrected_eligibility.json")
    assert len(split["train"]) == 12 and len(split["val"]) == 3 and len(split["test"]) == 3
