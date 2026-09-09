# Claude Phase 2 — Future-Science Ingestion Contract + Backend/API Report

**Branch:** `stage2-4-claude-integration-prep`
**Starting SHA:** `8271d4f54c00ef64ab3644f4218cfdeff53a9de0` (Phase 1 close-out, pushed)
**Scope:** Generic experiment-result ingestion contract + backend/API infrastructure only. No model training, no new scientific evaluation, no integration of Ismet's in-progress science, no invented future numbers, no final architecture/Pareto decision.

---

## 1. Repo/SHA

- Started this phase on `stage2-4-claude-integration-prep` @ `8271d4f` (verified local == remote before starting).
- All work this phase is additive: 3 new files, 1 existing file touched with a pure 16-line addition (2 imports + 1 new route). Zero existing files' logic modified.

## 2. Schema changes

New file `backend/app/schemas/experiment_manifest.py` (148 lines) defines the generic ingestion contract (governing prompt §24):

- `ExperimentCompletionState` (COMPLETE / BOUNDED_DIAGNOSTIC / BLOCKED_BY_DATA_ACCESS / PENDING / HISTORICAL / SUPERSEDED)
- `ReplicationClass` (EXTERNAL_REPLICATION / SAME_DATASET_HOLDOUT / SINGLE_RUN / NOT_APPLICABLE)
- `ManifestMetric`, `ManifestResultValue`, `SensitivityEntry`/`SensitivityBlock`, `ProvenanceRecord`, `CheckpointManifestRef`
- `ExperimentManifestEntry` — the full per-experiment record: experiment ID/version, dataset/dataset version, target, baseline/candidate/control config, metric (with directionality), `biological_subject_n` and `optimization_seed_n` as two independently required integers (`Field(ge=1)`, never one field standing in for the other), primary/control result, subject/class sensitivity, replication class, completion state, access blocker, provenance, checkpoint manifest, safe/unsafe claims, limitations — every field from governing-prompt §24's checklist is present.
- `ExperimentManifestFile` (top-level manifest with `schema_version` gated by `SUPPORTED_MANIFEST_SCHEMA_VERSIONS = {"1.0.0"}`) and `FutureScienceManifestEnvelope` (the API-facing wrapper).

All models use the repo's existing `StrictModel` convention (`extra="forbid"`), matching every other schema file.

## 3. Reused existing contracts (governing prompt §24/§25: "do not create a parallel redundant universe")

- `MetricKind`, `MetricDirectionality`, `SensitivityStatus`, `ResearchAvailability` are imported directly from `app.schemas.research` — not redefined.
- The `StrictModel` base class, `Reader`-class-with-`.status()`/`.artifact()`-returning-an-Envelope pattern, and module-level singleton instantiation all follow the exact convention already used by `engineering_readiness.py`, `day6.py`, `decision_inputs.py`, `operational_costs.py`.
- `REPOSITORY_ROOT` is imported from `app.research.catalog` rather than redefined.
- The generic `forbid_mixed_protocol_derivation` guard is an explicit generalization of `app.research.sleep_version_guard.resolve_version_safe_comparison` (same "same dataset + same dataset_version + same protocol_version, or refuse" principle), not a competing mechanism.

## 4. New status semantics

`ExperimentCompletionState` and `ReplicationClass` are two orthogonal enums (not one collapsed boolean or one giant enum), matching this codebase's established pattern of splitting concerns into separate typed enums (e.g. `ReadinessLevel` vs `QuantityStatus` vs `TargetEvidenceStatus` already coexist for exactly this reason). This means a result can independently be, e.g., `BOUNDED_DIAGNOSTIC` + `SAME_DATASET_HOLDOUT`, without conflating "how complete is this" with "what kind of replication is this."

## 5. Metric-direction handling

- `compute_benefit(metric, baseline, candidate)` in `future_science_ingestion.py` returns a positive value when the candidate is better, branching explicitly on `metric.directionality` (`LOWER_IS_BETTER` → `baseline.mean - candidate.mean`; `HIGHER_IS_BETTER` → `candidate.mean - baseline.mean`); `NOT_APPLICABLE` raises rather than silently guessing a direction. No universal subtraction exists anywhere in this module.
- A `KNOWN_METRIC_DIRECTIONS` registry (HR MAE, PTT MAE, QDE mass MAE → lower-is-better; sleep macro-F1, cognitive macro-F1 → higher-is-better) cross-checks any incoming manifest entry naming an already-established metric; a mismatch (reversed sign) is rejected with `CONFLICTING_METRIC_DIRECTION`, not silently accepted. A brand-new metric name not yet in the registry is accepted as a first sighting — this is intentionally permissive for genuinely new metrics, not a loophole for reversing a known one.
- Tested both directions explicitly (`test_compute_benefit_respects_declared_direction_both_ways`) plus both reversed-sign adversarial cases (`test_mae_direction_reversed_is_rejected`, `test_f1_direction_reversed_is_rejected`).

## 6. Cross-target protections

- `forbid_cross_target_comparison(entry_a, entry_b)` raises `CROSS_TARGET_COMPARISON_PROHIBITED` whenever `entry_a.target != entry_b.target` — e.g. HR MAE vs sleep macro-F1 can never be combined into one score.
- No field anywhere in the new schema (`ExperimentManifestEntry`, `ExperimentManifestFile`, `FutureScienceManifestEnvelope`) represents a "global score," "rank," or normalized cross-target value — confirmed by direct grep of the schema file, not just by omission in this report.
- No new endpoint aggregates across `target` values; `/research/future-science-manifest` returns one manifest's raw entries only.

## 7. Future ingestion adapter

New file `backend/app/research/future_science_ingestion.py` (230 lines):

- `load_and_validate_manifest(path)` — reads and validates a manifest file end to end, fail-closed at every stage.
- `validate_manifest_dict(raw)` — the pure validation core (also directly unit-testable without touching the filesystem): schema-version gate → Pydantic structural validation → per-entry semantic checks (metric direction, provenance, checkpoint mapping).
- `FutureScienceManifestReader` — the `Reader`-with-`.status()` singleton (`future_science_manifest`), matching every other research module's convention.
- No manifest satisfying this contract exists anywhere in `results/` — confirmed absent both before and after this phase's work (`results/stage2_4_science_completion_manifest.json` does not exist on this branch). All test fixtures use unmistakably fake identifiers (`test-experiment-alpha`, `test-dataset`, `test_metric_mae`, `results/test_fixture_only.json`) and live only inside `backend/tests/test_future_science_ingestion.py` — none were written into `results/`.

## 8. Fail-closed behavior (governing prompt §29 — every listed case implemented and tested)

| Failure mode | Typed error code | Test |
|---|---|---|
| Missing manifest | `MISSING_MANIFEST` | `test_missing_manifest_fails_closed`, `test_missing_manifest_raises_typed_error_from_loader` |
| Malformed JSON | `MALFORMED_JSON` | `test_malformed_json_fails_closed` |
| Wrong/unsupported schema version | `UNSUPPORTED_SCHEMA_VERSION` | `test_unsupported_schema_version_fails_closed` |
| Unknown completion/replication status | `UNKNOWN_STATUS` | `test_unknown_completion_state_fails_closed` |
| Conflicting metric direction | `CONFLICTING_METRIC_DIRECTION` | `test_mae_direction_reversed_is_rejected`, `test_f1_direction_reversed_is_rejected` |
| Missing provenance | `MISSING_PROVENANCE` | `test_missing_provenance_fails_closed` |
| Inconsistent/conflated subject-n | `SCHEMA_VALIDATION_FAILED` (both fields independently required, `ge=1`) | `test_subject_n_and_seed_n_are_both_required_independently` |
| Invalid checkpoint mapping | `INVALID_CHECKPOINT_MAPPING` | `test_invalid_checkpoint_mapping_is_rejected` |
| Mixed protocol version (V1/V2-style) | `MIXED_PROTOCOL_VERSION` | `test_mixed_protocol_version_derivation_is_blocked` |
| Cross-target comparison | `CROSS_TARGET_COMPARISON_PROHIBITED` | `test_cross_target_comparison_is_prohibited` |
| Diagnostic/blocked promoted to headline | `NOT_PROMOTABLE_TO_HEADLINE` | `test_non_complete_states_cannot_be_promoted_to_headline` (parametrized over all 5 non-COMPLETE states) |
| Stale-result fallback on ingestion failure | n/a (behavioral) | `test_ingestion_failure_never_falls_back_to_cached_or_canonical_science` — asserts two consecutive failed reads never leak PPG/Sleep/canonical field names or values |

Every failure path returns/raises a typed, branchable result — none silently substitutes a default, an old cached value, or a bare `True`.

## 9. Provenance

`ProvenanceRecord` requires `source_artifact_path` (non-empty, enforced), `dataset_version`, `protocol_version`; optionally carries `source_sha256`, `experiment_commit`, `checkpoint_manifest_path`, `subject_split_manifest_path`. An entry with a blank/whitespace-only `source_artifact_path` is rejected with `MISSING_PROVENANCE` — no result can become "canonical" without this, matching governing-prompt §30 exactly.

## 10. Backward compatibility

- `backend/app/api/routes/research.py` diff is a clean **16-line addition** (2 import lines + 1 new route block) — verified via `git diff --stat`. None of the 8 pre-existing route handlers were touched.
- Full pre-existing backend test suite (159 tests from Phase 1's close-out, including `test_research_api.py`, `test_reproducibility_panel.py`, `test_engineering_readiness.py`, `test_sleep_version_guard.py`, `test_decision_inputs.py`, `test_day6_hardware.py`) still passes unchanged.
- Live spot-check: `/research/summary` (existing) still returns its normal shape; `/research/future-science-manifest` (new) returns `PENDING_SCIENCE_HANDOFF`; full `openapi.json` route list shows all 10 prior routes plus the 1 new one — nothing removed or renamed.
- `ml/check_claim_consistency.py` still passes (exit 0, unaffected — this phase touched no claim-bearing artifact).
- `backend/app/research/decision_inputs.py` regeneration is still byte-identical against `results/pareto_decision_inputs.json` (checked again after this phase's edits) — no cross-layer drift introduced.

## 11. Tests

| Suite | Command | Result |
|---|---|---|
| New ingestion contract tests (isolated) | `.venv/bin/python -m pytest -q tests/test_future_science_ingestion.py` | **24 passed** (0 failed) |
| Backend (full) | `cd backend && .venv/bin/python -m pytest -q` | **183 passed**, 0 failed (159 Phase-1 baseline + 24 new) |
| Claim consistency | `ml/check_claim_consistency.py` | `STRUCTURED_TRACEABILITY_AND_FORBIDDEN_PATTERN_CHECK_PASS`, exit 0 |
| Decision-inputs determinism | `python -m app.research.decision_inputs` + `git diff` | byte-identical, no diff |
| Live API | `curl /research/future-science-manifest` and `/research/summary` | both correct; `openapi.json` shows 10 prior + 1 new route |

One test-authoring bug was caught and fixed during this phase before it reached the final suite: the test fixture initially used a lowercase `"single_run"` for `ReplicationClass`, which is defined with uppercase enum values (`"SINGLE_RUN"`) — 14 of the 24 new tests failed on first run with a Pydantic enum-validation error until the fixture was corrected. This was a test-fixture bug, not a production-code bug; no production file needed changing. Fixed, re-run, all 24 pass.

## 12. Bugs

None found in production code this phase (the one bug found — described in §11 — was in the new test fixture itself, caught before commit).

## 13. Risks / limitations disclosed

- The `KNOWN_METRIC_DIRECTIONS` registry is seeded with 5 metric names already used elsewhere in this repo; a genuinely new metric Ismet introduces will be accepted on first sighting with whatever directionality the manifest declares (no cross-check possible for a metric never seen before) — this is by design (§24's instruction not to over-engineer), not a gap, but worth noting: it means the direction-conflict guard only protects *already-known* metrics, not novel ones.
- `assert_promotable_to_headline` and `forbid_cross_target_comparison`/`forbid_mixed_protocol_derivation` are guard *functions*, not enforced at the Pydantic type level — any future Phase-3 consumer code must actually call them before treating an entry as a headline/derived-delta. This is the same pattern `sleep_version_guard.py` already uses successfully (a choke-point function, not a type-system guarantee), so it's consistent with established practice, but it is a discipline requirement for whoever writes the Phase-3 consumer, not a runtime-enforced invariant.
- No real manifest exists to validate the contract's ergonomics against; the schema's completeness is judged against governing-prompt §24's checklist and this codebase's existing science-representation needs (PPG/PTT/Sleep), not against Ismet's actual forthcoming file shape, which is not yet known.

## 14. Files

- `backend/app/schemas/experiment_manifest.py` — new, 148 lines
- `backend/app/research/future_science_ingestion.py` — new, 230 lines
- `backend/tests/test_future_science_ingestion.py` — new, 342 lines (24 tests)
- `backend/app/api/routes/research.py` — modified, +16 lines (additive only)
- `docs/CLAUDE_PHASE2_SCIENCE_INGESTION_CONTRACT_REPORT.md` — this report, new

No `results/*.json` file created, modified, or referenced as real evidence. No science file touched. No frontend file touched (Phase 2 is backend/API-only per user instruction).

## 15. Commit/push

Committed on `stage2-4-claude-integration-prep`; pushed to `origin/stage2-4-claude-integration-prep`; local/remote verified equal after push. `main` untouched throughout (reflog unchanged from Phase 1's close-out).

## 16. Phase verdict

**PHASE2_COMPLETE**

Generic experiment-result ingestion schema built, reusing existing enums/conventions wherever possible. Fail-closed validator covers every failure mode listed in governing-prompt §29, each with a dedicated adversarial test (24 total, all passing). Metric-direction handling is explicit and bidirectionally tested. Cross-target and mixed-protocol-version guards are in place and tested, generalizing the existing Sleep V1/V2 guard rather than duplicating it. One new read-only, backward-compatible API endpoint added; all 8 pre-existing endpoints unchanged and re-verified passing. No science evaluated, no Ismet in-progress work touched, no future numbers invented, no architecture/Pareto decision made. Ready for Phase 3 on explicit "DEVAM".
