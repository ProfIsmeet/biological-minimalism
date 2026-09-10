# Stage 3 Handoff to Emir and Integration Owner

Self-contained — no chat history required. Branch:
`stage3-science-completion`. **Not canonical** — pending both the ongoing
Codex independent audit of `ab798815882ac0723491dc489de2375f8bf5b774`
(untouched) and Emir's own review of this sprint's work.

## What is COMPLETE and may eventually be surfaced (once accepted)

- **LBNP thoracic EIS**: real, complete, negative result. Safe to cite as
  "thoracic EIS did not add value beyond ECG+pleth in this real n=12
  cohort" — never as an astronaut/microgravity claim.
- **GalaxyPPG corrected single fold**: real, complete, positive result
  (3 subjects). Safe to cite as "consistent, qualitatively-PPG-DaLiA-
  reproducing IMU benefit at this bounded scale" — never as full
  replication.

## What is BOUNDED / HISTORICAL — do not present as complete

- GalaxyPPG's pre-fix single-fold and full-6-fold-CV results: **INVALIDATED**
  by a real reference-signal-quality defect. Do not cite their MAE numbers
  for anything.
- HMC n=7 bounded diagnostic (prior sprint): historical, negative-leaning,
  too small to conclude anything about the full cohort either way.
- ds003838 n=3 bounded diagnostic (prior sprint): historical, inconclusive
  by design.

## What is PENDING (real work remaining, not a design choice)

- GalaxyPPG full 6-fold CV under the corrected 18-subject eligibility.
- HMC full-cohort training (access is real and working; 45/151 downloaded;
  training not started).
- ds003838 full 65-subject cohort (quantified: ~93GB/~9.4h additional
  download needed).

## What Integration Owner should NOT do

- Do not surface any INVALIDATED GalaxyPPG number anywhere.
- Do not present HMC or ds003838 as having a canonical full-cohort result.
- Do not select final architecture or compute a formal Pareto frontier.
- Do not merge this branch into a canonical integration branch without
  Emir's explicit acceptance.

## Recommendation for Emir

1. Route this branch for review alongside (not instead of) the ongoing
   Codex audit of the parent SHA.
2. Budget a dedicated session for GalaxyPPG's full corrected-eligibility
   CV (5 more folds, similar cost to what this sprint already spent) and
   for HMC's full-cohort download+training (likely the single largest
   remaining compute item across the whole project).
3. Treat the GalaxyPPG BLOCKER finding as a positive signal about this
   project's hostile-review discipline — it was found, not covered up,
   and fixed with full before/after transparency.
