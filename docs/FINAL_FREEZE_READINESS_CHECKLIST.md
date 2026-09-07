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

## Still OPEN before final freeze (do NOT close yet)
1. ☐ **Final architecture** — UNRESOLVED (no RETAIN outcome; interaction evidence unavailable).
2. ☐ **Formal Pareto** — NOT_READY (power/energy, mass, electrode montage, full BOM/module allocation absent).
3. ☐ **Missing power/mass** for every component; **full BOM** and module/attachment identities.
4. ☐ **Final paper freeze** and **final dashboard freeze**.
5. ☐ **Final jury rehearsal** (full live walkthrough + Q&A dry run).
6. ☐ Capture final environment pins (node + python lockfiles) at freeze time; then tag `vX.Y-final-freeze`.
