# Furkan Paper Handoff — Day 7 / Accelerated Day 8

Exact result-level and methodology-level updates needed if the IAC paper
cites any of these experiments. No marketing/narrative language included
— that judgment belongs to the paper's authors.

## Result-level updates required

1. **PPG-DaLiA IMU result**: any prior draft text citing "~23% HR-MAE
   improvement from adding IMU" or "9.09 → 7.03 bpm" must be revised. The
   correct, capacity-controlled figure is: after controlling for model
   capacity, synchronized IMU still improves HR-MAE by **~0.605 bpm
   (5/5 seeds consistent)**, but **~68% of the originally-reported total
   benefit (~1.88 bpm) is now attributed to model capacity/architecture,
   not IMU sensing information**. Cite
   `docs/PPG_DALIA_CAPACITY_CONTROL_RESULTS.md` for the full number set.
2. **PTT second-site result**: if cited as "second PPG site does not
   help HR estimation," add the heterogeneity caveat: **the aggregate
   negative result is driven almost entirely by one held-out subject
   (s2); the other 3 subjects show a heterogeneous, not uniformly
   negative, effect.** Cite `docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md`
   Appendix and `results/ptt_sensitivity_analysis.json`. Do not state
   "second PPG site is not useful" without this qualifier.
3. **New result available for citation**: Sleep-EDF EEG-vs-EEG+EOG
   sleep-stage classification — macro-F1 0.747→0.769 (4/5 seeds favor
   EOG), largest gains in N1/REM. This is a NEW target (not HR), useful
   if the paper wants to demonstrate the marginal-value methodology
   generalizes beyond heart rate. Cite `docs/SLEEP_EDF_EEG_EOG_RESULTS.md`.

## Methodology-level updates required

- If the paper describes the marginal-value methodology as validated only
  for HR/regression tasks, that is now outdated — it has been
  successfully applied to a classification task (5-class sleep stage) on
  a different modality family (EEG/EOG), with the same capacity-fairness
  discipline applied from the start (not retrofitted).
- If the paper discusses capacity/architecture fairness at all, it should
  now cite the PPG-DaLiA capacity-confound finding as a concrete example
  of why this matters — a naive ablation without a capacity-matched
  control substantially overstated a sensor's marginal value in this
  project's own data.
- If the paper claims or implies a path toward "the optimal sensor set,"
  it must now cite `docs/SENSOR_INTERACTION_LIMITATION.md`: one-at-a-time
  marginal experiments cannot prove global optimality because sensor
  interaction effects are unmeasured.
- Statistical reporting: any table quoting a multi-seed standard
  deviation should note whether it is population (ddof=0, as in the
  original artifacts) or sample (ddof=1, the now-recommended convention
  for new work) — see `docs/STATISTICAL_REPORTING_AUDIT.md`. The
  difference is ~1.12x for n=5 and does not change any directional
  conclusion, but exact numbers in a table should specify which
  convention was used.

## Explicitly NOT provided by this handoff

- No marketing or narrative phrasing.
- No claim about which sensors belong in a "final" architecture — that
  remains outside this document's and this track's scope.
- No operational-cost or Pareto content.
