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

## GalaxyPPG (full 6-fold grouped CV, this sprint)

**Safe**: see `docs/GALAXYPPG_STAGE3_FULL_CV_RESULTS.md` once written
(pending final aggregate) — will state the exact classification from
{SUPPORTIVE, MIXED, NEGATIVE, UNRESOLVED} based on all 24 real subjects'
held-out evaluation, never forced toward agreement/disagreement with
PPG-DaLiA.

**Unsafe**: "IMU always improves HR." "GalaxyPPG replicates/refutes
PPG-DaLiA" (even the full CV remains one dataset/device family; "did not
reproduce" / "reproduced under an independent protocol" is the correct
language per this project's established convention, never "replicated").

## HMC (real access restored this sprint; full training PENDING_DUE_TO_COMPUTE_OR_SESSION_LIMIT)

**Safe**: "PhysioNet's certificate is confirmed renewed and full-cohort
access is real and working. The full 151-recording download was resumed
this sprint; [N] recordings were downloaded and byte-verified by the end
of this session's time budget. Full-cohort A/B/C training is prepared
(`ml/train_hmc_sleep_a_b_c_full_cohort.py`) but was not completed within
this session — a genuine compute/time limit, not an access blocker or a
design choice."

**Unsafe**: "HMC replicates or fails to replicate Sleep-EDF" (no full
result exists yet this sprint). The n=7 bounded diagnostic remains
retained as historical, not promoted.

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
