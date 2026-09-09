# Stage 2-4 Science-Owner Sprint — Checkpoint Manifest & External Durability

## Sleep V2 corrected C (this sprint, real)

`ml/checkpoints/sleep_edf_model_c_shuffled_eog_seedfix_v2_seed{42-46}.pt`
(5 files). SHA256 + full config recorded inline in
`results/sleep_edf_shuffled_eog_control_seedfix_v2.json`'s
`checkpoint_manifest` array — traceable back to this exact result and to
`ml/train_sleep_edf_shuffled_eog_control_seedfix_v2.py` at commit
(see `git log` for this file's introducing commit).

## Sleep V2 corrected interaction (this sprint, real)

`ml/checkpoints/sleep_edf_interaction_{M_B_eeg_plus_resp,
M_AB_eeg_plus_eog_plus_resp}_seedfix_v2_seed{42-46}.pt` (10 files). SHA256 +
config in `results/sleep_edf_interaction_resp_seedfix_v2.json`'s
`checkpoint_manifest`. **Explicitly distinct from the pre-existing Day-10
V1 checkpoints of similar names** (no `seedfix_v2` suffix on those) — both
sets coexist on disk without collision or overwrite.

## HMC bounded n=7 diagnostic (this sprint, real)

`ml/checkpoints/hmc_bounded_n7_{A_eeg_only,B_eeg_plus_eog,
c_shuffled_eog}_seedfix_v2_seed{42-46}.pt` (15 files). Named distinctly
from what a future full-151-cohort run would use
(`hmc_sleep_*_seedfix_v2_seed*.pt`, no `bounded_n7` infix) — no collision
risk when the full cohort is eventually trained.

## Claude's transferred (noncanonical) A/B reproduction checkpoints

10 files, gitignored, hashes recorded in
`results/claude_to_ismet_science_transfer_manifest.json`. Status:
`NONCANONICAL_PENDING_ISMET_REVIEW` (adjudicated in
`docs/CLAUDE_AB_REPRODUCTION_ADJUDICATION.md` — accepted as supportive
evidence, never promoted to canonical, canonical file hash independently
verified unchanged).

## Result → checkpoint → dataset trace (Section 57 requirement)

Every new result artifact this sprint names its exact generating script,
exact dataset path, and exact checkpoint manifest inline — no orphan JSON:

- `results/qde_v2_leg_bioz_stage2.json` → `ml/train_qde_v2_leg_bioz.py` → `datasets/qde-bioimpedance/raw/dehydration_estimation.csv` (SHA256 recorded).
- `results/ds003838_eeg_minimalism_stage3_bounded_diagnostic.json` → `ml/train_ds003838_eeg_minimalism.py` → 3 real subject `.set` files (MD5-verified, recorded).
- `results/sleep_edf_shuffled_eog_control_seedfix_v2.json` → `ml/train_sleep_edf_shuffled_eog_control_seedfix_v2.py` → `datasets/sleep-edfx/raw/` (already-fingerprinted from a prior sprint).
- `results/sleep_edf_interaction_resp_seedfix_v2.json` → `ml/train_sleep_edf_interaction_resp_seedfix_v2.py` → same Sleep-EDF raw dir.
- `results/hmc_sleep_external_replication_stage3_bounded_n7.json` → `ml/train_hmc_sleep_a_b_c_bounded_n7.py` → `datasets/hmc-sleep-staging/raw/` (7 recordings, SHA256-verified against PhysioNet's own `SHA256SUMS.txt` before the cert expiry stopped further downloads).

## External durability

`LOCAL_HASH_VERIFIED_EXTERNAL_ARCHIVE_PENDING` for all new checkpoints this
sprint. No new GitHub Release was created — consistent with this sprint's
time-prioritization toward completing the science itself; external
archival (following the existing Day-8/Day-14 Release pattern) is a
recommended follow-up, not performed here, and is stated as pending rather
than falsely claimed durable.
