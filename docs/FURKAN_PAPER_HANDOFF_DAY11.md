# Furkan Paper Handoff — Day 11 (Engineering Methods / System Architecture + Engineering Results)

> Engineering addendum to the canonical scientific paper support (`docs/FURKAN_PAPER_HANDOFF_DAY10.md`).
> Everything here is derived only from committed Day-11 Part-2 artifacts, integrated in Part-3+4.
> **Boundary (hard):** do NOT write a total system power, a total system mass, a final BOM, a final
> architecture, or a formal Pareto frontier. The paper must state that engineering burden
> quantification remains **partial**.

## What is safe to put in the paper now

### Engineering Methods / System Architecture
- **Burden dimensions.** Each candidate sensor is characterised on separate, non-collapsed axes:
  new body region, new module, new sensing contacts, reference component/AFE power, raw data-rate
  increment, mass tier, and BOM readiness. These are never summed into one score.
- **Shared-module logic.** The reference topology is the Day-6 5-module / 9-component topology
  (not a final BOM). EOG is modelled in a `REFERENCE_SHARED_HEAD_MODULE` case: one spare channel of
  the existing ADS1299-class head AFE, reference/bias shared, **+2 lateral-ocular sensing electrodes,
  +0 module**. A standalone alternative (3–4 contacts, possibly +1 module) is documented but is not
  the reference case.
- **Reference operating points.** Duty-cycle assumptions are explicit reference-schedule assumptions,
  not deployable duty cycles (scientific sample rate ≠ product duty cycle).
- **Partial power accounting.** Power is kept in four separate layers (sensing IC / AFE / shared
  electronics / system). Only component and AFE boundaries are quantified; unknowns are carried as
  `null` + status, never 0.
- **No system total.** System average power, system mass, and the full BOM are explicitly `NOT_READY`
  / `PARTIAL`; the paper reports this as an honest, deliberate limitation.

### Engineering Results (all reference/component-boundary — label them as such)
- **IMU reference power:** ~0.018 mW (band 0.018–0.378 mW), BMI270 accel-only, gyro OFF, documented
  25 Hz point for the 32 Hz scientific requirement.
- **Wrist sensing-electronics lower bound:** LED-excluded lower bound (~0.048–0.413 mW across
  wrist-light/cabin cases); excludes LED, MCU, radio, regulator, battery. Not wrist-module power.
- **ECG AFE boundary:** 0.67 mW (2 ch × 335 µW/ch, ADS1292R, 250 s/s). AFE only, not chest-module power.
- **Other component references:** TMP117 0.01155 mW @1 Hz; OPT3001 0.00594 mW continuous (wrist) / 0
  (cabin, i.e. not body-worn); MAX86141 AFE floor ≤0.018 mW (LEDs excluded, dominant term OPEN).
- **EOG shared-head contact increment:** +2 sensing electrodes (interpretation-independent);
  incremental head-AFE power and mass `NOT_READY`.
- **Raw data-rate lower bound:** partial system raw total ~48.068 kbps (`channels × Hz × bits`;
  scientific-use-case head). Excludes light + thoracic/leg BioZ, protocol overhead, compression.
  **Not** radio bandwidth (`RADIO_DATA_RATE` NOT_READY).

## Suggested paper phrasing for the limitation
> "We quantify sensing-component and analog-front-end power boundaries and a partial raw data-rate
> budget, but do not report a system-average power, a system mass, a complete bill of materials, a
> final wearable architecture, or a formal Pareto frontier: these require LED/optical timing,
> EEG/BioZ operating points, MCU/radio/regulator behaviour, deployable duty schedules, and a
> mechanical reference design that are outside the current evidence. Engineering burden
> quantification therefore remains partial."

## What must NOT appear in the paper
- Any total/system power number, or treating a component/AFE figure as system power.
- Any system mass number, or treating package dimensions as wearable mass.
- A final BOM, a selected final architecture, or a computed Pareto frontier.
- Cross-target ranking (HR-MAE vs sleep macro-F1) or an "optimal sensor set".
- Zeroing EOG or second-PPG burden because of favourable/negative science.

## Traceability
Every figure above is traceable via `results/claim_traceability.json` (claims `day11-*`) →
`GET /research/engineering-readiness` → Research Mode "Engineering readiness (Day 11)" panel.
Source artifacts: `results/reference_power_budget_day11_part2.json`,
`results/reference_data_rate_budget_day11.json`, `results/reference_mass_readiness_day11_part2.json`,
`results/reference_bom_readiness_day11_part2.json`, `results/day11_part3_engineering_inputs.json`.
