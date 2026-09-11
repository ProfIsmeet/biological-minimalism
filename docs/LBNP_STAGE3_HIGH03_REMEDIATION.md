# LBNP Stage 3 — HIGH-03 Remediation

**Status: `PROTOCOL_COMPLIANT_RERUN_COMPLETE`.**

## The two real defects found

1. **Target-range non-enforcement.** The frozen protocol
   (`results/lbnp_protocol_stage1b.json`) specifies the primary target as
   "the 0-60 mmHg range" with stages 0/15/30/45/60. The original trainer
   (`ml/train_lbnp_thoracic_eis.py`) applied no range filter at all. Real
   inspection this sprint: **200/607 windows (33%) across all 12 eligible
   subjects were at stages 70/80/90/100 mmHg**, outside the frozen scope,
   and entered the reported result
   (`results/lbnp_thoracic_eis_stage3.json`).
2. **C-control same-stage leakage.** The frozen protocol's condition C
   requires EIS drawn "from a different stage's real EIS spectrum for the
   SAME subject." The original `deranged_eis()` only guaranteed
   `source_index != target_index` (a fixed-point-free permutation), not
   `source_stage != target_stage`. Measured this sprint: **13-25% of
   "deranged" C windows retained the same stage as the original** under
   the old function, for the first 4 subjects checked directly.

## Decision Gate outcome

Per the master prompt's Section 20 decision gate: real out-of-range
targets DID enter the old result, so **A/B/C were rerun** under a
protocol-compliant dataset and control.

## Disposition of the old result

`results/lbnp_thoracic_eis_stage3.json` is **preserved unchanged** and is
now understood as `HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL` — its aggregate
numbers (A_minus_B=-2.24, C_minus_B=-0.033, `COMPLETE_NEGATIVE`) were
computed over a mix of in-scope and out-of-scope target data, and its
C-control had real (though partial) same-stage leakage. It is not
deleted, but it must never be resolved as governing evidence — see
`ml/stage3_science_resolver.py`, which fails closed against this path.

## The new, protocol-compliant result

`ml/train_lbnp_thoracic_eis_v2_protocol_compliant.py` /
`results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json`:

- **Target-range enforcement**: 200 out-of-scope windows excluded before
  any feature/model construction. Every subject retains >=5 in-scope
  windows (n=12 unchanged).
- **C-control fix**: `deranged_eis_different_stage()` guarantees
  `source_stage != target_stage` for every window. Verified
  programmatically: **0 same-stage collisions remaining** across all 12
  subjects (the script raises if this is not exactly 0).
- **Result**: A_mean=20.973, B_mean=21.425, C_mean=20.132 (MAE, mmHg).
  A_minus_B=-0.452 (A slightly better than B — real EIS does not help),
  C_minus_B=-1.293 (B is *worse* than its own deranged-EIS control, robust
  under leave-one-subject-out).
- **Classification: `COMPLETE_MIXED`** (revised by the final
  source-of-truth remediation sprint from this document's original
  `COMPLETE_NEGATIVE` call). The C-vs-B comparison is the more diagnostic
  one (B and C share identical architecture/capacity, differing only in
  whether the EIS branch carries real stage-aligned information), and
  remains negative under leave-one-out exclusion of any single subject —
  but it SHRINKS SUBSTANTIALLY without subject 9, meaning even this more
  diagnostic comparison is not a uniform, subject-independent effect. The
  A-vs-B comparison is sign-sensitive (excluding subject 9 flips its
  aggregate sign) — disclosed explicitly in
  `leave_one_subject_out_sensitivity`. Given both key comparisons are
  substantially influenced by one subject, `COMPLETE_NEGATIVE` overstated
  the finding's stability; `COMPLETE_MIXED` (negative-leaning,
  heterogeneous) is the accurate governing classification — see
  `results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json`'s own
  `classification_history` field for the full correction record.

## Heterogeneity disclosed (not smoothed over)

Subjects 4 and 9 are large, opposing-direction outliers on A_minus_B
(+15.17 and -14.88 respectively) — a similar cancellation pattern to the
prior sprint's "subjects 4 and 7" finding, though the specific canceling
pair differs under the corrected in-scope-only dataset. This is reported
directly, not minimized.
