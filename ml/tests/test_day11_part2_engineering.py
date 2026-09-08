"""Tests for the Day-11 Part-2 engineering artifacts
(ml/build_day11_part2_engineering.py + results/*_day11_part2*.json / *_day11.json).

Validate arithmetic, unit consistency, the no-unknown->zero discipline, the
reference-vs-final flags, mass-tier validity, BOM vocabulary, and that NO
component/AFE power is mislabelled as system power. They retrain nothing and
modify no source artifact.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
RESULTS = REPO_ROOT / "results"

from ml.build_day11_part2_engineering import (  # noqa: E402
    ADS1292R_ECG,
    BMI270_LP,
    BMI270_NORMAL,
    OPT3001_P,
    TMP117_P,
    p_mw,
)

POWER = RESULTS / "reference_power_budget_day11_part2.json"
SHARED = RESULTS / "reference_shared_electronics_day11.json"
DATARATE = RESULTS / "reference_data_rate_budget_day11.json"
MASS = RESULTS / "reference_mass_readiness_day11_part2.json"
BOM = RESULTS / "reference_bom_readiness_day11_part2.json"
BLOCKERS = RESULTS / "pareto_blocker_progress_day11_part2.json"
PART3 = RESULTS / "day11_part3_engineering_inputs.json"

BOM_VOCAB = {"REFERENCE_SELECTED", "AVAILABLE", "PARTIAL", "MISSING", "NOT_APPLICABLE"}
MASS_TIERS = {"Tier0", "Tier1", "Tier2", "Tier3", "Tier4"}


def _load(p: Path) -> dict:
    assert p.exists(), f"{p} must be built via ml/build_day11_part2_engineering.py"
    return json.loads(p.read_text())


@pytest.fixture(scope="module")
def power():
    return _load(POWER)


@pytest.fixture(scope="module")
def datarate():
    return _load(DATARATE)


@pytest.fixture(scope="module")
def bom():
    return _load(BOM)


@pytest.fixture(scope="module")
def mass():
    return _load(MASS)


# 1. power arithmetic P = V * I ----------------------------------------------
def test_power_arithmetic_pmw_helper():
    assert p_mw(3.3, 3.5) == pytest.approx(0.01155)
    assert p_mw(3.3, 1.8) == pytest.approx(0.00594)
    assert p_mw(1.8, 10.0) == pytest.approx(0.018)
    assert p_mw(1.8, 210.0) == pytest.approx(0.378)


def test_component_reference_powers_match_v_times_i(power):
    rop = power["reference_operating_points"]
    assert rop["skin_temperature"]["reference_power_mW"]["value"] == pytest.approx(TMP117_P)
    assert rop["light_sensor"]["reference_power_mW"]["value"] == pytest.approx(OPT3001_P)
    assert rop["wrist_imu"]["reference_operating_point"]["reference_power_mW"] == pytest.approx(BMI270_LP)
    assert rop["ecg_chest"]["afe_reference_power_mW"]["value"] == pytest.approx(ADS1292R_ECG)
    # ECG = 2 channels x 335 uW
    assert rop["ecg_chest"]["afe_reference_power_mW"]["value"] == pytest.approx(2 * 0.335)


def test_wrist_boundary_is_sum_of_parts_and_band_ordered(power):
    b = power["module_sensor_electronics_boundaries"]["wrist_sensor_electronics_reference_power"]
    light = b["wrist_light_case_band_mW"]
    cabin = b["cabin_light_case_band_mW"]
    max86141 = p_mw(1.8, 10.0)
    assert light["reference_point"] == pytest.approx(max86141 + BMI270_LP + TMP117_P + OPT3001_P)
    assert light["upper_bound_bmi270_normal"] == pytest.approx(max86141 + BMI270_NORMAL + TMP117_P + OPT3001_P)
    # cabin case excludes light -> strictly lower than wrist case
    assert cabin["reference_point"] == pytest.approx(light["reference_point"] - OPT3001_P)
    # band lower <= upper for both
    assert light["reference_point"] <= light["upper_bound_bmi270_normal"]
    assert cabin["reference_point"] <= cabin["upper_bound_bmi270_normal"]
    # Audit H7: this is a calculated reference scenario from datasheet-typical
    # values, NOT a guaranteed lower bound.
    assert b["is_lower_bound"] is False
    assert b["power_semantic_class"] == "CALCULATED_REFERENCE_SCENARIO_LED_EXCLUDED"
    assert b["component_value_basis"] == "DATASHEET_TYPICAL_REFERENCE"
    assert b["id"] == "WRIST_SENSOR_ELECTRONICS_REFERENCE_SCENARIO_LED_EXCLUDED"
    assert b["readiness"] == "PARTIAL_LED_EXCLUDED_REFERENCE_SCENARIO"


# 2. data-rate arithmetic: raw = channels x hz x bits ------------------------
def test_data_rate_arithmetic(datarate):
    for m in datarate["modalities"]:
        ch, hz, bits, raw = m["channels"], m["sample_rate_hz"], m["bits_per_sample"], m["raw_payload_bit_rate"]
        if None in (ch, hz, bits):
            assert raw is None, f"{m['modality']}: incomplete inputs must yield null raw rate, not 0"
        else:
            assert raw == ch * hz * bits, f"{m['modality']} raw payload mismatch"


def test_data_rate_known_points(datarate):
    got = {m["modality"]: m["raw_payload_bit_rate"] for m in datarate["modalities"]}
    assert got["wrist_ppg"] == 1216
    assert got["wrist_imu"] == 1536
    assert got["skin_temperature"] == 16
    assert got["ecg_chest"] == 12000
    assert got["frontal_eeg"] == 2400
    assert got["frontal_eog_horizontal"] == 2400
    assert got["second_ppg_site"] == 28500


def test_system_raw_total_is_partial_sum(datarate):
    st = datarate["system_raw_total"]
    expected = 1216 + 1536 + 16 + 12000 + (2400 + 2400) + 28500
    assert st["value_bps"] == expected == 48068
    assert st["value_kbps"] == pytest.approx(48.068)
    assert st["not_a_radio_rate"] is True
    # must be labelled partial / lower bound, not a closed system number
    assert "PARTIAL" in st["framing"].upper()
    assert any("bioz" in e.lower() for e in st["excludes"])


def test_eog_data_rate_matches_frozen_burden_artifact(datarate):
    burden = json.loads((RESULTS / "eog_operational_burden_day10.json").read_text())
    frozen = burden["burden_output"]["data_rate_increment"]["raw_payload_bit_rate_bit_per_second"]
    eog = next(m for m in datarate["modalities"] if m["modality"] == "frontal_eog_horizontal")
    assert eog["raw_payload_bit_rate"] == frozen == 2400


# 3. no unknown -> zero (unknowns are null + status, never a bare 0) ----------
def test_bioz_and_eeg_power_not_ready_not_zero(power):
    rop = power["reference_operating_points"]
    for key in ("thoracic_bioz", "leg_bioz"):
        assert rop[key]["power"]["status"] == "NOT_READY"
    head = rop["frontal_eeg_eog_head"]
    assert head["afe_reference_power"]["status"] == "NOT_READY"
    assert head["eog_incremental_power"]["status"] == "NOT_READY"
    # second PPG total not faked
    assert rop["second_ppg_site"]["reference_power_total"]["status"] == "NOT_READY"
    # wrist PPG LED contribution unresolved, variables all null (not 0)
    for var in rop["wrist_ppg"]["led_contribution"]["variables"].values():
        assert var["value"] is None and var["class"] == "UNKNOWN"


def test_cabin_zero_is_documented_placement_exclusion(power):
    # The only legitimate 0.0 is the cabin-placement light exclusion, and it is
    # explicitly labelled (not a silent unknown->zero).
    light = power["reference_operating_points"]["light_sensor"]
    assert light["cabin_case"]["value_mW"] == 0.0
    assert light["cabin_case"]["contributes_to_body_worn_power"] is False
    assert "not a false zero" in light["cabin_case"]["note"].lower()
    # wrist case is the positive component power
    assert light["wrist_case"]["value_mW"] == pytest.approx(OPT3001_P)


# 4. no component/AFE total mislabelled as system total ----------------------
def test_no_system_power_asserted(power):
    assert power["system_total_calculated"] is False
    assert power["system_average_power"]["status"] == "SYSTEM_AVERAGE_POWER_NOT_READY"
    assert power["reference_operating_points"]["ecg_chest"]["is_chest_module_power"] is False


def test_shared_electronics_all_non_final():
    shared = _load(SHARED)
    assert shared["final_part"] is False
    for block in ("mcu", "radio", "regulator_pmic", "battery"):
        assert shared[block]["final_part"] is False
    # regulator efficiency must NOT be a silent 90%
    assert shared["regulator_pmic"]["efficiency"]["value"] is None
    # MCU currents unresolved so no power leaks into a sum
    assert shared["mcu"]["active_current"]["value"] is None
    assert shared["battery"]["used_to_compute_runtime"] is False


# 5. mass-tier validity ------------------------------------------------------
def test_mass_tiers_valid_and_all_tier0(mass):
    assert set(mass["tier_definitions"].keys()) == MASS_TIERS
    for m in mass["modules"]:
        assert m["tier"] in MASS_TIERS
        assert m["tier"] == "Tier0"
        assert m["module_mass_available"] is False
    assert mass["system_mass_status"] == "SYSTEM_MASS_NOT_READY"
    assert set(mass["per_module_answer"].values()) <= MASS_TIERS


# 6. BOM vocabulary + reference-vs-final -------------------------------------
def test_bom_status_vocabulary(bom):
    assert set(bom["vocabulary"]) == BOM_VOCAB
    for module in bom["modules"]:
        for item in module["items"]:
            assert item["status"] in BOM_VOCAB, f"{module['module_id']}/{item['item']}: {item['status']}"


def test_bom_shared_subsystems_reference_selected(bom):
    # MCU/radio/regulator/battery advanced to REFERENCE_SELECTED in worn modules
    for module in bom["modules"]:
        if module["module_id"] in ("wrist_module", "chest_module", "head_module", "leg_module"):
            statuses = {it["item"]: it["status"] for it in module["items"]}
            for shared_item in ("mcu", "radio", "regulator", "battery"):
                assert statuses[shared_item] == "REFERENCE_SELECTED"
    assert "REFERENCE_SELECTED" in bom["part2_advance"]
    assert bom["not_a_final_bom"] is True
    assert bom["system_readiness"]["final_bom"] == "FINAL_BOM_NOT_SELECTED"


def test_eog_contact_increment_defensible_two(bom, power):
    head = next(m for m in bom["modules"] if m["module_id"] == "head_module")
    electrodes = next(it for it in head["items"] if it["item"] == "electrodes")
    assert electrodes["status"] == "PARTIAL"
    assert "2" in electrodes["note"]
    # power artifact keeps EOG shared-vs-standalone honest
    head_p = power["reference_operating_points"]["frontal_eeg_eog_head"]
    assert head_p["reference_operating_configuration"]["channels_enabled"] == 2
    assert head_p["reference_operating_configuration"]["spare_channels_remaining"] == 2


# 7. Pareto blocker progress: incomparability never downgraded ----------------
def test_cross_dataset_incomparability_not_downgraded():
    blockers = _load(BLOCKERS)
    inc = next(b for b in blockers["blockers"] if b["id"] == "cross_dataset_incomparability")
    assert inc["after_part2_readiness"] == "BLOCKER"
    assert inc["part3_may_downgrade"] is False
    assert blockers["pareto_status"].startswith("NOT_READY")


# 8. Part-3 inputs: candidates carry burdens, no architecture decision --------
def test_part3_inputs_structure():
    part3 = _load(PART3)
    ids = {c["candidate"] for c in part3["candidates"]}
    assert {"wrist_imu", "frontal_eog_horizontal", "second_ppg_site"} <= ids
    imu = next(c for c in part3["candidates"] if c["candidate"] == "wrist_imu")
    assert imu["incremental_sensing_contacts"] == 0
    assert imu["raw_data_rate_increment_bps"] == 1536
    eog = next(c for c in part3["candidates"] if c["candidate"] == "frontal_eog_horizontal")
    assert eog["incremental_sensing_contacts"] == 2
    assert eog["raw_data_rate_increment_bps"] == 2400
    ppg2 = next(c for c in part3["candidates"] if c["candidate"] == "second_ppg_site")
    assert ppg2["raw_data_rate_increment_bps"] == 28500
    assert all("Part-3" in w or "architecture" in w or "final" in w or "NOT_READY" in w or "rank" in w or "sum" in w
               for w in part3["warnings"])


# 9. determinism: rebuild is byte-identical ----------------------------------
def test_rebuild_is_deterministic():
    import subprocess

    before = {p.name: p.read_text() for p in RESULTS.glob("*day11_part2*.json")}
    before.update({p.name: p.read_text() for p in [SHARED, DATARATE, BLOCKERS, PART3]})
    subprocess.run([sys.executable, str(REPO_ROOT / "ml" / "build_day11_part2_engineering.py")], check=True)
    for name, text in before.items():
        assert (RESULTS / name).read_text() == text, f"{name} changed on rebuild — not deterministic"
