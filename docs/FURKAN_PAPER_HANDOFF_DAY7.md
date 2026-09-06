# Furkan paper-writing handoff — Day 7

Purpose: tell the paper author exactly which methods/results are **frozen and
writable now**, which are **awaiting Ismet's Day-7 ML evidence**, and which are
**proposed/future-only**. Do not write anything from the second or third list as a
completed method or result. This is a handoff, not the paper.

Canonical framing (use this, not the old story): Biological Minimalism is an
**evidence-driven methodology for the target-specific marginal value of sensing
components**, combined with operational burden, provenance, robustness, and
architecture constraints. The final architecture decision status is **`NOT_READY`**
— a valid scientific result. There is **no** "selected optimal four sensors" claim.

---

## A. Frozen / writable now (methodology + results)

- **Marginal-value experimental design** — `docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md`.
- **PPG-DaLiA IMU HR result** — `results/ppg_dalia_imu_multiseed_replication.json`,
  `docs/MODEL_CONTRACT_PPG_DALIA_HR.md`. Writable as: synchronized wrist IMU reduced
  held-out HR MAE **9.086 → 7.208 bpm (~20.6% relative), replicated 5/5 seeds**.
  - Write the **multi-seed 20.6%**, not the single-seed 23%.
  - State that **A→B and A→C are capacity-confounded** (~8k vs ~29k params) and that
    the capacity-matched **C→B increment (0.776 bpm)** is the cleanest comparison. Do
    **not** call the full A→B benefit "pure IMU sensor value."
- **PTT second-PPG-site HR result** — `results/ptt_ppg_site_ablation.json`,
  `docs/MODEL_CONTRACT_PTT_HR.md`, `datasets/ptt-ppg/README.md`. Writable as:
  single-site baseline beat the two-site candidate in aggregate across 5 optimization
  seeds — **bounded, heterogeneous negative evidence**. Note **s2 dominates** and
  removing s2 descriptively reverses the aggregate; 5 seeds are optimization
  replications, not independent populations. Do **not** write "second site is useless"
  or "should be removed."
- **Robustness characterization** — `results/ppg_dalia_fault_robustness.json`,
  `docs/PHASE5_ROBUSTNESS_AUDIT_ADDENDUM.md`. Write S14-only scope, additive-IMU-noise
  calibration caveat, packet-loss = fail-closed **availability** (not accuracy),
  **no predictive uncertainty**. It is a bounded characterization, not generic
  "robustness."
- **Operational-burden method** — `docs/OPERATIONAL_COST_METHODOLOGY.md`,
  `docs/HARDWARE_TOPOLOGY_METHODOLOGY.md`. Reference component classes (not final BOM);
  module/body-region/contact representation; unknowns preserved as `null` (never 0).
- **Architecture decision gate** — `docs/FINAL_ARCHITECTURE_DECISION_RULE.md`. It is a
  **gate** (admissibility check), not a final selection rule; status `NOT_READY`.
- **Reproducibility approach** — `docs/REPRODUCIBILITY.md`,
  `results/checkpoint_inventory.json` (1 present + verified, 25 missing).
- **Target-specific evidence matrix** — `results/target_evidence_matrix.json`
  (HR/PPG-DaLiA + HR/PTT only). Cross-dataset raw-metric comparison is **prohibited**.

## B. Awaiting Ismet's Day-7 evidence (do NOT write as done)

- **Capacity-matched PPG-only control (A_cap)** — needed before the IMU benefit can be
  attributed to the sensor rather than model capacity. Until it exists, keep the
  capacity-confound caveat.
- **PTT leave-one-subject-out sensitivity** — needed to characterize the s2-dominated
  heterogeneity. Use only committed PTT numbers until then.
- **Sleep-EDF EEG vs EEG+EOG** — a *classification* target (schema is ready; **no**
  numbers exist). Do not invent accuracy/κ figures or that the candidate wins.

## C. Proposed / future-only (never as completed methods/results)

- Trained personalized **Biological Digital Twin** (architecture only, untrained;
  footprint: `results/digital_twin_architecture_footprint.json` — 153,801 params,
  ~601 KiB float32 — **architecture footprint, not deployment feasibility**).
- Calibrated predictive **uncertainty**.
- **Microgravity / astronaut** sensitivity and any spaceflight validation (motivation
  only).
- Physical **wearable** build/validation; total system **power/mass/BOM** (unknown =
  null; do not sum).
- A final **Pareto** architecture / minimal set (status `NOT_READY`).
- **Interaction effects** (one-at-a-time evidence does not prove a global minimum).
- The **Information Density Index (IDI)** — proposed and **superseded**; if mentioned,
  frame as a rejected universal-scalar concept, not a used metric.
