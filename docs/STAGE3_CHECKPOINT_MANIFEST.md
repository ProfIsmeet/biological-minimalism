# Stage 3 Checkpoint Manifest

## GalaxyPPG — corrected-eligibility (valid, this sprint)

15 checkpoints (5 A_cap + 5 B + 5 C), single corrected fold (18 real
eligible subjects, 3 test). Hashes in
`results/galaxyppg_hr_corrected_eligibility_stage3.json`'s
`checkpoint_manifest`. External archive: GitHub Release
`galaxyppg-corrected-eligibility-checkpoint-archive-v1` —
`EXTERNALLY_ARCHIVED_AND_VERIFIED` (15/15 redownload+SHA256 match).

## GalaxyPPG — pre-fix (INVALIDATED, retained as historical only)

- Single-fold diagnostic (prior sprint, 15 checkpoints,
  `galaxyppg_hr_{A_cap,B,C}_seed{N}.pt`): `EXTERNALLY_ARCHIVED_AND_VERIFIED`
  (archived before the defect was found), but the underlying result is
  `INVALIDATED_BY_REFERENCE_SIGNAL_QUALITY_DEFECT` — checkpoints remain
  hash-valid and loadable, only the scientific interpretation of their
  performance numbers is invalidated.
- Full 6-fold CV (this sprint, 75 checkpoints,
  `galaxyppg_hr_fullcv_fold{0-4}_{name}_seed{N}.pt` + reused fold 5):
  `LOCAL_HASH_VERIFIED_ONLY`, not externally archived (superseded by the
  corrected rerun before archival was prioritized) — same
  `INVALIDATED_BY_REFERENCE_SIGNAL_QUALITY_DEFECT` status.

## LBNP

No checkpoints — ridge regression, same convention as QDE V2 (a linear
model's coefficients are not scientifically necessary to serialize as a
checkpoint artifact; the deterministic trainer script is the
reproducibility guarantee).

## HMC

No new checkpoints this sprint (full-cohort training not started). n=7
bounded diagnostic's 15 checkpoints (prior sprint) unchanged,
`LOCAL_HASH_VERIFIED_ONLY`.

## Family separation (verified, no collisions)

| Family | Naming pattern |
|---|---|
| GalaxyPPG pre-fix single-fold | `galaxyppg_hr_{A_cap,B,C}_seed{N}.pt` |
| GalaxyPPG pre-fix full-CV | `galaxyppg_hr_fullcv_fold{K}_{name}_seed{N}.pt` |
| GalaxyPPG corrected | `galaxyppg_hr_corrected_{name}_seed{N}.pt` |
| HMC bounded n=7 | `hmc_bounded_n7_*_seedfix_v2_seed{N}.pt` |
| HMC full cohort (future) | `hmc_fullcohort_*_seedfix_v2_seed{N}.pt` (reserved, not yet used) |

No historical checkpoint was overwritten, relabeled, or had its filename
reused this sprint.
