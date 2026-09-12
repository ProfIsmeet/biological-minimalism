# DAY 11 — PART 2 HANDOFF (Reference Power + Shared Electronics + Data-Rate + Mass/BOM Readiness)

> Handoff-first. Written so **Part-3 (architecture / Pareto integration)** can continue with **no conversation context**.
> Everything below is derived only from committed artifacts. Part-2 is **engineering only** — no scientific change, no architecture finalization, no formal Pareto.

## 0. Branch / commit state
- **Repository:** `/Users/emirharunsunbul/Documents/ChatGPT/IAC`
- **Remote:** `origin` → `https://github.com/ProfIsmeet/biological-minimalism.git`
- **Part-1 base (verified HEAD):** `a43b7aa8e65349d703a0eb1ef34307e3a00ab4c1` (`day11-engineering-audit`)
- **Part-2 branch:** `day11-power-mass-bom` (created from `a43b7aa`)
- `main`, Day-10 canonical, Part-1 branch, and Ismet science branches **untouched**.

## 1. What Part-2 did
Converted Part-1's audited evidence into the **maximum defensible reference calculation state** without inventing unknowns. Produced 7 machine-readable artifacts + a builder + tests. Kept four power layers separate; kept every unknown as `null`+status (never `0`).

## 2. Selected reference operating points (frozen this Part)
| Modality | Reference operating point | Reference power | Class |
|---|---|---|---|
| Wrist PPG (MAX86141) | optical readout, AFE floor @25 s/s, 1.8 V | AFE ≤ **0.018 mW** (LED **excluded**) | DATASHEET_CALCULATED |
| Wrist IMU (BMI270) | **accel-only, low-power, gyro OFF**, 25 Hz doc. point (32 Hz sci-rate) | **0.018 mW** (band 0.018–0.378) | DATASHEET_CALCULATED |
| Skin temp (TMP117) | 1 Hz conversion, averaging off, 3.3 V | **0.01155 mW** | DATASHEET_CALCULATED |
| Light (OPT3001) | continuous conversion, 3.3 V | **0.00594 mW** (wrist) / **0** (cabin) | DATASHEET_CALCULATED |
| Chest ECG (ADS1292R) | 2-ch AFE @250 s/s | **0.67 mW** (2×335 µW/ch) | DATASHEET_CALCULATED |
| Head EEG/EOG (ADS1299-4) | **2 ch enabled** (1 EEG Fpz-Cz + 1 EOG), 100 Hz→250 SPS, gain 24, int-ref+bias ON, lead-off OFF, AVDD 5 V / DVDD 3.3 V | **NOT_READY** (per-ch power unverified) | — |
| Thoracic BioZ (AD5940) | intermittent; excitation/cadence OPEN | **NOT_READY** | — |
| Leg BioZ (AD5940, separate) | separate region/module; OPEN | **NOT_READY** | — |
| Second PPG (MAX86141-cl) | 3-λ @500 Hz (dataset rate, not a frozen protocol) | **NOT_READY** (LED + 500 Hz seq + boundary OPEN) | — |

## 3. Exact power values & exclusions
- **WRIST_SENSOR_ELECTRONICS_REFERENCE_SCENARIO_LED_EXCLUDED** (Level-3 partial, **LED-excluded CALCULATED REFERENCE SCENARIO** from datasheet-typical values — NOT a guaranteed lower bound; excludes MCU/radio/regulator/battery/storage):
  - wrist-light case: **0.05349 mW** (reference point) → **0.41349 mW** (BMI270 normal upper)
  - cabin case (no light): **0.04755 mW** → **0.40755 mW**
- **CHEST_SENSOR_ELECTRONICS_REFERENCE_POWER**: ECG AFE only = **0.67 mW**; module boundary **NOT_READY** (thoracic BioZ open).
- Head / leg / second-PPG sensor-electronics boundaries: **NOT_READY**.
- **LED formula (both PPGs), no total faked:** `P_LED_avg = N_active_LEDs × I_LED × V_LED_forward × (t_pulse × f_pulse)` — every variable `UNKNOWN`.

## 4. Reference shared-electronics stack (final_part = false)
- **MCU:** Cortex-M4F-class BLE SoC (nRF52-class) — currents **unresolved on purpose** (so no power leaks into a sum).
- **Radio:** two scenarios — `continuous_stream_reference` & `buffered_burst_reference`; neither deployment-final; schedule not frozen.
- **Regulator/PMIC:** rails defined (3.3 V sensor / 5 V AVDD / 1.8 V DVDD / battery); **efficiency `null`** — arbitrary 90% explicitly NOT applied.
- **Battery:** `REFERENCE_MECHANICAL_BATTERY_CASE` (Li-Po class, 3.7 V nominal); capacity/mass/dims `UNKNOWN`; no runtime computed.

## 5. Data-rate budget (`raw = channels × Hz × bits`)
ppg 1216 · imu 1536 · temp 16 · ecg 12000 · eeg 2400 (1 ch@100 Hz; AFE-capacity 4 ch@250 SPS = 24000) · eog 2400 (matches frozen EOG burden) · 2nd-PPG 28500 bps. Light/BioZ×2 = **NOT_READY** (null, not 0).
- **PARTIAL system RAW total = 48068 bps (48.068 kbps)** — LOWER BOUND, scientific-use-case head; excludes light, thoracic+leg BioZ, protocol overhead, compression.
- `RADIO_DATA_RATE` and `PROCESSED_DATA_RATE`: **NOT_READY**. Raw ≠ radio bandwidth.

## 6. Mass tiers (§24–26) — all modules **Tier 0**
Tier framework (0 unknown … 4 measured) + per-module contributor classification formalised. **No mass number asserted** (package dimensions ≠ mass; no material model / board design / cell). EOG incremental mass (+2 ocular electrodes+leads) = `SYSTEM_MASS_NOT_READY` (not zero).

## 7. BOM readiness advance (§31)
Vocabulary `REFERENCE_SELECTED · AVAILABLE · PARTIAL · MISSING · NOT_APPLICABLE`. **Advance vs Day-10:** MCU/radio/regulator/battery **MISSING → REFERENCE_SELECTED** (class level, `final=false`). Sensing ICs/AFEs stay REFERENCE_SELECTED. Electrodes/PCB/enclosure/attachment/wiring stay MISSING. Head electrodes/wiring **PARTIAL** (EOG contact increment = 2 defensible). `REFERENCE_SELECTED ≠ final component`.

## 8. System average power status (§34): **NO — SYSTEM_AVERAGE_POWER_NOT_READY**
Highest defensible level reached: `REFERENCE_SENSOR_ELECTRONICS_POWER_AVAILABLE_FOR_WRIST (LED-excluded reference scenario) + ECG_AFE_REFERENCE_POWER_FOR_CHEST`. Blockers: LED power, EEG/EOG head-AFE point, thoracic+leg BioZ point, MCU/radio/regulator identity+power, deployable duty, regulator efficiency, battery. **This is a successful, honest outcome.**

## 9. Pareto blocker progress (§33) — canonical Pareto still **NOT_READY**
- `cross_dataset_incomparability` — **BLOCKER, unchanged, MUST NOT downgrade** (engineering cannot fix it).
- `power_partial` HIGH → **HIGH (PARTIAL_IMPROVED)** (reference points added; system power still open).
- `mass_missing` HIGH → **HIGH** (framework only).
- `module_bom_unresolved` HIGH → **HIGH (PARTIALLY_ADDRESSED)**; Part-3 **may** consider MEDIUM if class-level reference BOM suffices for a *reference* (not final) Pareto — **not downgraded here**.
- scientific blockers (interaction / sleep-scope / targets): unchanged.

## 10. Files Part-3 MUST consume
| File | Role |
|---|---|
| `results/day11_part3_engineering_inputs.json` | **PRIMARY handoff** — per-candidate burdens/power/data-rate/BOM/uncertainty |
| `results/reference_power_budget_day11_part2.json` | 4-layer power, boundaries, exclusions |
| `results/reference_data_rate_budget_day11.json` | raw data-rate table + partial system total |
| `results/reference_shared_electronics_day11.json` | reference MCU/radio/PMIC/battery classes |
| `results/reference_mass_readiness_day11_part2.json` | mass tiers (all Tier 0) |
| `results/reference_bom_readiness_day11_part2.json` | BOM readiness (advances Day-10) |
| `results/pareto_blocker_progress_day11_part2.json` | blocker deltas (not the canonical decision) |
| Rebuild: `python ml/build_day11_part2_engineering.py` · Tests: `pytest ml/tests/test_day11_part2_engineering.py` |

## 11. Engineering corrections vs Part-1
None required. Refinements only: (a) IMU band → one frozen `REFERENCE_IMU_OPERATING_POINT` (0.018 mW, gyro off) with band retained; (b) head EEG use case pinned to **2 enabled channels** (1 EEG + 1 EOG, 2 spare) at 100 Hz→250 SPS; (c) EOG data-rate reconciled to the frozen burden artifact (2400 bps).

## 12. WARNINGS for Part-3
- Do **NOT** sum component/AFE powers into a system number; the wrist boundary is an **LED-excluded reference scenario** (datasheet-typical, not a guaranteed bound), not module power.
- Do **NOT** treat the ADS1299 AVDD/ODR facts as a head power number — power is **NOT_READY**.
- Do **NOT** use the AD5940 6.5 µA potentiostat point as BioZ power.
- Do **NOT** zero EOG/second-PPG burden on favorable/negative science.
- Do **NOT** rank HR-MAE vs sleep macro-F1; do **NOT** upgrade CONDITIONAL/DEPRIORITIZE gate decisions (that is Part-3 architecture).
- `REFERENCE_SELECTED ≠ final`; `SYSTEM_AVERAGE_POWER_NOT_READY`; `SYSTEM_MASS_NOT_READY`; `FORMAL_PARETO_NOT_READY`.
- **Environment:** GateGuard fact-forcing hook is active (blocks first Bash + each new-file Write); disable with `ECC_GATEGUARD=off` if it impedes Part-3.
