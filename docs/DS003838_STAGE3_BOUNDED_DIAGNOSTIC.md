# ds003838 Stage 3B — Bounded Diagnostic Disclosure

**This is NOT the frozen Stage-2/3 n=65 cohort result.**

## Why

Stage 1B directly measured the real per-subject EEG footprint via git-annex
object pointer sizes: ~1.47 GiB (memory task) per subject. For all 65
eligible subjects, that is ~96 GB. This session's actual measured download
throughput from OpenNeuro's S3 bucket was **~2.75 MB/s** (real, timed,
byte-verified) — at that rate, the full 65-subject cohort would take on the
order of **9-10 hours** to download, which is not feasible within this
session's time budget.

## What was actually done instead

Per Section 15's explicit allowance ("a scientifically valid preregistered
subset of subjects only if selected by neutral rules before outcomes") and
Section 78's guidance ("for huge restricted datasets, use a realistic
reproducibility verification strategy rather than copying massive datasets
merely to check a code path"):

1. **Real access was proven working** — a full byte-for-byte download of
   `sub-032_task-rest_eeg.set` (47,511,267 bytes) was verified to match the
   real git-annex MD5 (`1094cdcc2162461e26addedf71c1baa5`) exactly, via the
   real S3 ETag returned by `s3.amazonaws.com/openneuro.org`. This
   independently confirms the actual-file access channel this project relies
   on for ds003838 genuinely works (unlike GalaxyPPG/LBNP's Zenodo, which
   was blocked both sprints).
2. **A small, neutral-rule subject subset was downloaded**: the first
   eligible subject IDs in sorted order (`sub-032`, `sub-033`, `sub-034`) —
   chosen by a rule fixed before looking at any subject's data content, not
   by outcome.
3. **A real, working loader** (`ml/datasets/ds003838_eeg.py`) was built and
   run against these real files: real MNE EEGLAB parsing, real BIDS
   `trial_type` label parsing (never the raw numeric trigger code), real
   fixed-duration epoching matching the actual BIDS `duration` field.
4. **A real, bounded LOSO diagnostic** (`ml/train_ds003838_eeg_minimalism.py`)
   was trained and evaluated across however many of these subjects'
   downloads completed successfully — see
   `results/ds003838_eeg_minimalism_stage3_bounded_diagnostic.json` for the
   exact subject count actually used (network resets occurred during this
   session's downloads; the exact achieved n is recorded in that artifact,
   not assumed to be 3).

## What this diagnostic can and cannot support

With at most 3 subjects, subject-wise LOSO evaluates each held-out subject
against a training set of only 1-2 other subjects — **far too small a
biological n to draw any conclusion about the sparse-vs-full-EEG
question**. This diagnostic exists ONLY to prove: (a) the real-file access
path works end-to-end, (b) the loader correctly parses real BIDS
labels/epochs without leakage, (c) the frozen sparse channels are present
and the capacity-fair shared-encoder design runs correctly on real data.

**It does NOT stand in for, and must never be cited as, the frozen
Stage-2/3 n=65 result.** The full-cohort run remains a future-session task
once sufficient time/bandwidth budget is available (or a faster mirror/
access path is used).
