# GalaxyPPG Corrected Full-CV V2 External Archive

**Status: `EXTERNALLY_ARCHIVED_AND_VERIFIED`**

GitHub Release: `galaxyppg-corrected-fullcv-v2-checkpoint-archive-v1`
https://github.com/ProfIsmeet/biological-minimalism/releases/tag/galaxyppg-corrected-fullcv-v2-checkpoint-archive-v1

75 checkpoints uploaded individually (5 newly-trained folds x 5 seeds x 3
conditions A_cap/B/C, under the `GALAXYPPG_CORRECTED_ELIGIBILITY_CV_PROTOCOL_V2`
distinct `correctedcv_v2` namespace — never colliding with the pre-fix,
invalidated full-CV checkpoint names). Fold 5 reused the prior bounded
diagnostic result verbatim (no new checkpoints trained for fold 5this
sprint). Expected-membership manifest:
`results/galaxyppg_correctedcv_v2_expected_membership.json` (exact
filename/SHA256/size per checkpoint).

## Verification performed

1. **Local hash check**: computed SHA256 for all 75 checkpoint files on
   disk immediately after training, recorded in the expected-membership
   manifest above.
2. **Strict membership check**: 75/75 files present locally, matching the
   expected `fold{0-4}_{A_cap,B,C}_seed{42-46}` naming pattern with no
   missing or unexpected files.
3. **External upload**: all 75 files uploaded to the GitHub Release above
   via `gh release upload`, individually (per this project's established
   pattern — batch multi-file upload has previously failed for a
   shell-quoting-related reason unrelated to file correctness). 75/75
   uploads succeeded.
4. **Independent redownload verification**: `gh release download` into a
   fresh scratch directory, `sha256sum` computed on all 75 redownloaded
   files, compared against the expected-membership manifest — **75/75
   exact match** (0 missing, 0 unexpected, 0 mismatched). This is a
   genuine independent verification (fresh download, not the same file
   handle), not just re-checking the local copy. Scratch directory removed
   after verification.

## Historical archives — not touched

This sprint created a new, separate release rather than modifying any
prior archive (`day8-checkpoint-archive-v1`,
`sleep-v2-corrected-c-interaction-checkpoint-archive-v1`, etc.).
