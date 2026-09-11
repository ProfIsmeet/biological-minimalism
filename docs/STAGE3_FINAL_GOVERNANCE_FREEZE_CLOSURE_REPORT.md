# Stage 3 — Final Governance & Freeze Closure Report

Branch `stage3-final-governance-freeze-closure`, base
`stage3-final-source-of-truth-remediation @ 7a7803e3316def251df20091f0a5ddfa329c3936`.
No science was retrained, reevaluated, or numerically changed this
sprint — this is a pure governance/provenance/freeze-closure sprint.

## The structural problem

A third independent audit found the freeze did not genuinely fail
closed: `governing_artifacts` was a manually maintained dict that had
let the superseded LBNP result and the Galaxy bounded diagnostic sit
alongside real governing entries, and a freeze-consistency test contained
`if "historical" in key.lower(): continue` — governance depended on key
naming, not artifact state.

## The fix: a real governance registry + resolver

- **`results/stage3_governance_registry.json`**: every artifact in every
  Stage-3 family gets an explicit `status` (`GOVERNING`, `SUPPORTING`,
  `HISTORICAL`, `SUPERSEDED`, `INVALIDATED`, `NONCANONICAL_REPRODUCTION`,
  `PENDING`, or `HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL`). 18 families, 25
  tracked artifacts.
- **`ml/stage3_science_resolver.py`**: the only code path for "what is
  the current governing result for family X" — reads the registry, fails
  closed on zero or multiple `GOVERNING` artifacts, missing files, or an
  attempt to resolve a non-`GOVERNING` path directly.
- **`ml/build_stage3_scientific_freeze_manifest.py`**: rewritten to
  *derive* `governing_artifacts` and `historical_or_supporting_artifacts`
  from the registry — no second, independently-typed governing
  definition exists anywhere.

## LBNP current surfaces

| Artifact | Governance | Classification/Status |
|---|---|---|
| `results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json` | **GOVERNING** | `COMPLETE_MIXED` |
| `results/lbnp_thoracic_eis_stage3.json` | `HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL` | non-governing, resolver fails closed |
| `docs/STAGE3_HANDOFF_TO_EMIR_AND_INTEGRATION_OWNER.md` | fixed | now states `COMPLETE_MIXED` with corrected values |
| `docs/LBNP_STAGE3_HIGH03_REMEDIATION.md` | fixed (Option A) | classification updated to `COMPLETE_MIXED` in place |
| `docs/LBNP_STAGE3_RESULTS.md` | banner-marked (Option B) | top-of-document `HISTORICAL — SUPERSEDED` banner added, content preserved below |
| `docs/STAGE3_SCIENCE_COMPLETION_REPORT.md` | fixed | `COMPLETE_MIXED`, agrees with manifest/handoff/matrix/provenance |

## Galaxy current surfaces

`galaxyppg_external_replication` family: **GOVERNING** =
`results/galaxyppg_corrected_full_cv_result.json`
(`EXTERNAL_REPLICATION_SUPPORTIVE`). The bounded single-fold diagnostic
(`results/galaxyppg_hr_corrected_eligibility_stage3.json`) is now
**SUPPORTING**, not governing — removed from `governing_artifacts`.
`docs/STAGE3_SAFE_UNSAFE_CLAIMS.md`'s GalaxyPPG section rewritten from
"pending, 24 subjects" to the current corrected-cohort, full-CV state
with the exact required safe/unsafe claim wording.

## HMC current state

Per `results/hmc_current_download_inventory.json`'s `canonical_fields`:
`edf_files_present_n=59`, `complete_recording_pairs_n=58`,
`sha256_verified_recordings_n=52`, `partial_recordings=["SN060"]`,
`planned_full_cohort_n=151`. `full_cohort_scientific_status:
FULL_COHORT_PENDING`. Bounded n=7 diagnostic status: `BOUNDED_DIAGNOSTIC`
(unaffected, remains the only trained HMC evidence). All current-facing
consumers (`sensor_value_master_matrix_stage3_complete.json`,
`stage3_science_completion_manifest.json`,
`STAGE3_SCIENCE_COMPLETION_REPORT.md`) updated to cite this breakdown
instead of a bare stale count.

## Governance resolver

18 families resolved successfully: `sleep_edf_primary_ab`,
`sleep_edf_shuffled_control_c`, `sleep_edf_interaction`,
`sleep_checkpoint_identity`, `ppg_dalia_capacity_control`,
`ptt_second_ppg_site`, `qde_v2_leg_bioz`,
`galaxyppg_external_replication`, `galaxyppg_eligibility_qc`,
`lbnp_thoracic_eis`, `lbnp_target_stage_inventory`,
`hmc_bounded_diagnostic`, `hmc_current_download_state`,
`ds003838_bounded_diagnostic`, `stage3_completion_manifest`,
`stage3_consolidated_provenance`, `architecture_evidence_handoff`,
`sensor_value_master_matrix`, `environment_provenance`.

Negative-resolution tests (all pass, `ml/tests/test_stage3_governance_resolver.py`):
old LBNP result, both invalidated pre-QC Galaxy results, and the
noncanonical Sleep Mac reproduction all raise `GovernanceResolutionError`.

## Freeze

- 32 files tracked, 19 `governing_artifacts` (down from a prior ambiguous
  set that included 2 Galaxy candidates and an LBNP historical pointer).
- All hashes regenerated after every edit landed this sprint (verified
  stable across two consecutive regenerations).
- `ml/tests/test_stage3_governance_freeze_consistency.py` (6 tests) +
  `ml/tests/test_stage3_final_freeze_self_consistency.py` (rewritten, 4
  tests, key-name-heuristic bypass removed) enforce metadata-driven
  fail-closed behavior.

## Tests

- Static inventory before this sprint: **500**.
- Tests added this sprint: **26** net new (new files:
  `test_stage3_governance_resolver.py` 17,
  `test_stage3_governance_freeze_consistency.py` 6,
  `test_stage3_governance_hostile_probes.py` 4; `test_stage3_final_freeze_self_consistency.py`
  and `test_stage3_codex_fail_new_freeze_manifest.py` were rewritten in
  place to remove the key-name-heuristic bypass, net test-count-neutral).
- Static inventory after this sprint: **526**.
- Executed: **526 collected, 526 passed, 0 failed, 0 skipped, 0 collection errors.**

## Remaining carried limitations (not pretended closed)

- PPG/PTT cache provenance — unchanged `CARRIED_LIMITATION`.
- HMC full-cohort training, ds003838 full-cohort — untouched,
  `FULL_COHORT_PENDING`.
- 6 HMC complete recording pairs remain SHA256-unverified this sprint
  (disclosed in `results/hmc_current_download_inventory.json`).
- Historical Mac-reproduction checkpoint bytes — still unavailable in
  this repository (gitignored, generated on a separate machine),
  disclosed via `byte_availability_status` fields, never fabricated.

## Architecture

`FINAL_ARCHITECTURE = UNRESOLVED`. `FORMAL_PARETO = NOT_READY`. Verified
directly after every edit this sprint — unchanged.

## Verdict

`STAGE3_FINAL_GOVERNANCE_FREEZE_CLOSURE_REPORTED_COMPLETE_PENDING_INDEPENDENT_REAUDIT`
