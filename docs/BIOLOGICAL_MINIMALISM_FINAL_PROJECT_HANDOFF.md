# Biological Minimalism — Final Project Handoff (Stage 5)

This document is sufficient for a fresh expert to understand the final
project state without reading the entire repository. It is a summary; the
`results/final_*.json` artifacts it cites are the actual source of truth —
if this document and those artifacts ever disagree, the artifacts win.

## 1. Project objective

Long-duration spaceflight requires continuous physiological monitoring, but
every sensor added to a wearable costs mass, power, contact points, and crew
burden. Biological Minimalism asks, per candidate sensing modality, whether
it provides measurable incremental value after controlling for model
capacity, temporal correspondence, subject separation, heterogeneity, and
physical burden — and uses the resulting evidence, not intuition, to select
a final wearable architecture.

## 2. Final architecture

**CORE_PLUS_CONTEXT** — wrist PPG + IMU, chest ECG, frontal EEG + EOG,
`DISTRIBUTED_BODY_MODULE_TOPOLOGY` (3 modules: wrist/chest/head, EOG sharing
the head module's EEG AFE/reference infrastructure). Source of record:
`results/final_wearable_architecture.json`. Gate D (burden completeness):
`CONDITIONALLY_READY`, closed by Coordinator acceptance of bounded
engineering uncertainty. Gate E (EOG, sparse EEG): both `FREEZE_CONDITIONALLY`
with explicit, predefined revision triggers.

## 3. Strongest science

- **Wrist PPG+IMU → HR**: capacity-controlled A_cap→B +0.605 bpm on
  PPG-DaLiA (5/5 seeds), externally corroborated on GalaxyPPG's corrected
  cohort (A_cap→B +0.834 bpm, 12/18 participants favor B).
- **Frontal EEG+EOG → sleep stage**: same-dataset controlled B−A +0.028
  macro-F1 (4/5 seeds), with a shuffled-EOG control and a prospective n=8
  secondary holdout supporting the same direction (though N3 regresses while
  REM gains strongly in the secondary cohort — disclosed, not smoothed).

## 4. External replication

Three external-dataset checks exist, explicitly classed (never conflated):
GalaxyPPG (corrected cohort, `EXTERNAL_REPLICATION_SUPPORTIVE_WITH_HETEROGENEITY`),
HMC (`BOUNDED_EXTERNAL_DIAGNOSTIC`, n=7 of 151), ds003838
(`BOUNDED_EXTERNAL_DIAGNOSTIC`, n=3). An earlier GalaxyPPG analysis was
invalidated by a reference-ECG signal-quality defect in 6/24 subjects; only
the corrected 18-subject analysis is current governing evidence
(`results/galaxyppg_invalidated_evidence_registry.json`). See
`results/final_tables/table_c_external_replication.json`.

## 5. Negative / mixed results (preserved, not hidden)

- **Second-site PPG → HR/PTT**: negative, B−A +1.462 MAE, n=4, subject-fragile.
- **Leg BioZ (QDE V2)**: aggregate-negative but heterogeneous (7/10 subjects individually favor it), n=10.
- **Thoracic EIS (LBNP)**: `COMPLETE_MIXED`, sign-reverses without one subject, n=12.
- **EEG×Respiration interaction**: mixed-sign, "approximately additive or unresolved."

See `results/final_tables/table_d_negative_mixed_results.json`.

## 6. Engineering burden

Bounded (Tier 0-2) estimates for CORE_PLUS_CONTEXT: 3 body regions, 3
modules, 9 contacts most-likely (range 9-14), selected-topology battery-side
power 9.937 mW, battery-only mass 8.763 g, base raw data rate ~19.6 kbps.
Not measured or vendor-sourced; module-level total mass beyond battery cells
is `SYSTEM_MASS_NOT_READY`. See `results/final_tables/table_f_engineering_burden.json`.

## 7. Pareto rationale

A formal multi-objective Pareto dominance analysis is `COMPLETE`.
Pareto-relevant set: `{MINIMAL_CORE, CORE_PLUS_CONTEXT}` — both non-dominated
(`no_unique_pareto_winner: true`). CORE_PLUS_CONTEXT was selected by
Coordinator judgment (EOG's sleep-staging capability at low incremental
burden), **not** because it mathematically dominates MINIMAL_CORE. See
`results/stage4_formal_pareto_analysis.json` and `results/final_figure_manifest.json`
figure M (Pareto map).

## 8. Conditional uncertainties

- Gate D: `CONDITIONALLY_READY`, not fully verified.
- Gate E: EOG inclusion and sparse-EEG channel count both `FREEZE_CONDITIONALLY`, with predefined revision triggers tied to HMC/ds003838 full-cohort results.
- No vendor-specific BOM parts selected (class-level only); no target operating duration defined.

## 9. Pending science

HMC full cohort (151 subjects; 59 downloaded, 52 SHA-verified) and ds003838
full cohort (~93GB additional download) both remain
`LOWER_PRIORITY_EXTERNAL_WORK_PENDING` — explicitly not release blockers,
not run as part of Stage 5.

## 10. Digital Twin boundary

`ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED` (`results/digital_twin_architecture_footprint.json`,
unchanged by Stage 5). A 153,801-parameter untrained reference network; no
trained checkpoint, no validated multi-target performance, no
runtime/energy/latency measurement claimed. Verified unchanged and
undistorted across every new Stage-5 surface via
`ml/validate_stage5_final_release_freeze.py::check_digital_twin_not_promoted_in_stage5`.

## 11. Final claims

Central scientific message (frozen):

> Biological Minimalism evaluates whether sensing modalities provide measurable incremental value after controlling for model capacity, temporal correspondence, subject separation, heterogeneity, and physical burden. Some modalities retain value under stronger controls and external replication, while others become mixed, negative, fragile, or deprioritized.

All 17 claim areas (per-modality plus framing, engineering burden, and
robustness) with exact safe wording, evidence strength, and prohibited
stronger wording are in `results/final_claim_ledger.json`.

## 12. Reproducibility

12 governing experiments classified (never uniformly): most are
`CHECKPOINT_REPRODUCIBLE_FROM_ARCHIVE` (frozen checkpoint, GitHub-Release-
archived, SHA256-verified during the Day-13 clean-clone drill: 60/60
retrieved and verified); some are dataset-download-gated; the bounded
external diagnostics are `BOUNDED_DIAGNOSTIC_REPRODUCIBLE_IF_DATASET_LOCALLY_AVAILABLE`.
0 experiments currently fall in the `HISTORICALLY_UNVERIFIABLE_DUE_TO_MISSING_BYTES`
class. See `results/final_reproduction_manifest.json`.

## 13. Authoritative files

19 authoritative artifacts (9 carried forward from Stage 4, 10 new Stage-5
artifacts), each with canonical-text SHA256, owner, source stage, and
required-for-release/paper/jury flags — see
`results/final_project_manifest.json#authoritative_artifacts`. Full hash
freeze and fail-closed checks in `results/final_release_manifest.json`.

## 14. Release SHA

- Accepted Stage-3 SHA: `5c381014af61e5d10d41223963831b25b9ff23e6`
- Stage-4 final closure SHA: `691bc8c0fd464bc1741da2e69a7c5fa986c3294a`
- Stage-5 release-candidate commit SHA: reported in the branch push report (not embedded in any manifest file per this project's git discipline — see `results/final_release_manifest.json#final_project_sha_note`).

## 15. What remains outside final scope

- HMC full-cohort training, ds003838 full-cohort experiment (explicitly pending, not release blockers).
- Vendor-specific BOM part selection, flight-qualification, spaceflight/microgravity validation.
- Wiring the new Stage-5 synthesis artifacts (claim ledger, Tables A-F, jury pack, figure manifest) into new backend API endpoints or frontend UI panels — they exist as file-based artifacts for paper/jury/reproduction use today; Research Mode continues to serve the (unchanged) Stage-4 data live.
- Independent final project audit (this handoff produces a release *candidate*, not a verified-complete project — see `results/final_release_manifest.json#freeze_status`).
