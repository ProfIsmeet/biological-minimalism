# Furkan Paper-Support Package (Day 8)

Extends `docs/FURKAN_PAPER_HANDOFF_DAY7.md`. This package makes the paper writable **now** for
everything independent of Ismet's pending sleep evidence. Every number must be pulled from the
cited committed artifact — do not retype from memory. Pending items are marked and must not be
given numbers until integration.

---

## A. Frozen methodology map (sections writable now)

| Paper section | Writable now? | Source artifact(s) |
|---|---|---|
| Research question / marginal-value framework | YES | `docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md` |
| PPG-DaLiA protocol | YES | `results/ppg_dalia_imu_ablation.json`, `docs/MODEL_CONTRACT_PPG_DALIA_HR.md` |
| Capacity control | YES | `results/ppg_dalia_capacity_control.json`, `docs/PPG_DALIA_CAPACITY_CONTROL_RESULTS.md` |
| Shuffled-IMU control | YES | `results/ppg_dalia_imu_multiseed_replication.json` |
| PTT experiment | YES | `results/ptt_ppg_site_ablation.json`, `docs/MODEL_CONTRACT_PTT_HR.md` |
| PTT sensitivity | YES | `results/ptt_sensitivity_analysis.json` |
| Sleep primary protocol | YES | `results/sleep_edf_eeg_eog_ablation.json`, `docs/SLEEP_EDF_EEG_EOG_RESULTS.md` |
| Shuffled-EOG control | **PENDING** | on `origin/day8-sleep-strengthening-ml` — do not write numbers yet |
| Operational burden | YES | `results/pareto_decision_inputs.json`, `docs/OPERATIONAL_COST_METHODOLOGY.md` |
| Architecture gate | YES | `docs/FINAL_ARCHITECTURE_DECISION_RULE.md`, `results/architecture_decision_matrix.json` |
| Interaction limitation | YES | `docs/SENSOR_INTERACTION_LIMITATION.md` |
| Reproducibility | YES | `docs/REPRODUCIBILITY.md`, `*_reproducibility.json` |

---

## B. Results-table blueprint

**Table 1 — Target-specific marginal value (do NOT rank rows across datasets).**

| Exp | Target | Dataset | Baseline → Candidate | Metric | Result | Replication | Control |
|---|---|---|---|---|---|---|---|
| 1 | HR | PPG-DaLiA | PPG → PPG+IMU | MAE (bpm) ↓ | positive; capacity-matched C→B ~0.776, A_cap→B ~0.605 | 5/5 seeds | shuffled-IMU present |
| 2 | HR | PTT-PPG | 1 site → 2 sites | MAE (bpm) ↓ | aggregate worse (Δ≈+1.46), 2/4 subjects better | 5/5 seeds (opt.) | none (n/a) |
| 3 | Sleep stage | Sleep-EDF | EEG → EEG+EOG | macro-F1 ↑ | 0.7473→0.7693 (Δ≈0.022) | 4/5 seeds (bal-acc 5/5) | shuffled-EOG **PENDING** |

Pull exact cells from: Exp1 raw means `results/ppg_dalia_imu_ablation.json.overall_metrics` and
capacity deltas `results/ppg_dalia_capacity_control.json.primary_comparisons`; Exp2 means
`results/ptt_ppg_site_ablation.json.aggregate`; Exp3 means
`results/sleep_edf_eeg_eog_ablation.json.aggregate`.

**Caption must state:** columns are per-target; magnitudes across rows are NOT comparable.

---

## C. Limitations matrix (one row per experiment)

| Exp | Dataset | Population | n held-out | Model limitation | Control limitation | Architecture-implication limit |
|---|---|---|---|---|---|---|
| 1 | PPG-DaLiA | terrestrial free-living | 3 | raw A→B capacity-confounded; no uncertainty head | shuffled-IMU also helps (partial synchronization attribution) | CONDITIONAL only; no interaction evidence |
| 2 | PTT-PPG | terrestrial controlled | 4 | 6 vs 3 channels not fully separable from site | no negative control | DEPRIORITIZE only; not global removal; s2-sensitive |
| 3 | Sleep-EDF | terrestrial | 3 | effect ≈ seed SD (preliminary) | shuffled control + per-subject PENDING; secondary holdout PENDING | FUTURE_EVIDENCE_REQUIRED |

---

## D. Claim bank

**Safe (write freely):**
- Target- and dataset-specific marginal value was measured under frozen, subject-disjoint splits.
- IMU gives a small but replicated capacity-controlled HR benefit at near-zero incremental human burden in the colocated wrist reference.
- A second PPG site did not consistently help HR; the aggregate is heterogeneous and s2-sensitive.
- EOG gives a modest, preliminary sleep-staging benefit; balanced accuracy improved 5/5 seeds.
- The final architecture is NOT_READY, and this is reported honestly.

**Unsafe (never write):** "23% IMU benefit", "20.6% pure IMU value", "1.88 bpm current clean IMU",
"59/41 causal decomposition", "68% pure parameter causality", "four validated sensors", "optimal
architecture", "trained Digital Twin", "astronaut/microgravity validated", "robust".

**Future-only (write only after integration):** shuffled-EOG B>C numbers, SC4011 per-subject
dominance numbers, secondary-holdout outcome.

---

## E. Figure plan (artifact-backed only)

1. **Methodology pipeline** — question → controlled marginal → burden → gate → NOT_READY (schematic; no data).
2. **IMU capacity control** — A, A_cap, B, C bars; source `ppg_dalia_capacity_control.json` + `..._multiseed_replication.json`.
3. **PTT subject heterogeneity** — per-subject Δ (s2,s9,s14,s20); source `ptt_ppg_site_ablation.json.per_subject` + `ptt_sensitivity_analysis.json`.
4. **Sleep A/B (+C pending)** — macro-F1 per seed; source `sleep_edf_eeg_eog_ablation.json`; C shown as a PENDING placeholder, not a bar.
5. **Architecture/burden matrix** — source `architecture_decision_matrix.json` + `pareto_decision_inputs.json`.
6. **NOT_READY decision gate** — source `pareto_readiness_blockers.json`.

Any synthetic demo figure (Digital Twin traces) MUST be labeled "synthetic; untrained" if referenced.
