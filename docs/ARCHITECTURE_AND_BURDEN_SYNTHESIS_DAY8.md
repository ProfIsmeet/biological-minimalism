# Architecture, Operational Burden & Decision-Gate Synthesis (Day 8)

Jury-facing synthesis of the target-specific architecture matrix, the human-burden model,
the decision gate, the interaction limitation, and Pareto readiness. Every number here is
traceable to a committed artifact. Nothing here selects a final architecture.

Companion machine-readable artifacts:
- `results/architecture_decision_matrix.json` — per (target, candidate) gate decision
- `results/pareto_readiness_blockers.json` — structured NOT_READY blocker breakdown
- `results/system_architecture_topology.json` — modules / resources / signals
- `results/pareto_decision_inputs.json` — scientific value ⋈ operational burden (HR components)

---

## 1. Target-specific architecture matrix

| Target / dataset | Candidate | Scientific status | Evidence strength | Heterogeneity | Burden completeness | Interaction | **Gate decision** |
|---|---|---|---|---|---|---|---|
| HR / PPG-DaLiA | synchronized wrist IMU | positive, capacity-controlled (A_cap→B ~0.605, C→B ~0.776 bpm, 5/5) | strongly replicated but modest after capacity control | consistent direction, non-monotonic magnitude | PARTIAL (mass/power/latency missing) | unavailable | **CONDITIONAL_FOR_TARGET** |
| HR / PTT-PPG | second physical PPG site | aggregate negative, heterogeneous, s2-sensitive | replicated-but-variable | 2/4 subjects favor candidate | PARTIAL/MISSING (module boundary, mass) | unavailable | **DEPRIORITIZE_FOR_TARGET** |
| Sleep / Sleep-EDF | horizontal EOG + EEG | positive, modest (0.7473→0.7693, 4/5 seeds on this branch) | replicated-but-variable, preliminary | 3 subjects; per-subject + shuffled control PENDING | MISSING (not burden-linked) | unavailable | **FUTURE_EVIDENCE_REQUIRED** |

No pair reaches RETAIN. **Final architecture: UNRESOLVED.**

---

## 2. Human-burden model — burden lives at the body, not the part count

Master Review C established that user burden is dominated by *where and how a device touches the
body*, not by raw sensor count. The burden model is layered:

1. **Component level** — sensor / AFE / modality (e.g. accelerometer IC)
2. **Site level** — physical sensing site (e.g. distal vs proximal phalanx)
3. **Body-region level** — wrist / thorax / forehead-head / lower-leg / finger
4. **Module level** — shared wearable node (one enclosure)
5. **Contact level** — electrodes, optical contacts, strap/attachment, reference/bias contacts
6. **Shared-resource level** — battery, MCU, radio, clock, enclosure (counted **once** per module)

Burden **status** per quantity is one of: `known` · `architectural-count` · `reference` ·
`unresolved` · `unknown`. Unresolved/unknown values are never imputed as zero.

### 2.1 The "zero new module" case (a core Biological Minimalism insight)

A wrist IMU added to an already-worn wrist PPG module adds, in the colocated reference context
(`results/pareto_decision_inputs.json` → `wrist_imu`):

- **0** new body regions
- **0** new modules / enclosures
- **0** new straps / attachments
- **0** new skin electrodes or optical contacts

…while it *does* add compute (+21,024 model params), data throughput (+96 scalar samples/s),
and IC power (BMI270-class 0.018–0.378 mW active, average power still `unknown`). This is why
**"one fewer sensor" ≠ "meaningfully lower human burden."** The same logic bounds the second
PPG site *upward*: it adds ≥1 physical + optical sensing site, and its module boundary is
unresolved, so its human burden cannot be assumed zero.

### 2.2 EEG / BioZ physical realism (do not draw "one simple sensor")

Frontal EEG is **not** one clean contact. Preserved as explicit but unresolved requirements:
sensing electrode + reference electrode + bias/DRL (or equivalent) + skin-interface burden +
attachment/stability + motion/EMG susceptibility. Montage is **not** frozen. Leg BioZ similarly
carries geometry dependence, a multi-electrode requirement, an unresolved montage, and skin-
contact burden. No exact electrode counts are fabricated.

### 2.3 Light-sensor location

`LOCATION_UNRESOLVED` (wrist module vs cabin/ambient). Cabin-mounted light ⇒ **zero body-worn
burden**; wrist-mounted light ⇒ body-worn burden applies. It is **not counted** as body burden
until placement is frozen.

### 2.4 Duty cycle

The model separates: **sensor specification** vs **reference acquisition schedule** vs **actual
duty cycle** vs **average-power duty cycle**. Continuous acquisition in the experiments is a
`reference_schedule` / `engineering_assumption`, never a "datasheet-derived" duty cycle. Total
system power is **not** computed.

---

## 3. Decision gate — transparent, threshold-free

The gate (`docs/FINAL_ARCHITECTURE_DECISION_RULE.md`) is an **admissibility check**, not a
tie-break scorer. For each (target, candidate) it reasons through six explicit fields —
(1) scientific evidence, (2) evidence strength, (3) heterogeneity, (4) burden completeness,
(5) interaction limitation, (6) decision — and returns one of: `RETAIN_FOR_TARGET`,
`CONDITIONAL_FOR_TARGET`, `DEPRIORITIZE_FOR_TARGET`, `REMOVAL_CANDIDATE_FOR_TARGET`,
`FUTURE_EVIDENCE_REQUIRED`. No arbitrary numeric thresholds are added to force a decision.

## 4. Interaction limitation — why the global architecture stays open

`interaction_evidence_status = unavailable`. All experiments are one-component-at-a-time. A
one-at-a-time marginal does **not** establish global subset optimality, and the system must not
infer a greedy "remove all negative marginals" rule. A dedicated factorial design
(baseline / +A / +B / +A+B within one dataset/target/protocol) is future work. Therefore the
**global minimal architecture remains UNRESOLVED**, independent of the sign of any single result.

## 5. Pareto readiness — NOT_READY, explained

`pareto_status = NOT_READY`, `formal_pareto_calculated = false`. A judge should see *why* rather
than a fake frontier (`results/pareto_readiness_blockers.json`):

- Benefits are measured on **different datasets/targets** → raw metrics incomparable (MAE vs macro-F1).
- **Power** is partial (IC operating points only); **mass** is missing for every candidate.
- **Interaction** evidence is incomplete.
- **Module/BOM** boundaries (MCU, radio, battery, regulator, enclosure, attachment) unresolved.
- Sleep/EOG has **single-dataset, 3-subject, preliminary** evidence, and its shuffled control +
  per-subject breakdown are **pending integration** from Ismet's branch.

**What would unlock it:** a common comparable benefit frame per target, defensible average power +
finished mass per candidate, at least one interaction (factorial) experiment, a frozen module/BOM
boundary, and integration of the pending sleep evidence + secondary holdout.
