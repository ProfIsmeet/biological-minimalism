"""Guards the Day-11 engineering-readiness adapter's honesty invariants.

The endpoint must expose the Part-2 evidence WITHOUT fabricating a system total:
system power/mass stay NOT_READY, BOM PARTIAL, architecture UNRESOLVED, Pareto
NOT_READY, and no unknown is rendered as a zero quantity.
"""

from __future__ import annotations

import json

from app.research.engineering_readiness import EngineeringReadinessReader, engineering_readiness
from app.schemas.engineering_readiness import QuantityStatus, ReadinessLevel


def _readiness():
    envelope = engineering_readiness.artifact()
    assert envelope.availability.value == "available"
    assert envelope.readiness is not None
    return envelope.readiness


def test_system_states_remain_not_ready() -> None:
    r = _readiness()
    assert r.system_average_power_status == "SYSTEM_AVERAGE_POWER_NOT_READY"
    assert r.system_mass_status == "SYSTEM_MASS_NOT_READY"
    assert r.bom_status == "PARTIAL"
    assert r.formal_pareto_status == "FORMAL_PARETO_NOT_READY"
    assert r.final_architecture_status == "UNRESOLVED"


def test_raw_data_rate_is_partial_lower_bound_not_radio() -> None:
    r = _readiness()
    # The 48068 value is now READ from the frozen budget (AVAILABLE), not a fallback.
    assert r.raw_data_rate.value.status == QuantityStatus.AVAILABLE
    assert r.raw_data_rate.value.value == 48068.0
    assert r.raw_data_rate.status == "PARTIAL_LOWER_BOUND"
    assert r.raw_data_rate.radio_data_rate_status == "NOT_READY"


def test_candidate_burdens_match_frozen_evidence() -> None:
    r = _readiness()
    by_id = {c.candidate: c for c in r.candidates}
    assert set(by_id) == {"wrist_imu", "frontal_eog_horizontal", "second_ppg_site"}
    assert by_id["wrist_imu"].gate_status == "CONDITIONAL_FOR_TARGET"
    # A genuine present 0 stays AVAILABLE 0 (colocated wrist), not fabricated.
    assert by_id["wrist_imu"].incremental_sensing_contacts.status == QuantityStatus.AVAILABLE
    assert by_id["wrist_imu"].incremental_sensing_contacts.value == 0.0
    assert by_id["frontal_eog_horizontal"].incremental_sensing_contacts.value == 2.0
    assert by_id["second_ppg_site"].gate_status == "DEPRIORITIZE_FOR_TARGET"
    assert by_id["second_ppg_site"].raw_data_rate_increment.value == 28500.0


def test_missing_contacts_and_rate_are_unknown_never_zero(tmp_path) -> None:
    """Audit H4/SOFT-1/SOFT-2: a MISSING field must surface UNKNOWN(value=None),
    never a fabricated 0 and never the 48068 fallback."""
    results = tmp_path / "results"
    results.mkdir()
    # Candidate with contacts + data-rate fields OMITTED entirely.
    (results / "day11_part3_engineering_inputs.json").write_text(
        json.dumps({
            "part1_head_commit": "deadbeef",
            "candidates": [{
                "candidate": "wrist_imu",
                "scientific_target": "HR",
                "gate_status": "CONDITIONAL_FOR_TARGET",
                "mass_tier": "Tier0",
                "bom_readiness": "PARTIAL",
                # incremental_sensing_contacts and raw_data_rate_increment_bps ABSENT
            }],
        }),
        encoding="utf-8",
    )
    # Data-rate budget WITHOUT system_raw_total.value_bps.
    (results / "reference_data_rate_budget_day11.json").write_text(
        json.dumps({"system_raw_total": {"framing": "PARTIAL LOWER BOUND"}}),
        encoding="utf-8",
    )
    reader = EngineeringReadinessReader(repository_root=tmp_path)
    env = reader.artifact()
    r = env.readiness
    assert r is not None
    cand = r.candidates[0]
    assert cand.incremental_sensing_contacts.status == QuantityStatus.UNKNOWN
    assert cand.incremental_sensing_contacts.value is None
    assert cand.incremental_sensing_contacts.display == "Unknown"
    assert cand.raw_data_rate_increment.status == QuantityStatus.UNKNOWN
    assert cand.raw_data_rate_increment.value is None
    # System total must be UNKNOWN, NOT 48068.
    assert r.raw_data_rate.value.status == QuantityStatus.UNKNOWN
    assert r.raw_data_rate.value.value is None
    assert r.raw_data_rate.status == "UNKNOWN"


def test_null_and_malformed_values_are_unknown_not_crash(tmp_path) -> None:
    """Explicit null / non-numeric fields normalize to UNKNOWN, never TypeError."""
    results = tmp_path / "results"
    results.mkdir()
    (results / "day11_part3_engineering_inputs.json").write_text(
        json.dumps({
            "candidates": [{
                "candidate": "second_ppg_site",
                "incremental_sensing_contacts": None,          # explicit null
                "raw_data_rate_increment_bps": "twenty-eight", # malformed
            }],
        }),
        encoding="utf-8",
    )
    (results / "reference_data_rate_budget_day11.json").write_text(
        json.dumps({"system_raw_total": {"value_bps": "lots"}}),  # malformed total
        encoding="utf-8",
    )
    reader = EngineeringReadinessReader(repository_root=tmp_path)
    env = reader.artifact()  # must not raise
    r = env.readiness
    cand = r.candidates[0]
    assert cand.incremental_sensing_contacts.status == QuantityStatus.UNKNOWN
    assert cand.raw_data_rate_increment.status == QuantityStatus.UNKNOWN
    assert r.raw_data_rate.value.status == QuantityStatus.UNKNOWN


def test_unknown_power_is_not_ready_never_zero() -> None:
    r = _readiness()
    by_id = {c.candidate: c for c in r.candidates}
    # EOG and second-PPG reference power are unquantified -> NOT_READY, not "0 mW".
    for cid in ("frontal_eog_horizontal", "second_ppg_site"):
        cand = by_id[cid]
        assert cand.reference_component_power_status == ReadinessLevel.NOT_READY
        assert "0 mW" not in cand.reference_component_power_display
    # Panel rows for power/mass carry explicit NOT_READY, never a zero value.
    power_row = next(row for row in r.panel if row.dimension == "System average power")
    mass_row = next(row for row in r.panel if row.dimension == "System mass")
    assert power_row.status == ReadinessLevel.NOT_READY
    assert mass_row.status == ReadinessLevel.NOT_READY
    assert power_row.value_display == "Not ready"
    assert mass_row.value_display == "Not ready"
