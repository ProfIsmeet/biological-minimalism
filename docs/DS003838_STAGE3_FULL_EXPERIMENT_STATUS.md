# ds003838 Full Frozen Experiment — Status (Stage 3, Priority 4)

**Status: `PENDING_DUE_TO_COMPUTE_OR_SESSION_LIMIT`** (not `OUT_OF_SCOPE` —
this is a real, quantified compute/time blocker, not a scope decision).

## What is required for the full frozen experiment

The frozen full-cohort eligibility is **65 of 86 subjects** (confirmed
directly from `participants.tsv`'s `EEG_excluded` column, prior sprint —
unchanged). The bounded n=3 diagnostic (`sub-032`, `sub-033`, `sub-034`)
from the prior sprint already required downloading and byte-verifying
~4.3 GB of real memory-task EEG data.

## Quantified remaining cost

The full 65-subject cohort's real, measured per-subject memory-task file
size averages ~1.5 GiB (directly measured this project: sub-032 =
1,541,437,462 bytes, sub-033 = 1,774,673,538 bytes, sub-034 =
1,494,254,561 bytes). The remaining 62 subjects would require
approximately **~93 GB** of additional real download. At this sandbox's
own measured throughput this session (~2.75 MB/s, directly timed against
OpenNeuro's S3 bucket in the prior sprint), that is approximately **9.4
hours** of download time alone — before any training compute — which is
not feasible within this sprint's session/time budget, especially given
this sprint's compute was already committed to GalaxyPPG's full 6-fold CV
(Priority 1) and the real LBNP experiment (Priority 2), both explicitly
ranked higher.

## Disposition

The n=3 bounded diagnostic (`results/ds003838_eeg_minimalism_stage3_bounded_diagnostic.json`)
remains the best currently-available real evidence, unchanged from the
prior sprint, explicitly not promoted to a full result. This sprint did
not add new work to ds003838 — the quantified blocker above is restated
here for Stage 3 completeness, not re-derived from scratch.

## What would need to happen for full completion

1. A dedicated multi-hour (≥9.4h) download session for the remaining 62
   subjects' real memory-task EEG files (real, byte-verified against each
   file's git-annex hash, per this project's established practice).
2. Real, frozen full-cohort A/B/C training under the already-frozen
   protocol (`results/ds003838_protocol_stage1b.json` — sparse AF7/AF8/
   TP9/TP10 vs full 63-channel montage vs deranged-extra-channels
   control), using the already-built and tested loader/trainer code
   (`ml/datasets/ds003838_eeg.py`, `ml/train_ds003838_eeg_minimalism.py`)
   with no protocol changes required — the code already generalizes to
   any subject count.
