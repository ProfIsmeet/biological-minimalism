# Stage 4 — Codex Parent-Audit Delta Hardening

`INTEGRATION_OWNER` response to the independent Codex audit of
`stage2-4-science-owner-completion @ ab798815882ac0723491dc489de2375f8bf5b774`,
result: **`INDEPENDENT_PARENT_SCIENCE_AUDIT_CONDITIONAL_PASS`** (0 BLOCKER,
2 HIGH, several MEDIUM). This sprint does **not** remediate the underlying
Science Owner artifacts — none of the flagged files
(`results/sensor_value_master_matrix_stage4.json`,
`results/architecture_evidence_handoff_stage4.json`,
`results/hmc_split_stage3_bounded_n7.json`) exist on this branch; they live
only on the audited science branch, not yet integrated here. This sprint
hardens the **Stage-4 consumer side** so that when those artifacts are
eventually integrated, they cannot be misresolved, promoted, or overstated.

## Finding map

| Codex finding | Applicability | Action taken | Files changed | Test proving behavior | Remaining Science Owner responsibility | Status |
|---|---|---|---|---|---|---|
| **H-01**: checkpoint filename collision (accepted V2 checkpoint vs. noncanonical Mac reproduction share a filename, different hashes) | Direct — exactly the class of bug a filename-keyed consumer would hit | Built `resolve_checkpoint()`: identity tuple = `(experiment_version, arm, optimization_seed[, sha256])`, filename carried only as non-authoritative metadata. Fails closed with typed codes for every disagreement; `provenance_class=NONCANONICAL_SUPPORTIVE_REPRODUCTION` is never silently substituted when `require_accepted=True` (default). | `backend/app/schemas/stage4_science_guards.py`, `backend/app/research/stage4_science_guards.py` | `backend/tests/test_checkpoint_identity_resolution.py` (14 tests: identical-filename+different-hash/protocol/arm, missing hash, ambiguous, noncanonical-only-match, filename-never-read) | Produce the real checkpoint manifest with this identity tuple once the corrected V2 checkpoints are integrated | **MITIGATED** (infrastructure ready; not yet wired to a live manifest since none exists on this branch) |
| **H-02**: old ~23% PPG-only→PPG+IMU capacity-confounded figure exposed in `sensor_value_master_matrix_stage4.json`/`architecture_evidence_handoff_stage4.json` as though governing | Applicable to future ingestion — files don't exist here yet; current active docs/checker already correctly frame the figure as historical (see Investigation below) | Added `ExperimentCompletionState.HISTORICAL_CAPACITY_CONFOUNDED`; added `assert_not_governing_marginal_evidence()`, wired into `build_two_arm_comparison_narrative()`; added to `_INCOMPLETE_EVIDENCE_STATES` so `validate_claim_against_entry()` also rejects it. No new science number invented — governing comparison remains `results/ppg_dalia_capacity_control.json` (A_cap→B ≈0.605 bpm), cited but not copied/hardcoded. | `backend/app/schemas/experiment_manifest.py`, `backend/app/research/future_science_ingestion.py` | `backend/tests/test_codex_delta_hardening_guards.py` (5 tests: not headline-eligible, guard raises, narrative refuses either arm, claim validator rejects) | None — this is a consumer-side guard only; the confounded figure already lives only in historical docs Science Owner does not need to touch | **MITIGATED** |
| **MEDIUM**: HMC split provenance (`split_source` points to superseded pilot split despite training using `hmc_split_stage3_bounded_n7.json`) | Applicable to future ingestion — file doesn't exist here yet | Added `ProvenanceRecord.declared_split_source`; `assert_split_provenance_consistent()` fails `PROVENANCE_MISMATCH` when declared ≠ embedded (`subject_split_manifest_path`) | `backend/app/schemas/experiment_manifest.py`, `backend/app/research/future_science_ingestion.py` | `backend/tests/test_codex_delta_hardening_guards.py` (mismatch fails, match passes, one-sided is not falsely flagged) | Repair the source artifact's `split_source` pointer to the correct bounded-n7 split when handed off | **MITIGATED** (guard ready) |
| **MEDIUM**: HMC chronology overclaim ("before any HMC file was opened/downloaded" vs. verified-only "before bounded training/evaluation"); "preregistered" without justification | Applicable — no current live-surface violation found, but no prior guard existed either | Extended `ml/check_claim_consistency.py` FORBIDDEN list with both patterns | `ml/check_claim_consistency.py` | `ml/tests/test_claim_consistency_checker.py` (regex catches synthetic bad examples; live repo scan passes) | Use the accurate chronology phrasing in any future HMC handoff doc | **MITIGATED** |
| **MEDIUM**: GalaxyPPG/LBNP provenance level (official metadata verified ≠ local raw file hash/structure verified) | Applicable to future ingestion | Added `RawDataProvenanceLevel` enum (`OFFICIAL_METADATA_VERIFIED`/`LOCAL_RAW_REPORTED_ONLY`/`ACTUAL_FILE_VERIFIED`/`TRAINING_PENDING`) on `ProvenanceRecord`; `assert_raw_provenance_not_overstated()` rejects any non-`ACTUAL_FILE_VERIFIED` level being displayed as file-verified; survives into `ManifestEntryDisplayProjection` | `backend/app/schemas/experiment_manifest.py`, `backend/app/research/future_science_ingestion.py` | `backend/tests/test_codex_delta_hardening_guards.py` (3 non-verified levels rejected, ACTUAL_FILE_VERIFIED passes, level survives to projection) | Populate the real level once GalaxyPPG/LBNP Stage-3 delta lands | **MITIGATED** |
| **MEDIUM**: status vocabulary (`CANONICAL_UNCHANGED`, `SCIENCE_COMPLETE`, arbitrary self-promotion) | Applicable — no violation found on this branch, but the allowlist needed the specified members | Added `NONCANONICAL`, `REPORTED_COMPLETE`, `VERIFIED_COMPLETE`, `ACCEPTED_FOR_SCOPE`, `HISTORICAL_CAPACITY_CONFOUNDED` to the closed `ExperimentCompletionState` StrEnum (structural allowlist — unlisted strings fail `UNKNOWN_STATUS`). Added a matching claim-checker pattern for `CANONICAL_UNCHANGED`/`SCIENCE_COMPLETE` as defense-in-depth on prose surfaces. | `backend/app/schemas/experiment_manifest.py`, `ml/check_claim_consistency.py` | `backend/tests/test_codex_delta_hardening_guards.py` (`CANONICAL_UNCHANGED`/`SCIENCE_COMPLETE` rejected at both `validate_manifest_dict` and direct Pydantic construction; new allowlist members validate) | None — allowlist is enforced structurally regardless of what Science Owner writes | **MITIGATED** |
| **MEDIUM**: freeze-manifest CRLF/LF hash sensitivity (raw-byte vs. canonical-text) | Not remediating the Science Owner's manifest (out of scope this sprint); audited Stage-4's own hashing for the same flaw | No Stage-4 hashing existed before this sprint. The new checkpoint `sha256` field is explicitly raw-byte-only (binary files have no text-normalization ambiguity) with `HashKind` recorded. Added a separate `compute_raw_byte_sha256`/`compute_canonical_text_sha256` pair so any future text-based freeze artifact can be hashed with explicit, non-interchangeable kind metadata. | `backend/app/schemas/stage4_science_guards.py`, `backend/app/research/stage4_science_guards.py` | `backend/tests/test_checkpoint_identity_resolution.py::test_raw_byte_vs_canonical_text_hash_are_genuinely_distinct` | Fix the actual freeze manifest's CRLF/LF sensitivity (Science Owner scope, not touched) | **MITIGATED** (Stage-4-owned hashing only; Science Owner's manifest untouched) |
| **MEDIUM**: environment record inheritance (later result assumed reproducible via old Day-8 environment manifest) | Applicable to future ingestion | Added `EnvironmentProvenanceStatus` (`COMPLETE`/`INCOMPLETE`), fail-closed default `INCOMPLETE` on `ProvenanceRecord`; surfaced on the display projection | `backend/app/schemas/experiment_manifest.py`, `backend/app/research/future_science_ingestion.py` | `backend/tests/test_codex_delta_hardening_guards.py::test_missing_environment_provenance_defaults_to_incomplete_not_silently_complete` | Attach each future result's own environment provenance | **MITIGATED** |
| **MEDIUM**: cache provenance (weak filename-only cache binding hidden) | Applicable to future ingestion | Added `ProvenanceRecord.provenance_warnings: list[str]`, carried through to the display projection unmodified/unhidden | `backend/app/schemas/experiment_manifest.py`, `backend/app/research/future_science_ingestion.py` | `backend/tests/test_codex_delta_hardening_guards.py::test_provenance_warnings_are_never_hidden_in_display_projection` | Populate real cache-provenance warnings for PPG/PTT loaders (Science Owner scope; loaders not touched) | **MITIGATED** |
| **MEDIUM**: stale architecture handoffs (HMC-on-another-line, GalaxyPPG-still-blocked assumed authoritative) | Applicable to future ingestion | Added `ArtifactSupersessionHeader` (`source_version`, `source_sha`, `generated_at`, `superseded_by`) + `resolve_authoritative_artifact()`: returns the single non-superseded candidate, never assumes list/file-system order is meaningful, fails closed on all-superseded or ambiguous-non-superseded | `backend/app/schemas/stage4_science_guards.py`, `backend/app/research/stage4_science_guards.py` | `backend/tests/test_checkpoint_identity_resolution.py` (3 tests: stale superseded correctly, all-superseded fails, ambiguous-non-superseded fails) | Tag real architecture handoff artifacts with this header when produced | **MITIGATED** |
| **LOW**: Digital Twin present-tense "learns a personalized baseline" wording | Direct — found and fixed on `/digital-twin` page | Reworded from "would learn a personalized baseline over the first 48–72 hours, then continuously track..." to "is designed to support future personalized-baseline learning... when sufficient longitudinal subject-specific data are available." Removed the unsourced "48–72 hours" precision claim. Added a general present-tense-learns-baseline pattern to the claim checker as a regression guard. | `frontend/src/app/digital-twin/page.tsx`, `ml/check_claim_consistency.py` | `ml/tests/test_claim_consistency_checker.py` (pattern catches synthetic present-tense example; live repo scan passes) | None | **FIXED** |

## Investigation note: why several findings show no current live-surface violation

Neither `results/sensor_value_master_matrix_stage4.json`,
`results/architecture_evidence_handoff_stage4.json`, nor
`results/hmc_split_stage3_bounded_n7.json` exist on
`stage4-engineering-integration-prep` — Codex audited the separate
`stage2-4-science-owner-completion` branch, which has not been merged here.
Verified independently: `docs/FURKAN_PAPER_HANDOFF_DAY7.md`,
`docs/FURKAN_PAPER_SUPPORT_DAY8.md`, and
`docs/FURKAN_PAPER_HANDOFF_CANONICAL_DAY9.md` already correctly frame the
old ~23% figure as historical/single-seed and explicitly forbid citing it;
`ml/check_claim_consistency.py` already had a live forbidden pattern for it
(`r"\b23\s*%\s*(pure|imu)"`) before this sprint. `CANONICAL_UNCHANGED` and
`SCIENCE_COMPLETE` do not appear anywhere on this branch. This sprint's job
was therefore prospective: build the guard rails now so that when the
Science-Owner branch's problematic artifacts are eventually integrated
(after Stage-3 delta verification), these specific failure modes cannot
recur.

## Hostile self-review

Searched for: filename-only checkpoint lookup (none found, including in the
new guard code itself); the ~23% PPG headline on any live surface (only
appears in historical docs already correctly framed, and in this sprint's
own guard-function docstrings citing it as the example the guard exists
for — verified those docstring lines carry negation/historical markers on
the same line, so the claim checker does not and should not flag them);
stale `CANONICAL` language (none active); wrong HMC split pointer
consumption (guard built, not yet wired to any real artifact since none
exists here); preregistration-like HMC wording (none active); Galaxy/LBNP
verification overstatement (none active); present-tense Digital Twin
personalization (found and fixed, one instance); unknown→zero (none
introduced — `sha256`, `raw_data_provenance_level`, and
`declared_split_source` are all `str | None` with `None` meaning genuinely
unknown, never coerced); final-architecture leakage (none — no new code
touches `final_architecture_status`/`formal_pareto_status`).

One self-inflicted false positive was found and fixed during this sprint:
this document's own line-wrapped docstring in
`backend/app/schemas/experiment_manifest.py` split "must never" and
"CANONICAL_UNCHANGED" across two physical lines, defeating the checker's
same-line negation-exemption check. Reflowed to one line; re-verified clean.

No BLOCKER or HIGH findings remain unmitigated.

## Test matrix

| Suite | Result |
|---|---|
| Backend full suite | 269/269 passed (231 prior + 38 new) |
| ML full suite | 307 passed, 19 skipped (299 prior + 8 new; skips are legitimate dataset/checkpoint absence) |
| Frontend `tsc --noEmit` | clean |
| Frontend `eslint .` | clean |
| Frontend `next build` | succeeds, 12/12 static pages |
| Claim checker | `STRUCTURED_TRACEABILITY_AND_FORBIDDEN_PATTERN_CHECK_PASS` |

No model training was performed at any point in this sprint.

## Readiness wording

Per the governing prompt's exact distinction:

> Stage-4 integration infrastructure is ready.
> Stage-3 scientific inputs remain pending completion and/or delta verification.

`stage4-engineering-integration-prep` may be described as
`READY_FOR_CONTROLLED_SCIENCE_INTEGRATION_AFTER_STAGE3_SCIENCE_AND_DELTA_VERIFICATION`.
The science branches themselves (`stage2-4-science-owner-completion`,
`next-science-expansion-sprint`) are **not** described as accepted/canonical
integration inputs by this document or any artifact this sprint touched.
