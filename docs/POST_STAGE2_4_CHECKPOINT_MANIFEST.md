# Post-Stage2-4 Checkpoint Manifest

## Sleep V2 (from the prior sprint, externally archived THIS sprint)

15 checkpoints (5 corrected shuffled-EOG control C + 10 corrected
interaction M_B/M_AB). Expected-membership manifest:
`results/sleep_v2_new_checkpoints_expected_membership.json`.
External archive: GitHub Release `sleep-v2-corrected-c-interaction-checkpoint-archive-v1`
— `EXTERNALLY_ARCHIVED_AND_VERIFIED` (15/15 redownload+SHA256 match).

## GalaxyPPG (new this sprint)

15 checkpoints (5 A_cap + 5 B + 5 C), bounded single-fold. Hashes in
`results/galaxyppg_hr_external_replication_stage2.json`'s
`checkpoint_manifest`. External archive: GitHub Release
`galaxyppg-hr-checkpoint-archive-v1` — `EXTERNALLY_ARCHIVED_AND_VERIFIED`
(15/15 redownload+SHA256 match).

## HMC bounded n=7 (from the prior sprint, unchanged, not re-archived this sprint)

15 checkpoints (`hmc_bounded_n7_*`). `LOCAL_HASH_VERIFIED_ONLY` — not
externally archived this sprint (time-prioritized behind GalaxyPPG/Sleep
V2 durability).

## Family separation (verified, no collisions)

| Family | Naming pattern | Collision check |
|---|---|---|
| Sleep V1 (historical) | `sleep_edf_*_seed{N}.pt` (no `seedfix_v2`) | Confirmed distinct from V2 by suffix |
| Sleep V2 corrected A/B | `sleep_edf_{baseline,candidate}_*_seedfix_v2_seed{N}.pt` | Prior sprint, unchanged |
| Sleep V2 corrected C | `sleep_edf_model_c_shuffled_eog_seedfix_v2_seed{N}.pt` | This sprint |
| Sleep V2 interaction | `sleep_edf_interaction_{M_B,M_AB}_..._seedfix_v2_seed{N}.pt` | This sprint, distinct from Day-10 V1 interaction checkpoints (no `seedfix_v2` suffix) |
| HMC bounded n=7 | `hmc_bounded_n7_*_seedfix_v2_seed{N}.pt` | Prior sprint, distinct from any future full-151 run (`hmc_sleep_*` without `bounded_n7` infix) |
| GalaxyPPG | `galaxyppg_hr_{A_cap,B,C}_seed{N}.pt` | This sprint, new family, no prior collision possible |
| PPG-DaLiA (inherited) | `ppg_dalia_*` | Untouched this sprint |

No historical checkpoint was overwritten, relabeled, or had its filename
reused this sprint.
