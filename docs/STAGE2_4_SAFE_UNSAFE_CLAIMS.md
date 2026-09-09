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
- **Sleep V2 corrected C**: "B beats C by +0.0323 (4/5 seeds), nearly
  identical direction/magnitude to A→B (+0.0282, 4/5 seeds) — real evidence
  the EOG benefit reflects genuine temporal correspondence, not just
  capacity." N1 and REM classes show the largest B-vs-C gaps.
- **Sleep V2 corrected interaction**: real result is
  `approximately_additive_or_unresolved` (interaction mean −0.0078, SD
  0.0363, 3/5 seeds positive, 2/5 negative) — reported exactly as this
  frozen-rule outcome, never forced toward a cleaner answer. Resp alone
  (+0.0061) is much weaker than EOG alone (+0.0282), consistent with H2's
  low-bandwidth hypothesis, stated as a plausible explanation only.
- **HMC bounded n=7**: real result is negative-leaning — B−A = −0.0313 (only
  2/5 seeds favor B), B−C = +0.0080 (2/5 seeds favor B, near coin-flip).
  Explicitly reported as the frozen protocol's own predeclared negative
  outcome ("the Sleep-EDF EOG benefit did not reproduce on HMC's clinical
  cohort"), NOT generalized beyond this bounded n=7/1-test-recording
  diagnostic — full 151-cohort result is blocked by a genuine external
  PhysioNet TLS certificate expiry, not by design or effort.
- **QDE V2**: "Bilateral leg impedance did not show a robust,
  subject-consistent improvement over arm+trunk impedance for
  baseline-relative body-mass change in this n=10 cohort; a majority of
  subjects show a small favorable direction, but the aggregate is dominated
  and reversed by one outlier subject (subject 2)." Never "leg BioZ is
  useless" or "leg BioZ measures fluid shift."
- **GalaxyPPG / LBNP**: access blocked for two full prior sprints, resolved
  this sprint (Zenodo reachable again on one controlled recheck). Real
  archives downloaded and MD5-verified; real structure confirmed (24/16
  subjects respectively, independently re-confirmed from raw file
  structure for LBNP). A real cross-device UTC+9 timestamp bug was found
  and fixed for GalaxyPPG (verified via a working end-to-end R-peak
  reference-HR pipeline). Full A/B/C training was NOT completed this
  sprint (time-prioritized behind Sleep V2 and HMC per the master prompt's
  explicit ordering) — no IMU/EIS value claim is made, since no training
  was run.
- **ds003838**: "The n=3 bounded diagnostic proved the real-file access
  path and loader work correctly, and that the negative control (C)
  behaves exactly as expected (chance-level)." No claim about the actual
  sparse-vs-full-EEG information question — that remains open pending a
  larger cohort.

This ledger is updated with exact numbers in the final Stage 2-4 report
once all in-flight training/downloads complete.
