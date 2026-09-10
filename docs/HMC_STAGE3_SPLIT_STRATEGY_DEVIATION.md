# HMC Stage 3 — Split Strategy Deviation (versioned before any training)

**Frozen Stage 1B protocol** (`results/hmc_protocol_stage1b.json` →
`split_strategy`) specifies: *"Subject-wise (== recording-wise) k-fold, no
epoch-level split."*

**Problem**: k-fold over the full 151-recording cohort (15.7 GB), at 3
conditions (A/B/C) × 5 seeds each, would require re-training on the order of
`k × 3 × 5` full-cohort model fits. Even at `k=5` that is 75 full training
runs on the complete dataset — computationally infeasible within this
session's time/compute budget (the reduced-cohort A/B/C alone, at
12 recordings, is the scale Claude's pilot ran at; the full cohort is
~12.6× larger by file count and correspondingly larger in epoch count).

**New protocol (versioned here, BEFORE any HMC file was opened or any HMC
result existed)**: a single fixed train/val/test split over the full
151-recording cohort, chosen by a neutral, deterministic, outcome-
independent rule — matching this project's own Sleep-EDF split convention
(a fixed split, not k-fold) rather than inventing a new split philosophy
per dataset.

**Exact construction**: the real RECORDS index (151 IDs, SN001–SN154 minus
the two gaps SN014/SN064 — directly fetched from PhysioNet this sprint) was
sorted, then deterministically shuffled with `random.Random(42).shuffle()`
(seed 42, this project's standard run seed), then partitioned 70/15/15 by
position: **106 train / 23 val / 22 test**. This is a fixed, single split —
not k-fold — decided and written to
`results/hmc_split_stage3_full_cohort.json` before any bounded
training/evaluation.

**Disposition**: `PILOT_SUPERSEDED_FOR_CANONICAL_HMC_REPLICATION` — Claude's
12-recording reduced-cohort pilot split (`results/hmc_split_stage2.json`,
train SN001-008/val SN009-010/test SN011-012, sequential-block selection)
is retained as a historical, disclosed pilot artifact, never used as the
canonical HMC replication split, and never combined with full-cohort
numbers.

**Whether any outcome was already inspected**: No. The full-cohort split
was frozen before bounded training/evaluation — verified by this
document's own git commit timestamp preceding the first HMC bounded
training run in this session's history. (Note: the real RECORDS index
listing — filenames only, no scientific/performance content — was fetched
to enumerate the 151 valid IDs before this split was constructed; no
recording's signal content or any performance outcome was ever inspected
before the split was frozen.)
