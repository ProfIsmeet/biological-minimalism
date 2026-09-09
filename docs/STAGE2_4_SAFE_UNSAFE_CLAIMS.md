# Stage 2-4 Science Completion — Safe / Unsafe Claims

## Safe principles (governing all claims below)

- Sensor value is target-specific, dataset-specific, protocol-specific.
- Negative results are valid and reported in full.
- Heterogeneity (subject/class dominance) is evidence, not noise to average away.
- Missing evidence stays missing — never filled in by inference or extrapolation.
- Aligned-vs-shuffled controls are bounded mechanistic support, not causal proof.
- Independent-dataset replication is valuable only when the replication is
  genuinely independent (different subjects, different device/protocol family).
- Terrestrial data never equals astronaut/spaceflight/microgravity validation.

## Unsafe claims (never made, regardless of any individual result)

- Globally minimal sensor set / final four sensors.
- EOG or IMU declared strictly "necessary."
- Leg BioZ declared universally useless (or universally beneficial).
- Full cognitive state recovery from any EEG subset.
- Astronaut or microgravity validation from any terrestrial dataset in this
  project (QDE, GalaxyPPG, LBNP, HMC, ds003838 are ALL terrestrial).
- A validated Digital Twin.
- A universal cross-metric sensor ranking or fake weighted score.
- Formal global Pareto optimality (Pareto status remains `NOT_READY`).

## Per-experiment safe claim ledger (updated this sprint)

- **Sleep V2 corrected A/B**: "Under a corrected, seed-controlled,
  capacity-matched protocol, EOG added sleep-staging macro-F1 beyond EEG
  alone (mean +0.0282, 4/5 seeds favorable)." Cross-platform reproduction
  (Claude, Mac) independently confirms direction and favorable-seed count.
- **Sleep V2 corrected C**: see final numeric result once training
  completes this sprint (in progress) — claim will be scoped to "B vs.
  temporally-deranged-EOG control, same architecture/capacity."
- **Sleep V2 corrected interaction**: claim will state the exact
  `stability_classification` the numbers produce (`super_additive_leaning`
  / `sub_additive_leaning` / `approximately_additive_or_unresolved`) —
  never forced toward a "cleaner" answer.
- **HMC**: pending full-cohort training this sprint. If it completes: claim
  will be scoped to "independent-family reproduction attempt on a clinical
  cohort distinct from Sleep-EDF's healthy-volunteer population" — never
  "replication," per the frozen protocol's forbidden-claims list.
- **QDE V2**: "Bilateral leg impedance did not show a robust,
  subject-consistent improvement over arm+trunk impedance for
  baseline-relative body-mass change in this n=10 cohort; a majority of
  subjects show a small favorable direction, but the aggregate is dominated
  and reversed by one outlier subject (subject 2)." Never "leg BioZ is
  useless" or "leg BioZ measures fluid shift."
- **GalaxyPPG / LBNP**: access was blocked for two full prior sprints and
  is now resolved this sprint — any claim depends entirely on the actual
  training result, not yet known at the time this doc was written. No
  claim is made about IMU/EIS value until real numbers exist.
- **ds003838**: "The n=3 bounded diagnostic proved the real-file access
  path and loader work correctly, and that the negative control (C)
  behaves exactly as expected (chance-level)." No claim about the actual
  sparse-vs-full-EEG information question — that remains open pending a
  larger cohort.

This ledger is updated with exact numbers in the final Stage 2-4 report
once all in-flight training/downloads complete.
