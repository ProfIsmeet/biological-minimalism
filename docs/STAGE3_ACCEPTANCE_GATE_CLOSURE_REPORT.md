# Stage 3 — Acceptance Gate Closure Report

Branch `stage3-acceptance-gate-closure`, base
`stage3-final-governance-freeze-closure @ 55de743cb45d3f74a6c39db3a11e0d73c616282b`.
No science retrained, reevaluated, or numerically changed.

## The three open gates

The final acceptance audit found Gates 3 (resolver), 4 (freeze), and 5
(current narratives) still open, despite the science itself (Galaxy
HIGH-01/HIGH-02, LBNP v2 execution) being valid.

## Gate 3 — Resolver

**Defect**: `resolve_governing_path()` trusted the registry's `GOVERNING`
label alone. A tampered registry could relabel the historical LBNP result
as governing and the resolver would accept it.

**Fix**: added an `artifact_status_contract` to the registry declaring,
per artifact, either a `status_field` (a JSON key the resolver re-reads
live from the artifact's own content) or a registry-asserted
`artifact_semantic_status` fallback (explicitly weaker, disclosed as
such). `resolve_governing_path()` now performs the registry check AND an
independent semantic content check; either failing blocks resolution.

**Verified**: relabeling the old LBNP result as sole `GOVERNING` still
fails — its own `status` field says `HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL`.
Same defense verified for both invalidated Galaxy results (added real
`status: INVALIDATED_BY_REFERENCE_SIGNAL_QUALITY_DEFECT` fields), the
noncanonical Sleep reproduction (`status: NONCANONICAL_REPRODUCTION_PENDING_ISMET_REVIEW`),
and the bounded Galaxy diagnostic (`status: SUPPORTING_BOUNDED_DIAGNOSTIC`).

**`resolve_and_verify()`** implemented: resolves governance, then
recomputes the artifact's line-ending-normalized hash and compares
against the frozen manifest entry, raising `IntegrityVerificationError:
HASH_MISMATCH` on any difference. Verified against a real file: corrupted
`lbnp_thoracic_eis_stage3_v2_protocol_compliant.json`'s `A_mean`, confirmed
resolution failed, then restored the file byte-for-byte.

## Gate 4 — Freeze

**Defect**: the freeze builder silently omitted a family from
`governing_artifacts` if it had zero governing entries — a fail-open bug
in a system whose entire purpose is fail-closed governance.

**Fix**: `build_stage3_scientific_freeze_manifest.py` now HARD FAILS
(`FreezeBuildError`) if any registry family has zero or more than one
`GOVERNING` artifact. Verified with temp-registry probes for both cases.

**Cross-cutting docs**: `docs/STAGE3_SAFE_UNSAFE_CLAIMS.md` and
`docs/STAGE3_HANDOFF_TO_EMIR_AND_INTEGRATION_OWNER.md` are no longer
manually appended via a `CROSS_CUTTING_DOCS` list — they are now their
own governed families (`stage3_claims`, `stage3_handoff`), resolved,
frozen, and hash-verified identically to any result artifact.

**Family count**: registry actually contains **21** families (not the
previously-documented 18) — read dynamically via
`freeze["required_families_count"]` everywhere rather than hard-coded.

## Gate 5 — Current narratives

`docs/STAGE3_HANDOFF_TO_EMIR_AND_INTEGRATION_OWNER.md`'s opening "What is
COMPLETE" section was rewritten in place (not appended-to) to state
`COMPLETE_MIXED` with the full corrected values and sign-sensitivity
disclosure directly. The document was searched top-to-bottom for
`COMPLETE_NEGATIVE`, "stable negative", or old numbers presented as
current — the only remaining hits are inside explicit "do not cite"
prohibitions, not assertions. `docs/STAGE3_SAFE_UNSAFE_CLAIMS.md`'s HMC
section: removed the `[N]` placeholder (replaced with the real
59/58/52/1-partial breakdown) and the stale "cert renewal pending"
wording (access is confirmed restored); `results/sensor_value_master_matrix_stage3_complete.json`'s
HMC row had the same stale cert-blocking wording in `replication_state`
and `limitations` — fixed.

## Self-caught regression (disclosed, not hidden)

While adding real `status` fields to known-bad artifacts, two target
files (`results/sensor_marginal_value_contract.json`,
`results/sleep_edf_interaction_resp_day10.json`) turned out to be tracked
by the historical Day-14 freeze manifest. Modifying them broke that
manifest's frozen hashes and was caught immediately by the existing test
suite. Both files were reverted byte-for-byte before commit; their
registry entries use a registry-only `artifact_semantic_status` instead.

## Gate self-check

| Gate | Status |
|---|---|
| 1 — LBNP | PASS (unregressed: A=20.972675, B=21.425060, C=20.131778, `COMPLETE_MIXED`) |
| 2 — Galaxy | PASS (unregressed: A_cap-B=+0.834268, C-B=+0.916231) |
| 3 — Resolver | **CLOSED**: semantic content verification + hash integrity, both implemented and tested |
| 4 — Freeze | **CLOSED**: hard-fail on zero/duplicate governing, registry-derived, cross-cutting docs governed |
| 5 — Narratives | **CLOSED**: handoff opening section corrected directly, no internal contradiction |
| 6 — Pending work | HMC/ds003838 full cohort unchanged, `FULL_COHORT_PENDING`; architecture `UNRESOLVED` |

## Tests

Static inventory before this sprint: **526**. Tests added this sprint:
**13** (`test_stage3_gate3_semantic_and_integrity.py` 9,
`test_stage3_gate4_freeze_hard_fail.py` 4). Static inventory after: **539**.
Executed: **539 collected, 539 passed, 0 failed, 0 skipped, 0 collection errors.**

## Science non-regression

Confirmed byte/value-identical to base: Galaxy A_cap-B=+0.834268,
C-B=+0.916231; LBNP A=20.972675, B=21.425060, C=20.131778,
classification `COMPLETE_MIXED`.

## Remaining carried limitations

- PPG/PTT cache provenance — unchanged `CARRIED_LIMITATION`.
- HMC full-cohort training, ds003838 full-cohort — untouched,
  `FULL_COHORT_PENDING`.
- 6 HMC complete recording pairs remain SHA256-unverified this sprint.
- Historical Mac-reproduction checkpoint bytes remain unavailable in this
  repository (gitignored, generated on a separate machine).

## Architecture

`FINAL_ARCHITECTURE = UNRESOLVED`. `FORMAL_PARETO = NOT_READY`. Verified
directly after every edit this sprint.

## Verdict

`STAGE3_FIXED_ACCEPTANCE_GATES_REPORTED_CLOSED_PENDING_FINAL_INDEPENDENT_ACCEPTANCE`
