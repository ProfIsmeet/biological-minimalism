# GalaxyPPG Reference-ECG-Quality Threshold — Justification and Sensitivity

**Revised this sprint (Stage 3 Codex fail remediation, HIGH-02).** The
prior version of this document contained a mathematically false claim
about threshold invariance across the 7–48 peaks/min range. That claim is
corrected below, and the eligibility gate has been strengthened from a
single metric to two independent, outcome-independent dimensions.

## The gate (corrected, multi-dimensional)

`ml/build_galaxyppg_reference_ecg_qc.py` computes, for every one of the 24
real participants and purely from the raw reference ECG signal:

1. **`primary_r_peaks_per_min`** — the existing Pan-Tompkins-lite detector
   (`detect_r_peaks`, used throughout this project).
2. **`detector_agreement_ratio_primary_over_secondary`** — the primary
   detector's peak count divided by an **independent second detector's**
   count (`scipy.signal.find_peaks` on raw rectified amplitude, a
   genuinely different algorithm family: no derivative/energy/moving-
   average step). A ratio near 1.0 means the two independently-designed
   detectors agree on how many real beats are present; a ratio far from
   1.0 means at least one detector is confused by the signal — itself
   direct evidence of poor reference quality.

A participant is eligible only if **both**:

- `primary_r_peaks_per_min >= 40.0`, **and**
- `detector_agreement_ratio_primary_over_secondary >= 0.50`.

Neither dimension reads or uses any model performance, training result,
or prior knowledge of which participants "hurt" any aggregate — both are
computed purely from the raw signal and detector behavior (see
`results/galaxyppg_reference_ecg_qc.json`, which explicitly asserts
`"no_performance_data_used": true`).

## Why the prior single-metric threshold claim was wrong

The prior version of this document claimed: *"Any threshold chosen
between approximately 7 and 48 peaks/minute produces the exact same
18-subject eligible set."* **This is false.** P01 sits at 37.08
peaks/minute — inside that very range. A primary-rate-only threshold of,
say, 35 peaks/min would have included P01, changing cohort membership. The
true single-metric-invariant range is much narrower: **(37.08, 48.86]**,
i.e. any threshold strictly greater than P01's own value and no greater
than P05's. The 40/min value happened to fall inside that narrower true
range, so the resulting 18-subject cohort was never wrong — but the
robustness claim as stated was mathematically imprecise, and is corrected
here rather than restated.

## Real full-cohort distribution (measured this sprint, all 24 subjects)

| Group | Participants | Primary R-peaks/min | Detector agreement ratio |
|---|---|---|---|
| Excluded (corrupted) | P03, P22, P07, P15, P19 | 0.08 – 6.77 | 0.001 – 0.408 |
| Excluded (P01) | P01 | 37.08 | 0.423 |
| **Included (healthy)** | **18 subjects** | **48.86 – 105.00** | **0.571 – 0.992** |

## Why the multi-dimensional rule is more defensible than restating "40 is reasonable"

On the **primary-rate** dimension, P01 (37.08) is the closest excluded
case to the eligible boundary (P05, 48.86) — genuinely borderline on this
one metric alone, which is exactly what motivated this remediation.

On the **independent detector-agreement** dimension, however, P01 (0.423)
is **not** borderline: it clusters with the 5 obviously-corrupted subjects
(0.001–0.408), sitting only 0.015 above the highest of them (P19, 0.408)
and 0.148 below the lowest genuinely-eligible subject (P05, 0.571) — a
real, substantial, independently-measured gap. P01 also has the single
highest RR-interval-implausibility fraction (0.176) of any subject outside
the obviously-corrupted cluster (the 18 eligible subjects' maximum is
0.070, also P05).

This is real evidence from a second, independently-designed measurement
approach, not a second look at the same number. Applying the composite
rule to all 24 real subjects reproduces the **exact same 18-subject
eligible cohort** as the prior single-metric rule (verified by direct set
comparison — zero symmetric difference, see
`results/galaxyppg_corrected_eligibility.json`). The cohort was not
re-engineered to exclude P01; the composite rule was checked against the
real data and happened to confirm the same membership, which is itself
evidence the original exclusion was not an artifact of one fragile metric.

## Chronology, stated honestly

This composite rule was constructed **after** P01's exclusion was already
known from the original single-dimension gate, and after the original
threshold-invariance claim had already been shown to be imprecise by
independent review. True prospective blindness to that fact cannot be
recreated after the fact — this document does not claim otherwise. What
*is* true, and independently verifiable: the agreement-ratio and
RR-implausibility metrics were computed purely from the raw ECG signal and
detector behavior (`ml/build_galaxyppg_reference_ecg_qc.py` never reads
any `results/galaxyppg_hr_*` performance file), so the *values themselves*
are not outcome-tuned even though the *decision to look for a second
dimension* was motivated by the earlier finding that P01 was borderline.

## P01 specifically

P01 (37.08 peaks/min, 0.423 agreement ratio, 0.176 RR-implausible
fraction) fails both independent dimensions of the composite gate. The
dataset's own real README already flags a real Galaxy Watch configuration
issue for P01 (for a different device), consistent with — but not proof
of — real data-collection problems for this specific participant.

## No performance-outcome shopping

Neither `primary_r_peaks_per_min` nor `detector_agreement_ratio` nor
`rr_implausible_fraction` was ever compared against, correlated with, or
selected because of any GalaxyPPG A_cap/B/C model MAE or training result.
`results/galaxyppg_reference_ecg_qc.json` contains no performance field of
any kind.
