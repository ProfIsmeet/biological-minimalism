# GalaxyPPG External HR Replication — Real Results (Bounded to Single Fold)

**Scope: `BOUNDED_TO_SINGLE_FOLD`** — see
`docs/GALAXYPPG_SPLIT_STRATEGY_DEVIATION.md`. 16/4/4 real subject-held-out
train/val/test split (all 24 real, eligible participants —
`results/galaxyppg_eligibility_stage2.json`), 5 seeds, capacity-matched
A_cap/B/C. Trainer: `ml/train_galaxyppg_hr_external_replication.py`.
Reference: real Polar H10 ECG R-peaks (never device-derived HR).

## Parameter counts (capacity-fairness verified)

A_cap: 28,865. B/C: 29,089 (0.77% residual — same magnitude/rationale as
the existing PPG-DaLiA capacity-control precedent, disclosed not hidden).

## Exact aggregate results (MAE, bpm, 5 seeds, 6,872 real test windows)

| Model | Mean | SD (ddof=1) |
|---|---|---|
| A_cap | 11.379 | 0.344 |
| B | 11.128 | 0.964 |
| C | 11.876 | 0.531 |

A→B: mean **+0.251 bpm**, only **3/5 seeds favor B**. C→B: mean **+0.748
bpm**, only **3/5 seeds favor B**. Both directions are weak relative to
their own seed-to-seed SD (0.88 and 1.18 respectively) — a marginal,
inconsistent signal, not a clear replication.

## Per-subject results (real, checkpoint-based re-evaluation, no retraining)

| Subject | n windows | A_cap MAE | B MAE | C MAE | A→B | C→B |
|---|---|---|---|---|---|---|
| P01 | 1187 | 32.89 | 31.19 | 32.06 | +1.69 | +0.87 |
| P04 | 1857 | 10.70 | 7.36 | 10.92 | +3.34 | +3.56 |
| P09 | 1924 | 4.19 | 6.27 | 5.06 | **−2.08** | −1.21 |
| P21 | 1904 | 5.90 | 7.20 | 7.28 | **−1.30** | +0.08 |

**Genuine subject-level sign reversal, disclosed in full**: P01 and P04
favor B; P09 and P21 favor A_cap. This is not averaged away — it is the
real reason the pooled aggregate (+0.251 bpm, 3/5 seeds) is such a weak,
inconsistent signal.

**P01 is a real outlier** (MAE ≈32 bpm across all three conditions, far
above the other three subjects' 4–11 bpm range) — plausibly linked to the
same real data-quality issue the dataset's own README flags for P01
(Galaxy Watch configuration error), even though P01's E4/Polar data itself
passed this project's eligibility gate (file presence + sync-overlap
check). **Not excluded post hoc** — no outcome-based exclusion rule exists
in the frozen eligibility criteria, and removing P01 after seeing its poor
performance would be exactly the kind of post-hoc exclusion this project's
integrity rules forbid.

## Final classification

**`EXTERNAL_REPLICATION_MIXED`** (per the frozen classification menu). The
PPG-DaLiA finding (IMU helps HR estimation, capacity-controlled) does
**not** clearly replicate on GalaxyPPG at this bounded single-fold scale:
the pooled effect is small and only 3/5-seed-favorable, and per-subject
evidence is genuinely split in direction. This is reported as the honest
outcome, not forced toward agreement with PPG-DaLiA and not forced toward
a clean negative either.

## Safe claim

"Under a capacity-controlled, real ECG-referenced protocol on an
independent device/subject family (GalaxyPPG, single held-out fold, n=4
test subjects), the previously observed PPG-DaLiA IMU benefit showed a
weak, seed- and subject-inconsistent signal — neither a clear replication
nor a clear failure to replicate at this bounded scale."

## Unsafe claims (not made)

"IMU always improves HR." "GalaxyPPG confirms/replicates PPG-DaLiA."
"GalaxyPPG refutes PPG-DaLiA." Any claim beyond this single bounded fold
(a full 6-fold grouped CV covering all 24 subjects as test remains the
canonical completion of this experiment, not performed this sprint).
