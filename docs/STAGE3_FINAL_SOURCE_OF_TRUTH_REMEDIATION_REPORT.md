# Stage 3 — Final Source-of-Truth Remediation Report

Branch `stage3-final-source-of-truth-remediation`, base
`stage3-codex-fail-remediation @ 64181cf7754a3f919db87e694bc7ed411c0f2532`.
Remediates the second independent Codex re-audit's `FAIL` verdict: HIGH-01
and HIGH-02 were confirmed CLOSED and the corrected LBNP execution itself
was confirmed valid, but stale governing references to the superseded
LBNP result remained active in integration-facing artifacts.

## LBNP source-of-truth

**Governing result**: `results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json`
- n=12 eligible, 0-60 mmHg frozen scope enforced (407/607 in-scope
  windows, 200 excluded), different-stage C-control (0 collisions).
- A=20.973, B=21.425, C=20.132 mmHg MAE.
- A_minus_B=-0.452 (3/12 favor B) — **sign-reverses** excluding subject 9.
- C_minus_B=-1.293 (5/12 favor B) — remains negative but **shrinks
  substantially** excluding subject 9.
- **Classification: `COMPLETE_MIXED`** (revised from `COMPLETE_NEGATIVE`
  — a uniform-negative label overstated the finding's stability given
  both key comparisons are substantially subject-9-influenced).

**Superseded result**: `results/lbnp_thoracic_eis_stage3.json`, status
`HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL`, carries an explicit
`governing_evidence_note` forbidding its consumption as current evidence.
Preserved unchanged, never deleted.

## Stale artifacts fixed

| File | Old state | New state |
|---|---|---|
| `results/architecture_evidence_handoff_stage4.json` | thoracic-EIS candidate cited A-B=-2.24, `COMPLETE_NEGATIVE` | Cites A-B=-0.452/C-B=-1.293, `COMPLETE_MIXED`, sign-reversal disclosed |
| `results/sensor_value_master_matrix_stage3_complete.json` | LBNP row: A=27.62/B=29.86/C=29.83, subjects 4/7, `COMPLETE_NEGATIVE` | A=20.973/B=21.425/C=20.132, subjects 4/9, `COMPLETE_MIXED`, old run marked superseded |
| `results/stage3_galaxyppg_lbnp_consolidated_provenance.json` | `eis_result` pointed to old 607-window file as current | Points to v2 protocol-compliant result, old file explicitly marked historical |
| `results/stage3_science_completion_manifest.json` | `replication_class: COMPLETE_NEGATIVE`; HMC `actual_biological_n: 59` (file-presence, mislabeled as recording count); `test_suite: 482` | `replication_class: COMPLETE_MIXED`; HMC `actual_biological_n: 58` (complete recording pairs); `test_suite: 500` |
| `results/galaxyppg_hr_corrected_eligibility_stage3.json` | `scope_disclosure` said stale pre-correction "16/4/4" split | Corrected to the real "12/3/3" split actually used |
| `docs/STAGE3_SAFE_UNSAFE_CLAIMS.md` | LBNP safe/unsafe claims cited old numbers/classification | Rewritten with corrected numbers, `COMPLETE_MIXED`, and explicit unsafe-claim list per the master prompt |

## HMC current state (three-way reconciliation)

Per `results/hmc_current_download_inventory.json`:
- **59** `.edf` files present on disk.
- **58** complete recording pairs (edf + annotation) — SN060 is a partial
  download (missing annotation, file size far below the complete range).
- **52** of those 58 SHA256-verified against PhysioNet's own
  `SHA256SUMS.txt` (unchanged from a prior sprint's checkpoint — **not**
  re-verified this sprint, explicitly out of scope). 6 complete pairs
  remain un-re-verified this sprint.
- No download or verification work performed. `actual_biological_n: 58`
  is now used consistently (the defensible "complete recording" count,
  not the looser file-presence count).

## Test count

Reconciled to **500 passed, 0 failed, 0 skipped** (confirmed by direct
re-run; the prior 482-vs-486 inconsistency traced to
`stage3_science_completion_manifest.json` simply not having been updated
after the prior sprint's final test additions; this sprint added 20 more
tests on top of the reconciled 486).

## Freeze

New/updated `results/stage3_scientific_freeze_manifest.json` regenerated
**after** all source-of-truth fixes landed (per Section 15's explicit
ordering requirement), with an added `governing_artifacts` field
declaring exactly which file is current for each dataset (LBNP, Galaxy,
HMC, Stage-3 manifest), plus a historical-superseded pointer for LBNP.
`test_stage3_final_freeze_self_consistency.py` (5 tests) enforces this
programmatically: hashes all match current content, all governing
artifacts exist and are tracked, and no artifact whose own `status` field
says HISTORICAL/SUPERSEDED can be declared a non-historical governing
pointer.

## Remaining carried limitations

- HMC full-cohort training, ds003838 full-cohort — unchanged,
  `PENDING_DUE_TO_COMPUTE_OR_SESSION_LIMIT`, untouched this sprint.
- 6 HMC recording pairs remain SHA256-unverified this sprint (disclosed,
  not silently assumed verified).
- PPG/PTT cache provenance — unchanged `CARRIED_LIMITATION`.
- Section 27's full provenance-field expansion and Section 30's
  quarantine-history re-audit — the latter searched this sprint and found
  no live claim requiring correction; the former remains `PARTIAL` from
  the prior sprint, not re-attempted.

## Architecture

`FINAL_ARCHITECTURE = UNRESOLVED`. `FORMAL_PARETO = NOT_READY`. Verified
unchanged after every edit this sprint.

## Verdict

`STAGE3_FINAL_SOURCE_OF_TRUTH_REMEDIATION_REPORTED_COMPLETE_PENDING_INDEPENDENT_REAUDIT`
