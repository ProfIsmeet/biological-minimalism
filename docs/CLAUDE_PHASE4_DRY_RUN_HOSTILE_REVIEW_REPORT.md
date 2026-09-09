# Claude Phase 4 — Integration Dry-Run + Hostile Review Report

**Branch:** `stage2-4-claude-integration-prep`
**Starting SHA:** `7e8e567` (Phase 3 close-out, pushed)
**Scope:** integration dry-run + hostile software/project-logic review + final integration-
readiness contract only. No model training, no new scientific evaluation, no integration or
cherry-pick of Ismet's in-progress science, no invented scientific results, no final architecture
selection, no formal Pareto computation.

---

## 1. Dry-run architecture

`backend/tests/test_phase4_integration_dry_run.py` (17 tests) exercises the full pipeline —
synthetic manifest dict/file → `validate_manifest_dict`/`load_and_validate_manifest` →
`FutureScienceManifestReader.status()` → `display_projections` → the consumer-facing
`project_for_display`/`build_two_arm_comparison_narrative`/`validate_claim_against_entry`/
`assert_replication_claim_is_plausible` functions — as a real Ismet manifest would flow through
it, not just individual guards in isolation (which Phase 2/3 already covered). All fixtures use
the unmistakable sentinel prefix `phase4-dry-run-` and are proven (by a dedicated test in this same
file) never to leak into `results/`.

## 2. Cases tested

Master-prompt §50 representative cases, all present: positive MAE candidate, negative MAE
candidate, positive F1 candidate, heterogeneous subject effect, external replication, failed
replication, bounded diagnostic, blocked dataset, historical vs corrected version.

User's 13 explicit Phase-4 stress-test cases — all present, each with a dedicated named test:

| # | Case | Test |
|---|---|---|
| 1 | BOUNDED_DIAGNOSTIC trying to become headline | `test_case_bounded_diagnostic_cannot_become_headline` |
| 2 | SAME_DATASET_HOLDOUT mislabeled as EXTERNAL_REPLICATION | `test_case_same_dataset_holdout_mislabeled_as_external_replication_is_caught` |
| 3 | SUPERSEDED/HISTORICAL competing with preferred corrected version | `test_case_historical_and_superseded_vs_preferred_corrected_version` |
| 4 | Blocked dataset carrying stale numeric fields | `test_case_blocked_dataset_with_stale_numeric_fields_never_renders_a_number` |
| 5 | MAE and macro-F1 sign handling | `test_case_positive_mae_candidate`, `test_case_negative_mae_candidate_is_shown_not_hidden`, `test_case_positive_f1_candidate` |
| 6 | biological_subject_n accidentally copied from optimization_seed_n | `test_case_subject_n_copied_from_seed_n_cannot_corrupt_the_benefit` |
| 7 | Incomplete provenance/checkpoint mapping | `test_case_incomplete_provenance_and_checkpoint_mapping_fail_closed_at_file_level` |
| 8 | Mixed Sleep V1/V2 operands | `test_case_historical_and_superseded_vs_preferred_corrected_version` (uses literal `V1_HISTORICAL`/`V2_SEEDFIX_CORRECTED` naming) |
| 9 | Failed/negative external replication | `test_case_failed_negative_external_replication_is_shown_not_hidden` |
| 10 | Strong aggregate improvement with severe subject heterogeneity | `test_case_heterogeneous_subject_effect_is_visible_despite_strong_aggregate` |
| 11 | Missing control_result and benefit_value behavior | `test_case_missing_control_result_benefit_behavior` |
| 12 | Synthetic fixtures leaking into active project evidence | `test_case_synthetic_fixtures_never_leak_into_active_results` |
| 13 | Architecture/Pareto auto-upgrading from a new positive result | `test_case_ingestion_module_has_no_import_of_architecture_or_pareto_modules`, `test_case_ingesting_a_strong_positive_manifest_does_not_change_architecture_or_pareto_state` |

Plus `test_full_pipeline_dry_run_with_a_multi_state_manifest_file` — one manifest file with 4
entries in 4 different completion states, ingested through the real file-based reader, proving the
whole pipeline (not just isolated functions) discriminates correctly between them in one pass.

All 17 passed on first run. Full backend suite: **214 passed, 0 failed** (197 Phase-3 baseline + 17 new).

## 3. Fail-closed behavior

Every case above either raises a typed `ManifestValidationError` with the correct `ManifestErrorCode`,
or produces a projection with `is_headline_eligible=False` / `benefit_value=None` /
`benefit_display` starting with `"N/A —"`. No case silently substitutes a default, a stale number,
or an inferred label.

## 4. Hostile software findings

**One real finding, found and fixed this phase (not merely reviewed):** `ManifestEntryDisplayProjection`
— the schema explicitly documented as "the ONLY shape any frontend/paper/jury consumer should read
from" — omitted `subject_sensitivity`/`class_sensitivity` entirely. A consumer following that
documented guidance literally could not see per-subject/per-class heterogeneity at all, meaning a
strongly-positive aggregate `benefit_value` could visually read as uniform support even if driven
by a single subject. Root cause: Phase 3 built the promotion/labeling guards but did not audit
*completeness* of the safe-to-read projection against everything a jury/paper consumer would need.
**Fixed:** both fields added to the schema, populated in `project_for_display`, and rendered in
`FutureScienceHandoffCard.tsx` via a new `SensitivitySection` disclosure — verified via
`test_case_heterogeneous_subject_effect_is_visible_despite_strong_aggregate`.

**Second finding, addressed with a new guard (not previously covered):** nothing in Phase 2/3
checked whether a declared `EXTERNAL_REPLICATION` was *plausible* — the pipeline trusted the
manifest's own label unconditionally. Since a same-dataset holdout mislabeled as an independent
replication cannot be disproven from a single entry in isolation, a new function,
`assert_replication_claim_is_plausible(candidate, primary)`, now fails closed
(`SUSPICIOUS_REPLICATION_CLAIM`) whenever a claimed external replication shares the exact same
`dataset`+`dataset_version` as the primary result it claims to replicate. This is a heuristic, not
a proof — disclosed as a limitation in §13.

No other hardcoded metrics, stale fallbacks, wrong enums, wrong signs, or cache-confusion bugs
were found. `FutureScienceManifestReader` has zero caching (every `.status()` call re-reads from
disk fresh) — verified by reading the source; "cache confusion" is structurally impossible here.

## 5. Hostile project-logic findings

Answered against the actual current live system, not hypothetically:

- **Does the dashboard make many experiments look like one giant validated model?** No — each
  experiment (PPG-DaLiA, PTT, Sleep-EDF, and now the Stage 2-4 handoff) is a visually and
  structurally separate card/panel with its own provenance; no code anywhere computes a combined
  "overall model" score.
- **Does "replication" have a precise definition?** Yes — `ReplicationClass`, 4 values, 4 distinct
  rendered labels (tested), now additionally guarded against the specific mislabeling case above.
- **Can a user mistake terrestrial datasets for spaceflight evidence?** No — `environment_scope`
  (`ResearchEnvironmentScope`) is rendered both per-experiment (`ResearchMode.tsx:411`) and in the
  reproducibility footer (`ResearchMode.tsx:604`); no experiment in this codebase declares
  `SPACEFLIGHT` scope. Verified by grep this phase, not assumed.
- **Can a bounded diagnostic look canonical?** No — `assert_promotable_to_headline`, tested
  extensively across Phases 3 and 4.
- **Can an aggregate result hide heterogeneity?** This phase's real finding (§4) — now fixed.
- **Does "minimal" still look like sensor-count minimization?** No — unchanged from Phase 1's
  verification (`ContactBurden` schema distinguishes body region/module/contacts/electrodes; not
  re-litigated this phase since Phase 2-4's new code doesn't touch this area).
- **Does Digital Twin look trained?** No — Phase 1's fix (Mission Overview disclaimer) confirmed
  still live via Phase 3's browser check; not re-checked live this phase (no code in this area
  changed since).
- **Does architecture look selected? Does formal Pareto look available?** No to both — re-verified
  this phase via `test_case_ingesting_a_strong_positive_manifest_does_not_change_architecture_or_pareto_state`,
  which proves byte-identical `engineering_readiness`/`day6_research` output before and after
  ingesting a strongly-positive synthetic manifest.

## 6. Fixes

1. `ManifestEntryDisplayProjection` + `project_for_display`: added `subject_sensitivity`/
   `class_sensitivity` pass-through (backend schema + ingestion module).
2. `FutureScienceHandoffCard.tsx`: new `SensitivitySection` component rendering both fields via a
   `<details>` disclosure (matching the existing `EngineeringReadinessView.tsx` convention),
   surfacing `dominant_key` and any heterogeneity `note` explicitly.
3. `frontend/src/lib/types.ts`: added `FutureScienceSensitivityStatus`/`FutureScienceSensitivityEntry`/
   `FutureScienceSensitivityBlock` TS mirrors.
4. New guard: `assert_replication_claim_is_plausible` + `ManifestErrorCode.SUSPICIOUS_REPLICATION_CLAIM`.

## 7. Integration-readiness contract

`docs/CLAUDE_PHASE4_INTEGRATION_READINESS_CONTRACT.md` — 14 literal, ordered steps (verify SHA →
verify manifest → inspect status → merge strategy → run validator → regenerate artifacts → update
API → update Research Mode → update claims → update paper/jury → run full tests → run browser →
freeze candidate SHA → independent hostile audit), each referencing real commands/files in this
repo, with explicit **STOP** points requiring Emir's sign-off and an explicit "what this contract
does NOT automate" closing section (scientific correctness and promotion decisions remain human
calls).

## 8. Tests

| Suite | Command | Result |
|---|---|---|
| Phase 4 dry-run (isolated) | `pytest -q tests/test_phase4_integration_dry_run.py` | **17 passed** |
| Backend (full) | `cd backend && .venv/bin/python -m pytest -q` | **214 passed**, 0 failed (197 Phase-3 baseline + 17 new) |
| Claim consistency | `ml/check_claim_consistency.py` | PASS, exit 0 |
| Decision-inputs determinism | regen + `git diff` | byte-identical, no diff |
| Frontend typecheck/lint/build | `npx tsc --noEmit && npx eslint . && npm run build` | all clean; 12 routes generated |

## 9. Files

- `backend/app/schemas/experiment_manifest.py` — +7 lines (sensitivity fields on projection)
- `backend/app/research/future_science_ingestion.py` — +30 lines (sensitivity pass-through, new guard + error code)
- `backend/tests/test_phase4_integration_dry_run.py` — new, 432 lines (17 tests)
- `frontend/src/lib/types.ts` — +19 lines (sensitivity TS types)
- `frontend/src/components/research/FutureScienceHandoffCard.tsx` — +36 lines (`SensitivitySection`)
- `docs/CLAUDE_PHASE4_INTEGRATION_READINESS_CONTRACT.md` — new, 192 lines
- `docs/CLAUDE_PHASE4_DRY_RUN_HOSTILE_REVIEW_REPORT.md` — this report, new

No `results/*.json` touched. No science file touched. No architecture/Pareto decision made.

## 10. Commit/push

Committed on `stage2-4-claude-integration-prep`; pushed; local/remote verified equal. `main`
untouched throughout.

## 11. Remaining blockers

None for the software/integration-prep track. The only blocker for real integration is Ismet's
science-completion sprint itself — nothing in this branch is blocked on further software work.

## 12. Exact next operation after Ismet completes

Follow `docs/CLAUDE_PHASE4_INTEGRATION_READINESS_CONTRACT.md` Step 1 (verify Ismet's final SHA),
in order, only after Emir gives explicit instruction to begin integration. Do not skip to Step 2
or later without completing and reporting Step 1.

## 13. Disclosed limitations

- `assert_replication_claim_is_plausible` is a heuristic (same dataset+version as the primary ⇒
  implausible), not a proof of mislabeling in general — it cannot catch a replication claim made
  against a dataset with a *different* name that is nonetheless not a genuinely independent cohort.
  It is also not automatically invoked by `build_two_arm_comparison_narrative`; a future consumer
  writing a "replication narrative" must call it explicitly, same discipline pattern already
  accepted for the other guard functions.
- `biological_subject_n`/`optimization_seed_n` are still not surfaced on `ManifestEntryDisplayProjection`
  (found and left unresolved this phase — proven structurally harmless to the computed benefit via
  `test_case_subject_n_copied_from_seed_n_cannot_corrupt_the_benefit`, but a viewer cannot currently
  visually sanity-check these two counts against each other from the dashboard). Flagged for
  whoever wires the real post-integration Research Mode display in Step 8 of the readiness contract.

## 14. Phase verdict

**CLAUDE_PARALLEL_INTEGRATION_PREP_COMPLETE_READY_FOR_ISMET_HANDOFF**

All four phases of the governing prompt are complete. The software/engineering/API/Research-Mode/
claim/paper/jury infrastructure is hardened, tested (214 backend tests, up from 158 at the start of
this sprint), and structurally proven — via adversarial dry-run, not assumption — to be unable to
fabricate, conflate, or auto-promote a future Stage 2-4 science result. One genuine hostile-review
finding (heterogeneity visibility) was caught and fixed this phase, and one new guard
(replication-claim plausibility) was added in direct response to the user's explicit stress test.
No science was evaluated, no Ismet in-progress work was touched, no numbers were invented, and no
architecture/Pareto decision was made anywhere in this sprint.
