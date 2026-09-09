# Sleep V2 New Checkpoint External Archive

**Status: `EXTERNALLY_ARCHIVED_AND_VERIFIED`**

GitHub Release: `sleep-v2-corrected-c-interaction-checkpoint-archive-v1`
https://github.com/ProfIsmeet/biological-minimalism/releases/tag/sleep-v2-corrected-c-interaction-checkpoint-archive-v1

15 checkpoints uploaded individually (5 corrected shuffled-EOG control C +
10 corrected EEG×EOG×Resp interaction M_B/M_AB). Expected-membership
manifest: `results/sleep_v2_new_checkpoints_expected_membership.json`
(exact filename/SHA256/size/arm/seed per checkpoint).

## Verification performed

1. **Local hash check**: recomputed SHA256 for all 15 checkpoint files on
   disk, confirmed exact match against the hashes recorded inline in
   `results/sleep_edf_shuffled_eog_control_seedfix_v2.json` and
   `results/sleep_edf_interaction_resp_seedfix_v2.json`'s
   `checkpoint_manifest` arrays — 15/15 match.
2. **Strict membership check**: expected filename set (from the
   expected-membership manifest) compared against the actual files present
   in `ml/checkpoints/` matching the relevant naming pattern — exact set
   equality, no missing, no unexpected.
3. **External upload**: all 15 files uploaded to the GitHub Release above
   via `gh release upload` (individually, after a batch multi-file
   invocation failed for a shell-quoting reason unrelated to the files
   themselves).
4. **Independent redownload verification**: `gh release download` into a
   fresh scratch directory, then recomputed SHA256 for all 15 redownloaded
   files against the same expected-membership manifest — **15/15 exact
   match**. This is a genuine independent verification (fresh download,
   not the same file handle), not just re-checking the local copy.

## Historical archives — confirmed untouched

`day8-checkpoint-archive-v1` (1 asset, `biological_minimalism_checkpoints_
day8.tar.gz`, bundling the historical 50 checkpoints) and
`day14-checkpoint-archive-v1` (1 asset, `..._day14.tar.gz`, bundling 10
interaction checkpoints) were checked via `gh release view` — asset lists
unchanged, this sprint created a new, separate release rather than
modifying either.
