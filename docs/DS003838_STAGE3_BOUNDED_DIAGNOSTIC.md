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
   was trained and evaluated on all 3 subjects whose downloads completed
   successfully (`sub-032`, `sub-033`, `sub-034` — network resets occurred
   mid-download for all three at various points and were resumed with
   `curl -C - --retry`; all three final files were independently re-hashed
   and matched their real git-annex MD5s exactly: `f589e83435f7f9edca345c6b
   89afbe32`, `01269258ed5b4135ef840568b01764fa`,
   `019c28c2878fb148a2ed0dfb5b82122a`). See
   `results/ds003838_eeg_minimalism_stage3_bounded_diagnostic.json` for the
   exact result.

## A real file-format discovery made this sprint

ds003838's real `.set` files are **MATLAB v7.3 (HDF5)**, not the classic
MAT format `mne.io.read_raw_eeglab` expects — attempting to load with MNE
failed with a real `NotImplementedError: Please use HDF reader for matlab
v7.3 files, e.g. h5py`. `ml/datasets/ds003838_eeg.py` was corrected to read
the file directly via `h5py` (the real HDF5 tree was inspected first: a
top-level `data` dataset of shape `(n_samples, n_channels)` float32 and a
`srate` scalar — exactly what an EEGLAB continuous recording needs). This
is a real, disclosed mid-sprint protocol-implementation fix (not a
retroactive science change — no result existed yet when this was found and
fixed).

## Exact real result (n=3 subjects, LOSO, macro-F1)

| Condition | Mean macro-F1 | SD (ddof=1) |
|---|---|---|
| A (sparse 4ch) | 0.2263 | 0.0091 |
| B (full 63ch) | 0.2765 | 0.0522 |
| C (full arch, non-A channels deranged) | 0.2167 | 0.0000 |

For reference, always predicting the majority class (length 13, 468/972
epochs) yields macro-F1 ≈ 0.2167 exactly — **C's result is indistinguishable
from a majority-class-only classifier for all 3 subjects**, which is the
scientifically expected behavior for a deranged, information-destroyed
control. B is numerically higher than A, but driven by 2 of 3 subjects
(sub-032: 0.313, sub-033: 0.300, sub-034: 0.217 — sub-034's B result is
itself indistinguishable from majority-class-only).

## What this diagnostic can and cannot support

With only 3 subjects, subject-wise LOSO evaluates each held-out subject
against a training set of only 2 other subjects — **far too small a
biological n to draw any conclusion about the sparse-vs-full-EEG
question**, and the numbers above are consistent with that: performance is
barely above (A, one of three B subjects) or exactly at (C, one B subject)
chance/majority-class level. This diagnostic exists ONLY to prove: (a) the
real-file access path works end-to-end (byte-verified), (b) the loader
correctly parses real BIDS labels/epochs without leakage, (c) the frozen
sparse channels are present and the capacity-fair shared-encoder design
runs correctly on real data, (d) the negative control (C) behaves exactly
as a real negative control should (collapses to chance).

**It does NOT stand in for, and must never be cited as, the frozen
Stage-2/3 n=65 result.** The full-cohort run remains a future-session task
once sufficient time/bandwidth budget is available (or a faster mirror/
access path is used).
