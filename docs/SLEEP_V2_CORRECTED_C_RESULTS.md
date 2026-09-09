# Sleep V2 Corrected C (Shuffled-EOG Control) — Real Results

Trainer: `ml/train_sleep_edf_shuffled_eog_control_seedfix_v2.py` (Claude-
authored, cherry-picked, independently audited before running — see
`docs/CLAUDE_TO_ISMET_STAGE2_4_SCIENCE_TRANSFER_HANDOFF.md` §7). Result:
`results/sleep_edf_shuffled_eog_control_seedfix_v2.json`. 5 real seeds
(42-46), corrected H1 seeding order throughout, isolated
`control_shuffle_seed` (`run_seed + 200,000`).

**Capacity check passed**: Model C parameter count is exactly identical to
corrected Model B (verified by a hard assertion in the trainer before any
training began — real safeguard, not a post-hoc claim).

## Exact results (macro-F1, 5 seeds)

| Model | Mean | SD (ddof=1) |
|---|---|---|
| A (EEG only, corrected V2) | 0.7365 | 0.0279 |
| B (EEG+EOG, corrected V2) | 0.7647 | 0.0116 |
| C (EEG+shuffled-EOG, corrected V2) | 0.7324 | 0.0472 |

- **A→B**: mean +0.0282, 4/5 seeds favor B (unchanged from the existing
  canonical corrected A/B result).
- **A→C**: mean −0.0041, 3/5 seeds favor C (near-zero — C performs
  approximately like A, as expected: shuffled EOG should carry no more
  information than no EOG at all).
- **C→B**: mean +0.0323, 4/5 seeds favor B — **same direction and similar
  magnitude to A→B.**

## Interpretation

B beats C by almost the same margin it beats A, with an identical
favorable-seed count (4/5). Since B and C share exactly the same
architecture and parameter count, and C's ONLY difference from B is that
the EOG channel's temporal correspondence to the EEG/label has been
destroyed (within-subject, within-partition, real EOG distribution
preserved), this is genuine evidence that **B's benefit over A is
attributable to real temporal EOG-EEG correspondence, not merely to
capacity or the presence of a second (even if uninformative) channel.**

Per the frozen protocol's `negative_result_policy`
(`results/sleep_edf_shuffled_eog_control_seedfix_v2.json`'s
`frozen_protocol` block references the same predeclaration as V1): this is
the `if_shuffled_control_does_not_equal_candidate` outcome — i.e. the
positive case for a real EOG effect. It is NOT reinterpreted as anything
stronger than: "under a corrected, seed-controlled, capacity-matched
protocol, aligned EOG added sleep-staging information beyond both an
EEG-only baseline and an EEG+shuffled-EOG control of identical capacity."

## Subject sensitivity (C, mean macro-F1 across 5 seeds)

| Subject | C mean macro-F1 |
|---|---|
| SC4011 | 0.6862 |
| SC4081 | 0.7316 |
| SC4131 | 0.7729 |

SC4011 is the lowest-performing subject under C, consistent with it being
the subject most sensitive to losing real EOG information (it was also the
subject with the largest A→B gain in the primary corrected result) —
coherent, not contradictory, evidence.

## Class sensitivity (B vs C, mean across 5 seeds)

| Class | B mean | C mean | B−C |
|---|---|---|---|
| Wake | 0.9712 | 0.9568 | +0.0144 |
| N1 | 0.4605 | 0.3599 | **+0.1005** |
| N2 | 0.8384 | 0.8488 | −0.0105 |
| N3 | 0.8857 | 0.8613 | +0.0243 |
| REM | 0.6678 | 0.6349 | +0.0329 |

**N1 shows by far the largest B-vs-C gap** (real EOG helps most
distinguishing the hardest, rarest class), with REM second — broadly
consistent with this project's existing "REM-driven" pattern from the
primary A/B result. N2 shows a small, noise-level reversal (C marginally
above B) — reported honestly, not hidden.

## Historical (V1) comparison — kept separate

The V1 shuffled-EOG control (`results/sleep_edf_eeg_eog_control_analysis.json`)
remains completely unchanged and untouched by this sprint. No V1/V2 mixing
occurred — this document and its underlying result reference ONLY the
corrected V2 A/B (`results/sleep_edf_primary_seedfix_v2.json`).
