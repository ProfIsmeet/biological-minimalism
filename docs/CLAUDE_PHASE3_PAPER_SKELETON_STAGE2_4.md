# Paper Skeleton — Stage 2-4 Extension (Phase 3 Integration Prep)

Structural skeleton only. Sections backed by real, committed evidence are filled with that
evidence and cited to source artifacts. Sections that depend on Ismet's in-progress
science-completion sprint are marked `PENDING_SCIENCE_HANDOFF` — no HMC / ds003838 / Sleep-V2-C /
Sleep-V2-interaction number is invented here (governing prompt §42, §55). This is an
integration-prep structure, not the camera-ready paper; do not present the `PENDING_SCIENCE_HANDOFF`
markers in any public-facing dashboard view (they belong in this document only).

## Methods

- Marginal-value methodology (one-sensor-at-a-time ablation vs matched/shuffled control) —
  `docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md`, established and unchanged this phase.
- Capacity-control protocol for PPG+IMU — `results/ppg_dalia_capacity_control.json`.
- Sleep-EDF seed-before-model-init correction (H1) — `docs/SLEEP_SEEDING_PROTOCOL_V2.md`.
- **Stage 2-4 extension (PENDING_SCIENCE_HANDOFF):** HMC A/B/C protocol, ds003838 full-cohort
  protocol, corrected Sleep shuffled-EOG-control/interaction protocol. Protocol/deviation documents
  for these experiments are candidate work-in-progress on the Science Owner's separate branch, not
  yet present as canonical artifacts on this branch; neither the protocol documents nor the
  corresponding *results* exist here yet.

## Results

- PPG-DaLiA capacity-controlled IMU benefit: A_cap→B ≈0.605 bpm, C→B ≈0.776 bpm MAE, 5/5 seeds —
  `results/ppg_dalia_capacity_control.json`. **COMPLETE.**
- Sleep-EDF EEG+EOG (seed-corrected V2, primary A/B): macro-F1 +0.0282, 4/5 seeds —
  `results/sleep_scientific_remediation_day12.json`. **COMPLETE** (Primary A/B only; shuffled-EOG
  control C and interaction M_B/M_AB remain `SEED_CORRECTION_PENDING_FOLLOWUP` under the corrected
  protocol — do not report a corrected B-C or corrected interaction number).
- PTT second-PPG-site: aggregate negative, subject-2-dominated — `results/ptt_sensitivity_analysis.json`.
  **COMPLETE** (heterogeneous negative result, not hidden).
- **Stage 2-4 extension (PENDING_SCIENCE_HANDOFF):** HMC A/B/C, ds003838 full-cohort, corrected
  Sleep C/interaction. The historical `stage2-4-expansion-science` branch lineage (QDE V2 n=10,
  GalaxyPPG/LBNP blocked, ds003838 bounded n=3 diagnostic) exists in this branch's git ancestry as
  **HISTORICAL / intermediate evidence only** — governing prompt §7 explicitly forbids
  canonicalizing it as final Stage 2-4 science. It is not cited here as a Results-section number.

## External Replication

No result in this codebase is currently labeled `EXTERNAL_REPLICATION`. The Phase-2/3 ingestion
contract's `ReplicationClass` enum exists specifically so that when/if a future HMC or ds003838
result qualifies, it can be labeled `EXTERNAL_REPLICATION` — but only if Ismet's manifest declares
it so explicitly (governing prompt §38: "The UI must NOT automatically label a second result
'replication'"). Today: `PENDING_SCIENCE_HANDOFF`.

## Same-Dataset Holdout (distinct from External Replication)

Sleep-EDF prospective 8-subject secondary holdout (historical protocol, zero retraining, A→B 5/5
seeds, C→B 5/5 seeds) — `results/sleep_edf_secondary_holdout_evaluation.json`. **COMPLETE**,
labeled `SAME_DATASET_HOLDOUT` in this codebase's vocabulary — never conflated with an independent
replication (same dataset, same recording protocol, different subjects only).

## Negative Results

PTT second-PPG-site: aggregate negative HR-MAE effect, subject-2-dominated, disclosed with full
sensitivity analysis rather than omitted — `results/ptt_sensitivity_analysis.json`,
`results/ptt_sensitivity_day11.json`. This is the project's standing example that a negative
target-specific result is published, not hidden, and that "aggregate negative" does not
automatically mean "removal candidate" (engineering burden is assessed separately).

## Heterogeneity

- PTT: subject-2-dominated aggregate direction; sign flips if s2 is excluded (kept per protocol,
  sensitivity reported) — `results/ptt_sensitivity_analysis.json`.
- Sleep-EDF secondary holdout: 6/8 subjects B>A, 7/8 B>C, largest single subject ~41% of summed
  effect — no longer single-subject-dominated, but not uniform either (2/8 near-zero/slightly
  negative); class-level N3 regression disclosed alongside the REM gain —
  `results/sleep_edf_secondary_holdout_evaluation.json`.
- **Stage 2-4 extension:** the Phase-2 `SensitivityBlock` schema (`subject_sensitivity`,
  `class_sensitivity`, both carrying an explicit `AVAILABLE`/`UNAVAILABLE`/`PENDING` status) is
  ready to receive Ismet's future per-subject/per-class breakdowns without redesign.

## Limitations

- No spaceflight or microgravity data anywhere in this project; terrestrial evidence is motivation,
  not validation (`results/architecture_decision_matrix.json`, `docs/JURY_DEFENSE_MASTER.md`).
  System power/mass, formal Pareto frontier — all `NOT_READY`/`UNRESOLVED` (`results/pareto_readiness_blockers.json`).
- PTT cache provenance not yet stamped (documented M7 limitation, re-confirmed unchanged in Phase 1).
- Claim checker (`ml/check_claim_consistency.py`) verifies existence, not numerical correctness
  (documented M4 limitation).
- **Stage 2-4 extension:** HMC/ds003838/corrected-Sleep-C/interaction results are `PENDING_SCIENCE_HANDOFF`.

## Reproducibility

Full backend reproducibility panel (typed PASS/PARTIAL/FAIL/UNAVAILABLE/MALFORMED, never a
default PASS) — `backend/app/research/catalog.py::_reproducibility`, live at
`GET /research/summary`. 197 backend tests, 290 ML tests (19 legitimate dataset/checkpoint-absence
skips) passing as of this phase's close (see Phase 1/2/3 reports).

## Engineering / Architecture Boundary

- System average power: `SYSTEM_AVERAGE_POWER_NOT_READY`. System mass: `SYSTEM_MASS_NOT_READY`.
  BOM: `PARTIAL`. Final architecture: `UNRESOLVED`. Formal Pareto: `FORMAL_PARETO_NOT_READY`. All
  four are structurally separate typed fields from any component-level figure — a low component
  power can never render as "system power" (`backend/app/schemas/engineering_readiness.py`,
  re-verified live in Phase 1 §7).
- No architecture is presented as "selected" anywhere in this codebase; no formal Pareto frontier
  is computed anywhere in this codebase.
