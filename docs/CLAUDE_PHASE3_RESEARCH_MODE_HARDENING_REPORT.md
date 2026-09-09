# Claude Phase 3 — Research Mode / Frontend + Paper/Jury/Claim Infrastructure Report

**Branch:** `stage2-4-claude-integration-prep`
**Starting SHA:** `558a30b` (Phase 2 close-out, pushed)
**Scope:** Research Mode/frontend + paper/jury/claim infrastructure only, plus the explicit
consumer-guard verification requested by the user. No model training, no new scientific
evaluation, no integration of Ismet's in-progress science, no invented HMC/Sleep/ds003838 results,
no final architecture/Pareto decision.

---

## 1. Research Mode changes

Extended the Phase-2 backend with a **presentation/consumer layer** (`project_for_display`,
`build_two_arm_comparison_narrative`, `validate_claim_against_entry` in
`backend/app/research/future_science_ingestion.py`) and wired a real (though currently empty,
honest-pending) frontend consumer end to end:

- `ManifestEntryDisplayProjection` (new schema, `backend/app/schemas/experiment_manifest.py`) —
  the only shape any consumer should read: `completion_state_label`, `is_headline_eligible`,
  `replication_class_label`, `benefit_value`/`benefit_display`, `limitations`, `provenance_source`.
- `FutureScienceManifestEnvelope.display_projections` — populated only when `status == "INGESTED"`,
  always `[]` otherwise (never partial).
- Frontend: `FutureScienceHandoffCard.tsx` renders **only** `display_projections`, never
  `envelope.manifest.entries` directly — this is the structural mechanism that makes the frontend
  incapable of bypassing the backend guards (there is no raw data path to bypass with).
- Wired into `ResearchMode.tsx` via `researchStore.ts`, following the exact existing M12
  optional-panel-isolation pattern (a failure/pending state here can never break the core
  scientific panels).

## 2. Status rendering

`ExperimentCompletionState` and `ReplicationClass` each render as visually and textually distinct
badges (`COMPLETION_STATE_CLASS` / `REPLICATION_CLASS_CLASS` color maps in
`FutureScienceHandoffCard.tsx`) — COMPLETE (green), BOUNDED_DIAGNOSTIC (amber), BLOCKED_BY_DATA_ACCESS
(red), PENDING/HISTORICAL (slate), SUPERSEDED (dim red). A non-headline-eligible entry's numeric
field is replaced with `"N/A — <state label>"`, never left blank (which could read as "loading")
and never showing a number (which could read as a real result).

## 3. Replication handling

`replication_class_label` is produced by the backend from the manifest's own declared
`replication_class` only — the frontend has no logic capable of inferring "replication" from
anything else (no such code path exists to remove). Tested: all 4 `ReplicationClass` values produce
4 textually distinct labels (`test_guard_4_replication_class_is_never_inferred_only_echoed`).

## 4. Negative/heterogeneous handling

The existing PTT negative-result and Sleep-EDF heterogeneity presentations (`ResearchMode.tsx`,
already live) are unchanged and re-verified working (full test suite + live browser check). The
Phase-2/3 schema's `SensitivityBlock` (with `AVAILABLE`/`UNAVAILABLE`/`PENDING` status, reusing the
existing `SensitivityStatus` enum) is ready to carry a future heterogeneous Stage-2-4 result without
redesign — documented in `docs/CLAUDE_PHASE3_PAPER_SKELETON_STAGE2_4.md` §Heterogeneity.

## 5. Architecture/Pareto behavior

Unchanged and re-verified this phase: live `GET /research/engineering-readiness` still returns
`final_architecture_status = UNRESOLVED`, `formal_pareto_status = FORMAL_PARETO_NOT_READY`. No code
added this phase computes or could compute either from the future-science contract — the ingestion
module has no code path that touches architecture/Pareto state at all.

## 6. Paper skeleton

`docs/CLAUDE_PHASE3_PAPER_SKELETON_STAGE2_4.md` — 8 sections (Methods, Results, External
Replication, Same-Dataset Holdout, Negative Results, Heterogeneity, Limitations, Reproducibility,
Engineering/Architecture Boundary). Sections with real evidence are filled and cited to source
artifacts; Stage 2-4 sections (HMC, ds003838, corrected Sleep C/interaction) are marked
`PENDING_SCIENCE_HANDOFF` — not fabricated, not exposed on any live dashboard page (doc-only).

## 7. Jury skeleton

`docs/CLAUDE_PHASE3_JURY_FRAMEWORK_STAGE2_4.md` — answers all 9 example questions from governing
prompt §43, each citing either a real artifact or the specific software guard/test that enforces
the honest answer. Extends (does not duplicate) the existing `docs/JURY_DEFENSE_MASTER.md`.

## 8. Traceability (claim infrastructure, governing prompt §44)

`validate_claim_against_entry(entry, required_full_evidence=False)` — a claim citing a manifest
entry is rejected (`CLAIM_EVIDENCE_INSUFFICIENT`) if the entry's `completion_state` is
`BLOCKED_BY_DATA_ACCESS`, `PENDING`, or `SUPERSEDED` (unconditionally), or `BOUNDED_DIAGNOSTIC` when
`required_full_evidence=True`. Mixed-version claims (citing two entries from different
`dataset_version`/`protocol_version`) are separately rejected by `forbid_mixed_protocol_derivation`.
This directly implements the governing-prompt §44 rule ("blocked, pending, bounded diagnostic where
full evidence is required, superseded, or mixed-version") almost verbatim. Every experiment/artifact/
field/version/dataset/protocol/status pointer the rule requires already exists on
`ExperimentManifestEntry.provenance` (Phase 2).

## 9. Explicit consumer-guard verification (user's Phase-3 requirement)

A dedicated test file, `backend/tests/test_future_science_consumer_guards.py` (14 tests), maps
1:1 onto the 8 guard categories the user named, verified at the **consumer** boundary (i.e.
exercising `project_for_display`/`build_two_arm_comparison_narrative`/`validate_claim_against_entry`
as a real frontend/paper/jury consumer would, not just the raw Phase-2 guard functions in
isolation):

| # | Guard | Test(s) |
|---|---|---|
| 1 | `assert_promotable_to_headline` / promotion gate | `test_guard_1_non_complete_entry_never_yields_a_numeric_benefit_via_projection`, `test_guard_1_complete_entry_is_headline_eligible_with_a_real_benefit` |
| 2 | BOUNDED_DIAGNOSTIC vs COMPLETE separation | `test_guard_2_bounded_diagnostic_label_is_never_the_same_string_as_complete` |
| 3 | HISTORICAL/SUPERSEDED separation | `test_guard_3_historical_and_superseded_have_distinct_non_bypassable_labels` |
| 4 | EXTERNAL_REPLICATION vs SAME_DATASET_HOLDOUT | `test_guard_4_replication_class_is_never_inferred_only_echoed` |
| 5 | Mixed-protocol / V1-V2 protection | `test_guard_5_two_arm_narrative_refuses_mixed_protocol_version`, `test_guard_5_two_arm_narrative_succeeds_for_matched_protocol_version` |
| 6 | Metric directionality | `test_guard_6_benefit_sign_is_correct_for_both_directions_via_projection` |
| 7 | Cross-target comparison prohibition | `test_guard_7_two_arm_narrative_refuses_cross_target_comparison` |
| 8 | Missing/malformed manifest fail-closed | `test_guard_8_consumer_never_sees_partial_display_projections_on_failure`, `test_guard_8_required_full_evidence_claim_rejects_bounded_diagnostic`, `test_guard_8_claim_validator_always_rejects_incomplete_evidence_states` (×3 parametrized) |

All 14 passed on first run. No guard was weakened for UI convenience — the frontend component
(`FutureScienceHandoffCard.tsx`) has zero decision logic of its own; it only ever displays
backend-computed labels/booleans, which is a stronger guarantee than a frontend-side re-check would
be (there is no frontend code path capable of getting it wrong).

## 10. Frontend tests

No test runner exists in this repo (`frontend/package.json` devDependencies confirmed: no
jest/vitest/testing-library — matching the pre-existing, documented M12 precedent: "No automated
frontend test runner is configured; isolation verified by types + live browser validation.").
Consistent with that established convention (not introduced unilaterally this phase), guard
enforcement on the frontend is achieved via:
- TypeScript's own type system: `ExperimentCompletionState`/`ReplicationClass` are literal string
  unions; `Record<ExperimentCompletionState, string>` color maps in `FutureScienceHandoffCard.tsx`
  force a compile error if any state is missing a mapping (verified: `npx tsc --noEmit` clean).
- `npx eslint .` — clean, 0 warnings/errors.
- `npm run build` — clean, all 12 static routes generated, both before and after the
  `ResearchMode.tsx` wiring change.

## 11. Live browser

Backend (port 8000) + frontend dev server (port 3000) started; `/research`, `/digital-twin`,
`/mission-overview` all inspected via Chrome DevTools MCP:
- `/research`: new "Stage 2-4 Science Handoff" panel renders correctly with the honest
  `"Pending — Ismet's science-completion sprint is still in progress..."` message (confirmed via
  accessibility-tree snapshot and a scrolled screenshot). All pre-existing panels (reproducibility,
  PPG/PTT/Sleep cards, engineering readiness, hardware architecture, decision inputs, operational
  costs) unaffected.
- Network: all 14 requests on `/research` returned `200`, including the new
  `GET /research/future-science-manifest`.
- Console: **zero** error/warning messages on `/research`, `/digital-twin`, or `/mission-overview`.
- No fake future results visible anywhere; current canonical science intact; Digital Twin still
  reads as synthetic/conceptual on both the full page and (post-Phase-1-fix) the Mission Overview
  preview card.

## 12. Bugs

None found in production code this phase. (Process-management note, not a code bug: two dev-server
processes not started by this session were inadvertently killed by an over-broad `pkill` pattern
during cleanup — disclosed to the user immediately; no file or git state was affected.)

## 13. Risks/limitations disclosed

- `benefit_value` in `project_for_display` is only computed when `entry.control_result` is present;
  an entry with only `primary_result` and no `control_result` is still headline-eligible but shows
  its raw `primary_result.display` without a computed control-relative benefit. This is a
  deliberate, disclosed simplification (Phase 2's schema does not have a separate `baseline_result`
  field distinct from `control_result`) rather than a defect — flagged for whoever designs the
  eventual real consumer of Ismet's manifest to confirm this fits the actual field semantics Ismet
  produces.
- No automated frontend test runner exists (pre-existing, documented M12 limitation, not
  introduced or removed this phase); frontend guard verification relies on TypeScript
  exhaustiveness + live browser checks, consistent with established project convention.
- The paper skeleton and jury framework docs are structure/scaffolding, not final camera-ready
  content — by design (governing prompt §42/§43: "structure, not invented result claims").

## 14. Files

- `backend/app/schemas/experiment_manifest.py` — +29 lines (`ManifestEntryDisplayProjection`, `display_projections` field)
- `backend/app/research/future_science_ingestion.py` — +117 lines (projection/narrative/claim-validation functions, label maps)
- `backend/tests/test_future_science_consumer_guards.py` — new, 239 lines (14 tests)
- `frontend/src/lib/types.ts` — +58 lines (future-science TS types)
- `frontend/src/lib/api.ts` — +4 lines (`getFutureScienceManifest`)
- `frontend/src/store/researchStore.ts` — +45/-8 lines (new optional panel, M12 pattern)
- `frontend/src/components/research/FutureScienceHandoffCard.tsx` — new, 106 lines
- `frontend/src/components/research/ResearchMode.tsx` — +4 lines (wiring only)
- `docs/CLAUDE_PHASE3_PAPER_SKELETON_STAGE2_4.md` — new, 97 lines
- `docs/CLAUDE_PHASE3_JURY_FRAMEWORK_STAGE2_4.md` — new, 99 lines
- `docs/CLAUDE_PHASE3_RESEARCH_MODE_HARDENING_REPORT.md` — this report, new

No `results/*.json` file touched. No science file touched.

## 15. Commit/push

Committed on `stage2-4-claude-integration-prep`; pushed to origin; local/remote verified equal.
`main` untouched throughout.

## 16. Phase verdict

**PHASE3_COMPLETE**

Research Mode is now structurally ready to display Ismet's future science the moment it lands: a
frontend consumer exists, renders only backend-guard-cleared projections, and cannot bypass the
promotion gate, state separations, replication-class distinction, mixed-protocol protection, metric
directionality, cross-target prohibition, or fail-closed behavior — each independently verified by
a dedicated test named after the guard it proves. Paper and jury scaffolding exist with real current
evidence and honest `PENDING_SCIENCE_HANDOFF` markers for what doesn't exist yet. Claim-traceability
enforcement exists and is tested. No science evaluated, no Ismet in-progress work touched, no
invented numbers, no architecture/Pareto decision. Ready for Phase 4 on explicit "DEVAM".
