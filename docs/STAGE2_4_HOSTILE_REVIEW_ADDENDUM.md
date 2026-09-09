# Stage 2-4 Science-Owner Sprint — Hostile Review Addendum

Extends `docs/STAGE4_HOSTILE_SELF_REVIEW.md` (prior sprint) with findings
specific to this sprint's science-owner takeover work. Same scope caveat
applies: this is an internal audit of this branch only, not the final
integrated Claude+Ismet audit.

## New BLOCKER findings

None.

## New HIGH findings

1. **Real bug in Claude-transferred HMC loader**: `ml/datasets/hmc_sleep.py`'s
   `needed_raw_channels` computation checked whether the *derived*-EOG
   marker string was itself a raw channel name (it never is), so it
   silently never included either raw EOG channel needed to compute it —
   a real `KeyError` on the very first real-data training attempt. This is
   exactly the class of bug the transfer handoff's own disclosure warned
   about ("only smoke-level exercised... full load path never run in
   training"). **Fixed** this sprint (`ml/datasets/hmc_sleep.py`), with a
   regression test (`test_needed_raw_channels_expands_derived_eog_to_both_raw_channels`).
   Evidence this was a real, not cosmetic, defect: it produced a hard crash
   on real data, not a silently-wrong result — arguably the safer failure
   mode, but still a genuine correctness bug that would have blocked any
   real HMC B/C training indefinitely without root-causing it.

## New MEDIUM findings

2. **PhysioNet TLS certificate expiry mid-sprint**: genuinely external,
   independently verified via `openssl s_client` (real `notAfter` date in
   the past at the time of failure), not a local clock or credential
   issue. No workaround (e.g., `-k`/`--insecure`) was used — treated as a
   hard, non-bypassable blocker, exactly like a data-access permission
   issue would be. This capped the full HMC cohort download at 8/151
   recordings (7 with complete EDF+scoring pairs).
3. **Bounded diagnostics stack up**: this sprint now has THREE
   bounded/partial-cohort diagnostics (ds003838 n=3, HMC n=7, plus QDE's
   inherent n=10) — none individually mislabeled, but collectively the
   project should track how many of its "expansion" experiments remain at
   genuinely small scale before the paper/jury handoff overstates breadth.

## New LOW / INFO findings

4. Claude's transferred trainers (C, interaction, HMC A/B/C) all re-parse
   raw EDF files from scratch with no shared cache, exactly as Claude's own
   handoff disclosed (a real, acknowledged efficiency note, not a
   correctness issue) — unchanged this sprint.
5. Running two independent training jobs concurrently (Sleep interaction +
   HMC bounded n7) on shared CPU meaningfully slowed both relative to
   running them sequentially — a resource-scheduling observation, not a
   correctness issue.

## Dimension B/C spot-checks performed this sprint (beyond the prior sprint's coverage)

- **M0/M_A reuse for the interaction experiment**: independently verified
  (not just trusted) by direct source comparison — confirmed
  `ml/train_sleep_edf_interaction_resp.py` (original) and
  `ml/train_sleep_edf_primary_seedfix_v2.py` (corrected) both import
  `EPOCHS=20, BATCH_SIZE=64, LR=0.001` from/matching
  `ml/train_sleep_edf_eeg_eog_ablation.py`, and use the identical
  `SleepStageClassifier`/frozen split. Accepted.
- **C capacity-identity claim**: independently re-verified from the actual
  written result JSON (`frozen_protocol.capacity_identical_to_b: true`),
  not just the trainer's inline assertion.
- **HMC bounded n7's per-recording label distribution**: spot-checked on
  SN001 directly (854 real epochs, 5-class distribution
  `[151, 109, 430, 23, 141]` for W/N1/N2/N3/REM) before trusting the
  aggregate trainer output — a real, sane clinical-population distribution
  (N2-dominant, consistent with adult PSG norms), not a degenerate
  all-one-class artifact.
