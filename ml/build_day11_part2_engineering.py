"""Day-11 Part-2 engineering builder — reference power / data-rate / mass / BOM.

Deterministically derives the MAXIMUM DEFENSIBLE reference engineering state from
the frozen Day-11 Part-1 inputs, without inventing unknowns. Emits:

  results/reference_power_budget_day11_part2.json
  results/reference_shared_electronics_day11.json
  results/reference_data_rate_budget_day11.json
  results/reference_mass_readiness_day11_part2.json
  results/reference_bom_readiness_day11_part2.json
  results/pareto_blocker_progress_day11_part2.json
  results/day11_part3_engineering_inputs.json

Discipline (inherited from Part-1, docs/DAY11_PART1_HANDOFF.md):
  * Every numeric value carries a source class; unknowns are null/status, never 0.
  * Component/AFE-boundary powers are NOT summed into a system power number.
  * A sensor-electronics BOUNDARY (explicitly LED/MCU/radio/regulator/battery
    excluded, a calculated reference scenario) is a labelled partial, not system power.
  * REFERENCE selections are representative classes, final_part = false.

Run:  python ml/build_day11_part2_engineering.py
Source of truth: results/operational_cost_catalog.json,
                 results/power_calculation_inputs_day11.json,
                 results/hardware_topology_contract.json,
                 results/eog_operational_burden_day10.json
This script performs NO training and modifies NO source artifact.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
PART1_BASE_COMMIT = "e414ef5c0c2b00f7d80b681848d37d7c59e523b5"
PART1_HEAD_COMMIT = "a43b7aa8e65349d703a0eb1ef34307e3a00ab4c1"

SOURCE_CLASSES = {
    "DATASHEET_DIRECT",
    "DATASHEET_CALCULATED",
    "REFERENCE_SCHEDULE_ASSUMPTION",
    "ARCHITECTURE_ASSUMPTION",
    "MEASURED_IN_PROJECT",
    "UNKNOWN",
}


def _round(x: float | None, n: int = 5) -> float | None:
    return None if x is None else round(x, n)


# --------------------------------------------------------------------------- #
# Frozen datasheet points (mirrored from Part-1 inputs / catalog, cited).      #
# Power derivation is transparent: P[mW] = V[V] * I[uA] / 1000.                #
# --------------------------------------------------------------------------- #
def p_mw(v_volt: float, i_ua: float) -> float:
    return v_volt * i_ua / 1000.0


TMP117_P = p_mw(3.3, 3.5)          # 0.01155 mW @1 Hz, averaging off
OPT3001_P = p_mw(3.3, 1.8)         # 0.00594 mW continuous conversion
BMI270_LP = p_mw(1.8, 10.0)        # 0.018 mW accel-only low-power @25 Hz
BMI270_NORMAL = p_mw(1.8, 210.0)   # 0.378 mW accel-only normal @max ODR
MAX86141_AFE_CEIL = p_mw(1.8, 10.0)  # <=0.018 mW AFE readout floor (LED excluded)
ADS1292R_ECG = 2 * 0.335           # 0.67 mW = 2 x 335 uW/ch @250 s/s


def build_power_budget() -> dict:
    # Wrist sensing-electronics reference boundary (LED-excluded reference scenario, not a bound).
    # reference-point uses BMI270 low-power point; upper uses BMI270 normal.
    wrist_with_light_ref = MAX86141_AFE_CEIL + BMI270_LP + TMP117_P + OPT3001_P
    wrist_with_light_up = MAX86141_AFE_CEIL + BMI270_NORMAL + TMP117_P + OPT3001_P
    wrist_no_light_ref = MAX86141_AFE_CEIL + BMI270_LP + TMP117_P
    wrist_no_light_up = MAX86141_AFE_CEIL + BMI270_NORMAL + TMP117_P

    return {
        "artifact_id": "biological-minimalism-reference-power-budget-day11-part2-v1",
        "schema_version": "1.0.0",
        "part": "DAY11_PART2",
        "part1_base_commit": PART1_BASE_COMMIT,
        "part1_head_commit": PART1_HEAD_COMMIT,
        "statement": (
            "Maximum-defensible reference power state. Four accounting layers are kept "
            "separate: L1 component electrical spec, L2 reference acquisition power at one "
            "explicit operating point, L3 reference module sensor-electronics boundary "
            "(LED/MCU/radio/regulator/battery EXCLUDED), L4 system average power (NOT "
            "computed). No component powers are summed into a system number. Unknowns are "
            "null + status, never 0."
        ),
        "system_total_calculated": False,
        "prohibited": [
            "Do NOT sum component active powers into a system power number.",
            "Do NOT treat the LED-excluded wrist boundary as deployable optical power.",
            "Do NOT use the AD5940 6.5 uA potentiostat point as active BioZ power.",
            "Do NOT assert head-module (EEG/EOG) average power (operating point NOT_READY).",
        ],
        "reference_operating_points": {
            "wrist_ppg": {
                "component": "MAX86141",
                "level1_afe_current": {"max": 10.0, "unit": "uA", "class": "DATASHEET_DIRECT",
                                       "note": "optical readout floor @25 s/s; LED supply separate"},
                "voltage": {"value": 1.8, "unit": "V", "class": "DATASHEET_DIRECT"},
                "level2_afe_reference_power": {"max": _round(MAX86141_AFE_CEIL), "unit": "mW",
                                               "class": "DATASHEET_CALCULATED",
                                               "note": "<=1.8V x 10uA AFE floor; 64 Hz-mode current UNKNOWN"},
                "led_contribution": {
                    "status": "NOT_READY",
                    "formula": "P_LED_avg = N_active_LEDs * I_LED * V_LED_forward * (t_pulse * f_pulse)",
                    "variables": {
                        "N_active_LEDs": {"value": None, "class": "UNKNOWN",
                                          "note": "MAX86141 has 3 LED drivers; active count for the wrist optical stack not frozen"},
                        "I_LED_peak": {"value": None, "class": "UNKNOWN", "note": "drive current programmable; not frozen"},
                        "V_LED_forward": {"value": None, "class": "UNKNOWN", "note": "emitter forward voltage; emitters not selected"},
                        "t_pulse": {"value": None, "class": "UNKNOWN"},
                        "f_pulse": {"value": None, "class": "UNKNOWN", "note": "pulse rate tied to unfrozen 64 Hz optical sequencing"},
                    },
                    "note": "LED average power DOMINATES optical acquisition and is the OPEN wrist power blocker. No total is faked.",
                },
                "reference_acquisition_power_total": {"status": "NOT_READY",
                                                      "reason": "AFE floor known; dominant LED term unresolved. Total not asserted."},
                "readiness": "AFE_REFERENCE_ONLY_LED_EXCLUDED",
            },
            "wrist_imu": {
                "component": "BMI270",
                "task": "TASK_B_frozen_reference_operating_point",
                "reference_operating_point": {
                    "id": "REFERENCE_IMU_OPERATING_POINT",
                    "mode": "accelerometer-only, low-power sub-mode",
                    "gyroscope_enabled": False,
                    "gyro_rationale": "Current wrist scientific function (HR/motion, 3-axis 32 Hz) does not require gyroscope; gyro left disabled.",
                    "channels": 3,
                    "scientific_rate_hz": 32,
                    "nearest_documented_datasheet_point_hz": 25,
                    "odr_caveat": ("32 Hz is between the documented 25 Hz low-power point and max-ODR normal point. "
                                   "BMI270 supports an ODR >=32 Hz (e.g. 50 Hz); its exact current is not separately "
                                   "published, so the 25 Hz low-power point is used as the documented reference floor."),
                    "current_uA": 10.0,
                    "voltage_V": 1.8,
                    "reference_power_mW": _round(BMI270_LP),
                    "class": "DATASHEET_CALCULATED",
                },
                "retained_full_band": {"min": _round(BMI270_LP), "max": _round(BMI270_NORMAL), "unit": "mW",
                                       "class": "DATASHEET_CALCULATED",
                                       "note": "10-210 uA accel-only envelope x 1.8 V; kept for uncertainty, NOT the reference point"},
                "exclusions": ["MCU", "radio", "regulator", "battery", "idle/sleep duty"],
                "readiness": "REFERENCE_OPERATING_POINT_FROZEN",
            },
            "skin_temperature": {
                "component": "TMP117",
                "task": "TASK_C",
                "level1_current": {"value": 3.5, "unit": "uA", "class": "DATASHEET_DIRECT", "note": "avg @1 Hz, averaging off"},
                "voltage": {"value": 3.3, "unit": "V", "class": "ARCHITECTURE_ASSUMPTION"},
                "reference_power_mW": {"value": _round(TMP117_P), "class": "DATASHEET_CALCULATED"},
                "schedule_mapping": "1 Hz conversion, averaging off — maps to a real TMP117 continuous-conversion mode",
                "boundary": "component_only",
                "exclusions": ["MCU", "radio", "regulator", "shutdown-mode duty if intermittent"],
                "readiness": "COMPONENT_REFERENCE_POWER_AVAILABLE",
            },
            "light_sensor": {
                "component": "OPT3001-Q1-class",
                "task": "TASK_C",
                "level1_current": {"value": 1.8, "unit": "uA", "class": "DATASHEET_DIRECT"},
                "voltage": {"value": 3.3, "unit": "V", "class": "ARCHITECTURE_ASSUMPTION"},
                "reference_power_mW": {"value": _round(OPT3001_P), "class": "DATASHEET_CALCULATED"},
                "placement": "LOCATION_UNRESOLVED",
                "wrist_case": {"contributes_to_wrist_electronics_power": True, "value_mW": _round(OPT3001_P)},
                "cabin_case": {"contributes_to_body_worn_power": False, "value_mW": 0.0,
                               "note": "If cabin/ambient-mounted, ZERO body-worn burden. Not a false zero — a placement-conditional exclusion."},
                "boundary": "component_only",
                "readiness": "COMPONENT_REFERENCE_POWER_AVAILABLE_PLACEMENT_CONDITIONAL",
            },
            "ecg_chest": {
                "component": "ADS1292R",
                "task": "TASK_D",
                "id": "REFERENCE_ECG_AFE_POWER",
                "per_channel_uW": 335.0,
                "channels": 2,
                "sample_rate_sps": 250,
                "afe_reference_power_mW": {"value": _round(ADS1292R_ECG), "class": "DATASHEET_CALCULATED",
                                           "note": "2 x 335 uW/ch datasheet AFE point @250 s/s"},
                "supply_note": "Per-channel power point used directly; single combined rail not asserted.",
                "internal_blocks_note": "335 uW/ch is the datasheet per-channel AFE figure; lead-off excitation and external bias are NOT included.",
                "exclusions": ["MCU", "radio", "electrodes", "lead-off excitation", "regulator", "battery"],
                "readiness": "ECG_AFE_REFERENCE_POWER_AVAILABLE",
                "is_chest_module_power": False,
            },
            "frontal_eeg_eog_head": {
                "components": ["ADS1299-4-class (EEG)", "EOG on shared spare channel"],
                "task": "TASK_E_and_EOG_shared_case",
                "reference_operating_configuration": {
                    "id": "REFERENCE_HEAD_AFE_OPERATING_CONFIG",
                    "channels_enabled": 2,
                    "channel_breakdown": "1 EEG (Fpz-Cz derivation) + 1 horizontal EOG on a spare channel of the same 4-ch AFE",
                    "spare_channels_remaining": 2,
                    "afe_capacity_channels": 4,
                    "scientific_data_rate_hz": 100,
                    "nearest_supported_hardware_odr_sps": 250,
                    "odr_caveat": "ADS1299 minimum ODR is 250 SPS; the 100 Hz Sleep-EDF scientific rate maps to the 250 SPS nearest supported mode.",
                    "gain": {"value": 24, "class": "ARCHITECTURE_ASSUMPTION", "note": "standard EEG PGA gain; does not materially change data rate"},
                    "internal_reference_used": True,
                    "bias_drl_used": True,
                    "bias_contacts_shared": True,
                    "lead_off_detection": "disabled (not required by the current sleep-staging scientific use case)",
                    "supply": {"avdd_unipolar_v": 5.0, "avdd_bipolar_v": 2.5, "dvdd_v": 3.3,
                               "class": "DATASHEET_DIRECT",
                               "source": "TI ADS1299 datasheet (SBAS499), Electrical Characteristics — supply section (web-verified 2026-09)"},
                },
                "afe_reference_power": {
                    "status": "NOT_READY",
                    "reason": ("The per-channel power-dissipation table row (low-power vs high-resolution mode, "
                               "incl. internal reference + bias) could not be verified to an exact citable value in "
                               "this environment (no PDF text extraction; secondary search did not corroborate a "
                               "specific figure). Per Part-1 discipline, no head power is asserted."),
                    "exact_unlock": ("ADS1299 datasheet per-channel power dissipation at low-power mode, 250 SPS, "
                                     "gain 24, internal reference + bias ON, for the 2 enabled channels; plus session duty schedule."),
                },
                "eog_incremental_power": {
                    "status": "NOT_READY",
                    "note": ("EOG is ONE additional biopotential channel on the already-counted head-module AFE, sharing "
                             "reference/bias (REFERENCE_SHARED_HEAD_MODULE). Incremental electrical cost is not zero and not "
                             "quantified; it cannot be isolated without the per-channel head-AFE operating point. Adding EOG "
                             "changes enabled channels 1->2 (2 spare remain), adds NO new front-end circuitry in the shared case, "
                             "and adds +2 lateral-ocular sensing electrodes (wiring/electrode burden, not a new module)."),
                    "shared_vs_standalone": "Shared-reference: no new AFE/reference/bias. Standalone: separate front-end (up to +4 contacts, possibly +1 module).",
                },
                "readiness": "OPERATING_CONFIG_SPECIFIED_POWER_NOT_READY",
            },
            "thoracic_bioz": {
                "component": "AD5940-class",
                "task": "TASK_F",
                "id": "REFERENCE_BIOZ_EXPLORATORY_OPERATING_POINT",
                "canonical_deployment_status": "UNRESOLVED",
                "required_for_valid_measurement": [
                    "excitation waveform generation", "excitation frequency", "excitation amplitude",
                    "measurement ADC path", "internal DFT/processing engine usage", "measurement duration",
                    "measurement cadence", "electrode configuration",
                ],
                "power": {"status": "NOT_READY",
                          "reason": "No frozen BioZ operating protocol exists; the 6.5 uA potentiostat point is NOT BioZ measurement power. No exploratory point can be sourced cleanly, so power stays NOT_READY."},
                "readiness": "NOT_READY",
            },
            "leg_bioz": {
                "component": "AD5940-class (separate instance)",
                "task": "TASK_F_leg",
                "module_separation_note": "Leg BioZ is a separate body region and likely separate module from thoracic BioZ; AFE operating point may be reused but module/system burden differs.",
                "power": {"status": "NOT_READY", "reason": "Same as thoracic: no frozen excitation/cadence protocol; potentiostat quiescent != measurement power."},
                "readiness": "NOT_READY",
            },
            "second_ppg_site": {
                "component": "MAX86141-class extension",
                "task": "TASK_G",
                "scientific_rate_hz": 500,
                "rate_rationale": "500 Hz is the PhysioNet PTT dataset acquisition rate (proximal red/IR/green). It is a dataset sampling rate, NOT a frozen PTT protocol requirement for deployment.",
                "level2_afe_floor_mW": {"max": _round(MAX86141_AFE_CEIL), "class": "DATASHEET_CALCULATED",
                                        "note": "<10uA @25 s/s AFE floor; NOT the 500 Hz 3-wavelength sequencing current"},
                "led_contribution": {"status": "NOT_READY", "formula": "P_LED_avg = N_active_LEDs * I_LED * V_LED_forward * (t_pulse * f_pulse)",
                                     "note": "3 wavelengths (R/IR/G) x LED currents dominate; not frozen"},
                "module_boundary": "OPEN (shared / tethered / standalone undecided)",
                "reference_power_total": {"status": "NOT_READY",
                                          "reason": "LED power + 500 Hz AFE sequencing current + module boundary all open. Do NOT reuse wrist PPG power (different schedule)."},
                "readiness": "NOT_READY",
            },
        },
        "module_sensor_electronics_boundaries": {
            "note": ("Level-3 partials. LED, MCU, radio, regulator loss, battery, storage ALL excluded. "
                     "These are LED-excluded CALCULATED REFERENCE SCENARIOS built from datasheet-typical "
                     "operating points, NOT module system power and NOT guaranteed bounds (audit H7)."),
            "wrist_sensor_electronics_reference_power": {
                "id": "WRIST_SENSOR_ELECTRONICS_REFERENCE_SCENARIO_LED_EXCLUDED",
                "includes": ["MAX86141 AFE floor (LED-excluded)", "BMI270 reference operating point (accel-only low-power)",
                             "TMP117", "OPT3001 (wrist case only)"],
                "wrist_light_case_band_mW": {"reference_point": _round(wrist_with_light_ref),
                                             "upper_bound_bmi270_normal": _round(wrist_with_light_up),
                                             "class": "DATASHEET_CALCULATED"},
                "cabin_light_case_band_mW": {"reference_point": _round(wrist_no_light_ref),
                                             "upper_bound_bmi270_normal": _round(wrist_no_light_up),
                                             "class": "DATASHEET_CALCULATED",
                                             "note": "light excluded (cabin placement)"},
                # Audit H7: NOT a guaranteed lower bound. The included AFE/IMU numbers are
                # datasheet-typical (DATASHEET_TYPICAL_REFERENCE), which are not guaranteed
                # minima, so the aggregate is a calculated reference scenario, not a bound.
                "power_semantic_class": "CALCULATED_REFERENCE_SCENARIO_LED_EXCLUDED",
                "is_lower_bound": False,
                "component_value_basis": "DATASHEET_TYPICAL_REFERENCE",
                "directional_note": ("Excluding the dominant MAX86141 LED average power means realized "
                                     "sensing-electronics power is DIRECTIONALLY higher than this reference; "
                                     "however, because the included AFE/IMU values are datasheet-typical "
                                     "(not guaranteed minima), this figure is NOT a guaranteed lower bound."),
                "excludes": ["all LED/emitter power", "MCU", "radio", "regulator loss", "battery", "storage"],
                "readiness": "PARTIAL_LED_EXCLUDED_REFERENCE_SCENARIO",
            },
            "chest_sensor_electronics_reference_power": {
                "id": "CHEST_SENSOR_ELECTRONICS_REFERENCE_POWER",
                "ecg_afe_only_mW": _round(ADS1292R_ECG),
                "bioz_status": "NOT_READY",
                "module_boundary_status": "NOT_READY",
                "reason": "Only the ECG AFE (0.67 mW) is defensible; thoracic BioZ active power is NOT_READY, so a chest sensor-electronics boundary cannot be closed.",
                "excludes": ["thoracic BioZ (NOT_READY)", "MCU", "radio", "electrodes", "lead-off excitation", "regulator", "battery"],
                "readiness": "ECG_AFE_ONLY_MODULE_BOUNDARY_NOT_READY",
            },
            "head_sensor_electronics_reference_power": {"id": "HEAD_SENSOR_ELECTRONICS_REFERENCE_POWER",
                                                        "readiness": "NOT_READY",
                                                        "reason": "EEG/EOG AFE operating-point power NOT_READY."},
            "leg_sensor_electronics_reference_power": {"id": "LEG_SENSOR_ELECTRONICS_REFERENCE_POWER",
                                                       "readiness": "NOT_READY", "reason": "BioZ power NOT_READY."},
            "second_ppg_sensor_electronics_reference_power": {"id": "SECOND_PPG_SENSOR_ELECTRONICS_REFERENCE_POWER",
                                                              "readiness": "NOT_READY",
                                                              "reason": "LED power + 500 Hz sequencing + module boundary open."},
        },
        "system_average_power": {
            "status": "SYSTEM_AVERAGE_POWER_NOT_READY",
            "highest_defensible_level": ("REFERENCE_SENSOR_ELECTRONICS_POWER_AVAILABLE_FOR_WRIST (LED-excluded reference scenario) "
                                         "+ ECG_AFE_REFERENCE_POWER_FOR_CHEST; SYSTEM_AVERAGE_POWER_NOT_READY"),
            "blockers": ["LED optical power (wrist + 2nd PPG)", "EEG/EOG head-AFE operating point", "thoracic + leg BioZ operating point",
                         "MCU/radio/regulator identity + power", "deployable duty cycles", "regulator efficiency", "battery architecture"],
        },
    }


def build_shared_electronics() -> dict:
    return {
        "artifact_id": "biological-minimalism-reference-shared-electronics-day11-v1",
        "schema_version": "1.0.0",
        "part": "DAY11_PART2",
        "final_part": False,
        "statement": ("Reference shared-electronics CLASSES for an engineering calculation case only — NOT a final BOM and "
                      "NOT a procurement decision. Classes are representative of a low-power wearable; exact currents are "
                      "kept unresolved where not frozen so that NO system power is implied."),
        "mcu": {
            "reference_class": "ARM Cortex-M4F-class BLE wearable SoC (e.g. Nordic nRF52-class)",
            "selection_criteria_met": ["SPI/I2C sensor interfaces", "aggregate reference data rate (tens of kbps)",
                                       "local buffering + timestamping", "basic preprocessing", "integrated BLE control"],
            "chosen_for_maximum_performance": False,
            "active_current": {"value": None, "class": "UNKNOWN", "note": "representative class ~mA active; exact point NOT frozen"},
            "sleep_current": {"value": None, "class": "UNKNOWN", "note": "representative ~uA deep-sleep; exact point NOT frozen"},
            "voltage": {"value": None, "class": "UNKNOWN"},
            "clock": {"value": None, "class": "UNKNOWN"},
            "peripheral_assumptions": ["shared SPI bus to AFEs", "I2C to temp/light", "internal RTC for timestamping"],
            "source": "reference-class assumption (no datasheet frozen)",
            "final_part": False,
            "note": "No exact current is used in any power sum; system power stays NOT_READY by construction.",
        },
        "radio": {
            "reference_scenarios": {
                "continuous_stream_reference": {"description": "BLE continuous streaming of raw/lightly-processed data",
                                                "deployment_final": False, "duty": "high radio-on fraction"},
                "buffered_burst_reference": {"description": "Local storage + intermittent BLE burst upload",
                                             "deployment_final": False, "duty": "low radio-on fraction, higher local storage"},
            },
            "communication_schedule_frozen": False,
            "chosen_to_minimise_power": False,
            "final_part": False,
        },
        "regulator_pmic": {
            "rails_distinguished": ["sensor/analog rail (e.g. 3.3 V for TMP117/OPT3001; 5 V AVDD for EEG)",
                                    "digital rail (1.8 V AFE cores / DVDD)", "battery voltage"],
            "efficiency": {"value": None, "class": "UNKNOWN",
                           "note": "NOT frozen; an arbitrary 90% is explicitly NOT applied. Efficiency would be a labelled reference assumption ONLY when a system power calc is authorised."},
            "final_part": False,
        },
        "battery": {
            "id": "REFERENCE_MECHANICAL_BATTERY_CASE",
            "used_to_compute_runtime": False,
            "chemistry": {"value": "rechargeable Li-polymer (reference class)", "class": "ARCHITECTURE_ASSUMPTION"},
            "capacity": {"value": None, "class": "UNKNOWN"},
            "nominal_voltage": {"value": 3.7, "unit": "V", "class": "ARCHITECTURE_ASSUMPTION", "note": "typical Li-Po nominal; representative only"},
            "mass": {"value": None, "class": "UNKNOWN", "note": "no cell datasheet frozen; mass NOT asserted"},
            "dimensions": {"value": None, "class": "UNKNOWN"},
            "source": "reference-class assumption (no cell datasheet frozen)",
            "runtime_note": "No runtime computed — system average power is NOT_READY.",
            "final_part": False,
        },
        "data_rate_requirement_reference": "See results/reference_data_rate_budget_day11.json (partial raw payload ~48 kbps, radio rate NOT_READY).",
        "source_confidence": "LOW-MEDIUM (reference classes, not selected parts)",
    }


# Frozen data-rate points (channels, Hz, bits) mirrored from the catalog / EOG burden.
def build_data_rate_budget() -> dict:
    def raw(ch, hz, bits):
        return ch * hz * bits

    ppg = raw(1, 64, 19)          # 1216
    imu = raw(3, 32, 16)          # 1536
    temp = raw(1, 1, 16)          # 16
    ecg = raw(2, 250, 24)         # 12000
    eeg_sci = raw(1, 100, 24)     # 2400 (Fpz-Cz @100 Hz dataset rate)
    eog_sci = raw(1, 100, 24)     # 2400 (EOG horizontal @100 Hz)
    eeg_afe_cap = raw(4, 250, 24)  # 24000 (4-ch AFE @250 SPS nearest hardware ODR)
    second_ppg = raw(3, 500, 19)  # 28500

    head_sci_2ch = eeg_sci + eog_sci  # 4800
    wrist_raw_excl_light = ppg + imu + temp  # 2768

    # Partial system RAW total uses the current scientific use-case head framing (2ch@100Hz).
    partial_system_raw = ppg + imu + temp + ecg + head_sci_2ch + second_ppg  # 48068

    return {
        "artifact_id": "biological-minimalism-reference-data-rate-budget-day11-v1",
        "schema_version": "1.0.0",
        "part": "DAY11_PART2",
        "statement": ("Transparent data-rate table. raw_payload_bit_rate = channels x sample_rate x bits/sample. "
                      "For biopotential rows (EEG/EOG) sample_rate_hz is the resampled SCIENTIFIC/MODEL STREAM rate "
                      "(100 Hz), which is distinct from the AFE hardware acquisition rate (ADS1299-class >=250 SPS, "
                      "see hardware_acquisition_rate_sps). RAW excludes framing, protocol, and compression. "
                      "RADIO_DATA_RATE and PROCESSED_DATA_RATE are NOT computed (overhead/compression/schedule open)."),
        "equation": "raw_payload_bit_rate = channels x sample_rate_hz x bits_per_sample",
        "rate_class_separation": {
            "HARDWARE_ACQUISITION_RATE": "AFE ODR (e.g. ADS1299-class >=250 SPS); see per-row hardware_acquisition_rate_sps",
            "SCIENTIFIC_MODEL_STREAM_RATE": "resampled rate fed to the model (e.g. 100 Hz Sleep-EDF); used for payload rows here",
            "RAW_SENSOR_DATA_RATE": "computed from the stream rate where channels/rate/bits are frozen",
            "PROCESSED_DATA_RATE": "NOT_READY", "RADIO_DATA_RATE": "NOT_READY"},
        "modalities": [
            {"modality": "wrist_ppg", "module": "wrist_module", "channels": 1, "sample_rate_hz": 64, "bits_per_sample": 19,
             "raw_payload_bit_rate": ppg, "class": "DATASHEET_CALCULATED",
             "note": "64 Hz is a REFERENCE_SCHEDULE_ASSUMPTION; 19-bit MAX86141 conversion."},
            {"modality": "wrist_imu", "module": "wrist_module", "channels": 3, "sample_rate_hz": 32, "bits_per_sample": 16,
             "raw_payload_bit_rate": imu, "class": "DATASHEET_CALCULATED"},
            {"modality": "skin_temperature", "module": "wrist_module", "channels": 1, "sample_rate_hz": 1, "bits_per_sample": 16,
             "raw_payload_bit_rate": temp, "class": "DATASHEET_CALCULATED"},
            {"modality": "light_sensor", "module": "wrist_module", "channels": 1, "sample_rate_hz": None, "bits_per_sample": 16,
             "raw_payload_bit_rate": None, "class": "UNKNOWN",
             "note": "report cadence open; placement LOCATION_UNRESOLVED. NOT_READY (not zero)."},
            {"modality": "ecg_chest", "module": "chest_module", "channels": 2, "sample_rate_hz": 250, "bits_per_sample": 24,
             "raw_payload_bit_rate": ecg, "class": "DATASHEET_CALCULATED"},
            {"modality": "thoracic_bioz", "module": "chest_module", "channels": None, "sample_rate_hz": None, "bits_per_sample": 16,
             "raw_payload_bit_rate": None, "class": "UNKNOWN", "note": "BioZ cadence/channels open. NOT_READY."},
            {"modality": "frontal_eeg", "module": "head_module", "channels": 1, "sample_rate_hz": 100, "bits_per_sample": 24,
             "raw_payload_bit_rate": eeg_sci, "class": "DATASHEET_CALCULATED",
             # Audit M5: 100 Hz is the resampled scientific/model STREAM rate, NOT raw
             # hardware acquisition. The ADS1299-class AFE acquires at >=250 SPS.
             "rate_class": "SCIENTIFIC_MODEL_STREAM_RATE",
             "hardware_acquisition_rate_sps": 250,
             "hardware_acquisition_note": "ADS1299-class minimum ODR is 250 SPS; the 100 Hz value is the resampled Sleep-EDF scientific/model stream, not raw hardware acquisition.",
             "note": "Scientific use case: 1 EEG derivation @100 Hz (model stream). AFE-capacity framing = 4ch x 250 SPS x 24 = %d bps." % eeg_afe_cap},
            {"modality": "frontal_eog_horizontal", "module": "head_module", "channels": 1, "sample_rate_hz": 100, "bits_per_sample": 24,
             "raw_payload_bit_rate": eog_sci, "class": "DATASHEET_CALCULATED",
             "rate_class": "SCIENTIFIC_MODEL_STREAM_RATE",
             "hardware_acquisition_rate_sps": 250,
             "hardware_acquisition_note": "ADS1299-class minimum ODR is 250 SPS; the 100 Hz value is the resampled scientific/model stream, not raw hardware acquisition. On the shared AFE at 250 SPS the payload would be 6000 bps.",
             "note": "Matches frozen results/eog_operational_burden_day10.json (2400 bps at the 100 Hz model stream rate)."},
            {"modality": "second_ppg_site", "module": "optical_site_evaluation_branch", "channels": 3, "sample_rate_hz": 500, "bits_per_sample": 19,
             "raw_payload_bit_rate": second_ppg, "class": "DATASHEET_CALCULATED"},
            {"modality": "leg_bioz", "module": "leg_module", "channels": None, "sample_rate_hz": None, "bits_per_sample": 16,
             "raw_payload_bit_rate": None, "class": "UNKNOWN", "note": "BioZ cadence/channels open. NOT_READY."},
        ],
        "module_raw_totals": {
            "wrist_module": {"raw_bps_excl_light": wrist_raw_excl_light, "light_status": "NOT_READY_ADDS_UNKNOWN"},
            "chest_module": {"raw_bps_ecg_only": ecg, "bioz_status": "NOT_READY_ADDS_UNKNOWN"},
            "head_module": {"raw_bps_scientific_2ch_100hz": head_sci_2ch, "raw_bps_afe_capacity_4ch_250sps": eeg_afe_cap,
                            "note": "scientific use case enables 2 of 4 channels @100 Hz"},
            "leg_module": {"raw_bps": None, "status": "NOT_READY"},
            "optical_site_evaluation_branch": {"raw_bps": second_ppg},
        },
        "system_raw_total": {
            "value_bps": partial_system_raw,
            "value_kbps": _round(partial_system_raw / 1000.0, 3),
            "framing": "PARTIAL LOWER BOUND — scientific-use-case head (2ch@100Hz)",
            "excludes": ["light_sensor (open)", "thoracic BioZ (open)", "leg BioZ (open)", "protocol overhead", "compression"],
            "class": "DATASHEET_CALCULATED_PARTIAL",
            "not_a_radio_rate": True,
        },
        "radio_rate_status": "RADIO_DATA_RATE_NOT_READY (overhead, compression, and upload schedule unfrozen)",
    }


def build_mass_readiness() -> dict:
    tiers = {
        "Tier0": "unknown", "Tier1": "component/package-only known", "Tier2": "electronics-subassembly estimate",
        "Tier3": "reference module mechanical estimate", "Tier4": "prototype measured mass",
    }

    def module(mid, comps, note):
        return {
            "module_id": mid, "components": comps,
            "tier": "Tier0",
            "tier_rationale": ("Component package DIMENSIONS are datasheet-known for several parts, but package MASS is not "
                               "published and no material model is frozen (dimensions != mass). No PCB area/design, battery cell, "
                               "enclosure geometry, electrode/adhesive/strap, or wiring is selected. Tier-1 (component mass known) "
                               "is therefore NOT met."),
            "known_contributors": [], "estimated_contributors": [],
            "unknown_contributors": ["component/package mass", "PCB mass", "battery mass", "enclosure mass",
                                     "electrodes/adhesives/straps", "wiring/connectors"],
            "module_mass_available": False, "confidence": "N/A (no mass asserted)",
            "next_action": note,
        }

    return {
        "artifact_id": "biological-minimalism-reference-mass-readiness-day11-part2-v1",
        "schema_version": "1.0.0",
        "part": "DAY11_PART2",
        "statement": ("Honest mass-readiness advancement: the tier framework and per-module contributor classification are "
                      "formalised, but NO module or component mass number is asserted. Package dimensions are not mass; no "
                      "material model or board design is frozen. All modules remain Tier 0."),
        "tier_definitions": tiers,
        "no_measured_mass_exists": True,
        "modules": [
            module("wrist_module", ["MAX86141", "BMI270", "TMP117", "OPT3001-Q1 (LOCATION_UNRESOLVED)"],
                   "To reach Tier 2: freeze a PCB area estimate from component/connector footprints + documented FR-4 area-density model (labelled estimate); select component packages' masses from vendor mass data if available."),
            module("chest_module", ["ADS1292R", "AD5940-class (thoracic BioZ)"],
                   "To reach Tier 2: freeze electrode montage/count + adhesive materials, PCB area, AFE package masses."),
            module("head_module", ["ADS1299-4-class (EEG)", "EOG +2 ocular electrodes on shared AFE"],
                   "To reach Tier 2: select EEG electrode count/material + EOG 2 ocular electrode/lead materials; AFE package mass; head attachment."),
            module("leg_module", ["AD5940-class (separate instance)"],
                   "Lowest priority. To reach Tier 1: obtain AFE package mass; then electrodes/PCB/attachment."),
            module("optical_site_evaluation_branch", ["MAX86141-class extension + optical stack"],
                   "Module boundary (shared/tethered/standalone) must be frozen first — it determines whether a separate enclosure/battery mass exists at all."),
        ],
        "system_mass_status": "SYSTEM_MASS_NOT_READY",
        "per_module_answer": {"wrist_module": "Tier0", "chest_module": "Tier0", "head_module": "Tier0",
                              "leg_module": "Tier0", "optical_site_evaluation_branch": "Tier0"},
        "eog_incremental_mass": {"status": "SYSTEM_MASS_NOT_READY",
                                 "note": "+2 ocular electrodes + leads; materials not selected. Not zero, not quantified. See eog_operational_burden_day10.json."},
    }


def build_bom_readiness() -> dict:
    VOCAB = ["REFERENCE_SELECTED", "AVAILABLE", "PARTIAL", "MISSING", "NOT_APPLICABLE"]
    # REFERENCE_SELECTED = a representative reference class is chosen (final = false).

    def module(mid, rows):
        return {"module_id": mid, "items": rows}

    mcu = "REFERENCE_SELECTED"   # Cortex-M4F BLE SoC class (this Part-2)
    radio = "REFERENCE_SELECTED"  # BLE, scenario-level (this Part-2)
    reg = "REFERENCE_SELECTED"   # rail structure defined; efficiency unfrozen (this Part-2)
    batt = "REFERENCE_SELECTED"  # REFERENCE_MECHANICAL_BATTERY_CASE class; params unknown (this Part-2)

    return {
        "artifact_id": "biological-minimalism-reference-bom-readiness-day11-part2-v1",
        "schema_version": "1.0.0",
        "part": "DAY11_PART2",
        "not_a_final_bom": True,
        "advances_from": "results/reference_bom_readiness_day10.json",
        "vocabulary": VOCAB,
        "vocabulary_note": "REFERENCE_SELECTED = a representative reference class is chosen for calculation; it is NOT a final component (final = false).",
        "part2_advance": "MCU / radio / regulator / battery moved MISSING -> REFERENCE_SELECTED (class level, final=false). Sensing ICs/AFEs remain REFERENCE_SELECTED classes. Electrodes/PCB/enclosure/attachment/wiring remain MISSING (no geometry/materials).",
        "modules": [
            module("wrist_module", [
                {"item": "sensing_ic_ppg", "reference": "MAX86141", "status": "REFERENCE_SELECTED", "note": "AFE class; LEDs/optical stack MISSING"},
                {"item": "sensing_ic_imu", "reference": "BMI270", "status": "REFERENCE_SELECTED"},
                {"item": "sensing_ic_temp", "reference": "TMP117", "status": "REFERENCE_SELECTED"},
                {"item": "sensing_ic_light", "reference": "OPT3001-Q1", "status": "REFERENCE_SELECTED", "note": "LOCATION_UNRESOLVED (wrist vs cabin)"},
                {"item": "afe", "reference": "integrated in sensing ICs", "status": "REFERENCE_SELECTED"},
                {"item": "mcu", "reference": "Cortex-M4F BLE SoC class", "status": mcu, "note": "final=false; exact current unresolved"},
                {"item": "radio", "reference": "BLE (scenario-level)", "status": radio, "note": "continuous vs burst scenarios; final=false"},
                {"item": "regulator", "reference": "multi-rail PMIC/LDO (rails defined)", "status": reg, "note": "efficiency NOT frozen"},
                {"item": "battery", "reference": "REFERENCE_MECHANICAL_BATTERY_CASE (Li-Po class)", "status": batt, "note": "capacity/mass/dims unknown"},
                {"item": "electrodes", "reference": None, "status": "NOT_APPLICABLE", "note": "optical/thermal/light — no skin electrodes"},
                {"item": "pcb", "reference": None, "status": "MISSING"},
                {"item": "enclosure", "reference": None, "status": "MISSING"},
                {"item": "attachment", "reference": "wrist strap", "status": "MISSING", "note": "geometry/material MISSING"},
                {"item": "wiring", "reference": None, "status": "MISSING"},
            ]),
            module("chest_module", [
                {"item": "sensing_ic_ecg", "reference": "ADS1292R", "status": "REFERENCE_SELECTED"},
                {"item": "sensing_ic_bioz", "reference": "AD5940-class", "status": "REFERENCE_SELECTED", "note": "active BioZ operating point MISSING"},
                {"item": "afe", "reference": "ADS1292R + AD5940-class", "status": "REFERENCE_SELECTED"},
                {"item": "mcu", "reference": "Cortex-M4F BLE SoC class", "status": mcu, "note": "final=false"},
                {"item": "radio", "reference": "BLE (scenario-level)", "status": radio, "note": "final=false"},
                {"item": "regulator", "reference": "multi-rail PMIC/LDO", "status": reg},
                {"item": "battery", "reference": "REFERENCE_MECHANICAL_BATTERY_CASE", "status": batt},
                {"item": "electrodes", "reference": None, "status": "MISSING", "note": "montage/count/material OPEN"},
                {"item": "pcb", "reference": None, "status": "MISSING"},
                {"item": "enclosure", "reference": None, "status": "MISSING"},
                {"item": "attachment", "reference": None, "status": "MISSING"},
                {"item": "wiring", "reference": None, "status": "MISSING"},
            ]),
            module("head_module", [
                {"item": "sensing_ic_eeg", "reference": "ADS1299-4-class", "status": "REFERENCE_SELECTED", "note": "operating-point power MISSING"},
                {"item": "sensing_ic_eog", "reference": "shared ADS1299-4 spare channel", "status": "REFERENCE_SELECTED", "note": "+2 ocular electrodes; shared reference/bias"},
                {"item": "afe", "reference": "ADS1299-4-class", "status": "REFERENCE_SELECTED"},
                {"item": "mcu", "reference": "Cortex-M4F BLE SoC class", "status": mcu, "note": "final=false"},
                {"item": "radio", "reference": "BLE (scenario-level)", "status": radio, "note": "final=false"},
                {"item": "regulator", "reference": "multi-rail PMIC/LDO (5V AVDD + DVDD)", "status": reg},
                {"item": "battery", "reference": "REFERENCE_MECHANICAL_BATTERY_CASE", "status": batt},
                {"item": "electrodes", "reference": "EEG montage + 2 EOG ocular", "status": "PARTIAL", "note": "EOG sensing-contact increment=2 defensible; EEG count OPEN; materials MISSING"},
                {"item": "pcb", "reference": None, "status": "MISSING"},
                {"item": "enclosure", "reference": None, "status": "MISSING"},
                {"item": "attachment", "reference": "head band + peri-ocular extension", "status": "MISSING"},
                {"item": "wiring", "reference": "2 EOG leads to head AFE", "status": "PARTIAL", "note": "count defensible; material MISSING"},
            ]),
            module("leg_module", [
                {"item": "sensing_ic_bioz", "reference": "AD5940-class (separate)", "status": "REFERENCE_SELECTED", "note": "active BioZ operating point MISSING"},
                {"item": "afe", "reference": "AD5940-class", "status": "REFERENCE_SELECTED"},
                {"item": "mcu", "reference": "Cortex-M4F BLE SoC class", "status": mcu, "note": "final=false"},
                {"item": "radio", "reference": "BLE (scenario-level)", "status": radio, "note": "final=false"},
                {"item": "regulator", "reference": "multi-rail PMIC/LDO", "status": reg},
                {"item": "battery", "reference": "REFERENCE_MECHANICAL_BATTERY_CASE", "status": batt},
                {"item": "electrodes", "reference": None, "status": "MISSING"},
                {"item": "pcb", "reference": None, "status": "MISSING"},
                {"item": "enclosure", "reference": None, "status": "MISSING"},
                {"item": "attachment", "reference": None, "status": "MISSING"},
                {"item": "wiring", "reference": None, "status": "MISSING"},
            ]),
            module("optical_site_evaluation_branch", [
                {"item": "sensing_ic_ppg2", "reference": "MAX86141-class extension", "status": "REFERENCE_SELECTED", "note": "optical stack MISSING; 500 Hz current MISSING"},
                {"item": "afe", "reference": "MAX86141-class", "status": "REFERENCE_SELECTED"},
                {"item": "mcu", "reference": None, "status": "MISSING", "note": "module boundary OPEN — shared/tethered/standalone undecided"},
                {"item": "radio", "reference": None, "status": "MISSING", "note": "only if standalone"},
                {"item": "regulator", "reference": None, "status": "MISSING"},
                {"item": "battery", "reference": None, "status": "MISSING", "note": "only if standalone"},
                {"item": "electrodes", "reference": None, "status": "NOT_APPLICABLE", "note": "optical"},
                {"item": "pcb", "reference": None, "status": "MISSING"},
                {"item": "enclosure", "reference": None, "status": "MISSING"},
                {"item": "attachment", "reference": None, "status": "MISSING"},
                {"item": "wiring", "reference": None, "status": "MISSING"},
            ]),
        ],
        "system_readiness": {
            "system_average_power": "SYSTEM_AVERAGE_POWER_NOT_READY",
            "system_mass": "SYSTEM_MASS_NOT_READY",
            "final_bom": "FINAL_BOM_NOT_SELECTED",
        },
    }


def build_pareto_blocker_progress() -> dict:
    return {
        "artifact_id": "biological-minimalism-pareto-blocker-progress-day11-part2-v1",
        "schema_version": "1.0.0",
        "part": "DAY11_PART2",
        "not_the_canonical_pareto_decision": True,
        "source_of_truth": "results/pareto_readiness_blockers.json",
        "statement": "Part-2 progress against each Pareto blocker. Engineering-only. Does NOT recompute or downgrade the canonical Pareto decision; Part-3 may act on these.",
        "blockers": [
            {"id": "cross_dataset_incomparability", "before_part2": "BLOCKER",
             "evidence_added": "NONE (engineering cannot address scientific incomparability)",
             "after_part2_readiness": "BLOCKER", "still_unresolved": "Per-target comparable benefit frame",
             "part3_may_downgrade": False, "note": "MUST NOT be downgraded by any engineering work."},
            {"id": "power_partial", "before_part2": "HIGH (component IC points only)",
             "evidence_added": ["Frozen REFERENCE_IMU_OPERATING_POINT (0.018 mW ref, 0.018-0.378 band)",
                                "TMP117 0.01155 mW + OPT3001 0.00594 mW component reference powers",
                                "REFERENCE_ECG_AFE_POWER 0.67 mW", "MAX86141 AFE floor <=0.018 mW (LED-excluded)",
                                "WRIST_SENSOR_ELECTRONICS_REFERENCE_SCENARIO_LED_EXCLUDED band (LED-excluded reference scenario, not a bound)",
                                "Reference MCU/radio/regulator CLASSES"],
             "after_part2_readiness": "HIGH (PARTIAL_IMPROVED)",
             "still_unresolved": ["LED optical power", "EEG/EOG head-AFE operating point", "thoracic + leg BioZ operating point",
                                  "deployable duty", "regulator efficiency", "battery", "system average power"],
             "part3_may_downgrade": False, "note": "System average power still NOT_READY; do not drop below HIGH."},
            {"id": "mass_missing", "before_part2": "HIGH",
             "evidence_added": ["Tier-0..4 framework formalised", "per-module contributor classification (all Tier 0)"],
             "after_part2_readiness": "HIGH", "still_unresolved": "Every mass number (no material model / board design / cell)",
             "part3_may_downgrade": False},
            {"id": "module_bom_unresolved", "before_part2": "HIGH",
             "evidence_added": ["MCU/radio/regulator/battery MISSING -> REFERENCE_SELECTED (class, final=false)"],
             "after_part2_readiness": "HIGH (PARTIALLY_ADDRESSED)",
             "still_unresolved": ["final component selections", "enclosure", "PCB", "electrode materials", "attachment", "2nd-PPG module boundary"],
             "part3_may_downgrade": "CANDIDATE — Part-3 MAY reduce to MEDIUM if class-level reference BOM is accepted as sufficient for a reference (not final) Pareto; not downgraded here."},
            {"id": "interaction_evidence_incomplete", "before_part2": "MEDIUM (PARTIALLY_ADDRESSED)",
             "evidence_added": "NONE (scientific)", "after_part2_readiness": "MEDIUM", "still_unresolved": "interaction coverage across other pairs/targets",
             "part3_may_downgrade": False},
            {"id": "sleep_single_dataset_scope", "before_part2": "MEDIUM", "evidence_added": "NONE (scientific)",
             "after_part2_readiness": "MEDIUM", "still_unresolved": "independent-dataset replication", "part3_may_downgrade": False},
            {"id": "targets_incomplete", "before_part2": "MEDIUM", "evidence_added": "NONE (scientific)",
             "after_part2_readiness": "MEDIUM", "still_unresolved": "additional target-specific experiments", "part3_may_downgrade": False},
        ],
        "data_compute_axis": {"note": "Not a blocker; strengthened by results/reference_data_rate_budget_day11.json (explicit raw payloads)."},
        "pareto_status": "NOT_READY (unchanged)",
    }


def build_part3_inputs() -> dict:
    return {
        "artifact_id": "biological-minimalism-day11-part3-engineering-inputs-v1",
        "schema_version": "1.0.0",
        "part": "DAY11_PART2",
        "role": "PRIMARY handoff to Part-3 (architecture/Pareto integration). Part-2 does NOT decide architecture.",
        "part1_head_commit": PART1_HEAD_COMMIT,
        "consumes": ["results/reference_power_budget_day11_part2.json", "results/reference_data_rate_budget_day11.json",
                     "results/reference_mass_readiness_day11_part2.json", "results/reference_bom_readiness_day11_part2.json",
                     "results/reference_shared_electronics_day11.json", "results/pareto_blocker_progress_day11_part2.json"],
        "candidates": [
            {"candidate": "wrist_imu", "scientific_target": "heart_rate (VALIDATED_POSITIVE, within-dataset)",
             "gate_status": "CONDITIONAL_FOR_TARGET", "reference_module": "wrist_module (colocated)",
             "incremental_body_region": 0, "incremental_sensing_contacts": 0, "incremental_module": 0,
             "reference_component_power_mW": {"reference_point": _round(BMI270_LP), "band": [_round(BMI270_LP), _round(BMI270_NORMAL)]},
             "reference_module_boundary_power": "included in WRIST_SENSOR_ELECTRONICS_REFERENCE_SCENARIO_LED_EXCLUDED (LED-excluded reference scenario, not a bound)",
             "mass_tier": "Tier0", "raw_data_rate_increment_bps": 1536, "bom_readiness": "REFERENCE_SELECTED (BMI270)",
             "uncertainty": "exact 32 Hz-compatible mode current within 10-210 uA band; deployable duty open",
             "architecture_decision_implications": "Near-zero incremental human contact burden; power is the best-characterised of all candidates.",
             "pareto_readiness_implications": "Power PARTIAL, mass MISSING — cannot be a full Pareto coordinate yet."},
            {"candidate": "frontal_eog_horizontal", "scientific_target": "sleep_stage_5class (within-dataset, primary n=3 + secondary n=8, never pooled)",
             "gate_status": "CONDITIONAL_FOR_TARGET", "reference_module": "head_module (REFERENCE_SHARED_HEAD_MODULE)",
             "incremental_body_region": "0 or 1 (peri-ocular adjacency; framing-dependent, not forced)",
             "incremental_sensing_contacts": 2, "incremental_module": 0,
             "reference_component_power_mW": {"status": "NOT_READY", "note": "one channel on shared head AFE; head AFE operating point NOT_READY"},
             "reference_module_boundary_power": "NOT_READY", "mass_tier": "Tier0", "raw_data_rate_increment_bps": 2400,
             "bom_readiness": "electrodes PARTIAL (contact increment=2 defensible), power/mass MISSING",
             "uncertainty": "standalone-vs-shared wiring (2 vs up to 4 contacts, +0 vs +1 module); head-AFE power fully open",
             "architecture_decision_implications": "Materially higher contact burden than IMU (>=2 new ocular electrodes + new peri-ocular site); this is why EOG stays CONDITIONAL despite strong within-dataset science.",
             "pareto_readiness_implications": "Power + mass MISSING; contact/module/data-rate PARTIAL/AVAILABLE."},
            {"candidate": "second_ppg_site", "scientific_target": "heart_rate (VALIDATED_NEGATIVE aggregate, s2-driven, heterogeneous)",
             "gate_status": "DEPRIORITIZE_FOR_TARGET", "reference_module": "optical_site_evaluation_branch (OPEN_BOUNDARY)",
             "incremental_body_region": 1, "incremental_sensing_contacts": 1, "incremental_module": "OPEN (shared/tethered/standalone)",
             "reference_component_power_mW": {"status": "NOT_READY", "note": "LED power + 500 Hz sequencing + boundary open"},
             "reference_module_boundary_power": "NOT_READY", "mass_tier": "Tier0", "raw_data_rate_increment_bps": 28500,
             "bom_readiness": "MISSING (module boundary open)",
             "uncertainty": "highest raw data-rate increment of all candidates (28.5 kbps); LED power dominant + unquantified",
             "architecture_decision_implications": "Do NOT let the negative HR result zero the engineering burden: +1 optical site, +1 contact region, highest data rate.",
             "pareto_readiness_implications": "Power/mass/module-boundary all MISSING; robustness evidence MISSING."},
        ],
        "reference_baseline_components": [
            {"component": "wrist_ppg (MAX86141)", "power": "AFE floor <=0.018 mW (LED-excluded); reference total NOT_READY", "raw_data_rate_bps": 1216, "bom": "REFERENCE_SELECTED", "mass_tier": "Tier0"},
            {"component": "skin_temperature (TMP117)", "power_mW": _round(TMP117_P), "raw_data_rate_bps": 16, "bom": "REFERENCE_SELECTED", "mass_tier": "Tier0"},
            {"component": "light_sensor (OPT3001)", "power_mW": _round(OPT3001_P), "placement": "LOCATION_UNRESOLVED", "raw_data_rate_bps": "NOT_READY (cadence open)", "bom": "REFERENCE_SELECTED", "mass_tier": "Tier0"},
            {"component": "ecg_chest (ADS1292R)", "power_mW": _round(ADS1292R_ECG), "raw_data_rate_bps": 12000, "bom": "REFERENCE_SELECTED", "mass_tier": "Tier0"},
            {"component": "frontal_eeg (ADS1299-4)", "power": "NOT_READY (operating config specified; per-channel power unverified)", "raw_data_rate_bps": 2400, "bom": "REFERENCE_SELECTED", "mass_tier": "Tier0"},
            {"component": "thoracic_bioz (AD5940)", "power": "NOT_READY", "raw_data_rate_bps": "NOT_READY", "bom": "REFERENCE_SELECTED", "mass_tier": "Tier0"},
            {"component": "leg_bioz (AD5940 sep.)", "power": "NOT_READY", "raw_data_rate_bps": "NOT_READY", "bom": "REFERENCE_SELECTED", "mass_tier": "Tier0"},
        ],
        "warnings": [
            "Do NOT sum these into a system power or mass number.",
            "Do NOT rank cross-target benefits (HR MAE vs sleep macro-F1).",
            "Do NOT upgrade CONDITIONAL/DEPRIORITIZE gate decisions — that is Part-3 architecture, out of Part-2 scope.",
            "REFERENCE_SELECTED != final component. final_part = false everywhere.",
            "System average power NOT_READY; system mass NOT_READY; formal Pareto NOT_READY.",
        ],
    }


def main() -> int:
    outputs = {
        "reference_power_budget_day11_part2.json": build_power_budget(),
        "reference_shared_electronics_day11.json": build_shared_electronics(),
        "reference_data_rate_budget_day11.json": build_data_rate_budget(),
        "reference_mass_readiness_day11_part2.json": build_mass_readiness(),
        "reference_bom_readiness_day11_part2.json": build_bom_readiness(),
        "pareto_blocker_progress_day11_part2.json": build_pareto_blocker_progress(),
        "day11_part3_engineering_inputs.json": build_part3_inputs(),
    }
    for name, obj in outputs.items():
        (RESULTS / name).write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
        print(f"wrote results/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
