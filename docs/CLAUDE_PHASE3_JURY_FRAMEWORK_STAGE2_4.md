# Jury Framework — Stage 2-4 Handoff (Phase 3 Integration Prep)

Structure for evidence-backed answers, extending `docs/JURY_DEFENSE_MASTER.md` with the questions
specific to the Stage 2-4 science-completion handoff and the Phase 2/3 ingestion contract. Every
answer below cites either a real committed artifact or the specific software guard that enforces
the honest answer — no answer here asserts a Stage 2-4 result that does not yet exist (governing
prompt §43, §55).

## 1. What actually replicated?

Nothing is currently labeled an independent external replication anywhere in this codebase. The
Sleep-EDF secondary holdout is a **same-dataset holdout** (`SAME_DATASET_HOLDOUT` in
`ReplicationClass`), not an external replication — same dataset, same recording protocol, held-out
subjects only. `ReplicationClass.EXTERNAL_REPLICATION` exists in the Phase-2 schema specifically
for a future case (e.g. HMC vs Sleep-EDF) — but only becomes true when Ismet's manifest declares it
explicitly; the software never infers "replication" from a second run existing
(`app/schemas/experiment_manifest.py::ReplicationClass`, tested in
`test_guard_4_replication_class_is_never_inferred_only_echoed`).

## 2. Which result was negative?

PTT second-PPG-site: aggregate negative HR-MAE effect, subject-2-dominated
(`results/ptt_sensitivity_analysis.json`). Published with full sensitivity disclosure, not hidden
or reframed as neutral.

## 3. Why isn't the final architecture chosen yet?

`final_architecture_status = UNRESOLVED` (live at `GET /research/engineering-readiness`).
Blockers, in order of severity: cross-dataset metric incomparability (BLOCKER — HR MAE and sleep
macro-F1 are not rankable on one axis), system power/mass unquantified (HIGH), interaction evidence
only partial (MEDIUM, one controlled pair tested) — `results/pareto_readiness_blockers.json`. No
code path in this repository computes a "winning sensor" from `B > A`.

## 4. How do you separate seeds from subjects?

Every Phase-2/3 manifest entry requires `biological_subject_n` and `optimization_seed_n` as two
independently-required integers (`Field(ge=1)` on both, no shared default) — a manifest that omits
either fails closed with `SCHEMA_VALIDATION_FAILED`
(`test_subject_n_and_seed_n_are_both_required_independently`). In the existing canonical Sleep-EDF
result: n=3 biological subjects (primary, `results/sleep_scientific_remediation_day12.json`) / n=8
(secondary holdout, `results/sleep_edf_secondary_holdout_evaluation.json`), 5 optimization seeds —
never pooled into a combined "n=11" or "n=8 seeds" figure; the two counts are reported by two
separate artifacts and are never summed.

## 5. Why doesn't the system show a global sensor ranking?

`forbid_cross_target_comparison()` raises `CROSS_TARGET_COMPARISON_PROHIBITED` for any attempt to
compare two entries with different `target` values (e.g. HR MAE vs sleep macro-F1) — tested in
`test_guard_7_two_arm_narrative_refuses_cross_target_comparison`. No field in the Phase-2/3 schema
represents a "global score" (confirmed by direct grep of the schema during Phase 2). The existing
`target_evidence_matrix` API endpoint's `cross_target_comparability` field states the prohibition
explicitly to any consumer.

## 6. What does a blocked dataset mean?

`ExperimentCompletionState.BLOCKED_BY_DATA_ACCESS` — the experiment was designed and frozen but the
underlying raw data could not be obtained (e.g. GalaxyPPG/LBNP `zenodo.org` unreachable, per the
historical Stage 1B/2 access-gate commits). A blocked entry is never headline-eligible
(`assert_promotable_to_headline` raises `NOT_PROMOTABLE_TO_HEADLINE`) and can never support a paper
claim (`validate_claim_against_entry` raises `CLAIM_EVIDENCE_INSUFFICIENT` for this state
unconditionally) — verified in `test_guard_8_claim_validator_always_rejects_incomplete_evidence_states`.

## 7. What is the difference between same-dataset holdout and independent replication?

A same-dataset holdout (`SAME_DATASET_HOLDOUT`) reuses the same recording protocol and instrument
as the primary result, testing generalization only across held-out *subjects* within one dataset.
An independent replication (`EXTERNAL_REPLICATION`) uses a genuinely different dataset/cohort/
recording setup. The two `ReplicationClass` labels are guaranteed textually distinct
(`test_guard_4_replication_class_is_never_inferred_only_echoed` asserts all 4 declared classes
produce 4 distinct human-readable labels) so a reviewer reading the dashboard cannot confuse one
for the other.

## 8. Why doesn't terrestrial evidence prove astronaut validity?

No dataset in this project (PPG-DaLiA, Sleep-EDF, PTT, or the Stage-2-4 candidates HMC/ds003838/
GalaxyPPG/LBNP) contains spaceflight or microgravity subjects. `ResearchEnvironmentScope` in the
existing schema already distinguishes `TERRESTRIAL_FREE_LIVING` / `TERRESTRIAL_CONTROLLED` /
`ANALOG` / `SIMULATION` / `SPACEFLIGHT` as five separate values — every current experiment's scope
is terrestrial; none claims `SPACEFLIGHT`. Terrestrial results are the project's evidentiary method
demonstration; spaceflight applicability is stated motivation, never validated data.

## 9. Why isn't the Digital Twin validated?

`TorchInferenceEngine.runs_real_inference = False`; the module's own docstring states it does not
run a forward pass (`backend/app/ml/inference.py`, re-verified intact in Phase 1). The
`/digital-twin` full page explicitly states "synthetic, conceptual... untrained and not validated";
the Mission Overview preview card was found in Phase 1 to lack this disclaimer and was fixed to add
one (`frontend/src/components/panels/DigitalTwinPreview.tsx`). No checkpoint has been trained for
this system in this project's scope.

---

## Meta-question: how do we know these answers won't rot when Ismet's manifest lands?

Every answer above traces to either (a) a committed artifact that does not change without a new
commit, or (b) a software guard with a dedicated adversarial test (Phase 2: 24 tests in
`test_future_science_ingestion.py`; Phase 3: 14 tests in `test_future_science_consumer_guards.py`,
one per guard category listed in this document). When Ismet's manifest arrives, these same guards
— not new ad hoc logic — will govern what the dashboard and this jury framework are allowed to say
about it.
