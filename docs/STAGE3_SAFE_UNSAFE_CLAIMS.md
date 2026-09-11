# Stage 3 Safe / Unsafe Claims

## LBNP (protocol-compliant rerun, HIGH-03/final-source-of-truth remediation - CURRENT)

**Safe with limitation**: "Corrected LBNP shows no stable aggregate
incremental thoracic EIS benefit over ECG+pleth under the frozen
terrestrial 0-60 mmHg protocol, with substantial subject heterogeneity."
Full detail: real, frozen LOSO protocol on the actual-file-verified usable
cohort (n=12 of 16 — 4 subjects excluded for real missing pleth data, a
predeclared data-quality rule), with the frozen 0-60 mmHg target range
enforced (407/607 in-scope windows; 200 out-of-scope 70-100mmHg windows
excluded) and a different-stage-enforced C-control (0 same-stage
collisions). A−B mean −0.452 mmHg MAE (3/12 subjects favor B) — this
SIGN-REVERSES if subject 9 is excluded via leave-one-out. C−B mean −1.293
mmHg (5/12 favor B over C) — remains negative under leave-one-out but
shrinks substantially without subject 9. Classification: `COMPLETE_MIXED`.

**Unsafe**: "Thoracic BioZ is useless [in general]." "Thoracic EIS
definitively worsens prediction for all subjects." "This proves central
hypovolemia cannot be detected via impedance." Any microgravity/
astronaut/spaceflight fluid-shift-disproven equivalence. Any claim about
abdominal/arm EIS sites (untested). Citing the old 607-window execution
(`results/lbnp_thoracic_eis_stage3.json`, A−B≈−2.24, `COMPLETE_NEGATIVE`,
`HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL`) as governing.

## GalaxyPPG (corrected full 6-fold grouped CV, COMPLETE - CURRENT)

**Current state**: source cohort n=24; 6 excluded for a real corrupted-
reference-ECG data-integrity defect (multi-dimensional QC, HIGH-02),
leaving 18 real eligible participants. Full 6-fold grouped CV complete —
every one of the 18 eligible subjects tested exactly once. Governing
result: `results/galaxyppg_corrected_full_cv_result.json`, classification
`EXTERNAL_REPLICATION_SUPPORTIVE`. Participant-level A_cap→B=+0.834268
bpm (12/18 favor B); C→B=+0.916231 bpm (13/18 favor B, HIGH-01-corrected).
Window-weighted aggregation agrees to <0.02 bpm. No sign reversal under
leave-one-out exclusion of the most extreme subject, but real,
disclosed heterogeneity: 6/18 subjects favor A_cap over B, 5/18 favor C
over B.

**Safe**: "In the independently corrected 18-participant GalaxyPPG
cohort, aligned IMU provided a modest aggregate improvement over the
capacity-near-matched PPG-only baseline and deranged-IMU control, with
meaningful participant heterogeneity."

**Unsafe**: "IMU always improves HR" / universal or all-subject benefit.
"GalaxyPPG replicates/refutes PPG-DaLiA" (even the full CV remains one
dataset/device family; "qualitatively consistent with" / "did not
reproduce" is the correct language per this project's established
convention, never "replicated"). "24/24 subjects eligible" (6 were
excluded for a real data-integrity defect). Any astronaut/microgravity
validation claim. Any claim of causal necessity for IMU inclusion. Citing
the invalidated pre-fix single-fold or full-CV results
(`results/galaxyppg_hr_external_replication_stage2.json`,
`results/galaxyppg_hr_full_grouped_cv_stage3.json`) as current.

## HMC (real access restored; full training FULL_COHORT_PENDING)

**Safe**: "PhysioNet's certificate is confirmed renewed and full-cohort
access is real and working. Current download state
(`results/hmc_current_download_inventory.json`): 59 edf files present,
58 complete recording pairs (edf+annotation), 52 SHA256-verified against
PhysioNet's own SHA256SUMS.txt, 1 partial (`SN060`). Full-cohort A/B/C
training is prepared (`ml/train_hmc_sleep_a_b_c_full_cohort.py`) but has
not been completed — a genuine compute/time-budget limit across multiple
sprints, not an access blocker or a design choice."

**Unsafe**: "HMC replicates or fails to replicate Sleep-EDF" (no full
result exists yet). The n=7 bounded diagnostic
(`results/hmc_sleep_external_replication_stage3_bounded_n7.json`) has
status `BOUNDED_DIAGNOSTIC` — it is the only trained HMC evidence, not
"historical," and must not be promoted to a full-cohort claim.

## ds003838 (unchanged, quantified blocker documented this sprint)

**Safe**: "The full 65-subject cohort requires ~93 GB / ~9.4h of
additional real download beyond the n=3 bounded diagnostic already
completed — quantified this sprint, not attempted given higher-priority
GalaxyPPG/LBNP/HMC work."

**Unsafe**: Any sparse-vs-full EEG information claim beyond the n=3
bounded diagnostic (unchanged, already disclosed as inconclusive).

## Carried-forward unsafe claims (unchanged, still governing)

All prior sprints' forbidden claims remain in force: no final
architecture, no formal Pareto, no astronaut/microgravity validation from
any terrestrial dataset, no fake global sensor score, no sensor declared
strictly necessary.
