"""Guards the Day-11 engineering-readiness adapter's honesty invariants.

The endpoint must expose the Part-2 evidence WITHOUT fabricating a system total:
system power/mass stay NOT_READY, BOM PARTIAL, architecture UNRESOLVED, Pareto
NOT_READY, and no unknown is rendered as a zero quantity.
"""

from __future__ import annotations

from app.research.engineering_readiness import engineering_readiness
from app.schemas.engineering_readiness import ReadinessLevel


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
    assert r.raw_data_rate.partial_lower_bound_bps == 48068
    assert r.raw_data_rate.partial_lower_bound_kbps == 48.068
    assert r.raw_data_rate.radio_data_rate_status == "NOT_READY"


def test_candidate_burdens_match_frozen_evidence() -> None:
    r = _readiness()
    by_id = {c.candidate: c for c in r.candidates}
    assert set(by_id) == {"wrist_imu", "frontal_eog_horizontal", "second_ppg_site"}
    assert by_id["wrist_imu"].gate_status == "CONDITIONAL_FOR_TARGET"
    assert by_id["wrist_imu"].incremental_sensing_contacts == 0
    assert by_id["frontal_eog_horizontal"].gate_status == "CONDITIONAL_FOR_TARGET"
    assert by_id["frontal_eog_horizontal"].incremental_sensing_contacts == 2
    assert by_id["second_ppg_site"].gate_status == "DEPRIORITIZE_FOR_TARGET"
    assert by_id["second_ppg_site"].raw_data_rate_increment_bps == 28500


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
