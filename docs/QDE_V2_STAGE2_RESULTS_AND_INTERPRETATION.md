# QDE V2 Leg-BioZ — Stage 2A Results and Interpretation

Real LOSO ridge-regression training run, frozen protocol
(`results/qde_v2_protocol_stage1b.json`), machine-readable result:
`results/qde_v2_leg_bioz_stage2.json`. Trainer:
`ml/train_qde_v2_leg_bioz.py`. Reproducibility: exact clean-state rerun
match confirmed (`results/qde_v2_leg_bioz_stage2_reproducibility.json`).

## Exact results (subject-macro MAE in kg, n=10 subjects, 9 points each)

| Condition | Mean MAE | SD (ddof=1) |
|---|---|---|
| A (arm+trunk only) | 0.7358 | 0.1124 |
| B (arm+trunk+legs) | 0.7876 | 0.2858 |
| C (B-dim, legs deranged) | 0.7280 | 0.1195 |

A−B mean: **−0.0518** (B is *worse* on average). C−B mean: **−0.0596** (the
deranged-leg control is *also* better than the real leg-impedance condition
on average).

**7 of 10 subjects individually favor B over A, and 7 of 10 favor B over
C** — but the aggregate mean says the opposite. This is a real, disclosed
**single-subject-dominance** finding: subject 2's A−B delta is **−0.71 kg**,
roughly 9× the typical subject's delta magnitude (the other 9 subjects'
deltas range from −0.12 to +0.08). Subject 2 alone flips the sign of the
aggregate mean despite being a minority pattern by subject count. Subject
10 (−0.12) is a smaller second contributor in the same direction.

## Scientific interpretation (frozen limits from the protocol, not chosen post hoc)

**This is a negative-leaning, subject-concentrated result.** Bilateral leg
impedance did **not** clearly add predictive information beyond arm+trunk
impedance for baseline-relative body-mass change in this n=10 cohort — by
majority-of-subjects count the effect is mildly positive, but the
mean-aggregate result is dominated and reversed by one outlier subject. Per
this project's small-N discipline (already applied to PTT n=4 and QDE
n=10), **the aggregate mean is not a more "correct" number than the
per-subject breakdown — both are reported, neither is suppressed.**

Per the frozen safe-interpretation bound (`results/qde_v2_protocol_stage1b.json`
`negative_result_policy`), the honest statement is:

> Bilateral leg segment impedance did not show a robust, subject-consistent
> improvement over the preregistered upper-body BioZ baseline for
> exercise-associated baseline-relative body-mass change in this QDE
> cohort; the aggregate effect is dominated by one outlier subject, and a
> majority of subjects show only a small favorable direction.

This does **not** establish microgravity fluid shift, astronaut validation,
exact TBW, dehydration liters, or universal leg-BioZ necessity/uselessness
— per `docs/STAGE1B_EXPANSION_FORBIDDEN_CLAIMS.md`.

## Historical result — unchanged, untouched

`ml/train_bioimpedance.py` / `ml/datasets/qde_bioimpedance.py`'s original
InBody-TBW experiment is a completely separate target and was not modified,
re-run, or reinterpreted by this Stage-2 work.
