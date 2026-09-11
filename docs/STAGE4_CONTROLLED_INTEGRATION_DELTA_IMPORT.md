# Stage 4 Controlled Integration — Delta Import Record

Branch: `stage4-controlled-integration`, created from `stage4-engineering-integration-prep @ a656fb98e3601617291fe55c6e0fc590a0058f43`.

This record supersedes the "NOT MET" status of preconditions #1/#2/#4/#9/#10 in
`docs/STAGE4_CONTROLLED_INTEGRATION_READINESS_CONTRACT.md`: `PROJECT_COORDINATOR`
(Emir) has explicitly authorized controlled Stage-4 integration against the
independently-accepted Stage-3 SHA below (coordinator state
`STAGE3_CORE_AND_PRIORITY_SCOPE_VERIFIED_COMPLETE_WITH_LOWER_PRIORITY_EXTERNAL_WORK_PENDING`,
`CONTROLLED_STAGE4_INTEGRATION_AUTHORIZED`). That older contract's precondition
table describes state as of the prior sprint and should be read as historical
context, not current status.

## What was NOT done

No blind whole-branch merge of `stage3-gate3-final-resolver-closure` was
performed. Instead: (1) a read-only reconnaissance pass listed every file on
that branch (632 tracked files) and classified them by directory; (2) the
Stage-3 scientific freeze manifest's own 31-entry file list was used as the
authoritative "what does Stage-3 say is load-bearing for current science"
set; (3) only those 31 files, the resolver module, and the resolver/freeze
governance test suite were copied via `git show <sha>:<path>`, never
`git merge`/`git cherry-pick` of the branch itself.

Explicitly excluded: `datasets/` (README/audit docs only, no raw data —
raw data is gitignored on both branches), `ml/checkpoints/` (gitignored,
no binaries tracked), `ml/experiments/` (23 experiment-authoring
files/figures), `ml/datasets/` (15 training-time dataset loader modules),
`ml/train_*.py` / `ml/verify_*_reproducibility.py` (training scripts),
`results/figure_sources/` and `results/paper_tables/` (paper-production
artifacts derived from governing evidence, not governing evidence
themselves), and all other `ml/tests/*` files not directly testing
resolver/governance/freeze behavior.

## Accepted Stage-3 reference

- Branch: `stage3-gate3-final-resolver-closure`
- SHA: `5c381014af61e5d10d41223963831b25b9ff23e6` (confirmed exact match to
  `origin/stage3-gate3-final-resolver-closure`)
- Merge-base with `stage4-engineering-integration-prep`: `0e03c63729ce7a1e374edd978ef55f9edd45f435`
  (the two lineages diverged here; this integration is a controlled cherry-pick
  of specific files, not a merge of divergent history)

## Files imported (via `git show <sha>:<path>`, byte-identical to Stage-3)

Governance/resolver infrastructure:
- `results/stage3_governance_registry.json`
- `results/galaxyppg_invalidated_evidence_registry.json` (supplementary blocklist)
- `ml/stage3_science_resolver.py` (public API: `resolve_current`, `resolve_and_verify`,
  `resolve_governing_path`, `resolve_by_path_or_status`, `list_families`; the private
  `_resolve_current_unverified` helper exists in the file but is never imported or
  called by any Stage-4 code — enforced by
  `backend/tests/test_stage3_evidence_bridge.py::test_bridge_never_imports_the_private_unverified_helper`)
- `ml/build_stage3_scientific_freeze_manifest.py`

The 31 freeze-manifest-tracked artifacts, all governing + tracked
historical/supporting per the registry: `architecture_evidence_handoff_stage4.json`,
`ds003838_eeg_minimalism_stage3_bounded_diagnostic.json`, `stage3_environment_snapshot.json`,
`galaxyppg_corrected_eligibility.json`, `galaxyppg_reference_ecg_qc.json`,
`galaxyppg_eligibility_stage2.json`, `galaxyppg_corrected_full_cv_result.json`,
`galaxyppg_hr_corrected_eligibility_stage3.json`, `galaxyppg_hr_external_replication_stage2.json`
(INVALIDATED, imported only so the registry/freeze/resolver can enforce it never
resolves as governing), `galaxyppg_hr_full_grouped_cv_stage3.json` (INVALIDATED, same
reason), `hmc_sleep_external_replication_stage3_bounded_n7.json`,
`hmc_current_download_inventory.json`, `lbnp_target_stage_inventory.json`,
`lbnp_thoracic_eis_stage3_v2_protocol_compliant.json` (GOVERNING),
`lbnp_thoracic_eis_stage3.json` (HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL, imported only
for the same fail-closed enforcement reason), `qde_v2_leg_bioz_stage2.json`,
`sensor_value_master_matrix_stage3_complete.json`, `sleep_v2_checkpoint_accepted_mapping.json`,
`sleep_edf_interaction_resp_seedfix_v2.json` (GOVERNING),
`claude_noncanonical_sleep_edf_primary_seedfix_v2_reproduction.json` (NONCANONICAL_REPRODUCTION),
`sleep_edf_shuffled_eog_control_seedfix_v2.json`, `docs/STAGE3_SAFE_UNSAFE_CLAIMS.md`,
`stage3_science_completion_manifest.json`, `stage3_galaxyppg_lbnp_consolidated_provenance.json`,
`docs/STAGE3_HANDOFF_TO_EMIR_AND_INTEGRATION_OWNER.md`, `results/stage3_scientific_freeze_manifest.json`
(then regenerated in place — see below).

Already present and verified byte-identical to Stage-3 before import (no action
needed): `results/ppg_dalia_capacity_control.json`, `results/ptt_ppg_site_ablation.json`,
`results/sleep_edf_primary_seedfix_v2.json`, `results/sleep_edf_interaction_resp_day10.json`.

Resolver/governance test suite imported (59 tests, all passing):
`test_stage3_governance_resolver.py`, `test_stage3_governance_hostile_probes.py`,
`test_stage3_governance_freeze_consistency.py`, `test_stage3_gate3_final_resolver_closure.py`,
`test_stage3_gate3_semantic_and_integrity.py`, `test_stage3_gate4_freeze_hard_fail.py`,
`test_stage3_codex_h_freeze_manifest_hash_semantics.py`, `test_stage3_codex_fail_new_freeze_manifest.py`.

## One documented, non-blocking freeze-manifest divergence

`results/sensor_marginal_value_contract.json` is a HISTORICAL (never-governing)
artifact. This integration branch's own prior lineage had already enriched its
content (added a lower-is-better vs higher-is-better sign-convention
clarification, and a cross-reference to the Day-10 Sleep-EDF interaction
result) after the point where Stage-3's snapshot was taken — this is not new
science and not a change made during this sprint, it predates this branch. The
Stage-3 freeze manifest's hash for this one non-governing entry therefore does
not match current on-disk content. Rather than overwrite the richer local
content with Stage-3's older snapshot, or weaken the imported freeze-consistency
test, `ml/build_stage3_scientific_freeze_manifest.py` (Stage-3's own,
unmodified builder) was re-run against current disk state. The regenerated
manifest is byte-for-byte identical to Stage-3's in every governance-relevant
field (`governing_artifacts`, `required_families`,
`historical_or_supporting_artifacts`) — only this one non-governing entry's
hash changed to match current content. This does not affect `resolve_current()`
for any family: hash verification only applies to the GOVERNING path per
family, never to historical/supporting entries.

## Verification performed

- All 21 registry families resolve successfully through `resolve_current()`.
- 59/59 imported resolver/governance tests pass (hostile probes: historical
  LBNP, invalidated GalaxyPPG, noncanonical Sleep, zero/duplicate governing,
  hash-corrupted content all correctly fail closed).
- Cross-checked every extracted numeric value in the new
  `backend/app/research/stage3_evidence.py` bridge against the governing
  prompt's own stated values (GalaxyPPG +0.834/+0.916 bpm, PPG-DaLiA
  +0.605/+0.776 bpm, Sleep B-A +0.0282, LBNP -0.452/-1.293, HMC n=7/151) —
  all match exactly, live from the resolved artifacts, not copied from the prompt text.

## Claim-ledger staleness found and fixed (integration bug, not a science change)

Three pre-existing claims in `results/claim_traceability.json` cited
pre-seedfix-V2 Sleep-EDF files (`sleep_edf_eeg_eog_ablation.json`,
`sleep_edf_interaction_resp_day10.json`, `sleep_edf_eeg_eog_control_analysis.json`)
with their old, superseded numbers instead of the now-governing
`*_seedfix_v2.json` files and numbers. Repointed all three to the governing
artifacts with the corrected values (qualitative conclusions unchanged in all
three cases — this is a provenance-pointer fix, not a reinterpretation).
`sleep-secondary-holdout` and `sleep-n3-regression` were deliberately left
untouched: their source artifact (`sleep_edf_secondary_holdout_evaluation.json`)
is not one of the 21 Stage-3 registry families, so there is no accepted
governing replacement to point them to — flagged here for Ismet/Emir rather
than resolved unilaterally.

Five new claims were added for the newly-integrated families (GalaxyPPG, LBNP,
QDE, HMC, ds003838), each sourced from the governing artifact and the new
`/research/stage3-evidence/{family_id}` API surface.
`ml/check_claim_consistency.py`'s static `KNOWN_ROUTES` allowlist was updated
to include the two new routes (it does not auto-discover routes from
`research.py`); the checker passes cleanly after the update.
