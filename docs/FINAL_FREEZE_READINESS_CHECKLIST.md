# Final-Freeze Readiness Checklist (Day 8/9 — post canonical integration)

Prepares the repository for eventual final scientific freeze. **Do not freeze yet.** As of the
Day-9 canonical integration, the sleep shuffled control, per-subject decomposition, and prospective
secondary holdout are **integrated and re-verified**, and external checkpoint archival is
**verified durable**; the remaining open items are architecture/BOM/power-mass and final
rehearsal/freeze, not science integration. Status: ☐ open · ◐ partial · ☑ done.

## Git
- ☑ Canonical branch `day8-9-systems-readiness` carries the merged Day-9 science (merge `731c83d`).
- ☑ Working tree clean at each commit; no conflict markers.
- ☑ No raw datasets committed (archive verification lists 0 raw dataset files; `.gitignore` covers payloads).
- ☐ Tag strategy: `day9-canonical-integration` is acceptable as a **non-final** checkpoint tag; reserve `vX.Y-final-freeze` for after architecture/BOM/rehearsal close. Do NOT tag final now.

## Scientific artifacts
- ☑ Result JSONs present for all three experiments + capacity/sensitivity/robustness + sleep control/per-subject/secondary.
- ☑ Methodology contract (`results/sensor_marginal_value_contract.json`) regenerated (v1.5.0) from merged builder; deterministic second-run zero-diff.
- ☑ Provenance SHA chain re-verified after regeneration (contract → decision-inputs source SHA updated `4941eed3`→`c0d25942`; day6 operational artifacts zero-diff).
- ☑ **NEWLY CLOSED — Sleep negative control** integrated (`results/sleep_edf_eeg_eog_control_analysis.json`; C→B 5/5).
- ☑ **NEWLY CLOSED — Sleep per-subject analysis** integrated (`results/sleep_edf_per_subject_analysis.json`; SC4011-dominated primary).
- ☑ **NEWLY CLOSED — Prospective secondary holdout** integrated & reproducible (`results/sleep_edf_secondary_holdout_evaluation.json`; A→B 5/5, n=8, zero retraining).
- ☑ Dataset manifests present (`datasets/DATASET_MATRIX.md`); secondary cohort codes recorded.

## Checkpoint archival
- ☑ **NEWLY CLOSED — external durability verified.** GitHub Release `day8-checkpoint-archive-v1`, asset `biological_minimalism_checkpoints_day8.tar.gz`, SHA256 `5e0661a6…`, 50 checkpoints, 0 raw datasets.
- ☑ Independently re-downloaded and re-hashed on the integration Mac — byte-for-byte match.
- ☑ Archival schema flipped pending → verified (`results/checkpoint_archival_schema.json`).

## Dashboard / Research Mode
- ☑ No hardcoded science values on live surfaces; **claim consistency checker passes (0 issues)** with new stale-pending detectors.
- ☑ **NEWLY CLOSED — Research Mode Case 3** now serves primary (n=3) + secondary (n=8) + shuffled control + class-level via the API (no pooling).
- ◐ Live browser walkthrough performed during integration; final jury-rehearsal walkthrough still pending.

## Paper
- ☑ All current numbers traceable to an artifact (`results/claim_traceability.json`; 0 pending claims).
- ☑ Canonical paper-support state consolidated (Day-7/8/9 handoffs; see `docs/FURKAN_PAPER_HANDOFF_DAY9.md` + this checklist).
- ☑ All claims bounded (safe/unsafe/future claim bank); N3 regression disclosed.
- ☐ **OPEN — final paper freeze** (text still being written by Furkan).

## Reproducibility / environment
- ☑ Checkpoint SHAs recorded; external durability verified.
- ☑ Training environment captured (`results/environment_manifest.json`, `environment_freeze_full_pip.txt`: Python 3.13.0 + torch 2.6.0 CPU).
- ◐ Integration/backend env is Python 3.14 + torch 2.14 (distinct from frozen training env — documented, not conflated). Frontend env separate.
- ☑ Split files + per-experiment code version recorded in provenance.

## Day 10 — Newly closed (scientific reproducibility & first interaction)
- ☑ **Frozen environment verified** — field-by-field EXACT_FROZEN_ENVIRONMENT (`results/day10_frozen_environment_verification.json`).
- ☑ **Dataset fingerprint coverage** — 266/266 raw records present + fingerprinted (16/198/36/16), 0 committed to git (`results/dataset_fingerprint_manifest_day10.json`).
- ☑ **Checkpoint durability** — re-confirmed externally durable (GitHub Release, 50 checkpoints).
- ☑ **Canonical result reproduction** — every checkpoint-based result re-evaluated from frozen weights with zero numerical difference; `SCIENTIFIC_REPRODUCTION_PASS` (`results/day10_scientific_reproduction.json`).
- ☑ **Robustness reproduction** — full 114/114 conditions within 1e-4 bpm (max 7.6e-6).
- ☑ **N3 diagnostic verification** — recomputed and matches canonical Day-9 figures (precision 0.499→0.430, recall 0.853→0.884, +605 N2→N3 FP).
- ☑ **First interaction experiment** — predeclared EEG×EOG×Resp factorial run; approximately additive/unresolved (+0.0031 ± 0.0434). One controlled pair only; NOT global interaction knowledge, NOT a synergy claim.
- ◐ **EOG operational burden** — materially improved, not fully closed (`results/eog_operational_burden_day10.json`): 2 incremental sensing electrodes (interpretation-independent); power/mass still NOT_READY.
- ◐ **Reference BOM readiness** — datasheet-backed reference table (`results/reference_bom_readiness_day10.json`); still SYSTEM_AVERAGE_POWER_NOT_READY / SYSTEM_MASS_NOT_READY / FINAL_BOM_NOT_SELECTED.

**Scientific freeze status:** `READY_WITH_KNOWN_LIMITATIONS`.
**Project freeze status:** `NOT_READY_FOR_FINAL_PROJECT_FREEZE` (engineering/paper/presentation/rehearsal unfinished). These two are tracked separately and must not be conflated — scientific reproducibility being ready does NOT mean the project is ready to freeze.

## Still OPEN before final freeze (do NOT close yet)
1. ☐ **Final architecture** — UNRESOLVED (no RETAIN outcome; interaction evidence now **partial** — one controlled pair — not global).
2. ☐ **Formal Pareto** — NOT_READY (power/energy, mass, electrode montage, full BOM/module allocation absent; interaction coverage incomplete).
3. ☐ **Missing power/mass** for every component; **full BOM** and module/attachment identities.
4. ☐ **Final paper freeze** and **final dashboard freeze**.
5. ☐ **Final jury rehearsal** (full live walkthrough + Q&A dry run).
6. ☐ Capture final environment pins (node + python lockfiles) at freeze time; then tag `vX.Y-final-freeze`.

## Day 11 — Engineering evidence integrated (Parts 1–4)
Part-1 audited engineering evidence and froze calc inputs; Part-2 produced reference power/data-rate/mass/BOM readiness; Part-3+4 integrated that evidence into the decision gate, Pareto readiness, Research Mode, traceability, and this checklist.
- ☑ **Reference power** — component/AFE boundaries quantified (IMU ~0.018 mW band 0.018–0.378; ECG AFE 0.67 mW; TMP117 0.01155 mW; OPT3001 0.00594 mW; MAX86141 AFE floor ≤0.018 mW LED-excluded; wrist sensing-electronics LED-excluded lower bound). `results/reference_power_budget_day11_part2.json`.
- ☑ **Raw data-rate** — partial lower bound ~48.068 kbps (not radio bandwidth; RADIO_DATA_RATE NOT_READY). `results/reference_data_rate_budget_day11.json`.
- ◐ **Module BOM** — PARTIAL: MCU/radio/regulator/battery MISSING → REFERENCE_SELECTED (class, final=false); electrodes/PCB/enclosure/attachment MISSING. `results/reference_bom_readiness_day11_part2.json`.
- ◐ **Mass** — Tier-0..4 framework only; all modules Tier 0; no mass number. `results/reference_mass_readiness_day11_part2.json`.
- ☑ **Decision gate re-run** — IMU + EOG remain `CONDITIONAL_FOR_TARGET`, second PPG `DEPRIORITIZE_FOR_TARGET`, final architecture `UNRESOLVED`; engineering evidence did NOT upgrade any decision (`results/architecture_decision_matrix.json` → `day11_engineering_integration`).
- ☑ **Pareto re-run** — `FORMAL_PARETO_NOT_READY`; no blocker downgraded (`results/pareto_readiness_blockers.json` → `day11_part2_updates`).
- ☑ **Research Mode** — new `/research/engineering-readiness` endpoint + Engineering readiness panel; unknowns render as “Not ready”, never 0.
- ☑ **Claim traceability + checker** — 9 engineering claims added; checker extended for bald system-power/mass/BOM/zero-burden/Pareto-optimal claims.

**Engineering freeze status (open blockers):**
- ☐ **System average power** — `SYSTEM_AVERAGE_POWER_NOT_READY` (LED timing, EEG/BioZ operating points, MCU/radio, regulator efficiency, deployable duty, battery).
- ☐ **System mass** — `SYSTEM_MASS_NOT_READY` (no mechanical reference design).
- ☐ **Full BOM** — PARTIAL (no final component/enclosure/electrode selection).
- ☐ **Final mechanical architecture** — unresolved.
- ☐ **Formal Pareto** — NOT_READY (benefit axes not comparable; burden incomplete).

**Scientific freeze status:** `READY_WITH_KNOWN_LIMITATIONS` (unchanged by Day-11 engineering work).
**Engineering freeze status:** `NOT_READY` (system power/mass/full BOM/mechanical architecture/formal Pareto open — do not conflate with scientific validity).
**Project freeze status:** `NOT_READY_FOR_FINAL_PROJECT_FREEZE`.
Power/mass do NOT need to be solved for Day-11 completion; their unresolved state intentionally carries into Day-12.
