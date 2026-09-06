"""Deterministic Day 6 hardware-topology and readiness artifact builder/reader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.research.catalog import REPOSITORY_ROOT, ResearchArtifactError
from app.schemas.hardware_topology import (
    ArchitectureResource,
    ArchitectureSignal,
    ContactBurden,
    Day6ComponentReadiness,
    EvidenceConfidence,
    HardwareTopologyContract,
    HardwareTopologyEnvelope,
    ParetoReadinessDay6,
    ParetoReadinessDay6Envelope,
    ReadinessStatus,
    SystemArchitectureTopology,
    TargetCoverageEntry,
    TargetEvidenceStatus,
    LocationStatus,
    TopologyComponent,
    TopologyModule,
    TopologyStatus,
)
from app.schemas.operational_cost import OperationalCostCatalog
from app.schemas.research import ResearchAvailability

TOPOLOGY_PATH = "results/hardware_topology_contract.json"
SYSTEM_ARCHITECTURE_PATH = "results/system_architecture_topology.json"
READINESS_PATH = "results/pareto_readiness_day6.json"
OPERATIONAL_CATALOG_PATH = "results/operational_cost_catalog.json"
DECISION_INPUTS_PATH = "results/pareto_decision_inputs.json"
METHODOLOGY_PATH = "docs/HARDWARE_TOPOLOGY_METHODOLOGY.md"
DAY5_OPERATIONAL_SHA256 = "51a61717f23004d75cb04d4c7cfaebe3dbd300080cf99b0602cfa6edeb5f0280"
DAY5_BASE_COMMIT = "fcf7a811e410c6b00ada4dee4ec5dd4ce33db441"
RETRIEVAL_DATE = "2026-09-05"

STABLE_COMPONENT_IDS = (
    "wrist_imu",
    "second_ppg_site",
    "wrist_ppg",
    "ecg_chest",
    "thoracic_bioz",
    "skin_temperature",
    "light_sensor",
    "frontal_eeg",
    "leg_bioz",
)

TARGET_IDS = (
    "heart_rate",
    "heart_rate_variability",
    "respiration",
    "blood_pressure_or_pat",
    "workload",
    "fatigue",
    "sleep_or_circadian",
    "fluid_status",
)


def _unknown(unit: str, *, basis: str = "marginal", kind: str = "exact", note: str) -> dict[str, Any]:
    return {
        "availability": "unknown",
        "value_kind": kind,
        "value": None,
        "minimum": None,
        "typical": None,
        "maximum": None,
        "unit": unit,
        "basis": basis,
        "evidence_level": "unknown",
        "provenance_ids": [],
        "notes": [note],
    }


def _exact(
    value: float,
    unit: str,
    evidence_id: str,
    *,
    basis: str = "marginal",
    evidence_level: str = "derived",
    note: str,
) -> dict[str, Any]:
    return {
        "availability": "known",
        "value_kind": "exact",
        "value": value,
        "minimum": None,
        "typical": None,
        "maximum": None,
        "unit": unit,
        "basis": basis,
        "evidence_level": evidence_level,
        "provenance_ids": [evidence_id],
        "notes": [note],
    }


def _range(
    unit: str,
    evidence_id: str,
    *,
    minimum: float | None = None,
    typical: float | None = None,
    maximum: float | None = None,
    basis: str = "marginal",
    evidence_level: str = "manufacturer_spec",
    note: str,
) -> dict[str, Any]:
    return {
        "availability": "known",
        "value_kind": "range",
        "value": None,
        "minimum": minimum,
        "typical": typical,
        "maximum": maximum,
        "unit": unit,
        "basis": basis,
        "evidence_level": evidence_level,
        "provenance_ids": [evidence_id],
        "notes": [note],
    }


def _mass_unknown() -> dict[str, Any]:
    return {
        "component_mass": _unknown("g", note="Manufacturer package dimensions are not component mass."),
        "pcb_or_module_incremental_mass": _unknown("g", note="PCB, passives, interconnect, and assembly are not frozen."),
        "finished_wearable_mass": _unknown(
            "g", note="Enclosure, battery, attachment, electrodes, and allocated shared hardware are not frozen."
        ),
    }


def _compute_unknown(note: str) -> dict[str, Any]:
    return {
        "dtype": None,
        "bytes_per_value": None,
        "input_tensor_shapes": [],
        "baseline_model_weight_memory": _unknown("bytes", basis="total", note=note),
        "candidate_model_weight_memory": _unknown("bytes", basis="total", note=note),
        "incremental_model_weight_memory": _unknown("bytes", note=note),
        "baseline_input_buffer_memory": _unknown("bytes", basis="total", note=note),
        "candidate_input_buffer_memory": _unknown("bytes", basis="total", note=note),
        "incremental_input_buffer_memory": _unknown("bytes", note=note),
        "embedded_inference_latency": _unknown("ms", note="No embedded target benchmark exists."),
        "notes": [note, "Desktop timing is not used as embedded latency."],
    }


def _compute_wrist_imu() -> dict[str, Any]:
    return {
        "dtype": "float32",
        "bytes_per_value": 4,
        "input_tensor_shapes": ["baseline PPG: [1, 512]", "candidate PPG: [1, 512] + IMU: [3, 256]"],
        "baseline_model_weight_memory": _exact(32260, "bytes", "ppg_dalia_model_parameter_count", basis="total", note="8065 parameters × 4 bytes."),
        "candidate_model_weight_memory": _exact(116356, "bytes", "ppg_dalia_model_parameter_count", basis="total", note="29089 parameters × 4 bytes."),
        "incremental_model_weight_memory": _exact(84096, "bytes", "ppg_dalia_model_parameter_count", note="21024 parameters × 4 bytes."),
        "baseline_input_buffer_memory": _exact(2048, "bytes", "ppg_dalia_window_parameters", basis="total", note="512 float32 PPG values."),
        "candidate_input_buffer_memory": _exact(5120, "bytes", "ppg_dalia_window_parameters", basis="total", note="1280 float32 values across PPG and IMU."),
        "incremental_input_buffer_memory": _exact(3072, "bytes", "ppg_dalia_window_parameters", note="768 added float32 IMU values."),
        "embedded_inference_latency": _unknown("ms", note="No embedded target benchmark exists."),
        "notes": ["Weight memory excludes framework, activations, allocator, and runtime workspace.", "Input buffers exclude alignment, double buffering, and preprocessing workspace."],
    }


def _compute_second_ppg() -> dict[str, Any]:
    return {
        "dtype": "float32",
        "bytes_per_value": 4,
        "input_tensor_shapes": ["baseline: [3, 4000]", "candidate: [6, 4000]"],
        "baseline_model_weight_memory": _exact(33156, "bytes", "ptt_checkpoint_manifest", basis="total", note="8289 parameters × 4 bytes."),
        "candidate_model_weight_memory": _exact(34500, "bytes", "ptt_checkpoint_manifest", basis="total", note="8625 parameters × 4 bytes."),
        "incremental_model_weight_memory": _exact(1344, "bytes", "ptt_checkpoint_manifest", note="336 parameters × 4 bytes."),
        "baseline_input_buffer_memory": _exact(48000, "bytes", "ptt_window_parameters", basis="total", note="12000 float32 values."),
        "candidate_input_buffer_memory": _exact(96000, "bytes", "ptt_window_parameters", basis="total", note="24000 float32 values."),
        "incremental_input_buffer_memory": _exact(48000, "bytes", "ptt_window_parameters", note="12000 added float32 values."),
        "embedded_inference_latency": _unknown("ms", note="No embedded target benchmark exists."),
        "notes": ["Weight memory excludes framework, activations, allocator, and runtime workspace.", "Input buffers exclude alignment, double buffering, and preprocessing workspace."],
    }


def _data(
    *,
    channels: float | None,
    sample_rate: float | None,
    bits: float | None,
    evidence_id: str | None,
    note: str,
) -> dict[str, Any]:
    known = evidence_id is not None
    channel_q = _exact(channels, "channels", evidence_id, note=note) if known and channels is not None else _unknown("channels", note=note)
    rate_q = _exact(sample_rate, "Hz", evidence_id, note=note) if known and sample_rate is not None else _unknown("Hz", note=note)
    bits_q = _exact(bits, "bits_per_sample", evidence_id, note=note) if known and bits is not None else _unknown("bits_per_sample", note=note)
    if known and channels is not None and sample_rate is not None:
        scalar = _exact(channels * sample_rate, "scalar_samples_per_second", evidence_id, note=note)
    else:
        scalar = _unknown("scalar_samples_per_second", note=note)
    if known and channels is not None and sample_rate is not None and bits is not None:
        bitrate = _exact(channels * sample_rate * bits, "bit_per_second", evidence_id, note=f"channels × sample rate × bits/sample; {note}")
        equation = "raw_payload_bit_rate = channels × sample_rate × bits_per_sample"
    else:
        bitrate = _unknown("bit_per_second", note="Sample schedule or digital word width is not frozen.")
        equation = None
    return {
        "channel_count": channel_q,
        "sample_rate": rate_q,
        "bits_per_sample": bits_q,
        "scalar_sample_throughput": scalar,
        "raw_payload_bit_rate": bitrate,
        "protocol_overhead_bit_rate": _unknown("bit_per_second", note="Framing, headers, retransmission, and bus/radio overhead are not frozen."),
        "equation": equation,
        "notes": ["Raw payload excludes protocol overhead.", note],
    }


def _power(
    *,
    boundary: str,
    condition: str,
    duty_status: str,
    duty_assumption: str,
    voltage: dict[str, Any],
    current: dict[str, Any],
    active_power: dict[str, Any],
    active_fraction: dict[str, Any],
    average_power: dict[str, Any],
    daily_energy: dict[str, Any],
    exclusions: list[str],
) -> dict[str, Any]:
    return {
        "boundary": boundary,
        "operating_condition": condition,
        "duty_cycle_status": duty_status,
        "duty_cycle_assumption": duty_assumption,
        "supply_voltage": voltage,
        "active_current": current,
        "active_power": active_power,
        "active_fraction": active_fraction,
        "average_power": average_power,
        "daily_energy": daily_energy,
        "equations": ["P = V × I", "P_avg = Σ(P_state × duty_fraction_state)", "E_day = P_avg × 24 h"],
        "excluded_subsystems": exclusions,
    }


DAY6_EVIDENCE = [
    {
        "evidence_id": "day6_bmi270_datasheet",
        "evidence_level": "manufacturer_spec",
        "title": "BMI270 Datasheet, document BST-BMI270-DS000-07",
        "source_reference": "https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf",
        "component_or_artifact_identity": "Bosch Sensortec BMI270",
        "operating_condition": "Electrical table at VDD=1.8 V and TA=25°C; current depends on accelerometer/gyro mode and ODR.",
        "value_characterization": "Manufacturer operating points and digital resolution; not a complete wrist-module power measurement.",
        "version_or_date": "BST-BMI270-DS000-07",
        "assumptions": ["BMI270 is a representative wearable IMU candidate, not a final BOM selection."],
        "manufacturer": "Bosch Sensortec",
        "source_url": "https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf",
        "retrieval_date": RETRIEVAL_DATE,
        "page_or_section": "Table 1, Basic electrical parameter specifications",
        "exact_parameters": ["VDD typical 1.8 V", "accelerometer-only low-power 10 µA at 25 Hz", "accelerometer-only normal 210 µA at maximum ODR", "accelerometer output 16 bit"],
    },
    {
        "evidence_id": "day6_max86141_datasheet",
        "evidence_level": "manufacturer_spec",
        "title": "MAX86140/MAX86141 Wearable Optical AFE Data Sheet, Rev. 5",
        "source_reference": "https://www.analog.com/en/products/max86141.html",
        "component_or_artifact_identity": "Analog Devices MAX86141 optical AFE class",
        "operating_condition": "Optical readout channel at 25 samples/s for the published <10 µA point; LED supply and current are application-dependent.",
        "value_characterization": "AFE reference point only; excludes LEDs, photodiodes, MCU, radio, regulators, and final optical stack.",
        "version_or_date": "Rev. 5, 2023-08-24",
        "assumptions": ["MAX86141 is a representative AFE class; emitters and detectors remain open."],
        "manufacturer": "Analog Devices",
        "source_url": "https://www.analog.com/en/products/max86141.html",
        "retrieval_date": RETRIEVAL_DATE,
        "page_or_section": "Features and product details",
        "exact_parameters": ["1.8 V main supply", "optical readout <10 µA typical at 25 samples/s", "19-bit ADC", "three LED drivers", "two simultaneous optical readout channels", "SPI"],
    },
    {
        "evidence_id": "day6_tmp117_datasheet",
        "evidence_level": "manufacturer_spec",
        "title": "TMP117 High-Accuracy Low-Power Digital Temperature Sensor Data Sheet, Rev. D",
        "source_reference": "https://www.ti.com/lit/ds/symlink/tmp117.pdf",
        "component_or_artifact_identity": "Texas Instruments TMP117",
        "operating_condition": "1 Hz conversion cycle, averaging off, serial bus inactive, TA=25°C; 3.3 V reference supply assumed for derived power.",
        "value_characterization": "Manufacturer average current at the stated conversion schedule; component only.",
        "version_or_date": "Rev. D, September 2022",
        "assumptions": ["A 3.3 V shared wrist rail is an explicit reference-architecture assumption."],
        "manufacturer": "Texas Instruments",
        "source_url": "https://www.ti.com/lit/ds/symlink/tmp117.pdf",
        "retrieval_date": RETRIEVAL_DATE,
        "page_or_section": "Electrical Characteristics, Power Supply",
        "exact_parameters": ["3.5 µA typical average current at 1 Hz with averaging off", "16-bit temperature result register", "I2C/SMBus"],
    },
    {
        "evidence_id": "day6_opt3001_datasheet",
        "evidence_level": "manufacturer_spec",
        "title": "OPT3001-Q1 Ambient Light Sensor Data Sheet, Rev. C",
        "source_reference": "https://www.ti.com/product/OPT3001-Q1",
        "component_or_artifact_identity": "Texas Instruments OPT3001-Q1 component class",
        "operating_condition": "Continuous conversion; 1.8 µA typical operating current; 3.3 V reference supply assumed for derived power.",
        "value_characterization": "Manufacturer component current; excludes shared MCU, communications, regulator losses, and system idle power.",
        "version_or_date": "Rev. C, 2025-06-11",
        "assumptions": ["A 3.3 V shared wrist rail is an explicit reference-architecture assumption."],
        "manufacturer": "Texas Instruments",
        "source_url": "https://www.ti.com/product/OPT3001-Q1",
        "retrieval_date": RETRIEVAL_DATE,
        "page_or_section": "Product details and features",
        "exact_parameters": ["1.8 µA typical operating current", "1.6 V to 3.6 V supply", "I2C/SMBus", "continuous or single-shot modes"],
    },
    {
        "evidence_id": "day6_ads1292r_datasheet",
        "evidence_level": "manufacturer_spec",
        "title": "ADS129x Low-Power 2-Channel 24-Bit Biopotential AFE Data Sheet, Rev. C",
        "source_reference": "https://www.ti.com/product/ADS1292R",
        "component_or_artifact_identity": "Texas Instruments ADS1292R",
        "operating_condition": "Published 335 µW/channel AFE point; two channels; 250 samples/s selected within the supported range.",
        "value_characterization": "Two-channel AFE power only; excludes electrodes, MCU, radio, regulators, memory, and attachment.",
        "version_or_date": "Rev. C, 2020-04-24",
        "assumptions": ["Continuous 250 samples/s is a reference schedule for HR/HRV signal capture, not validated mission sufficiency."],
        "manufacturer": "Texas Instruments",
        "source_url": "https://www.ti.com/product/ADS1292R",
        "retrieval_date": RETRIEVAL_DATE,
        "page_or_section": "Product details and features",
        "exact_parameters": ["335 µW/channel", "two 24-bit channels", "125 samples/s to 8 ksamples/s", "integrated respiration impedance", "SPI"],
    },
    {
        "evidence_id": "day6_ads1299_datasheet",
        "evidence_level": "manufacturer_spec",
        "title": "ADS1299-x 4/6/8-Channel 24-Bit EEG AFE Data Sheet, Rev. C",
        "source_reference": "https://www.ti.com/product/ADS1299-4",
        "component_or_artifact_identity": "Texas Instruments ADS1299-4 class",
        "operating_condition": "Four-channel EEG AFE class; 250 samples/s reference payload rate; session duty cycle and complete power state are open.",
        "value_characterization": "Identity, channels, resolution, rate support, and interface only; no Day 6 EEG average power asserted.",
        "version_or_date": "Rev. C, 2017-01-25",
        "assumptions": ["Frontal montage and electrode count remain open."],
        "manufacturer": "Texas Instruments",
        "source_url": "https://www.ti.com/product/ADS1299-4",
        "retrieval_date": RETRIEVAL_DATE,
        "page_or_section": "Product details and data sheet overview",
        "exact_parameters": ["four 24-bit channels", "250 samples/s to 16 ksamples/s", "SPI"],
    },
    {
        "evidence_id": "day6_ad5940_datasheet",
        "evidence_level": "manufacturer_spec",
        "title": "AD5940/AD5941 High-Precision Impedance and Electrochemical AFE Data Sheet, Rev. G",
        "source_reference": "https://www.analog.com/en/products/AD5940.html",
        "component_or_artifact_identity": "Analog Devices AD5940 impedance AFE class",
        "operating_condition": "2.8 V to 3.6 V device supply; measurement sequence, excitation, electrodes, and duty cycle not frozen.",
        "value_characterization": "Representative bioimpedance AFE class; the 6.5 µA low-power potentiostat point is not used as active BioZ measurement power.",
        "version_or_date": "Rev. G, 2026-02-09",
        "assumptions": ["Separate AD5940-class instances represent thoracic and leg measurement branches unless a later topology revision proves sharing."],
        "manufacturer": "Analog Devices",
        "source_url": "https://www.analog.com/en/products/AD5940.html",
        "retrieval_date": RETRIEVAL_DATE,
        "page_or_section": "Features, power, and bioimpedance applications",
        "exact_parameters": ["2.8 V to 3.6 V supply", "16-bit ADC", "SPI", "body and skin impedance applications", "6 kB sequencer/FIFO SRAM"],
    },
]


def _hardware_records() -> dict[str, dict[str, Any]]:
    common_exclusions = ["shared MCU", "memory", "wireless radio", "regulator loss", "battery", "enclosure", "attachment"]
    unknown_active_fraction = _unknown("fraction", basis="total", note="A deployable state schedule is not frozen.")
    unknown_avg = _unknown("mW", note="Average component power requires a compatible operating point and explicit state schedule.")
    unknown_energy = _unknown("mWh_per_day", note="Daily energy requires a defensible average component power.")

    records: dict[str, dict[str, Any]] = {}
    records["wrist_ppg"] = {
        "identity": {"manufacturer": "Analog Devices", "part_number_or_class": "MAX86141", "device_class": "dual-channel wearable optical AFE", "status": "representative_component_class", "rationale": "Provides wearable PPG readout, 19-bit conversion, LED drivers, FIFO, and SPI; final emitters, detectors, and optical stack remain open.", "evidence_ids": ["day6_max86141_datasheet"], "exclusions": ["Not a complete optical module or final PPG hardware identity."]},
        "required_afe": "MAX86141-class optical AFE plus unresolved emitters and photodiode optical stack",
        "host_interface": "SPI to shared wrist MCU",
        "host_mcu_status": "OPEN — shared wrist MCU/radio identity not selected",
        "power_energy": _power(boundary="incremental_afe", condition="Published MAX86141 optical-readout reference at 25 samples/s; final 64 Hz scientific-parity mode and LED currents unresolved.", duty_status="frozen", duty_assumption="Continuous acquisition is required for the current HR windowing reference; optical state timing remains open.", voltage=_exact(1.8, "V", "day6_max86141_datasheet", evidence_level="manufacturer_spec", note="Main AFE supply; LED supply is separate."), current=_range("uA", "day6_max86141_datasheet", maximum=10, note="Published optical readout is <10 µA typical at 25 samples/s; encoded as an upper reference bound."), active_power=_range("mW", "day6_max86141_datasheet", maximum=0.018, evidence_level="derived", note="<1.8 V × 10 µA; AFE optical-readout reference only."), active_fraction=_exact(1.0, "fraction", "ppg_dalia_window_parameters", basis="total", evidence_level="reference_schedule", note="Continuous acquisition is an experiment-reference schedule assumption (the frozen HR windowing runs continuously), not a datasheet-derived duty cycle."), average_power=unknown_avg, daily_energy=unknown_energy, exclusions=common_exclusions + ["LED/emitter power", "photodiode", "optical/mechanical losses"]),
        "mass": _mass_unknown(),
        "data_rate": _data(channels=1, sample_rate=64, bits=19, evidence_id="day6_max86141_datasheet", note="One scientific-reference PPG stream at 64 Hz with MAX86141 19-bit conversion."),
        "compute_memory": _compute_unknown("No component-specific model-memory allocation is assigned to the baseline wrist PPG component."),
        "unresolved_dependencies": ["LED wavelengths and currents", "photodiode and optical geometry", "64 Hz operating-point power", "shared MCU/radio identity", "finished module mass"],
    }
    records["wrist_imu"] = {
        "identity": {"manufacturer": "Bosch Sensortec", "part_number_or_class": "BMI270", "device_class": "wearable six-axis IMU used in accelerometer-only mode", "status": "representative_candidate", "rationale": "Wearable-focused digital IMU with 16-bit accelerometer and SPI/I2C; representative identity is independent of the positive HR result.", "evidence_ids": ["day6_bmi270_datasheet"], "exclusions": ["The PPG-DaLiA checkpoint was trained on Empatica E4 32 Hz acceleration, not BMI270 output."]},
        "required_afe": "integrated digital MEMS sensing and conversion",
        "host_interface": "SPI or I2C to shared wrist MCU",
        "host_mcu_status": "OPEN — shared wrist MCU/radio identity not selected",
        "power_energy": _power(boundary="incremental_sensor_ic", condition="BMI270 accelerometer-only manufacturer reference points at 1.8 V, 25°C: 10 µA low-power at 25 Hz and 210 µA normal at maximum ODR.", duty_status="frozen", duty_assumption="Continuous acquisition while HR inference is active; exact 32 Hz-compatible BMI270 mode and resampling parity remain unresolved.", voltage=_exact(1.8, "V", "day6_bmi270_datasheet", evidence_level="manufacturer_spec", note="Datasheet typical supply condition."), current=_range("uA", "day6_bmi270_datasheet", minimum=10, maximum=210, note="Two documented accelerometer-only operating points; not a statistical interval or a 32 Hz typical value."), active_power=_range("mW", "day6_bmi270_datasheet", minimum=0.018, maximum=0.378, evidence_level="derived", note="1.8 V × documented 10–210 µA operating points."), active_fraction=_exact(1.0, "fraction", "ppg_dalia_window_parameters", basis="total", evidence_level="reference_schedule", note="Continuous acquisition is an experiment-reference schedule assumption (synchronized HR windows run continuously), not a datasheet-derived duty cycle."), average_power=unknown_avg, daily_energy=unknown_energy, exclusions=common_exclusions),
        "mass": _mass_unknown(),
        "data_rate": _data(channels=3, sample_rate=32, bits=16, evidence_id="day6_bmi270_datasheet", note="Scientific-reference three-axis stream at 32 Hz; BMI270 mode/parity remains to be validated."),
        "compute_memory": _compute_wrist_imu(),
        "unresolved_dependencies": ["32 Hz-compatible acquisition/resampling validation", "selected range/filter settings", "shared MCU/radio identity", "component and finished-module mass"],
    }
    records["skin_temperature"] = {
        "identity": {"manufacturer": "Texas Instruments", "part_number_or_class": "TMP117", "device_class": "high-accuracy digital contact temperature sensor", "status": "representative_candidate", "rationale": "Low-power I2C device with a documented 1 Hz current point; thermal coupling and physiological validity remain separate design questions.", "evidence_ids": ["day6_tmp117_datasheet"], "exclusions": ["Component accuracy is not evidence of validated skin-temperature target performance."]},
        "required_afe": "integrated temperature conversion",
        "host_interface": "I2C to shared wrist MCU",
        "host_mcu_status": "OPEN — shared wrist MCU/radio identity not selected",
        "power_energy": _power(boundary="incremental_sensor_ic", condition="TMP117 at 1 Hz, averaging off, serial bus inactive, 25°C; 3.3 V shared rail assumption.", duty_status="frozen", duty_assumption="One conversion per second for low-rate temperature trending; no claim that this schedule is scientifically validated.", voltage=_exact(3.3, "V", "day6_tmp117_datasheet", note="Explicit shared-rail engineering assumption within the 1.8–5.5 V device range."), current=_exact(3.5, "uA", "day6_tmp117_datasheet", evidence_level="manufacturer_spec", note="Typical average current at 1 Hz, averaging off, bus inactive."), active_power=_exact(0.01155, "mW", "day6_tmp117_datasheet", note="3.3 V × 3.5 µA."), active_fraction=_unknown("fraction", basis="total", note="Internal conversion/standby fraction is not separately allocated; manufacturer average current is used."), average_power=_exact(0.01155, "mW", "day6_tmp117_datasheet", note="Derived from the documented 1 Hz average current at the explicit 3.3 V rail."), daily_energy=_exact(0.2772, "mWh_per_day", "day6_tmp117_datasheet", note="0.01155 mW × 24 h."), exclusions=common_exclusions + ["thermal-path heater/self-heating effects"]),
        "mass": _mass_unknown(),
        "data_rate": _data(channels=1, sample_rate=1, bits=16, evidence_id="day6_tmp117_datasheet", note="One 16-bit temperature result per second; I2C overhead excluded."),
        "compute_memory": _compute_unknown("No validated temperature model or embedded compute contract exists."),
        "unresolved_dependencies": ["thermal coupling to skin", "placement bias and calibration", "shared MCU/radio identity", "component and finished-module mass"],
    }
    records["light_sensor"] = {
        "identity": {"manufacturer": "Texas Instruments", "part_number_or_class": "OPT3001-Q1 class", "device_class": "digital ambient light sensor", "status": "representative_component_class", "rationale": "Documented low-current, continuous/single-shot I2C light sensing; final sample interval and optical window remain open.", "evidence_ids": ["day6_opt3001_datasheet"], "exclusions": ["Automotive qualification is not required or claimed for the final system."]},
        "required_afe": "integrated ambient-light conversion",
        "host_interface": "I2C to shared wrist MCU",
        "host_mcu_status": "OPEN — shared wrist MCU/radio identity not selected",
        "power_energy": _power(boundary="incremental_sensor_ic", condition="OPT3001-Q1 continuous-conversion typical current with an explicit 3.3 V shared rail.", duty_status="frozen", duty_assumption="Continuous-conversion reference mode; reporting interval and target sufficiency remain open.", voltage=_exact(3.3, "V", "day6_opt3001_datasheet", note="Explicit shared-rail engineering assumption within the 1.6–3.6 V range."), current=_exact(1.8, "uA", "day6_opt3001_datasheet", evidence_level="manufacturer_spec", note="Typical operating current in continuous conversion."), active_power=_exact(0.00594, "mW", "day6_opt3001_datasheet", note="3.3 V × 1.8 µA."), active_fraction=_exact(1.0, "fraction", "day6_opt3001_datasheet", basis="total", evidence_level="reference_schedule", note="Continuous-conversion is an engineering reference-schedule assumption; the datasheet documents the device's continuous-conversion capability, not that continuous acquisition is required. Not a datasheet-derived duty cycle."), average_power=_exact(0.00594, "mW", "day6_opt3001_datasheet", note="Same as active component power for continuous-conversion reference mode."), daily_energy=_exact(0.14256, "mWh_per_day", "day6_opt3001_datasheet", note="0.00594 mW × 24 h."), exclusions=common_exclusions + ["optical-window attenuation"]),
        "mass": _mass_unknown(),
        "data_rate": _data(channels=1, sample_rate=None, bits=None, evidence_id="day6_opt3001_datasheet", note="Reporting interval and transmitted word format are not frozen."),
        "compute_memory": _compute_unknown("No validated ambient-light model or embedded compute contract exists."),
        "unresolved_dependencies": ["reporting interval", "optical window", "shared MCU/radio identity", "component and finished-module mass"],
    }
    records["ecg_chest"] = {
        "identity": {"manufacturer": "Texas Instruments", "part_number_or_class": "ADS1292R", "device_class": "two-channel 24-bit ECG/respiration AFE", "status": "representative_candidate", "rationale": "Portable biopotential AFE with two channels, respiration capability, and a published per-channel power point.", "evidence_ids": ["day6_ads1292r_datasheet"], "exclusions": ["Electrode topology and diagnostic/clinical performance are not frozen."]},
        "required_afe": "ADS1292R-class biopotential AFE",
        "host_interface": "SPI to shared chest MCU",
        "host_mcu_status": "OPEN — shared chest MCU/radio identity not selected",
        "power_energy": _power(boundary="incremental_afe", condition="Two ADS1292R channels at published 335 µW/channel; 250 samples/s reference acquisition.", duty_status="frozen", duty_assumption="Continuous reference acquisition for candidate HR/HRV timing; target validation is still absent.", voltage=_unknown("V", note="Published per-channel power is used directly; a single exact combined analog/digital rail point is not asserted."), current=_unknown("uA", note="Published per-channel power is used directly; rail-specific current is not collapsed."), active_power=_exact(0.67, "mW", "day6_ads1292r_datasheet", note="2 channels × 0.335 mW/channel."), active_fraction=_exact(1.0, "fraction", "day6_ads1292r_datasheet", basis="total", evidence_level="reference_schedule", note="Continuous acquisition is an engineering reference-schedule assumption; the datasheet documents continuous-conversion capability, not a required or validated system duty cycle. Not a datasheet-derived duty cycle."), average_power=_exact(0.67, "mW", "day6_ads1292r_datasheet", note="AFE-only power at 100% reference acquisition."), daily_energy=_exact(16.08, "mWh_per_day", "day6_ads1292r_datasheet", note="0.67 mW × 24 h; AFE only."), exclusions=common_exclusions + ["electrodes and lead-off excitation", "input protection"]),
        "mass": _mass_unknown(),
        "data_rate": _data(channels=2, sample_rate=250, bits=24, evidence_id="day6_ads1292r_datasheet", note="Two channels at a selected 250 samples/s reference point within the supported range."),
        "compute_memory": _compute_unknown("No validated ECG inference model or embedded compute contract exists."),
        "unresolved_dependencies": ["electrode count/type/layout", "input protection", "shared chest MCU/radio identity", "finished chest-module mass", "scientific target validation"],
    }
    bioz_power = _power(boundary="incremental_afe", condition="AD5940-class identity only; active BioZ excitation, frequency sweep, and measurement sequence are open.", duty_status="open", duty_assumption="Intermittent candidate measurement; schedule not frozen.", voltage=_range("V", "day6_ad5940_datasheet", minimum=2.8, maximum=3.6, note="Manufacturer supply range."), current=_unknown("uA", note="The published low-power potentiostat point is not active BioZ measurement current."), active_power=_unknown("mW", note="Active BioZ measurement configuration is not frozen."), active_fraction=unknown_active_fraction, average_power=unknown_avg, daily_energy=unknown_energy, exclusions=common_exclusions + ["excitation path", "electrodes", "input protection"])
    for component_id, label, location in (("thoracic_bioz", "thoracic", "shared chest"), ("leg_bioz", "segmental leg", "leg")):
        records[component_id] = {
            "identity": {"manufacturer": "Analog Devices", "part_number_or_class": "AD5940 class", "device_class": "16-bit impedance AFE", "status": "representative_component_class", "rationale": "Manufacturer explicitly supports body/skin impedance and sequenced duty cycling; measurement settings remain open.", "evidence_ids": ["day6_ad5940_datasheet"], "exclusions": ["The low-power potentiostat current is not used as active BioZ measurement power."]},
            "required_afe": "AD5940-class impedance excitation and measurement AFE",
            "host_interface": f"SPI to {location} module MCU",
            "host_mcu_status": f"OPEN — {location} module MCU/radio identity not selected",
            "power_energy": bioz_power,
            "mass": _mass_unknown(),
            "data_rate": _data(channels=None, sample_rate=None, bits=16, evidence_id="day6_ad5940_datasheet", note="ADC resolution is known; excitation/sample schedule and output representation are open."),
            "compute_memory": _compute_unknown(f"No validated {label} BioZ model or embedded compute contract exists."),
            "unresolved_dependencies": ["electrode count/type/layout", "excitation frequencies and amplitude", "measurement schedule", "MCU/radio identity", "finished-module mass", "scientific target validation"],
        }
    records["frontal_eeg"] = {
        "identity": {"manufacturer": "Texas Instruments", "part_number_or_class": "ADS1299-4 class", "device_class": "four-channel 24-bit EEG AFE", "status": "representative_component_class", "rationale": "EEG-specific four-channel AFE class with 250 samples/s support; montage, power state, and session schedule remain open.", "evidence_ids": ["day6_ads1299_datasheet"], "exclusions": ["No final headband, electrode, or channel montage is selected."]},
        "required_afe": "ADS1299-4-class EEG AFE",
        "host_interface": "SPI to dedicated head-module MCU",
        "host_mcu_status": "OPEN — head-module MCU/radio identity not selected",
        "power_energy": _power(boundary="incremental_afe", condition="ADS1299-4 identity and payload reference only; full operating point and session schedule are open.", duty_status="open", duty_assumption="Intermittent/session-based candidate use; session duration and frequency are not frozen.", voltage=_unknown("V", note="Final analog/digital rail configuration is open."), current=_unknown("uA", note="Final channel and reference configuration is open."), active_power=_unknown("mW", note="No complete selected operating point is asserted."), active_fraction=unknown_active_fraction, average_power=unknown_avg, daily_energy=unknown_energy, exclusions=common_exclusions + ["electrodes", "bias/reference network", "input protection"]),
        "mass": _mass_unknown(),
        "data_rate": _data(channels=4, sample_rate=250, bits=24, evidence_id="day6_ads1299_datasheet", note="Four channels at the minimum supported 250 samples/s reference payload."),
        "compute_memory": _compute_unknown("No validated frontal-EEG inference model or embedded compute contract exists."),
        "unresolved_dependencies": ["montage and electrode count/type", "session schedule", "power state", "MCU/radio identity", "headband mass", "scientific target validation"],
    }
    records["second_ppg_site"] = {
        "identity": {"manufacturer": "Analog Devices", "part_number_or_class": "MAX86141-class extension", "device_class": "additional wearable optical interface and dual-channel-capable AFE class", "status": "representative_component_class", "rationale": "The class can support multiple LED drivers and two optical receivers, but the experiment's exact six-channel hardware is not a final device design.", "evidence_ids": ["day6_max86141_datasheet"], "exclusions": ["Does not establish whether electronics are shared, tethered, or a standalone module."]},
        "required_afe": "MAX86141-class optical AFE capacity plus unresolved added emitters/photodiode",
        "host_interface": "SPI; routing to shared or dedicated MCU remains open",
        "host_mcu_status": "OPEN — module boundary and host identity not selected",
        "power_energy": _power(boundary="incremental_component_class", condition="MAX86141 optical-readout reference only; three-wavelength 500 Hz site schedule and LED currents are not covered by the <10 µA point.", duty_status="open", duty_assumption="Continuous during the frozen experiment; deployable duty cycle is open.", voltage=_exact(1.8, "V", "day6_max86141_datasheet", evidence_level="manufacturer_spec", note="Main AFE supply; LED supply is separate."), current=_range("uA", "day6_max86141_datasheet", maximum=10, note="Published <10 µA reference at 25 samples/s; not the 500 Hz multi-wavelength site current."), active_power=_range("mW", "day6_max86141_datasheet", maximum=0.018, evidence_level="derived", note="AFE readout reference only; not deployable second-site power."), active_fraction=unknown_active_fraction, average_power=unknown_avg, daily_energy=unknown_energy, exclusions=common_exclusions + ["all added LED/emitter power", "photodiode", "tether or second-module electronics"]),
        "mass": _mass_unknown(),
        "data_rate": _data(channels=3, sample_rate=500, bits=19, evidence_id="day6_max86141_datasheet", note="Frozen experiment's three added site channels at 500 Hz combined with the representative AFE's 19-bit conversion; protocol overhead excluded."),
        "compute_memory": _compute_second_ppg(),
        "unresolved_dependencies": ["shared versus standalone module boundary", "emitters/photodiode and LED currents", "AFE sequencing at 500 Hz", "attachment/cabling", "component and finished-module mass"],
    }
    return records


def _identity(record: dict[str, Any]) -> dict[str, Any]:
    return record["identity"]


def _contact(
    body_regions: list[str],
    contact_type: str,
    new_region: bool | None,
    new_site: bool | None,
    sites: int | None,
    optical: int | None,
    dry: int | None,
    adhesive: int | None,
    straps: int | None,
    head: bool,
    cable: bool | None,
) -> ContactBurden:
    return ContactBurden(
        body_regions=body_regions,
        contact_type=contact_type,
        new_contact_region_required=new_region,
        new_physical_sensing_site_required=new_site,
        physical_sensing_sites=sites,
        optical_interfaces=optical,
        dry_electrodes=dry,
        adhesive_or_wet_electrodes=adhesive,
        straps=straps,
        head_worn_hardware=head,
        external_cable_required=cable,
    )


def _target_matrix() -> dict[str, dict[str, TargetCoverageEntry]]:
    matrix: dict[str, dict[str, TargetCoverageEntry]] = {}
    for component_id in STABLE_COMPONENT_IDS:
        matrix[component_id] = {
            target: TargetCoverageEntry(
                status=TargetEvidenceStatus.UNVALIDATED,
                note="No frozen target-specific validation artifact supports this component/target pair.",
            )
            for target in TARGET_IDS
        }

    matrix["wrist_imu"]["heart_rate"] = TargetCoverageEntry(
        status=TargetEvidenceStatus.VALIDATED_POSITIVE,
        evidence_ids=["ppg_dalia_imu_hr"],
        note="Positive marginal value within the frozen PPG-DaLiA PPG-plus-IMU experiment only.",
    )
    matrix["second_ppg_site"]["heart_rate"] = TargetCoverageEntry(
        status=TargetEvidenceStatus.VALIDATED_NEGATIVE,
        evidence_ids=["ptt_second_ppg_site_hr"],
        note="Negative aggregate marginal value within the frozen PTT one-site versus two-site experiment, with heterogeneity.",
    )
    matrix["wrist_ppg"]["heart_rate"] = TargetCoverageEntry(
        status=TargetEvidenceStatus.PARTIAL_EVIDENCE,
        evidence_ids=["ppg_dalia_imu_hr"],
        note="PPG-only baseline has held-out HR metrics, but no experiment establishes universal wrist-PPG sufficiency.",
    )
    candidate_pairs = {
        "wrist_imu": ("workload", "fatigue"),
        "wrist_ppg": ("heart_rate_variability", "blood_pressure_or_pat"),
        "skin_temperature": ("fatigue", "sleep_or_circadian"),
        "light_sensor": ("sleep_or_circadian",),
        "ecg_chest": ("heart_rate", "heart_rate_variability", "respiration", "blood_pressure_or_pat"),
        "thoracic_bioz": ("respiration", "fluid_status"),
        "frontal_eeg": ("workload", "fatigue", "sleep_or_circadian"),
        "leg_bioz": ("fluid_status",),
        "second_ppg_site": ("blood_pressure_or_pat",),
    }
    for component_id, targets in candidate_pairs.items():
        for target in targets:
            matrix[component_id][target] = TargetCoverageEntry(
                status=TargetEvidenceStatus.CANDIDATE,
                note="Engineering target hypothesis only; no frozen project validation currently supports it.",
            )
    return matrix


def build_topology() -> HardwareTopologyContract:
    hardware = _hardware_records()
    modules = [
        TopologyModule(module_id="wrist_module", label="Shared wrist module", body_location="wrist", worn_body=True, topology_status=TopologyStatus.FROZEN_REFERENCE, component_ids=["wrist_ppg", "wrist_imu", "skin_temperature", "light_sensor"], shared_resources=["enclosure", "attachment strap", "battery", "host MCU", "wireless radio", "clock"], notes=["Shared resource identities and allocation remain open; each must be counted once.", "light_sensor is listed here as its candidate wrist placement, but its location_status is LOCATION_UNRESOLVED (wrist vs cabin/ambient). It must not be counted as body-worn burden until placement is frozen."]),
        TopologyModule(module_id="chest_module", label="Shared chest module", body_location="thorax", worn_body=True, topology_status=TopologyStatus.FROZEN_REFERENCE, component_ids=["ecg_chest", "thoracic_bioz"], shared_resources=["enclosure", "battery", "host MCU", "wireless radio", "clock"], notes=["ECG/BioZ electrode sharing is not assumed until a montage is validated."]),
        TopologyModule(module_id="head_module", label="Intermittent frontal EEG module", body_location="forehead/head", worn_body=True, topology_status=TopologyStatus.FROZEN_REFERENCE, component_ids=["frontal_eeg"], shared_resources=["head attachment", "battery", "host MCU", "wireless radio"], notes=["Electrode count, montage, and session schedule remain open."]),
        TopologyModule(module_id="leg_module", label="Experimental leg BioZ module", body_location="lower leg", worn_body=True, topology_status=TopologyStatus.FROZEN_REFERENCE, component_ids=["leg_bioz"], shared_resources=["attachment", "battery", "host MCU", "wireless radio"], notes=["Electrode topology and operating schedule remain open."]),
        TopologyModule(module_id="optical_site_evaluation_branch", label="Second PPG-site evaluation branch", body_location="finger/phalanx", worn_body=True, topology_status=TopologyStatus.OPEN_BOUNDARY, component_ids=["second_ppg_site"], shared_resources=[], notes=["One additional optical site is fixed; shared, tethered, or standalone electronics remain unresolved."]),
    ]
    specs = {
        "wrist_ppg": ("Wrist PPG", "photoplethysmography", "wrist_module", "wrist", "ventral/dorsal wrist optical window", "continuous", "Continuous while HR inference is active.", "reference baseline candidate", _contact(["wrist"], "reflective optical interface", True, True, 1, 1, 0, 0, 1, False, False), "MAX86141-class AFE plus optical stack", "SPI to shared wrist MCU", ["enclosure", "strap", "battery", "MCU", "radio", "clock"], True, "MEDIUM"),
        "wrist_imu": ("Wrist IMU", "three-axis acceleration", "wrist_module", "wrist", "inside shared wrist enclosure", "continuous", "Continuous and synchronized with PPG during HR inference.", "reference candidate", _contact(["wrist"], "no additional body interface", False, False, 0, 0, 0, 0, 0, False, False), "integrated BMI270 digital MEMS", "SPI/I2C to shared wrist MCU", ["enclosure", "strap", "battery", "MCU", "radio", "clock"], False, "HIGH"),
        "skin_temperature": ("Skin temperature", "contact temperature", "wrist_module", "wrist", "shared wrist skin-facing surface", "periodic", "One conversion per second reference schedule.", "reference candidate", _contact(["wrist"], "thermal path within existing wrist interface", False, False, 0, 0, 0, 0, 0, False, False), "integrated TMP117 conversion", "I2C to shared wrist MCU", ["enclosure", "strap", "battery", "MCU", "radio"], False, "MEDIUM"),
        "light_sensor": ("Ambient light sensor", "ambient light", "wrist_module", "wrist module outward surface", "outward optical aperture", "continuous", "Continuous-conversion reference; report cadence open.", "reference candidate", _contact([], "no body contact", False, False, 0, 0, 0, 0, 0, False, False), "integrated OPT3001-Q1-class conversion", "I2C to shared wrist MCU", ["enclosure", "battery", "MCU", "radio"], False, "MEDIUM"),
        "ecg_chest": ("Chest ECG", "electrocardiography", "chest_module", "thorax", "chest electrode montage (open)", "continuous", "Continuous reference acquisition; target sufficiency unvalidated.", "reference candidate", _contact(["thorax"], "electrode interface, type and count open", True, True, None, 0, 0, None, None, False, None), "ADS1292R-class biopotential AFE", "SPI to shared chest MCU", ["enclosure", "battery", "MCU", "radio", "clock"], True, "MEDIUM"),
        "thoracic_bioz": ("Thoracic BioZ / ICG", "thoracic bioimpedance", "chest_module", "thorax", "thoracic electrode montage (open)", "intermittent", "Intermittent candidate; cadence and duration open.", "optional evidence-required", _contact(["thorax"], "electrode interface; sharing with ECG unresolved", False, None, None, 0, 0, None, 0, False, None), "AD5940-class impedance AFE", "SPI to shared chest MCU", ["enclosure", "battery", "MCU", "radio", "clock"], False, "LOW"),
        "frontal_eeg": ("Frontal EEG", "electroencephalography", "head_module", "forehead/head", "frontal montage (open)", "intermittent", "Session-based candidate; duration/frequency open.", "optional evidence-required", _contact(["head/forehead"], "dry or wet electrode montage open", True, True, None, 0, None, None, None, True, False), "ADS1299-4-class EEG AFE", "SPI to head-module MCU", ["head attachment", "battery", "MCU", "radio"], True, "LOW"),
        "leg_bioz": ("Leg BioZ", "segmental bioimpedance", "leg_module", "lower leg", "segmental electrode montage (open)", "intermittent", "Experimental sessions only; cadence open.", "optional evidence-required", _contact(["lower leg"], "electrode montage open", True, True, None, 0, 0, None, None, False, None), "AD5940-class impedance AFE", "SPI to leg-module MCU", ["attachment", "battery", "MCU", "radio"], True, "LOW"),
        "second_ppg_site": ("Second physical PPG site", "photoplethysmography", "optical_site_evaluation_branch", "finger/phalanx", "one added proximal phalanx optical site", "continuous", "Continuous in the frozen experiment; deployable schedule open.", "optional evidence-required", _contact(["finger/phalanx"], "reflective optical interface", True, True, 1, 1, 0, 0, None, False, None), "MAX86141-class capacity plus optical stack", "SPI; shared/tethered host open", [], None, "MEDIUM"),
    }
    # Physical placement status. Only the ambient light sensor has a genuinely
    # unresolved placement (a wrist-worn outward aperture *or* a cabin/ambient mount
    # are both consistent with current evidence). Per the operational catalog's
    # "wearable versus cabin placement" open question, it must not be counted as
    # body-worn burden until placement is frozen. All other components have a
    # settled reference placement.
    location_status_map = {"light_sensor": LocationStatus.LOCATION_UNRESOLVED}
    location_alternatives_map = {
        "light_sensor": [
            "wrist-worn outward optical aperture (shares the wrist module)",
            "cabin/ambient fixed mount (contributes zero body-worn burden)",
        ]
    }
    extra_unresolved = {
        "light_sensor": [
            "Physical placement is unresolved (wrist module vs cabin/ambient mount); "
            "body-worn burden must not be attributed until placement is frozen."
        ]
    }
    components: list[TopologyComponent] = []
    for component_id in STABLE_COMPONENT_IDS:
        label, modality, module_id, region, site, operation, schedule, optionality, contact, afe, interface, shared, new_module, confidence = specs[component_id]
        record = hardware[component_id]
        components.append(TopologyComponent(component_id=component_id, label=label, modality=modality, module_id=module_id, location_status=location_status_map.get(component_id, LocationStatus.FROZEN), location_alternatives=location_alternatives_map.get(component_id, []), target_body_region=region, physical_sensing_site=site, operation_mode=operation, operating_schedule=schedule, optionality=optionality, contact_burden=contact, required_afe=afe, required_mcu_or_interface=interface, shared_resources=shared, new_module_required=new_module, hardware_identity=_identity(record), evidence_confidence=EvidenceConfidence(confidence), unresolved_dependencies=record["unresolved_dependencies"] + extra_unresolved.get(component_id, [])))
    return HardwareTopologyContract(
        schema_version="1.0.0",
        topology_id="biological-minimalism-day6-reference-topology-v1",
        title="Day 6 engineering reference topology — not a final BOM or selected architecture",
        methodology_path=METHODOLOGY_PATH,
        reference_architecture_not_final_bom=True,
        stable_component_ids=list(STABLE_COMPONENT_IDS),
        modules=modules,
        components=components,
        target_coverage=_target_matrix(),
        global_unresolved_dependencies=["Final MCU/radio/battery/regulator identities and allocation", "Validated electrode montages and materials", "Optical emitter/detector stacks and drive schedules", "Component, PCB/module, and finished wearable mass", "Embedded inference latency and activation/workspace memory", "Scientific validation beyond the two frozen HR ablations"],
    )


def build_system_architecture(topology: HardwareTopologyContract) -> SystemArchitectureTopology:
    resources: list[ArchitectureResource] = []
    for module in topology.modules:
        for resource in module.shared_resources:
            resource_id = f"{module.module_id}:{resource.lower().replace(' ', '_')}"
            resources.append(ArchitectureResource(resource_id=resource_id, resource_type=resource, module_id=module.module_id, allocation_status="OPEN_IDENTITY_COUNT_ONCE", shared_by=module.component_ids, double_count_prohibited=True))
    interfaces = {item.component_id: item.required_mcu_or_interface for item in topology.components}
    signals = [
        ArchitectureSignal(signal_id=f"{component_id}_signal", source_component_id=component_id, destination=f"{next(item.module_id for item in topology.components if item.component_id == component_id)} host", interface=interfaces[component_id], target_ids=[target for target, entry in topology.target_coverage[component_id].items() if entry.status != TargetEvidenceStatus.UNVALIDATED], validation_status="Only statuses in hardware_topology_contract.target_coverage are authoritative")
        for component_id in STABLE_COMPONENT_IDS
    ]
    return SystemArchitectureTopology(schema_version="1.0.0", architecture_id="biological-minimalism-day6-system-topology-v1", source_topology_path=TOPOLOGY_PATH, modules=topology.modules, resources=resources, signals=signals)


def build_operational_catalog(raw_catalog: dict[str, Any]) -> OperationalCostCatalog:
    raw = json.loads(json.dumps(raw_catalog))
    raw["schema_version"] = "2.0.0"
    raw["catalog_id"] = "biological-minimalism-operational-cost-v2"
    raw["generated_from_commit"] = DAY5_BASE_COMMIT
    raw["hardware_topology_path"] = TOPOLOGY_PATH
    raw["revision_history"] = [{"schema_version": "1.0.0", "source_commit": "49e94712f2c20e6cc3e2eb13338a64632703dc15", "source_sha256": DAY5_OPERATIONAL_SHA256, "change_summary": "Accepted Day 5 non-scalar operational-cost baseline before hardware identities."}]
    raw["evidence"] = [item for item in raw["evidence"] if not item["evidence_id"].startswith("day6_")] + DAY6_EVIDENCE
    raw["scientific_join_contract"]["cost_contract_status"] = "operational_cost_v2_day6_characterized"
    raw["scientific_join_contract"]["scientific_contract_status"] = "reviewed_scientific_contract_integrated_in_decision_inputs_v2"
    hardware = _hardware_records()
    for component in raw["components"]:
        record = hardware[component["component_id"]]
        component["candidate_hardware_identity"] = record["identity"]["part_number_or_class"]
        component["hardware_characterization"] = {"topology_component_id": component["component_id"], **record}
        component["operation_mode"] = {
            "wrist_ppg": "continuous", "wrist_imu": "continuous", "skin_temperature": "periodic", "light_sensor": "continuous", "ecg_chest": "continuous", "thoracic_bioz": "intermittent", "frontal_eeg": "intermittent", "leg_bioz": "intermittent", "second_ppg_site": "continuous"
        }[component["component_id"]]
        if component["component_id"] in {"wrist_ppg", "wrist_imu", "light_sensor", "ecg_chest"}:
            evidence_id = record["identity"]["evidence_ids"][0]
            component["duty_cycle"] = _exact(100, "percent", evidence_id, basis="total", note="Day 6 reference acquisition schedule; not total system duty cycle.")
        elif component["component_id"] == "skin_temperature":
            component["duty_cycle"] = _unknown("percent", basis="total", kind="range", note="One conversion per second is frozen, but internal active-state fraction is not separately specified.")
        else:
            component["duty_cycle"] = _unknown("percent", basis="total", kind="range", note="Operating schedule remains open.")
    return OperationalCostCatalog.model_validate(raw)


def _component_readiness(component_id: str) -> Day6ComponentReadiness:
    science = ReadinessStatus.AVAILABLE if component_id in {"wrist_imu", "second_ppg_site"} else (ReadinessStatus.PARTIAL if component_id == "wrist_ppg" else ReadinessStatus.MISSING)
    power = {"skin_temperature": ReadinessStatus.AVAILABLE, "light_sensor": ReadinessStatus.AVAILABLE, "ecg_chest": ReadinessStatus.AVAILABLE}.get(component_id, ReadinessStatus.PARTIAL if component_id in {"wrist_ppg", "wrist_imu", "second_ppg_site"} else ReadinessStatus.MISSING)
    average = ReadinessStatus.AVAILABLE if component_id in {"skin_temperature", "light_sensor", "ecg_chest"} else ReadinessStatus.MISSING
    physical = ReadinessStatus.AVAILABLE if component_id in {"wrist_ppg", "wrist_imu", "skin_temperature", "light_sensor"} else ReadinessStatus.PARTIAL
    data = ReadinessStatus.AVAILABLE if component_id in {"wrist_imu", "second_ppg_site"} else ReadinessStatus.PARTIAL
    robustness = ReadinessStatus.AVAILABLE if component_id == "wrist_imu" else ReadinessStatus.MISSING
    return Day6ComponentReadiness(component_id=component_id, scientific_benefit=science, target_coverage=ReadinessStatus.PARTIAL, component_power=power, average_power_and_energy=average, component_mass=ReadinessStatus.MISSING, finished_mass=ReadinessStatus.MISSING, physical_burden=physical, compute_and_data=data, robustness_evidence=robustness, provenance=ReadinessStatus.AVAILABLE, unresolved_dependencies=_hardware_records()[component_id]["unresolved_dependencies"])


def build_readiness() -> ParetoReadinessDay6:
    return ParetoReadinessDay6(
        schema_version="1.0.0",
        readiness_id="biological-minimalism-day6-pareto-readiness-v1",
        topology_path=TOPOLOGY_PATH,
        operational_catalog_path=OPERATIONAL_CATALOG_PATH,
        decision_inputs_path=DECISION_INPUTS_PATH,
        global_pareto_ready=False,
        target_specific_pareto_ready=False,
        structural_assessment_available=True,
        formal_pareto_authorized=False,
        classification="STRUCTURAL_ONLY_DESCRIPTIVE; FORMAL_PARETO_NOT_READY",
        component_matrix=[_component_readiness(component_id) for component_id in STABLE_COMPONENT_IDS],
        blockers=["Scientific benefit is validated only for two HR additions and those experiments use different datasets, populations, baselines, and model families.", "Deployable average power/energy is absent for optical sensing, IMU at the scientifically compatible rate, BioZ, EEG, and the second PPG site.", "Component, PCB/module, and finished wearable masses are unquantified for every component.", "Electrode montages and shared-electrode allocation are unresolved for ECG, thoracic BioZ, EEG, and leg BioZ.", "Final MCU, memory, radio, battery, regulator, enclosure, and attachment identities/allocations are open.", "Only heart rate has frozen marginal-value experiments; HRV, respiration, BP/PAT, workload, fatigue, sleep/circadian, and fluid targets are not validated."],
        limited_structural_conclusion="For the frozen PTT heart-rate experiment only, the second PPG site worsened aggregate error while adding one physical and optical sensing site. This does not authorize global removal or final architecture selection.",
        prohibited_inferences=["No universal sensor score", "No raw cross-dataset MAE/RMSE ranking", "No total wearable power from IC/AFE power", "No finished wearable mass from package dimensions", "No final component retain/remove outcome"],
    )


def _load_json(root: Path, relative_path: str) -> dict[str, Any]:
    try:
        raw = json.loads((root / relative_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResearchArtifactError(f"Day 6 artifact could not be read ({relative_path}): {exc}") from exc
    if not isinstance(raw, dict):
        raise ResearchArtifactError(f"Day 6 artifact must be an object: {relative_path}")
    return raw


def write_day6_artifacts(repository_root: str | Path = REPOSITORY_ROOT) -> list[Path]:
    root = Path(repository_root).resolve()
    topology = build_topology()
    system = build_system_architecture(topology)
    operational = build_operational_catalog(_load_json(root, OPERATIONAL_CATALOG_PATH))
    readiness = build_readiness()
    outputs = {
        TOPOLOGY_PATH: topology.model_dump(mode="json"),
        SYSTEM_ARCHITECTURE_PATH: system.model_dump(mode="json"),
        OPERATIONAL_CATALOG_PATH: operational.model_dump(mode="json"),
        READINESS_PATH: readiness.model_dump(mode="json"),
    }
    paths: list[Path] = []
    for relative_path, payload in outputs.items():
        path = root / relative_path
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        paths.append(path)
    return paths


class Day6ResearchReader:
    def __init__(self, repository_root: str | Path = REPOSITORY_ROOT) -> None:
        self.repository_root = Path(repository_root).resolve()

    def topology(self) -> HardwareTopologyEnvelope:
        try:
            topology = HardwareTopologyContract.model_validate(_load_json(self.repository_root, TOPOLOGY_PATH))
            system = SystemArchitectureTopology.model_validate(_load_json(self.repository_root, SYSTEM_ARCHITECTURE_PATH))
        except (ResearchArtifactError, ValidationError) as exc:
            return HardwareTopologyEnvelope(availability=ResearchAvailability.UNAVAILABLE, error=str(exc))
        return HardwareTopologyEnvelope(availability=ResearchAvailability.AVAILABLE, topology=topology, system_architecture=system)

    def readiness(self) -> ParetoReadinessDay6Envelope:
        try:
            readiness = ParetoReadinessDay6.model_validate(_load_json(self.repository_root, READINESS_PATH))
        except (ResearchArtifactError, ValidationError) as exc:
            return ParetoReadinessDay6Envelope(availability=ResearchAvailability.UNAVAILABLE, error=str(exc))
        return ParetoReadinessDay6Envelope(availability=ResearchAvailability.AVAILABLE, readiness=readiness)


day6_research = Day6ResearchReader()


if __name__ == "__main__":
    for generated in write_day6_artifacts():
        print(generated)
