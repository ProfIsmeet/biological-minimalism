# Furkan Paper Handoff — Day 9 (Sleep-EDF Secondary Holdout)

Exact result-level and methodology-level updates needed if the IAC paper
cites the Sleep-EDF EOG result. No marketing/narrative language — that
judgment belongs to the paper's authors. See `docs/FURKAN_PAPER_HANDOFF_DAY7.md`
for prior (still valid, unchanged) PPG-DaLiA/PTT/Sleep-EDF-primary updates.

## What changed since Day 7/8

The Sleep-EDF EOG result previously rested on a shuffled-EOG negative
control (Day 8) plus a 3-subject primary test where the aggregate effect
was driven almost entirely by one subject (SC4011). Day 9 adds a
**prospective secondary holdout**: 8 subjects from the same PhysioNet
Sleep-EDFx cassette study, never used in training/validation/the primary
test, frozen and predeclared before any evaluation, evaluated with the
existing frozen checkpoints (no retraining).

## Result-level updates required if citing the Sleep-EDF result

1. **Original primary experiment** (unchanged, still cite as-is): macro-F1
   0.747→0.769 (baseline→aligned candidate), 4/5 seeds favor EOG; shuffled-
   EOG control macro-F1 0.742 (≈ baseline, control fails to help, 5/5 seeds
   favor the aligned candidate over the shuffled control). Cite
   `docs/SLEEP_EDF_SHUFFLED_EOG_RESULTS.md`.
2. **New: prospective secondary holdout (n=8, independent cohort)**: same
   direction reproduces — A 0.653, B 0.686, C 0.656 macro-F1 (5-seed means);
   A→B and C→B both favor B in 5/5 seeds. **This is same-dataset
   generalization evidence, not independent-dataset replication** — do not
   describe it as "validated on a second dataset" or "population-level
   replication." Cite `docs/SLEEP_EDF_SECONDARY_HOLDOUT_RESULTS.md`.
3. **Subject-level claim upgrade**: if the paper previously noted "the
   sleep-stage result is driven by one subject" as a limitation, that
   limitation is now **partially addressed but not eliminated** — the
   secondary cohort's effect is more distributed (largest single-subject
   share of the summed effect is 41%, vs. the primary test being carried
   almost entirely by one of three subjects), and 6/8 secondary subjects
   favor the candidate. Two secondary subjects (SC4191, SC4251) show a
   small negative or near-zero effect — do not omit this if citing the
   subject-level table.
4. **Class-level claim**: the N1/REM improvement pattern (largest gains in
   REM, consistent with EOG's expected relevance to eye-movement-driven
   staging) reproduces in the secondary cohort. N3 is one class that
   **regresses** under the aligned-EOG model in the secondary cohort —
   this did not appear as a regression in the primary cohort. If the paper
   claims "every class improves," that claim must be scoped to the primary
   cohort only, or revised.

## Methodology-level updates required

- If the paper wants to claim the marginal-value finding "generalizes,"
  the precise, defensible framing is: *generalizes to an independent
  cohort within the same dataset/recording protocol*, not to an
  independent dataset or population. This is deliberate — see
  `docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md` SS8's new prospective-
  secondary-holdout supplement, added specifically to prevent this
  overclaim.
- The evidence-strength taxonomy category itself (`replicated-with-control`)
  was **not** upgraded by the secondary holdout — a qualifier tag
  (`prospective_secondary_holdout_supported`) was appended instead. If the
  paper reports evidence strength as a label, use the tagged form, not a
  new invented category.
- Predeclaration discipline extended cleanly to a purely evaluation-only
  (no-retraining) secondary study: cohort identity was frozen and
  committed to git before the corresponding raw files were even
  downloaded, and before any prediction was computed. Useful precedent if
  the paper discusses this project's methodological rigor.

## Explicitly NOT provided by this handoff

- No marketing or narrative phrasing.
- No claim about which sensors belong in a "final" architecture.
- No claim of astronaut, spaceflight, or microgravity validation.
- No claim that the primary (n=3) and secondary (n=8) cohorts are one
  pooled n=11 test set — they must be reported separately in any table.
