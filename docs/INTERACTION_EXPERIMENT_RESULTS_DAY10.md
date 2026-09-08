# Sleep-EDF EEG x EOG x Resp Interaction Experiment — Results (Day 10)

Predeclaration: `docs/INTERACTION_EXPERIMENT_PREDECLARATION_DAY10.md` (frozen
before training M_B/M_AB). Feasibility audit:
`docs/INTERACTION_EXPERIMENT_FEASIBILITY_DAY10.md`. Source artifact:
`results/sleep_edf_interaction_resp_day10.json`.

## Capacity fairness (verified before any result was inspected)

All four configurations are the identical `SleepStageClassifier` class,
differing only in `in_channels`. Parameter counts: M0=8,197, M_A=8,309,
M_B=8,309, M_AB=8,421. The per-channel parameter cost is **exactly constant
(112 params/channel)** across every step (M0→M_A, M0→M_B, M_B→M_AB) - the
predeclared safeguard passed, so this result is interpreted rather than
aborted.

## Four-configuration results (5 seeds, sample SD)

| Config | Channels | Macro-F1 mean ± SD | Source |
|---|---|---|---|
| M0 | EEG | 0.7473 ± 0.0244 | Existing frozen checkpoints (not retrained) |
| M_A | EEG + EOG | 0.7693 ± 0.0132 | Existing frozen checkpoints (not retrained) |
| M_B | EEG + Resp | 0.7332 ± 0.0240 | New (Day 10) |
| M_AB | EEG + EOG + Resp | 0.7583 ± 0.0229 | New (Day 10) |

## Benefit and interaction terms

| Term | Mean | Sample SD | Seeds favoring positive |
|---|---|---|---|
| Benefit(A) = M_A − M0 | +0.0220 | 0.0228 | 4/5 |
| Benefit(B) = M_B − M0 | −0.0140 | 0.0281 | 2/5 |
| Benefit(AB) = M_AB − M0 | +0.0111 | 0.0289 | 3/5 |
| **Interaction = Benefit(AB) − Benefit(A) − Benefit(B)** | **+0.0031** | **0.0434** | 2/5 positive, 3/5 negative |

## Interpretation

**Candidate B (Resp oro-nasal) alone does not show a clear benefit** over
EEG-only in this cohort - its mean effect is slightly negative and only
2/5 seeds favor it, with a sample SD (0.028) larger than its own mean
magnitude (0.014). This is itself a legitimate, disclosed negative/null
result: adding a respiratory channel to raw EEG does not clearly improve
5-class sleep-stage classification under this frozen protocol.

**The interaction term is centered near zero (+0.003) with a sample SD
(0.043) roughly 14x its own mean**, and its per-seed sign is split 2
positive / 3 negative. Per the predeclared interpretation rules, this is
classified **`approximately_additive_or_unresolved`** - there is no
consistent evidence of either super-additive (synergy) or sub-additive
(redundancy) interaction between EOG and Resp for this target. The honest
reading is that the data do not resolve the interaction question one way or
the other at n=5 seeds; a larger seed count or a different candidate-B
signal would be needed to say more.

**This experiment does not upgrade or weaken any existing claim.** M0 and
M_A reproduce their already-frozen values exactly (loaded, not retrained).
The new information is entirely about M_B and M_AB, and about Resp/EOG
interaction - it does not change the EOG marginal-value finding, its
control, or its secondary-holdout support.

## H2 correction (Day 12): Resp channel bandwidth caveat

The Resp oro-nasal channel used here is natively sampled at **1 Hz**, not
100 Hz as originally stated in the Day-10 feasibility audit (corrected in
`docs/SLEEP_RESPIRATION_RATE_PROVENANCE_DAY12.md`). It is represented on
the same 100 Hz tensor grid as EEG/EOG via MNE's FFT-based upsampling on
load - the training arrays themselves are unchanged by this correction
(the loader has always used `preload=True` and has always produced this
exact resampled representation). The scientific consequence: despite equal
tensor length, the Resp channel cannot carry information above ~0.5 Hz
(its native Nyquist limit), unlike the genuinely-100-Hz EEG/EOG channels.
This is a plausible contributing explanation for Candidate B (Resp alone)
showing no clear benefit, and is now an explicit limitation of this
experiment - it does **not** strengthen the interaction claim in either
direction.

## What this experiment does NOT establish

- No claim of physiological synergy or redundancy between EOG and
  respiratory signals - "interaction" here is a purely statistical
  decomposition of measured macro-F1 differences.
- No claim about which sensors belong in a final architecture.
- No claim that Resp oro-nasal is globally unhelpful for sleep staging -
  this is one dataset, one architecture, one 12/3/3 split, 5 seeds.
- No resolution of the project's broader "one-at-a-time marginal value
  does not prove global minimality" limitation (`docs/SENSOR_INTERACTION_LIMITATION.md`)
  - this experiment materially **addresses** that limitation for one
  specific pair of candidates on one target, but does not close it in
  general (PPG-DaLiA IMU×EDA/TEMP and PTT second-site×IMU interactions
  remain open, per the feasibility audit's deferred candidates).
