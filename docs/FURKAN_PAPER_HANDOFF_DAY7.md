# Furkan paper-writing handoff — Day 7 (post-ML integration)

Purpose: tell the paper author exactly which methods/results are **frozen and
writable now**, which **must be described carefully** (with mandatory caveats),
and which are **proposed/future-only**. Do not write anything from the third
list as a completed method or result. This is a handoff, not the paper. No
marketing/narrative phrasing is provided — that judgment belongs to the paper's
authors.

Canonical framing (use this, not the old story): Biological Minimalism is an
**evidence-driven methodology for the target-specific marginal value of sensing
components**, combined with operational burden, provenance, robustness, and
architecture constraints. Evidence now spans three targets/datasets (PPG-DaLiA
IMU→HR, PTT second-site→HR, Sleep-EDF EOG→sleep-stage). The final architecture
decision status is **`NOT_READY`** — a valid scientific result. There is **no**
"selected optimal four sensors" claim and **no** cross-dataset ranking.

---

## A. Frozen / writable now (methodology + results)

- **Marginal-value experimental design** — `docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md`
  (methodology v1.2.0, now covering regression AND classification targets).
- **PPG-DaLiA IMU HR result** — `results/ppg_dalia_imu_multiseed_replication.json`.
  Original protocol: synchronized wrist IMU reduced held-out HR MAE
  **9.086 → 7.208 bpm, replicated 5/5 seeds**. Write the **multi-seed** figure,
  not the single-seed 23%. See the mandatory capacity caveat in section B.
- **PPG-DaLiA capacity-matched control (A_cap)** — `results/ppg_dalia_capacity_control.json`,
  `docs/PPG_DALIA_CAPACITY_CONTROL_RESULTS.md`. A_cap (28,865 params, two
  independent PPG encoders + fusion) isolates architecture/capacity from IMU
  information. Writable: capacity-controlled IMU-information benefit
  **A_cap→B ≈ 0.605 bpm, 5/5 seeds**; the already-capacity-matched **C→B
  synchronization increment ≈ 0.776 bpm, 5/5 seeds** is the cleanest comparison.
- **PPG-DaLiA shuffled-IMU negative control (Model C)** — established: synchronized
  IMU beats shuffled IMU 5/5 seeds. A_cap→C is **not** a clean context claim
  (only 1/5 seeds favor C); do not describe A→C as "pure context information."
- **PTT second-PPG-site HR result** — `results/ptt_ppg_site_ablation.json`,
  `results/ptt_sensitivity_analysis.json`. Single-site baseline beat the two-site
  candidate in aggregate (17.540 vs 19.003 bpm MAE) across 5 optimization seeds
  — **bounded, heterogeneous negative evidence**. See the mandatory s2 caveat in B.
- **Sleep-EDF EEG-vs-EEG+EOG sleep-stage result** — `results/sleep_edf_eeg_eog_ablation.json`,
  `docs/SLEEP_EDF_EEG_EOG_RESULTS.md`. Adding horizontal EOG to EEG Fpz-Cz
  improved macro-F1 **0.747 → 0.769 (4/5 seeds favor EOG)**, balanced accuracy
  5/5, largest class gains in **N1 and REM**. A **new, non-HR classification**
  target demonstrating the methodology generalizes beyond regression. See the
  mandatory preliminary/limitations caveat in B.
- **Statistical-reporting convention** — `results/sd_convention_audit.json`,
  `docs/STATISTICAL_REPORTING_AUDIT.md`. New multi-seed reporting uses **sample
  SD (ddof=1)**; historical frozen artifacts keep ddof=0 unchanged. Any SD in a
  table must state its convention (difference ≈1.12× for n=5; no directional
  conclusion changes).
- **Robustness characterization** — `results/ppg_dalia_fault_robustness.json`,
  `docs/PHASE5_ROBUSTNESS_AUDIT_ADDENDUM.md`. Write S14-only scope, additive-IMU-noise
  calibration caveat, packet-loss = fail-closed **availability** (not accuracy),
  **no predictive uncertainty**. It is a bounded characterization, not generic
  "robustness," and a **separate axis** from marginal value.
- **Operational-burden method** — `docs/OPERATIONAL_COST_METHODOLOGY.md`,
  `docs/HARDWARE_TOPOLOGY_METHODOLOGY.md`. Component classes (not final BOM);
  module/body-region/contact representation; unknowns preserved as `null` (never 0).
- **Architecture decision gate** — `docs/FINAL_ARCHITECTURE_DECISION_RULE.md`. A
  **gate** (admissibility check), not a final selection rule; status `NOT_READY`.
- **Interaction limitation** — `docs/SENSOR_INTERACTION_LIMITATION.md`. One-at-a-time
  marginal evidence does not establish a globally minimal sensor subset.
- **Reproducibility approach** — `docs/REPRODUCIBILITY.md`,
  `results/checkpoint_inventory.json`, `results/checkpoint_manifest_consolidated.json`.
- **Target-specific evidence matrix** — `results/target_evidence_matrix.json`
  (HR/PPG-DaLiA, HR/PTT, sleep-stage/Sleep-EDF). Cross-dataset raw-metric
  comparison is **prohibited**; the three entries are **not ranked**.

## B. Must be described carefully (mandatory caveats)

- **PPG-DaLiA original A→B effect is capacity-confounded**: any prior text citing
  "~23% HR-MAE improvement from adding IMU," "~20.6%," or "9.09 → 7.03 bpm" as
  *pure IMU sensor value* must be revised. **Approximately 68% of the original
  A→B gap (~1.88 bpm) was recovered by a capacity-/architecture-matched PPG-only
  control (A_cap)** — i.e. a large majority of the apparent benefit is
  attributable to architecture/capacity rather than uniquely to IMU information.
  The POSITIVE direction survives at **reduced magnitude (~0.6 bpm, 5/5 seeds)**.
  Do **not** phrase the 68% as "pure model-capacity causality" (A_cap changes
  architecture/representation as well as raw parameter count).
- **PTT aggregate is s2-sensitive and heterogeneous**: the aggregate negative
  result is driven almost entirely by held-out subject **s2**; descriptively
  excluding s2 flips the aggregate direction (Δ ≈ 1.95 bpm). Per-subject, **2 of
  4 favor the candidate**. The 5/5 seed agreement is optimization replication,
  **not** five independent population replications. Do **not** write "second PPG
  site is useless / redundant / should be removed."
- **Sleep-EDF is a modest, preliminary positive**: only **3 held-out test
  subjects**, no per-subject breakdown yet, no shuffled-EOG negative control,
  single dataset, terrestrial population. Write as *preliminary marginal-value
  evidence*. Do **not** claim EOG is necessary/universal, that it validates
  astronaut/spaceflight sleep monitoring, or rank it against the HR experiments
  (macro-F1 must never be placed beside MAE as if comparable).

## C. Proposed / future-only (never as completed methods/results)

- Trained personalized **Biological Digital Twin** (architecture only, untrained;
  footprint: `results/digital_twin_architecture_footprint.json` — 153,801 params,
  ~601 KiB float32 — **architecture footprint, not deployment feasibility**; the
  Sleep-EDF result does **not** validate the Digital Twin).
- Calibrated predictive **uncertainty**.
- **Microgravity / astronaut** sensitivity and any spaceflight validation (motivation only).
- Physical **wearable** build/validation; total system **power/mass/BOM** (unknown =
  null; do not sum).
- A final **Pareto** architecture / minimal set (status `NOT_READY`).
- **Interaction factorial** experiments (one-at-a-time evidence does not prove a global minimum).
- The **Information Density Index (IDI)** — proposed and **superseded**; if mentioned,
  frame as a rejected universal-scalar concept, not a used metric.
