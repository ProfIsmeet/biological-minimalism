# Day-12 Audit Remediation Handoff

**Branch:** `day12-audit-remediation` (off `origin/day11-canonical-integration` @169f99d)
**Status:** REMEDIATION CANDIDATE — pushed, NOT merged to main/final.
**Scientific freeze:** `SCIENTIFIC_FREEZE_HOLD_PENDING_H1_H2` (Ismet owns H1/H2).

Machine-readable companions:
- `results/audit_remediation_status_day12.json` — per-finding status (§52)
- `results/cross_layer_consistency_matrix_day12.json` — 16 rows × 5 layers, all resolve (§43)

## 1. Ismet support integrated (additive-only)

Merge `2ce0989` (`--no-ff` of support tip `f2d895e`). Tree vs canonical = 58 new files +
4 CRLF/UTF-8-fix files, **0 deletions, 0 rewrites** of existing engineering/scientific
canonical artifacts. Deliberately did **not** fast-forward through the scientific-parallel
branch (which deletes the Day-11 engineering integration). Brought: CRLF backend hash fix,
UTF-8 test encoding fixes, `ml/engineering/ppg_led_power.py`, 60-checkpoint inventory,
arithmetic/integration-map/visual-integrity JSONs, reproduction docs, figure sources, paper
tables, sensitivity analyses, audit docs. **No H1/H2 outcomes.**

## 2. Fixed findings (Claude-owned)

All 4 high (H3, H4, H5, H7) + medium/low (M1, M2, M4, M5, M6, M7, M8, M9, M10, M11, M12,
M15, M20, M30, M3, L1) — see the status JSON for per-finding commit/tests/limitation.
Highlights:

- **H3** artifact-driven reproduction, typed component statuses, no default PASS.
- **H4** typed engineering `Quantity`, no unknown→0 / 48068 fallbacks.
- **H5/M15** capacity-controlled PPG headline (0.605 bpm), historical demoted, per-comparison stats.
- **H7** power reference scenario (not guaranteed lower bound), propagated all layers.
- **M4** claim checker relabeled + mechanical field/route validation; 12 broken traceability refs fixed.
- **M9** verifier + archive exit codes and guards.
- **M10** Torch mock-passthrough honesty + Digital Twin conditional wording.
- **M12** optional research panels load in isolation.
- **M2** documented hash policy; fixed a pre-existing platform-dependent freeze-manifest hash test.

## 3. Remaining H1/H2 (Ismet)

`DEFERRED_TO_ISMET_H1_H2`. Do not finalize scientific freeze, rewrite Sleep metrics, or
change interaction metrics until `CLAUDE_H1_H2_SCIENTIFIC_REMEDIATION_HANDOFF.md` lands.
M5 added rate-class **schema support** but left all Resp values to Ismet.

## 4. New / changed canonical source paths

- New: `results/audit_remediation_status_day12.json`, `results/cross_layer_consistency_matrix_day12.json`,
  `docs/HASH_PROVENANCE_POLICY.md`, `docs/TEST_TAXONOMY.md`, `docs/AUDIT_REMEDIATION_HANDOFF_DAY12.md`.
- Regenerated from builders (fix-at-source): `results/reference_power_budget_day11_part2.json`,
  `results/reference_data_rate_budget_day11.json`, `results/day11_part3_engineering_inputs.json`,
  `results/pareto_blocker_progress_day11_part2.json`, `results/sensor_marginal_value_contract.json`,
  `results/pareto_decision_inputs.json`, `results/scientific_freeze_manifest_day14.json`.
- Edited: `results/claim_traceability.json` (12 refs).

## 5. UI changes (frontend)

- `ResearchMode.tsx`: status-dependent reproducibility panel; controlled-comparisons block
  (HEADLINE/HISTORICAL); deltaClass direction-only.
- `EngineeringReadinessView.tsx`: `QuantityValue` renders UNKNOWN as amber "Unknown", never 0.
- `digital-twin/page.tsx`: conditional "would learn / simulated, not learned".
- `store/researchStore.ts`: isolated optional-panel loading.
- `lib/types.ts`: new `ReproComponent`, `EngineeringQuantity`, `ControlledComparison` types.
- `tsc --noEmit` clean, `eslint` clean, `next build` succeeds.

## 6. Traceability changes

`ml/check_claim_consistency.py` now (a) resolves each `source_field` dotted path inside its
artifact, (b) validates `api_surface` against known routes, (c) prints
`STRUCTURED_TRACEABILITY_AND_FORBIDDEN_PATTERN_CHECK_PASS` with an explicit
paraphrase/existence limitation. All 26 claims resolve.

## 7. Archive status

`archival/checkpoints_day8/` historical archive is untouched. `build_checkpoint_archive.py`
now refuses to overwrite it without `BIOMIN_ARCHIVE_OVERWRITE=1` and fails closed on
empty/collision/missing/mismatch/leaked-dataset. 60-checkpoint inventory integrated.

## 8. Test results

- Backend: **145 passed** (`backend/.venv/bin/python -m pytest`).
- ML (non-training): **273 passed, 21 skipped** (skips need real datasets).
- Frontend: tsc clean, eslint clean, `next build` OK. No configured test runner (§42).
- Claim checker: PASS. Decision-inputs verification: PASS.
- Adversarial fixtures added: reproduction empty/malformed/failed/partial; engineering
  missing/null/malformed; archive empty/hash-mismatch/collision; traceability nonexistent
  field/route; CRLF/LF equivalence; cache mismatch/legacy; Torch false-inference guard.

## 9. Codex re-audit instructions

- **Branch:** `origin/day12-audit-remediation` (final HEAD after this commit).
- **Start here:** `results/audit_remediation_status_day12.json` +
  `results/cross_layer_consistency_matrix_day12.json`.
- **High-risk areas to re-check:** (a) reproduction overall-status derivation cannot reach PASS
  from bad evidence; (b) engineering Quantity never renders 0 for missing; (c) PPG headline is
  capacity-controlled everywhere; (d) power wording carries no "guaranteed lower bound"; (e) the
  contract→decision-inputs→freeze-manifest SHA cascade is internally consistent on an LF checkout;
  (f) verifier/archive exit codes.
- Re-run: `backend/.venv/bin/python -m pytest`, `ml/tests`, `ml/check_claim_consistency.py`,
  `python -m app.research.decision_inputs` (from backend/).

## 10. Day-12 normal roadmap readiness

**READY_AFTER_H1_H2_AND_REAUDIT.** Do not resume normal Day-12 roadmap work until: Ismet
H1/H2 remediation lands, Codex re-audit passes on this branch, and Emir reviews. This branch
must not be merged to final canonical before then.

### Known remaining limitations (not blockers, tracked in status JSON)
- M6/M11 addressed for the headline/engineering flows; a full operand-labeling and
  hand-maintained-JSON de-duplication sweep is not exhaustive.
- M7 stamped the PPG cache; the PTT cache loader uses the same pattern but is not yet stamped.
- Frontend has no automated test runner; M12 isolation is structural + browser-validated.
