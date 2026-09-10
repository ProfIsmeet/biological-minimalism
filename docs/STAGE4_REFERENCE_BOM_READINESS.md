# Stage 4 Reference BOM Readiness

Source of truth: `results/stage4_engineering_readiness.json` (`bom` block),
extending `results/reference_bom_readiness_day11_part2.json`. **This is a
`PARTIAL_REFERENCE_BOM`, not a final BOM.** `final = false` on every line
below; nothing here has been explicitly approved as flight hardware.

## What this report advances vs. what stays unchanged

Day-11 Part-2 already moved MCU/radio/regulator/battery from `MISSING` to
`REFERENCE_SELECTED` at the **class level only** (e.g. "Cortex-M4F BLE SoC
class", "efficiency NOT frozen"). This report attaches a **numeric operating
point** to each of those class-level selections, and additionally advances
PCB/enclosure/attachment/wiring from `MISSING` to `REFERENCE_SELECTED` at a
**generic mass-allowance level** (no specific vendor part chosen).

| Item | Before (Day-11 Part-2) | After (this report) | Evidence |
|---|---|---|---|
| MCU | `REFERENCE_SELECTED` (class only) | `REFERENCE_SELECTED` (class + numeric operating point: 5 mA active / 2 µA sleep @ 3.3 V, 10% duty → 1.66 mW average) | `ENGINEERING_ASSUMPTION` |
| Radio | `REFERENCE_SELECTED` (class only) | `REFERENCE_SELECTED` (class + numeric operating point: 5 mA TX/RX / 1 µA idle @ 3.3 V, 1% duty → 0.169 mW average) | `ENGINEERING_ASSUMPTION` |
| Regulator | `REFERENCE_SELECTED` (efficiency NOT frozen) | `REFERENCE_SELECTED` (efficiency = 0.85) | `ENGINEERING_ASSUMPTION` |
| PCB | `MISSING` | `REFERENCE_SELECTED` (generic small-PCB mass allowance per module: 0.5–0.8 g; no stackup/vendor chosen) | `ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE` |
| Enclosure | `MISSING` | `REFERENCE_SELECTED` (generic polymer shell mass allowance per module: 1.5–3.0 g) | `ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE` |
| Attachment | `MISSING` (geometry/material) | `REFERENCE_SELECTED` (generic strap/patch/headband mass allowance: 3.0–4.0 g) | `ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE` |
| Wiring | `MISSING` | `REFERENCE_SELECTED` (generic per-module interconnect mass allowance: 0.2–0.8 g) | `ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE` |
| Battery | `REFERENCE_SELECTED` (capacity/mass/dims unknown) | `REFERENCE_SELECTED` (150 mAh / 3.7 V Li-Po class, 190 Wh/kg → 0.293 g per module instance) | `ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE` |

Sensing ICs (MAX86141, BMI270, TMP117, OPT3001-Q1, ADS1292R, ADS1299-4-class,
AD5940-class) remain exactly as Day-11 Part-2 left them — `REFERENCE_SELECTED`
at the representative-part-class level, unchanged by this report.

## Still MISSING / still open

- Sensing-IC BioZ active operating point beyond this report's engineering assumption (thoracic + leg).
- Exact ADS1299 datasheet power-dissipation table value (head AFE power stays an assumption).
- EEG electrode montage exact channel count (OPEN); only the +2 EOG increment is defensible.
- `second_ppg_site` module boundary (shared/tethered/standalone) — still `MISSING`, no BOM line advanced for it.
- Vendor-specific part numbers for MCU/radio/regulator/battery — class-level reference only, no specific manufacturer part chosen.
- PCB stackup, enclosure geometry, and specific strap/electrode materials — mass-allowance level only, no CAD or material spec.

## System readiness (per this report)

| Dimension | Status |
|---|---|
| `system_average_power` | `PARTIAL_READY` (was `SYSTEM_AVERAGE_POWER_NOT_READY`) |
| `system_mass` | `PARTIAL` (was `SYSTEM_MASS_NOT_READY`) |
| `final_bom` | `FINAL_BOM_NOT_SELECTED` (unchanged — no line in this table is final) |
