# Hardware Topology Methodology — Day 6

## Scope and honesty boundary

This document freezes an engineering **reference topology**, not a final product architecture or bill of materials. Representative parts make interfaces and component-level operating points concrete; they do not imply procurement, medical suitability, target validation, comfort, complete wearable power, or finished mass.

Every numeric quantity keeps its unit, basis, evidence level, operating condition, and provenance. `unknown` is null, never zero. A numeric zero is permitted only for a verified structural absence, such as no new contact region for an IMU placed inside the existing wrist enclosure.

## Frozen physical topology

| Module | Location | Components | Shared resources counted once |
|---|---|---|---|
| Wrist | wrist | PPG, IMU, skin temperature, ambient light | enclosure, strap, battery, host MCU, radio, clock |
| Chest | thorax | ECG, thoracic BioZ/ICG | enclosure, battery, host MCU, radio, clock |
| Head | forehead/head | intermittent frontal EEG | head attachment, battery, host MCU, radio |
| Leg | lower leg | experimental segmental BioZ | attachment, battery, host MCU, radio |
| Optical evaluation branch | finger/proximal phalanx | second physical PPG site | electronics boundary remains open |

Co-location does not prove electrode sharing. The chest ECG and thoracic BioZ montage, the second PPG site's tether/module allocation, every final MCU/radio/battery/regulator identity, and attachment details remain open.

## Representative identities

The wrist IMU is represented by Bosch BMI270; the skin-temperature sensor by TI TMP117; the light sensor by the TI OPT3001-Q1 class; chest ECG by TI ADS1292R; frontal EEG by the TI ADS1299-4 class; both BioZ branches by the Analog Devices AD5940 class; and optical readout by the Analog Devices MAX86141 class. Candidate selection is based on modality, interface, channel/rate capability, and availability of primary manufacturer specifications—not on the desired scientific outcome.

MAX86141 is an AFE class, not a complete PPG module. AD5940's low-power potentiostat current is deliberately not treated as active BioZ measurement current. BMI270 has not been proven equivalent to the Empatica E4 accelerometer used in the frozen PPG-DaLiA experiment.

## Power and energy boundaries

Power is characterized only at one of three explicit incremental boundaries: sensor IC, AFE, or representative component class. Shared MCU, memory, radio, regulator loss, battery, enclosure, attachment, emitters, electrodes, and other listed subsystems are excluded. Component values must never be summed into “total wearable power” while those terms and operating schedules remain unresolved.

Derived equations are:

- component power in mW = voltage in V × current in µA / 1000;
- average component power = sum of state power × state fraction, but only when the state schedule is explicit;
- daily component energy in mWh/day = average component power in mW × 24 h;
- raw payload rate in bit/s = channels × samples/s × bits/sample, excluding protocol overhead.

Day 6 can calculate average power and daily energy only for TMP117 at the explicit 1 Hz manufacturer-average-current condition, OPT3001-Q1 in the explicit continuous reference mode, and two ADS1292R AFE channels at the cited per-channel power point. These values remain component/AFE-only. The PPG, 32 Hz-compatible IMU mode, BioZ, EEG, and second-site optical deployment schedules are insufficient for defensible averages.

## Mass and physical burden

Component package mass, incremental assembled PCB/module mass, and finished wearable mass are three separate quantities. None is defensibly available from the reviewed sources, so all remain null. Package dimensions are not converted into mass.

Physical burden is reported as body region, new sensing site, optical interface, electrodes, strap/head hardware, cable status, and module-boundary status. The co-located wrist IMU adds no physical sensing site or contact region. The second PPG branch adds one physical optical sensing site; whether it adds a complete module or distinct contact-region allocation remains open. Unknown electrode counts remain null.

## Compute and data

Model weights use serialized tensor element counts × four bytes for the frozen float32 checkpoints. Input buffer memory uses input tensor values × four bytes and excludes activation/workspace memory. Raw bit rate excludes packet framing, timestamps, retransmission, encryption, storage formatting, and radio overhead. Desktop benchmark timing is not embedded inference latency; embedded latency remains null until measured on a selected target MCU/runtime.

## Scientific target mapping

The matrix distinguishes `VALIDATED_POSITIVE`, `VALIDATED_NEGATIVE`, `PARTIAL_EVIDENCE`, `CANDIDATE`, and `UNVALIDATED`. Only wrist IMU→heart rate and second PPG site→heart rate have frozen marginal experiments. Candidate mappings for HRV, respiration, BP/PAT, workload, fatigue, sleep/circadian, and fluid status are engineering hypotheses, not project validation.

Raw error magnitudes from PPG-DaLiA and the pulse-transit-time dataset are not cross-dataset ranking coordinates.

## Primary sources and retrieval

All external sources were retrieved 2026-09-05. Exact revision, operating condition, location, and extracted parameters live in `results/operational_cost_catalog.json`.

- Bosch Sensortec, BMI270 product page and data sheet.
- Analog Devices, MAX86141 product page/data sheet.
- Texas Instruments, TMP117 Rev. D data sheet.
- Texas Instruments, OPT3001-Q1 Rev. C product page/data sheet.
- Texas Instruments, ADS1292R Rev. C product page/data sheet.
- Texas Instruments, ADS1299-4 Rev. C product page/data sheet.
- Analog Devices, AD5940/AD5941 Rev. G product page/data sheet.

## Reproduction

`PYTHONPATH=backend backend/.venv/bin/python -m app.research.day6` deterministically regenerates the topology, system architecture, revised operational catalog, and readiness audit. `python -m app.research.decision_inputs` regenerates the joined decision inputs afterward.
