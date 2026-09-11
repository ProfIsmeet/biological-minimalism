# Stage 3 — Codex Fail Remediation Report

Branch `stage3-codex-fail-remediation`, base
`stage3-science-completion @ aaa87c212d2e11fa74efa601ee262c3c9d08146b`.
Remediates the independent Codex audit's `INDEPENDENT STAGE3 DELTA AUDIT
FAIL` verdict on that SHA.

## HIGH findings — all three closed

### HIGH-01: GalaxyPPG participant-level C used aligned ACC instead of deranged ACC

**Defect**: `ml/train_galaxyppg_corrected_full_cv.py`'s per-subject
breakdown (and its Fold-5 source,
`ml/build_galaxyppg_corrected_per_subject_results.py`) supplied the
aligned test ACC to `model_c` instead of the deranged test ACC used by
the always-correct fold-level C evaluation.

**Fix**: no retraining. Loaded the already-trained, already-archived C
checkpoints and re-evaluated with a correctly-reconstructed per-subject
derangement (`ml/fix_galaxyppg_participant_c_evaluation.py::deranged_acc_for_subject_at_index`,
keyed by each subject's position in `sorted(test_ids)`, matching
`deranged_acc_stable`'s own internal indexing exactly).

**Verification**: a strong-consistency check (concatenated corrected
per-participant C predictions must reproduce the fold-level C MAE)
passed with **0.00e+00 diff across all 30 fold/seed checks**
(`results/galaxyppg_high01_strong_consistency_check.json`).

**Corrected numbers**: participant-level C_to_B: +0.904 → **+0.916 bpm**
(13/18 favor B, unchanged count); window-weighted C_to_B (+0.920, always
correct) unchanged. No sign reversal. Final classification
`EXTERNAL_REPLICATION_SUPPORTIVE` unchanged. A_cap/B untouched.

**Tests**: `ml/tests/test_stage3_codex_fail_high01_galaxyppg_participant_c.py`
(5 tests, tensor-level, not string/declaration checks).

### HIGH-02: P01 eligibility not independently justified

**Defect**: the prior threshold-robustness claim ("any threshold 7-48
peaks/min gives the same 18-subject cohort") was **mathematically
false** — P01 (37.08 peaks/min) sits inside that range.

**Fix**: corrected the false claim, then built
`results/galaxyppg_reference_ecg_qc.json` — a second, independently-
designed R-peak detector (`scipy.signal.find_peaks` on raw amplitude, no
derivative/energy step) plus RR-implausibility and clipping metrics, for
all 24 real subjects, purely from raw signal/detector behavior
(`no_performance_data_used: true`).

**Adjudication (Outcome A)**: P01 fails **both** independent dimensions
— primary rate 37.08 < 40, and detector-agreement ratio 0.423 clusters
with the 5 obviously-corrupted subjects (0.001–0.408), a real 0.148 gap
below the lowest genuinely-eligible subject (P05, 0.571). P01 also has
the highest RR-implausible fraction (0.176) outside the corrupted
cluster. The composite rule (`primary_rate>=40 AND agreement_ratio>=0.50`)
reproduces the **exact same 18-subject cohort** (zero symmetric
difference) — no retraining needed.

**Tests**: `ml/tests/test_stage3_codex_fail_high02_p01_qc.py` (6 tests).

### HIGH-03: LBNP frozen 0-60 mmHg range not enforced

**Defects**: (1) the frozen protocol specifies "the 0-60 mmHg range" but
the trainer applied no filter — **200/607 windows (33%)** at 70/80/90/100
mmHg entered the reported result. (2) The frozen C-control requires a
*different stage*, not merely a different index — the original
derangement allowed 13-25% same-stage "control" windows.

**Fix**: `ml/train_lbnp_thoracic_eis_v2_protocol_compliant.py` filters to
stage≤60 before any feature construction (n=12 cohort unchanged) and
`deranged_eis_different_stage()` guarantees zero same-stage collisions
(verified programmatically, script raises if not exactly 0).

**Result**: A=20.973, B=21.425, C=20.132 mmHg MAE. A_minus_B=-0.452
(sign-sensitive to subject 9 under leave-one-out — disclosed).
C_minus_B=-1.293, **robust** under leave-one-out (the more diagnostic
comparison, since B/C share identical capacity). Classified
`COMPLETE_NEGATIVE`.

Old `results/lbnp_thoracic_eis_stage3.json` preserved unchanged, marked
`OUT_OF_PROTOCOL_SCOPE_HISTORICAL`.

**Tests**: `ml/tests/test_stage3_codex_fail_high03_lbnp_protocol_compliance.py`
(6 tests, behavioral not string-based).

## Prior HIGH/MEDIUM remediation status (this sprint's re-audit)

| Finding | Status | Evidence |
|---|---|---|
| H-01 (checkpoint namespace) | **CLOSED** (was PARTIAL) | Completed 2→20-entry mapping, `ACCEPTED_CANONICAL` removed |
| H-02 (capacity-confounded PPG headline) | CLOSED (prior sprint) | Unchanged this sprint |
| HMC split-source/chronology | CLOSED (prior sprint) | Unchanged this sprint |
| Freeze-manifest CRLF/LF semantics | CLOSED (prior sprint, Day-14 manifest) | New Section 32 manifest is separate |
| PPG/PTT cache provenance | **CARRIED_LIMITATION** | `docs/STAGE3_PPG_PTT_CACHE_PROVENANCE_LIMITATION.md`, unchanged — full fix still judged unsafe mid-remediation-sprint |
| Status vocabulary (CANONICAL) | **CLOSED** (new instance found+fixed) | Section 24/29, this sprint |
| Fold-5 provenance | **CLOSED** (new bug found) | Section 16, this sprint |
| Invalid-Galaxy fail-closed | **CLOSED** (new) | Section 17, resolver + tests |
| Experiment ID collisions | **CLOSED** (2 found) | Section 18, this sprint |
| HMC count consistency | **CLOSED** | Section 26, reconciled to 59/151 |
| Quarantine transfer history | **OPEN** | Not re-audited this sprint — no new evidence found requiring a change; deferred |
| Consolidated GalaxyPPG/LBNP provenance | **PARTIAL** | Existing `results/stage3_galaxyppg_lbnp_consolidated_provenance.json` not expanded to the full Section 27 field list this sprint — timebox reached; carried forward |

## GalaxyPPG final state

- Cohort: 18/24 eligible (composite QC gate, HIGH-02).
- Folds: 6 (`GALAXYPPG_CORRECTED_ELIGIBILITY_CV_PROTOCOL_V2`), fold 5 reused
  and provenance-corrected (Section 16).
- A/B/C: participant-level A_cap→B +0.834 (12/18), C→B +0.916 (13/18,
  HIGH-01-corrected); window-weighted A_cap→B +0.845, C→B +0.920.
- Heterogeneity: 6/18 favor A_cap over B, 5/18 favor C over B; no sign
  reversal under leave-one-out.
- Checkpoints: 75/75 (full CV) + 15/15 (bounded diagnostic), both
  externally archived and independently SHA256-verified.
- Invalidated evidence: `galaxyppg_hr_external_replication_stage2.json`,
  `galaxyppg_hr_full_grouped_cv_stage3.json` — both fail-closed via the
  new resolver (Section 17).

## LBNP final state

- n=12 eligible (pleth-quality exclusion, unchanged).
- Target range: 0-60 mmHg enforced (HIGH-03); 200/607 windows excluded.
- A=20.973, B=21.425, C=20.132 mmHg MAE. A_minus_B=-0.452 (sign-sensitive),
  C_minus_B=-1.293 (robust).
- Classification: `COMPLETE_NEGATIVE`.

## Tests

Full `ml/tests/` suite: **486 passed, 0 failed, 0 skipped** (32 new tests
this sprint across 9 new test files).

## Remaining work

HMC full-cohort training and ds003838 remain genuinely
`PENDING_DUE_TO_COMPUTE_OR_SESSION_LIMIT` — lower priority, unchanged
scope this sprint (no download/training attempted, per explicit
prohibition). PPG/PTT cache provenance remains a disclosed
`CARRIED_LIMITATION`. Quarantine transfer history and full Section-27
provenance-field expansion were not re-audited/completed this sprint —
disclosed as `OPEN`/`PARTIAL` rather than falsely closed.

## Architecture

`FINAL_ARCHITECTURE = UNRESOLVED`. `FORMAL_PARETO = NOT_READY`. Unchanged
— this remediation fixed defects and stale wording, it made no
architecture decision.

## Verdict

`STAGE3_CODEX_FAIL_REMEDIATION_REPORTED_COMPLETE_PENDING_INDEPENDENT_REAUDIT` —
all three HIGH findings closed with real fixes and passing tests; several
MEDIUM/provenance items closed; a small number of lower-priority items
(quarantine transfer history, full Section-27 field expansion) remain
honestly disclosed as open/partial rather than falsely marked complete.
