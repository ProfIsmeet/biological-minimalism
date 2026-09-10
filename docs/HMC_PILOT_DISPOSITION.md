# HMC 12-Recording Pilot — Disposition

**Status: `PILOT_SUPERSEDED_FOR_CANONICAL_HMC_REPLICATION`, retained as a
historical, disclosed data point.**

Claude's Stage-2 sprint downloaded and byte-verified (SHA256 against
PhysioNet's official `SHA256SUMS.txt`) a reduced 12-of-151 recording pilot
(`SN001`–`SN012`) due to a bandwidth constraint on that session's
environment, with a sequential-block split
(`results/hmc_split_stage2.json`: train SN001-008 / val SN009-010 / test
SN011-012). **No training was ever run on this pilot** — it is data +
loader-format confirmation only (channel labels `EEG C4-M1`, `EOG E1-M2`,
`EOG E2-M2` and the `_sleepscoring.txt` annotation format were confirmed
directly from real files this way).

This sprint downloads and trains on the **full 151-recording cohort**
(`results/hmc_split_stage3_full_cohort.json`, a neutral deterministic
70/15/15 split, frozen before any bounded training/evaluation — see
`docs/HMC_STAGE3_SPLIT_STRATEGY_DEVIATION.md`).

**The 12-recording pilot split/data is never used as, combined with, or
compared numerically against the full-cohort canonical result.** It is
retained in the repository purely as a disclosed historical artifact
documenting how the HMC loader's real-file format was first confirmed.
