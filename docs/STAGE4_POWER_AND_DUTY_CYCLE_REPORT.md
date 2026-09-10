# Stage 4 Power and Duty-Cycle Report

Source of truth: `results/stage4_engineering_readiness.json` (`power` block), computed
by `scripts/build_stage4_engineering_readiness.py`. Extends — does not replace —
`results/reference_power_budget_day11_part2.json`. Every `DATASHEET_DIRECT`/
`DATASHEET_CALCULATED` value below is carried over from Day-11 Part-2 unchanged;
only previously-`NOT_READY` fields are newly computed here, each explicitly tagged
`ENGINEERING_ASSUMPTION` or `ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE` — **never**
relabeled as a datasheet fact.

## Component operating points

| Component | Power | Evidence class | Note |
|---|---|---|---|
| `wrist_ppg` AFE (MAX86141-class) | 0.018 mW | `DATASHEET_CALCULATED` (frozen) | LED-excluded floor, unchanged from Day-11 Part-2 |
| `wrist_ppg` LED contribution | 0.768 mW | `ENGINEERING_ASSUMPTION` | 2 LEDs, 20 mA, 3.0 V, 100 µs pulse, 64 Hz — computed via `ml/engineering/ppg_led_power.compute_led_power()`, not a new formula |
| `wrist_ppg` total (AFE + LED) | 0.786 mW | mixed (see components) | LED contribution kept visible, never merged silently (rule 36) |
| `wrist_imu` (BMI270) | 0.018 mW | `DATASHEET_CALCULATED` (frozen) | Accel-only low-power reference operating point, unchanged |
| `skin_temperature` (TMP117) | 0.01155 mW | `DATASHEET_CALCULATED` (frozen) | 1 Hz continuous conversion |
| `light_sensor` (OPT3001-Q1) | 0.00594 mW | `DATASHEET_CALCULATED` (frozen) | Wrist case; context-only role (rule 41), not promoted to predictive necessity |
| `ecg_chest` AFE (ADS1292R) | 0.67 mW | `DATASHEET_CALCULATED` (frozen) | 2 ch @ 250 sps |
| `thoracic_bioz` (AD5940-class) | 0.033 mW | `ENGINEERING_ASSUMPTION` | 50 kHz tetrapolar excitation, 4 mA active / 5 µA standby, 100 ms burst per 1 s (10% duty) |
| `leg_bioz` (AD5940-class, separate instance) | 0.033 mW | `ENGINEERING_ASSUMPTION` | Same scenario as thoracic; **EXPERIMENTAL, excluded from base total** (rule 47) |
| `head_afe_eeg_eog` (ADS1299-4-class) | 1.575 mW | `ENGINEERING_ASSUMPTION` | 2 active channels (1 EEG + 1 shared EOG), 150 µA/ch + 300 µA fixed overhead @ 2.5 V. Day-11 Part-2 explicitly could not verify an exact ADS1299 datasheet power table row in its environment; this environment has the same limitation, so this stays an explicit order-of-magnitude estimate, not a re-labeled datasheet value. |
| EOG incremental power | 0.375 mW | `ENGINEERING_ASSUMPTION` | 2nd-channel increment over 1-EEG-channel-only baseline; shares reference/bias, adds no new AFE/module |
| `mcu` (Cortex-M4F BLE SoC class) | 1.66 mW | `ENGINEERING_ASSUMPTION` | 5 mA active / 2 µA sleep @ 3.3 V, 10% active duty (periodic feature-extraction burst) |
| `radio` (BLE, scenario-level) | 0.169 mW | `ENGINEERING_ASSUMPTION` | 5 mA TX/RX / 1 µA idle @ 3.3 V, 1% active duty (low-duty-cycle connection-interval streaming) |
| Regulator efficiency | 0.85 | `ENGINEERING_ASSUMPTION` | Reference buck/high-efficiency-LDO assumption, applied once at the power-tree boundary |

## LED power model

Formula (unchanged, from `ml/engineering/ppg_led_power.py`, already frozen in
Day-11 Part-2 as `wrist_ppg.led_contribution.formula`):

```
P_LED_avg = N_active_LEDs * I_LED_peak * V_LED_forward * (t_pulse * f_pulse)
```

Wrist scenario: `N=2, I=20 mA, V=3.0 V, t_pulse=100 µs, f_pulse=64 Hz` → duty
factor 0.64% → **0.768 mW average**. This is an explicit engineering assumption
(green + IR emitters for HR-only use case, mid-range programmable drive current),
not a datasheet-guaranteed minimum or maximum (rule 35). LED power dominates
the wrist module's total power, as flagged by Day-11 Part-2's own `led_contribution.note`.

Second-PPG-site scenario (characterized for completeness, **excluded from every
base total** — optional/deprioritized, rule 48): `N=3, I=20 mA, V=3.0 V,
t_pulse=100 µs, f_pulse=500 Hz` → **6.0 mW average**. Higher than the wrist
scenario because of the 3-wavelength/500 Hz PTT-dataset-matched rate.

## Duty schedule (`ASSUMED_USE_SCHEDULE`, not a datasheet fact)

| Module/component | State | Duty fraction | Note |
|---|---|---|---|
| `wrist_ppg` | active_acquisition | 1.0 | Continuous optical acquisition |
| `wrist_imu` | active_acquisition | 1.0 | Continuous — required for PPG motion-artifact correction |
| `skin_temperature` | periodic_acquisition | 1.0 | 1 Hz continuous conversion (duty already folded into the frozen power figure) |
| `light_sensor` | periodic_acquisition | 1.0 | Continuous low-rate polling (duty already folded into the frozen power figure) |
| `ecg_chest` | active_acquisition | 1.0 | Continuous cardiac monitoring |
| `thoracic_bioz` | periodic_acquisition | 0.10 | 100 ms burst / 1 s period |
| `head_afe_eeg_eog` | active_acquisition | 1.0 | Continuous — required for sleep-staging scientific use case |
| `mcu` | processing | 0.10 | Periodic feature-extraction/fusion burst |
| `radio` | transmission | 0.01 | Low-duty-cycle BLE connection-interval streaming |

Every duty fraction above is an `ASSUMED_USE_SCHEDULE` entry, kept structurally
separate from `DATASHEET_OPERATING_POINT` fields (rule 50) — none of it is a
datasheet-defined behavior.

## Regulator / power-tree assumption

A single reference buck/high-efficiency-LDO conversion stage is assumed at
85% efficiency, applied once at the power-tree boundary to convert the
summed load-side (post-regulation) power into a battery-side (pre-regulation)
figure. No per-rail conversion-loss breakdown is modeled; this is a system-level
approximation, explicitly labeled as such.

## System average power — PARTIAL_READY

| Quantity | Value | Scope |
|---|---|---|
| Base-topology load-side total | **6.150 mW** | wrist_ppg (incl. LED) + wrist_imu + skin_temperature + light_sensor + ecg_chest_afe + thoracic_bioz + head_afe_eeg_eog + mcu + radio |
| Base-topology battery-side total | **7.236 mW** | load-side total ÷ 0.85 regulator efficiency |
| `leg_bioz` (excluded) | 0.033 mW | EXPERIMENTAL, not in any base total |
| `second_ppg_site` incl. LED (excluded) | 6.018 mW | OPTIONAL/DEPRIORITIZED_FOR_CURRENT_TARGET, not in any base total |

**Status: `PARTIAL_READY`**, not `READY` — because every newly-closed contributor
is an `ENGINEERING_ASSUMPTION`, not a measured or vendor-verified value; the
battery itself is reference-class only (see mass/BOM reports); and this total
excludes enclosure/thermal effects on component current, battery self-discharge,
charging-circuit power, and manufacturing/process variation.

## Sensitivity note

The dominant single contributor is `ecg_chest_afe` (0.67 mW, frozen datasheet
value) followed by `head_afe_eeg_eog` (1.575 mW, engineering assumption) and
`mcu` (1.66 mW, engineering assumption) — together these three account for
roughly 62% of the base-topology load-side total. The two largest contributors
are both `ENGINEERING_ASSUMPTION`-class, so the overall system total's
uncertainty is dominated by assumption uncertainty, not by the frozen
datasheet-calculated components. No lower/upper sensitivity band is asserted
beyond this qualitative statement — that would require a defined uncertainty
range per assumption, which is not yet frozen (kept honestly absent rather
than inventing pseudo-precision, rule 60).

## Unresolved contributors (explicitly still open)

- Exact ADS1299 datasheet power-dissipation table value (head AFE remains an assumption, not verified).
- Vendor-specific MCU/radio/regulator/battery part numbers (class-level reference only).
- Battery self-discharge, charging-circuit power, enclosure thermal effects.
- `second_ppg_site` 500 Hz AFE sequencing current beyond the 25 s/s floor already frozen.
