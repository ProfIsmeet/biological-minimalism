"""Stage 4 engineering-readiness computation (INTEGRATION_OWNER sprint).

Computes every previously-NOT_READY engineering number that Day-11 Part-2
(results/reference_power_budget_day11_part2.json,
results/reference_data_rate_budget_day11.json,
results/reference_mass_readiness_day11_part2.json,
results/reference_bom_readiness_day11_part2.json) left open, using explicit
engineering-assumption scenarios (never datasheet facts pretending to be
more certain than they are). Writes the single frozen master artifact
results/stage4_engineering_readiness.json.

Run once; the output is a frozen artifact read read-only by the backend
(same pattern as every other results/*.json in this repo). Re-run only if
an assumption below is deliberately revised.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ml"))

from engineering.ppg_led_power import LedPowerInputs, compute_led_power  # noqa: E402

OUT_PATH = REPO_ROOT / "results" / "stage4_engineering_readiness.json"
DAY11_POWER_PATH = REPO_ROOT / "results" / "reference_power_budget_day11_part2.json"

# Read the 5 already-frozen Day-11 Part-2 component power values from their
# source artifact rather than hand-copying them as constants (rule 70: one
# authoritative source, not a hand-maintained duplicate that can silently
# diverge if the frozen artifact is ever revised).
_day11_power = json.loads(DAY11_POWER_PATH.read_text(encoding="utf-8"))["reference_operating_points"]

EV_DATASHEET_DIRECT = "DATASHEET_DIRECT"
EV_DATASHEET_CALCULATED = "DATASHEET_CALCULATED"
EV_ENGINEERING_ASSUMPTION = "ENGINEERING_ASSUMPTION"
EV_ENGINEERING_ALLOWANCE = "ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE"
EV_ASSUMED_USE_SCHEDULE = "ASSUMED_USE_SCHEDULE"
EV_NOT_READY = "NOT_READY"

# ---------------------------------------------------------------------------
# 1. PPG LED scenario (wrist_ppg) — closes the dominant wrist power blocker.
# Reuses ml/engineering/ppg_led_power.compute_led_power exactly; no new
# formula invented. Parameters are an explicit ENGINEERING_ASSUMPTION
# scenario, not a datasheet-guaranteed operating point (H7 guard: typical
# != minimum, and here it is an assumption, not even a typical table value).
# ---------------------------------------------------------------------------
WRIST_PPG_LED_SCENARIO = LedPowerInputs(
    n_active_leds=2,  # green + IR; red channel not enabled for HR-only use case
    i_led_peak_ma=20.0,  # mid-range MAX86141-programmable drive current
    v_led_forward_v=3.0,  # typical green/IR emitter forward voltage
    t_pulse_seconds=100e-6,  # 100 us pulse width
    f_pulse_hz=64.0,  # matches the already-frozen 64 Hz wrist_ppg acquisition rate
)
wrist_ppg_led = compute_led_power(WRIST_PPG_LED_SCENARIO)

# second_ppg_site remains OPTIONAL/DEPRIORITIZED_FOR_CURRENT_TARGET (rule 48);
# characterized for completeness only, excluded from every base-system total.
SECOND_PPG_LED_SCENARIO = LedPowerInputs(
    n_active_leds=3,  # red + IR + green (PTT dataset 3-wavelength acquisition)
    i_led_peak_ma=20.0,
    v_led_forward_v=3.0,
    t_pulse_seconds=100e-6,
    f_pulse_hz=500.0,  # matches the already-frozen 500 Hz second_ppg_site rate
)
second_ppg_led = compute_led_power(SECOND_PPG_LED_SCENARIO)

WRIST_PPG_AFE_MW = _day11_power["wrist_ppg"]["level2_afe_reference_power"]["max"]  # frozen Day-11 Part-2 value, LED-excluded
SECOND_PPG_AFE_MW = _day11_power["second_ppg_site"]["level2_afe_floor_mW"]["max"]  # frozen Day-11 Part-2 value, LED-excluded (25 s/s floor; 500 Hz current still open)

wrist_ppg_total_mw = WRIST_PPG_AFE_MW + wrist_ppg_led.total_average_power_mw
second_ppg_total_mw = SECOND_PPG_AFE_MW + second_ppg_led.total_average_power_mw

# ---------------------------------------------------------------------------
# 2. Head AFE (EEG + shared EOG) engineering-assumption power.
# Day-11 Part-2 explicitly could not verify an exact ADS1299 per-channel
# power-dissipation table row in that environment. This environment has the
# same limitation (no datasheet PDF access) — so this is NOT relabeled as
# DATASHEET_CALCULATED. It is an explicit order-of-magnitude engineering
# estimate for 2 active channels (1 EEG + 1 shared EOG) + internal reference
# + bias, at the already-frozen supply point (AVDD bipolar 2.5V, DVDD 3.3V).
# ---------------------------------------------------------------------------
HEAD_AFE_ACTIVE_CHANNELS = 2  # 1 EEG (Fpz-Cz) + 1 EOG (horizontal), shared AFE
HEAD_AFE_PER_CHANNEL_CURRENT_UA = 150.0  # engineering estimate, per active channel
HEAD_AFE_FIXED_OVERHEAD_CURRENT_UA = 300.0  # reference + bias + digital, engineering estimate
HEAD_AFE_SUPPLY_V = 2.5  # AVDD bipolar rail (frozen Day-11 Part-2 supply point)
head_afe_current_ua = HEAD_AFE_ACTIVE_CHANNELS * HEAD_AFE_PER_CHANNEL_CURRENT_UA + HEAD_AFE_FIXED_OVERHEAD_CURRENT_UA
head_afe_power_mw = head_afe_current_ua * HEAD_AFE_SUPPLY_V / 1000.0

# EOG incremental-only power (2nd channel minus the 1-EEG-channel-only baseline)
head_afe_one_channel_current_ua = 1 * HEAD_AFE_PER_CHANNEL_CURRENT_UA + HEAD_AFE_FIXED_OVERHEAD_CURRENT_UA
head_afe_one_channel_power_mw = head_afe_one_channel_current_ua * HEAD_AFE_SUPPLY_V / 1000.0
eog_incremental_power_mw = head_afe_power_mw - head_afe_one_channel_power_mw

# ---------------------------------------------------------------------------
# 3. Thoracic / leg BioZ (AD5940-class) engineering-assumption operating point.
# Tetrapolar excitation, burst-sampled (not continuous) — duty cycle chosen
# for a slow physiological process (fluid shift), NOT a frozen LBNP
# requirement; see docs note on the open LBNP-science dependency (rule 46).
# ---------------------------------------------------------------------------
BIOZ_EXCITATION_FREQ_HZ = 50_000  # standard tetrapolar ICG/thoracic BioZ excitation reference
BIOZ_ACTIVE_CURRENT_MA = 4.0  # AD5940-class active measurement current, engineering estimate
BIOZ_STANDBY_CURRENT_MA = 0.005  # AD5940-class low-power standby, engineering estimate
BIOZ_SUPPLY_V = 3.3
BIOZ_MEASUREMENT_WINDOW_S = 0.1  # 100 ms burst per measurement
BIOZ_MEASUREMENT_PERIOD_S = 1.0  # 1 measurement per second
bioz_duty_fraction = BIOZ_MEASUREMENT_WINDOW_S / BIOZ_MEASUREMENT_PERIOD_S
bioz_avg_current_ma = (
    BIOZ_ACTIVE_CURRENT_MA * bioz_duty_fraction + BIOZ_STANDBY_CURRENT_MA * (1 - bioz_duty_fraction)
)
bioz_avg_power_mw = bioz_avg_current_ma * BIOZ_SUPPLY_V

# ---------------------------------------------------------------------------
# 4. MCU / radio reference numeric operating points (nRF52840-class combined
# MCU+BLE-radio SoC — already REFERENCE_SELECTED at class level in Day-11
# Part-2 BOM as "Cortex-M4F BLE SoC class" / "BLE (scenario-level)"; this
# closes the "exact current unresolved" note with an explicit scenario).
# ---------------------------------------------------------------------------
MCU_SUPPLY_V = 3.3
MCU_ACTIVE_CURRENT_MA = 5.0  # CPU active, sensor fusion / feature extraction burst
MCU_SLEEP_CURRENT_MA = 0.002
MCU_ACTIVE_DUTY_FRACTION = 0.10  # 10% duty: periodic burst processing, not continuous
mcu_avg_current_ma = MCU_ACTIVE_CURRENT_MA * MCU_ACTIVE_DUTY_FRACTION + MCU_SLEEP_CURRENT_MA * (
    1 - MCU_ACTIVE_DUTY_FRACTION
)
mcu_avg_power_mw = mcu_avg_current_ma * MCU_SUPPLY_V

RADIO_TX_RX_CURRENT_MA = 5.0  # BLE TX/RX burst, 0 dBm class
RADIO_IDLE_CURRENT_MA = 0.001
RADIO_ACTIVE_DUTY_FRACTION = 0.01  # 1% duty: low-duty-cycle BLE connection-interval streaming
radio_avg_current_ma = RADIO_TX_RX_CURRENT_MA * RADIO_ACTIVE_DUTY_FRACTION + RADIO_IDLE_CURRENT_MA * (
    1 - RADIO_ACTIVE_DUTY_FRACTION
)
radio_avg_power_mw = radio_avg_current_ma * MCU_SUPPLY_V

# ---------------------------------------------------------------------------
# 5. Regulator efficiency reference assumption (closes "efficiency NOT
# frozen" note). Applied once, at the system power-tree boundary, to convert
# load-side (post-regulation) power to battery-side (pre-regulation) power.
# ---------------------------------------------------------------------------
REGULATOR_EFFICIENCY = 0.85  # reference buck/high-efficiency-LDO assumption

# ---------------------------------------------------------------------------
# 6. Duty schedule — explicit per-module active fraction (ASSUMED_USE_SCHEDULE,
# not a datasheet fact). Component power figures above are either already
# "continuous-equivalent" (TMP117 1Hz, OPT3001 continuous, ECG continuous)
# or intermittent-burst (BioZ, MCU, radio) with duty already folded in above.
# This table is the deployable schedule referenced by rule 49/50.
# ---------------------------------------------------------------------------
DUTY_SCHEDULE = {
    "wrist_ppg": {"state": "active_acquisition", "duty_fraction": 1.0, "note": "continuous optical acquisition"},
    "wrist_imu": {"state": "active_acquisition", "duty_fraction": 1.0, "note": "continuous, required for PPG motion-artifact correction"},
    "skin_temperature": {"state": "periodic_acquisition", "duty_fraction": 1.0, "note": "1 Hz continuous conversion (already folded into frozen 0.01155 mW figure)"},
    "light_sensor": {"state": "periodic_acquisition", "duty_fraction": 1.0, "note": "continuous low-rate polling (already folded into frozen 0.00594 mW figure); context-only role, not promoted to predictive necessity"},
    "ecg_chest": {"state": "active_acquisition", "duty_fraction": 1.0, "note": "continuous cardiac monitoring"},
    "thoracic_bioz": {"state": "periodic_acquisition", "duty_fraction": bioz_duty_fraction, "note": "100 ms measurement burst per 1 s; duty already folded into bioz_avg_power_mw"},
    "head_afe_eeg_eog": {"state": "active_acquisition", "duty_fraction": 1.0, "note": "continuous, required for sleep-staging scientific use case"},
    "mcu": {"state": "processing", "duty_fraction": MCU_ACTIVE_DUTY_FRACTION, "note": "periodic feature-extraction/fusion burst; duty already folded into mcu_avg_power_mw"},
    "radio": {"state": "transmission", "duty_fraction": RADIO_ACTIVE_DUTY_FRACTION, "note": "low-duty-cycle BLE connection-interval streaming; duty already folded into radio_avg_power_mw"},
}

# ---------------------------------------------------------------------------
# 7. System average power — base topology only (excludes leg BioZ, excludes
# second_ppg_site per rules 47/48/57). Every module power figure above is
# already an AVERAGE (duty-folded where applicable). Sum at load, then apply
# regulator efficiency to get battery-side power.
# ---------------------------------------------------------------------------
WRIST_IMU_MW = _day11_power["wrist_imu"]["reference_operating_point"]["reference_power_mW"]  # frozen Day-11 Part-2 reference operating point (low-power accel-only)
TMP117_MW = _day11_power["skin_temperature"]["reference_power_mW"]["value"]  # frozen
OPT3001_MW = _day11_power["light_sensor"]["reference_power_mW"]["value"]  # frozen, wrist case
ECG_AFE_MW = _day11_power["ecg_chest"]["afe_reference_power_mW"]["value"]  # frozen

base_topology_load_mw = {
    "wrist_ppg_total_incl_led": wrist_ppg_total_mw,
    "wrist_imu": WRIST_IMU_MW,
    "skin_temperature": TMP117_MW,
    "light_sensor": OPT3001_MW,
    "ecg_chest_afe": ECG_AFE_MW,
    "thoracic_bioz": bioz_avg_power_mw,
    "head_afe_eeg_eog": head_afe_power_mw,
    "mcu": mcu_avg_power_mw,
    "radio": radio_avg_power_mw,
}
system_load_side_total_mw = sum(base_topology_load_mw.values())
system_battery_side_total_mw = system_load_side_total_mw / REGULATOR_EFFICIENCY

# leg_bioz and second_ppg_site increments (NOT in base total)
leg_bioz_increment_mw = bioz_avg_power_mw  # same AD5940-class assumption, separate instance
second_ppg_increment_mw = second_ppg_total_mw

# ---------------------------------------------------------------------------
# 8. Data-rate extensions (closes light_sensor / thoracic_bioz / leg_bioz
# NOT_READY rows) + radio (transmitted, protocol-overhead-adjusted) rate.
# ---------------------------------------------------------------------------
LIGHT_SAMPLE_RATE_HZ = 0.1  # 1 sample / 10 s, context-only cadence
light_bps = 1 * LIGHT_SAMPLE_RATE_HZ * 16

BIOZ_SAMPLE_RATE_HZ = 1.0  # 1 measurement / s (matches BIOZ_MEASUREMENT_PERIOD_S)
BIOZ_CHANNELS = 1  # single tetrapolar impedance magnitude channel, scientific/model stream
BIOZ_BITS_PER_SAMPLE = 16
thoracic_bioz_bps = BIOZ_CHANNELS * BIOZ_SAMPLE_RATE_HZ * BIOZ_BITS_PER_SAMPLE
leg_bioz_bps = BIOZ_CHANNELS * BIOZ_SAMPLE_RATE_HZ * BIOZ_BITS_PER_SAMPLE  # same assumption, separate instance

# Existing frozen raw rows (from reference_data_rate_budget_day11.json),
# reused verbatim — not recomputed, cited by value for the base-topology sum.
WRIST_PPG_BPS = 1216
WRIST_IMU_BPS = 1536
SKIN_TEMP_BPS = 16
ECG_CHEST_BPS = 12000
HEAD_SCIENTIFIC_2CH_100HZ_BPS = 4800  # EEG 2400 + EOG 2400, already frozen

base_topology_raw_bps = {
    "wrist_ppg": WRIST_PPG_BPS,
    "wrist_imu": WRIST_IMU_BPS,
    "skin_temperature": SKIN_TEMP_BPS,
    "light_sensor": light_bps,
    "ecg_chest": ECG_CHEST_BPS,
    "thoracic_bioz": thoracic_bioz_bps,
    "head_eeg_eog_scientific": HEAD_SCIENTIFIC_2CH_100HZ_BPS,
}
system_raw_total_bps = sum(base_topology_raw_bps.values())

# Protocol-overhead-adjusted transmitted (radio) rate: BLE ATT/L2CAP/link-layer
# overhead reference assumption — engineering assumption, not a frozen BLE
# implementation. 20% overhead is a commonly-cited order-of-magnitude BLE
# notification-overhead reference for small payloads; NOT a guaranteed figure.
RADIO_PROTOCOL_OVERHEAD_FRACTION = 0.20
system_transmitted_bps = system_raw_total_bps * (1 + RADIO_PROTOCOL_OVERHEAD_FRACTION)

# Optional branch increments (excluded from base_topology_raw_bps/base total)
SECOND_PPG_BPS = 28500  # frozen, unchanged
leg_bioz_increment_bps = leg_bioz_bps

# ---------------------------------------------------------------------------
# 9. Mass model — Tier2 (electronics-subassembly estimate) per module, using
# generic small-IC/PCB/enclosure/strap engineering allowances (NOT vendor
# mass data, NOT measured). Explicitly ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE.
# ---------------------------------------------------------------------------
IC_PACKAGE_MASS_MG = 10.0  # generic small QFN/WLCSP sensor-IC package allowance, per IC
SMALL_PCB_MASS_G = {"wrist_module": 0.6, "chest_module": 0.8, "head_module": 0.7, "leg_module": 0.5}
ENCLOSURE_MASS_G = {"wrist_module": 3.0, "chest_module": 2.0, "head_module": 2.5, "leg_module": 1.5}
ATTACHMENT_MASS_G = {
    "wrist_module": 4.0,  # elastomer strap
    "chest_module": 3.0,  # adhesive electrode patch set
    "head_module": 3.5,  # headband + peri-ocular extension
    "leg_module": 3.0,  # strap
}
WIRING_MASS_G = {"wrist_module": 0.2, "chest_module": 0.8, "head_module": 0.6, "leg_module": 0.5}
BATTERY_REFERENCE_MAH = 150.0
BATTERY_REFERENCE_V = 3.7
BATTERY_ENERGY_DENSITY_WH_PER_KG = 190.0  # typical small Li-Po reference
battery_energy_wh = BATTERY_REFERENCE_MAH / 1000.0 * BATTERY_REFERENCE_V
battery_mass_g = battery_energy_wh / BATTERY_ENERGY_DENSITY_WH_PER_KG * 1000.0

IC_COUNTS = {"wrist_module": 4, "chest_module": 2, "head_module": 1, "leg_module": 1}  # AFE/sensor ICs per module

module_mass_g = {}
for mod in ("wrist_module", "chest_module", "head_module", "leg_module"):
    ic_mass_g = IC_COUNTS[mod] * IC_PACKAGE_MASS_MG / 1000.0
    module_mass_g[mod] = {
        "component_ic_mass_g": round(ic_mass_g, 4),
        "pcb_mass_g": SMALL_PCB_MASS_G[mod],
        "battery_mass_g": round(battery_mass_g, 3),
        "enclosure_mass_g": ENCLOSURE_MASS_G[mod],
        "attachment_mass_g": ATTACHMENT_MASS_G[mod],
        "wiring_mass_g": WIRING_MASS_G[mod],
    }
    module_mass_g[mod]["module_total_g"] = round(sum(module_mass_g[mod].values()), 3)

# EOG incremental mass: +2 ocular electrodes + leads only (shared module/AFE/battery)
EOG_ELECTRODE_MASS_G_EACH = 0.15
EOG_LEAD_MASS_G_EACH = 0.05
eog_incremental_mass_g = 2 * (EOG_ELECTRODE_MASS_G_EACH + EOG_LEAD_MASS_G_EACH)

system_mass_base_topology_g = sum(m["module_total_g"] for m in module_mass_g.values())

# leg_module mass computed for completeness but EXCLUDED from base system mass
# (leg BioZ remains EXPERIMENTAL, rule 47).
system_mass_base_topology_excl_leg_g = system_mass_base_topology_g - module_mass_g["leg_module"]["module_total_g"]


def q(value, unit, evidence, note=None, basis=None):
    d = {"value": round(value, 6) if isinstance(value, float) else value, "unit": unit, "evidence_class": evidence}
    if note:
        d["note"] = note
    if basis:
        d["basis"] = basis
    return d


artifact = {
    "artifact_id": "biological-minimalism-stage4-engineering-readiness-v1",
    "schema_version": "1.0.0",
    "sprint": "STAGE4_PARALLEL_ENGINEERING_AND_CLEAN_INTEGRATION_PREPARATION",
    "generated_role": "INTEGRATION_OWNER",
    "statement": (
        "Advances Day-11 Part-2/3 engineering readiness from NOT_READY toward "
        "PARTIAL_READY by filling in explicit ENGINEERING_ASSUMPTION operating "
        "scenarios for every previously-open blocker (LED power, EEG/EOG AFE "
        "power, thoracic/leg BioZ power, MCU/radio/regulator numeric points, "
        "duty schedule, mass tiers). This is NOT a final architecture, NOT a "
        "final BOM, and NOT a guaranteed-minimum power/mass figure. All "
        "component-level DATASHEET_DIRECT/DATASHEET_CALCULATED values are "
        "carried over unchanged from results/reference_power_budget_day11_part2.json "
        "and results/reference_data_rate_budget_day11.json; only previously-"
        "NOT_READY fields are newly populated here, each tagged with its own "
        "evidence_class so a reader can distinguish datasheet fact from "
        "engineering assumption at every field."
    ),
    "prohibited": [
        "Do NOT present system_average_power_battery_side_mw as a guaranteed minimum or maximum.",
        "Do NOT include leg_bioz or second_ppg_site in any 'base system' total.",
        "Do NOT relabel ENGINEERING_ASSUMPTION fields (head AFE power, BioZ power, MCU/radio/regulator numeric points, mass allowances) as DATASHEET_DIRECT or DATASHEET_CALCULATED.",
        "Do NOT treat this artifact as FINAL_ARCHITECTURE=RESOLVED or FORMAL_PARETO=READY.",
    ],
    "power": {
        "wrist_ppg": {
            "afe_reference_power_mw": q(WRIST_PPG_AFE_MW, "mW", EV_DATASHEET_CALCULATED, "frozen Day-11 Part-2 value, LED-excluded"),
            "led_scenario": {
                "n_active_leds": WRIST_PPG_LED_SCENARIO.n_active_leds,
                "i_led_peak_ma": WRIST_PPG_LED_SCENARIO.i_led_peak_ma,
                "v_led_forward_v": WRIST_PPG_LED_SCENARIO.v_led_forward_v,
                "t_pulse_seconds": WRIST_PPG_LED_SCENARIO.t_pulse_seconds,
                "f_pulse_hz": WRIST_PPG_LED_SCENARIO.f_pulse_hz,
                "evidence_class": EV_ENGINEERING_ASSUMPTION,
                "formula": wrist_ppg_led.formula,
                "duty_factor": wrist_ppg_led.duty_factor,
                "led_average_power_mw": q(wrist_ppg_led.total_average_power_mw, "mW", EV_ENGINEERING_ASSUMPTION, "computed via ml/engineering/ppg_led_power.compute_led_power"),
            },
            "total_incl_led_mw": q(wrist_ppg_total_mw, "mW", EV_ENGINEERING_ASSUMPTION, "AFE (datasheet) + LED (engineering assumption); LED contribution kept visible, not merged silently"),
        },
        "wrist_imu": q(WRIST_IMU_MW, "mW", EV_DATASHEET_CALCULATED, "frozen Day-11 Part-2 reference operating point, accel-only low-power, unchanged"),
        "skin_temperature": q(TMP117_MW, "mW", EV_DATASHEET_CALCULATED, "frozen, unchanged"),
        "light_sensor": q(OPT3001_MW, "mW", EV_DATASHEET_CALCULATED, "frozen, unchanged, wrist case"),
        "ecg_chest_afe": q(ECG_AFE_MW, "mW", EV_DATASHEET_CALCULATED, "frozen, unchanged"),
        "thoracic_bioz": {
            "scenario": {
                "excitation_freq_hz": BIOZ_EXCITATION_FREQ_HZ,
                "active_current_ma": BIOZ_ACTIVE_CURRENT_MA,
                "standby_current_ma": BIOZ_STANDBY_CURRENT_MA,
                "supply_v": BIOZ_SUPPLY_V,
                "measurement_window_s": BIOZ_MEASUREMENT_WINDOW_S,
                "measurement_period_s": BIOZ_MEASUREMENT_PERIOD_S,
                "evidence_class": EV_ENGINEERING_ASSUMPTION,
                "lbnp_science_dependency_note": "Excitation frequency/electrode configuration is a general tetrapolar bioimpedance engineering reference, independent of any specific experiment. The 1 Hz measurement CADENCE, however, is an engineering placeholder — the cadence appropriate for detecting LBNP-induced fluid shifts specifically depends on the physiological time constant that Ismet's LBNP Stage-3 science will characterize; this value must be revisited once that evidence lands.",
            },
            "average_power_mw": q(bioz_avg_power_mw, "mW", EV_ENGINEERING_ASSUMPTION, "duty-folded average"),
        },
        "leg_bioz": {
            "note": "Same AD5940-class engineering assumption as thoracic_bioz, separate instance. EXPERIMENTAL — excluded from base system total (rule 47).",
            "average_power_mw": q(leg_bioz_increment_mw, "mW", EV_ENGINEERING_ASSUMPTION),
            "included_in_base_total": False,
        },
        "head_afe_eeg_eog": {
            "scenario": {
                "active_channels": HEAD_AFE_ACTIVE_CHANNELS,
                "per_channel_current_ua": HEAD_AFE_PER_CHANNEL_CURRENT_UA,
                "fixed_overhead_current_ua": HEAD_AFE_FIXED_OVERHEAD_CURRENT_UA,
                "supply_v": HEAD_AFE_SUPPLY_V,
                "evidence_class": EV_ENGINEERING_ASSUMPTION,
                "note": (
                    "Day-11 Part-2 explicitly could not verify an exact ADS1299 "
                    "per-channel power-dissipation table row in its environment "
                    "(no PDF text extraction available). This environment has the "
                    "same limitation. This is therefore an explicit order-of-"
                    "magnitude ENGINEERING_ASSUMPTION for 2 active channels (1 EEG "
                    "+ 1 shared EOG) + internal reference + bias at the already-"
                    "frozen AVDD-bipolar (2.5V) supply point — NOT a verified "
                    "datasheet table value. Supersede with the exact datasheet "
                    "figure or bench measurement when available. SCOPE: analog "
                    "(AVDD) current only — DVDD digital-supply current (3.3V, "
                    "also frozen in Day-11 Part-2) is NOT included in this power "
                    "figure, matching the same AFE-only convention already used "
                    "for wrist_ppg/ecg_chest above."
                ),
            },
            "average_power_mw": q(head_afe_power_mw, "mW", EV_ENGINEERING_ASSUMPTION),
            "eog_incremental_power_mw": q(eog_incremental_power_mw, "mW", EV_ENGINEERING_ASSUMPTION, "2nd-channel increment over 1-EEG-channel-only baseline; shares reference/bias, adds no new module"),
        },
        "mcu": {
            "scenario": {
                "supply_v": MCU_SUPPLY_V,
                "active_current_ma": MCU_ACTIVE_CURRENT_MA,
                "sleep_current_ma": MCU_SLEEP_CURRENT_MA,
                "active_duty_fraction": MCU_ACTIVE_DUTY_FRACTION,
                "evidence_class": EV_ENGINEERING_ASSUMPTION,
                "reference_class": "Cortex-M4F BLE SoC class (nRF52840-class), matches Day-11 Part-2 BOM REFERENCE_SELECTED entry",
            },
            "average_power_mw": q(mcu_avg_power_mw, "mW", EV_ENGINEERING_ASSUMPTION),
        },
        "radio": {
            "scenario": {
                "supply_v": MCU_SUPPLY_V,
                "tx_rx_current_ma": RADIO_TX_RX_CURRENT_MA,
                "idle_current_ma": RADIO_IDLE_CURRENT_MA,
                "active_duty_fraction": RADIO_ACTIVE_DUTY_FRACTION,
                "evidence_class": EV_ENGINEERING_ASSUMPTION,
                "reference_class": "BLE (scenario-level), matches Day-11 Part-2 BOM REFERENCE_SELECTED entry",
            },
            "average_power_mw": q(radio_avg_power_mw, "mW", EV_ENGINEERING_ASSUMPTION),
        },
        "regulator": {
            "efficiency": q(REGULATOR_EFFICIENCY, "fraction", EV_ENGINEERING_ASSUMPTION, "reference buck / high-efficiency-LDO assumption; applied once at the power-tree boundary"),
            "reference_class": "multi-rail PMIC/LDO, matches Day-11 Part-2 BOM REFERENCE_SELECTED entry",
        },
        "duty_schedule": DUTY_SCHEDULE,
        "system_average_power": {
            "status": "PARTIAL_READY",
            "reason": "Every previously-listed blocker (LED, EEG/EOG AFE, thoracic BioZ, MCU/radio/regulator numeric points, duty cycles) now has an explicit engineering-assumption value. Remains PARTIAL (not READY) because: (a) every closed value is ENGINEERING_ASSUMPTION not measured/vendor-verified, (b) battery selection is reference-class only, (c) leg BioZ and second PPG site are deliberately excluded from this total.",
            "base_topology_load_side_mw": q(system_load_side_total_mw, "mW", EV_ENGINEERING_ASSUMPTION, "sum of base-topology module average powers, pre-regulator"),
            "base_topology_battery_side_mw": q(system_battery_side_total_mw, "mW", EV_ENGINEERING_ASSUMPTION, f"load-side total / regulator efficiency ({REGULATOR_EFFICIENCY})"),
            "contributors_mw": {k: round(v, 6) for k, v in base_topology_load_mw.items()},
            "excluded_from_base_total": {
                "leg_bioz_mw": round(leg_bioz_increment_mw, 6),
                "second_ppg_site_incl_led_mw": round(second_ppg_increment_mw, 6),
            },
            "not_included_in_any_total": [
                "enclosure/thermal effects on component current",
                "battery self-discharge",
                "charging circuit power",
                "manufacturing/process variation",
            ],
        },
    },
    "data_rate": {
        "statement": "Extends results/reference_data_rate_budget_day11.json. Frozen DATASHEET_CALCULATED rows are reused unchanged (cited by value, not recomputed). Only previously-NOT_READY rows (light_sensor, thoracic_bioz, leg_bioz) and the transmitted/radio rate are newly computed here.",
        "newly_closed_modalities": {
            "light_sensor": {"channels": 1, "sample_rate_hz": LIGHT_SAMPLE_RATE_HZ, "bits_per_sample": 16, "raw_payload_bit_rate_bps": light_bps, "evidence_class": EV_ENGINEERING_ASSUMPTION, "note": "1 sample / 10 s context-only cadence"},
            "thoracic_bioz": {"channels": BIOZ_CHANNELS, "sample_rate_hz": BIOZ_SAMPLE_RATE_HZ, "bits_per_sample": BIOZ_BITS_PER_SAMPLE, "raw_payload_bit_rate_bps": thoracic_bioz_bps, "evidence_class": EV_ENGINEERING_ASSUMPTION},
            "leg_bioz": {"channels": BIOZ_CHANNELS, "sample_rate_hz": BIOZ_SAMPLE_RATE_HZ, "bits_per_sample": BIOZ_BITS_PER_SAMPLE, "raw_payload_bit_rate_bps": leg_bioz_bps, "evidence_class": EV_ENGINEERING_ASSUMPTION, "included_in_base_total": False, "note": "EXPERIMENTAL leg module, excluded from base total"},
        },
        "base_topology_raw_bps": {k: round(v, 3) for k, v in base_topology_raw_bps.items()},
        "system_raw_total_bps": q(system_raw_total_bps, "bps", EV_ENGINEERING_ASSUMPTION, "sum of base-topology raw contributions; excludes leg_bioz and second_ppg_site"),
        "protocol_overhead": {
            "fraction": RADIO_PROTOCOL_OVERHEAD_FRACTION,
            "evidence_class": EV_ENGINEERING_ASSUMPTION,
            "note": "commonly-cited order-of-magnitude BLE notification/ATT/L2CAP overhead reference for small payloads; NOT a specific BLE stack's measured overhead",
        },
        "system_transmitted_bps": q(system_transmitted_bps, "bps", EV_ENGINEERING_ASSUMPTION, "raw x (1 + protocol_overhead_fraction); still excludes compression, retransmission, connection-event scheduling loss"),
        "processed_data_rate_status": EV_NOT_READY,
        "processed_data_rate_reason": "No on-device feature-extraction/compression pipeline data-reduction factor is frozen; processed rate remains NOT_READY (not assumed equal to raw or to transmitted).",
        "excluded_from_base_total_bps": {
            "second_ppg_site": SECOND_PPG_BPS,
            "leg_bioz": round(leg_bioz_increment_bps, 3),
        },
    },
    "mass": {
        "statement": "Advances all 4 base-topology modules (wrist, chest, head, leg-characterized-but-excluded) from Tier0 to Tier2 (electronics-subassembly estimate) using generic small-IC/PCB/enclosure/strap engineering allowances. NOT vendor mass data, NOT measured (no Tier3/Tier4 claimed).",
        "tier_achieved": "Tier2",
        "tier_definition": "electronics-subassembly estimate (per results/reference_mass_readiness_day11_part2.json tier_definitions)",
        "evidence_class": EV_ENGINEERING_ALLOWANCE,
        "allowances_used": {
            "ic_package_mass_mg_per_ic": IC_PACKAGE_MASS_MG,
            "battery_reference": {"capacity_mah": BATTERY_REFERENCE_MAH, "voltage_v": BATTERY_REFERENCE_V, "energy_density_wh_per_kg": BATTERY_ENERGY_DENSITY_WH_PER_KG, "computed_mass_g": round(battery_mass_g, 3)},
        },
        "modules": module_mass_g,
        "eog_incremental_mass_g": q(eog_incremental_mass_g, "g", EV_ENGINEERING_ALLOWANCE, "+2 ocular electrodes + leads only; shares module/AFE/battery, so this is the ONLY incremental mass EOG adds"),
        "system_mass_base_topology_excl_leg_g": q(system_mass_base_topology_excl_leg_g, "g", EV_ENGINEERING_ALLOWANCE, "wrist + chest + head modules only; leg_module computed but excluded (EXPERIMENTAL, rule 47)"),
        "system_mass_status": "PARTIAL",
        "not_included": [
            "inter-module wiring harness beyond per-module wiring allowance",
            "external cabling to a central hub (module boundary still OPEN for optical evaluation branch)",
            "manufacturing tolerance/process mass",
            "adhesive/gel consumables mass beyond the modeled patch allowance",
        ],
    },
    "bom": {
        "statement": "Advances MCU/radio/regulator/battery from class-only REFERENCE_SELECTED (Day-11 Part-2) to REFERENCE_SELECTED with an attached numeric operating point (this artifact). PCB/enclosure/attachment/wiring move from MISSING to REFERENCE_SELECTED at a generic allowance level (mass only, not a specific vendor part).",
        "not_a_final_bom": True,
        "final": False,
        "items_advanced": [
            {"item": "mcu", "from": "REFERENCE_SELECTED (class only)", "to": "REFERENCE_SELECTED (class + numeric operating point)"},
            {"item": "radio", "from": "REFERENCE_SELECTED (class only)", "to": "REFERENCE_SELECTED (class + numeric operating point)"},
            {"item": "regulator", "from": "REFERENCE_SELECTED (efficiency NOT frozen)", "to": "REFERENCE_SELECTED (efficiency = 0.85 engineering assumption)"},
            {"item": "pcb", "from": "MISSING", "to": "REFERENCE_SELECTED (generic small-PCB mass allowance, no specific stackup/vendor)"},
            {"item": "enclosure", "from": "MISSING", "to": "REFERENCE_SELECTED (generic polymer shell mass allowance)"},
            {"item": "attachment", "from": "MISSING (geometry/material)", "to": "REFERENCE_SELECTED (generic strap/patch/headband mass allowance)"},
            {"item": "wiring", "from": "MISSING", "to": "REFERENCE_SELECTED (generic per-module interconnect mass allowance)"},
        ],
        "still_missing": [
            "sensing_ic_bioz active operating point beyond engineering assumption (thoracic + leg)",
            "head AFE exact datasheet power table value",
            "electrode materials/montage exact count for EEG (count remains OPEN; only +2 EOG increment is defensible)",
            "second_ppg_site module boundary (shared/tethered/standalone)",
            "vendor-specific part numbers for MCU/radio/regulator/battery (class-level only)",
        ],
    },
    "final_architecture_status": "UNRESOLVED",
    "formal_pareto_status": "FORMAL_PARETO_NOT_READY",
    "source_artifacts": [
        "results/reference_power_budget_day11_part2.json",
        "results/reference_data_rate_budget_day11.json",
        "results/reference_mass_readiness_day11_part2.json",
        "results/reference_bom_readiness_day11_part2.json",
        "ml/engineering/ppg_led_power.py",
    ],
}

OUT_PATH.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
print(f"wrote {OUT_PATH}")
print(f"wrist_ppg_led: {wrist_ppg_led}")
print(f"system_load_side_total_mw={system_load_side_total_mw:.4f} battery_side={system_battery_side_total_mw:.4f}")
print(f"system_raw_total_bps={system_raw_total_bps:.2f} transmitted_bps={system_transmitted_bps:.2f}")
print(f"system_mass_base_topology_excl_leg_g={system_mass_base_topology_excl_leg_g:.3f}")
