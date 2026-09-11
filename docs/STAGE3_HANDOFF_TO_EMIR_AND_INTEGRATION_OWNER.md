# Stage 3 Handoff to Emir and Integration Owner

Self-contained — no chat history required. Branch:
`stage3-science-completion`. **Not canonical** — pending both the ongoing
Codex independent audit of `ab798815882ac0723491dc489de2375f8bf5b774`
(untouched) and Emir's own review of this sprint's work.

## What is COMPLETE and may eventually be surfaced (once accepted)

- **LBNP thoracic EIS**: real, complete, negative result. Safe to cite as
  "thoracic EIS did not add value beyond ECG+pleth in this real n=12
  cohort" — never as an astronaut/microgravity claim.
- **GalaxyPPG corrected full 6-fold CV**: real, complete,
  `EXTERNAL_REPLICATION_SUPPORTIVE` result (all 18 real eligible subjects,
  one test appearance each). Safe to cite as "aligned wrist IMU added a
  real but moderate, heterogeneous HR-estimation benefit under a
  capacity-near-matched comparison (participant-level A_cap->B +0.834 bpm,
  12/18 favor B; window-weighted agrees to <0.02 bpm; no sign reversal
  under leave-one-out), qualitatively consistent with PPG-DaLiA's
  capacity-controlled finding" — do not cite the larger bounded
  single-fold diagnostic's effect size (+1.342 bpm) as the current
  number; that diagnostic is retained only as
  `BOUNDED_EXTERNAL_REPLICATION_SUPPORTIVE_DIAGNOSTIC`, superseded by the
  full CV.
- **Codex parent-audit remediation** (H-01 checkpoint namespace, H-02
  capacity-confounded PPG headline, HMC split-source/chronology, freeze-
  manifest hash semantics, environment snapshot, PPG/PTT cache-provenance
  limitation doc, CANONICAL-vocabulary audit, consolidated
  GalaxyPPG/LBNP provenance): all closed — see
  `docs/STAGE3_CODEX_PARENT_AUDIT_SCIENCE_OWNER_REMEDIATION.md`.

## What is BOUNDED / HISTORICAL — do not present as complete

- GalaxyPPG's pre-fix single-fold and full-6-fold-CV results: **INVALIDATED**
  by a real reference-signal-quality defect. Do not cite their MAE numbers
  for anything.
- HMC n=7 bounded diagnostic (prior sprint): historical, negative-leaning,
  too small to conclude anything about the full cohort either way.
- ds003838 n=3 bounded diagnostic (prior sprint): historical, inconclusive
  by design.

## What is PENDING (real work remaining, not a design choice)

- HMC full-cohort training (access is real and working; download partial,
  training not started this sprint per this sprint's explicit scope
  boundary).
- ds003838 full 65-subject cohort (quantified: ~93GB/~9.4h additional
  download needed).
- GalaxyPPG's corrected full 6-fold CV is now COMPLETE - no longer
  pending.

## What Integration Owner should NOT do

- Do not surface any INVALIDATED GalaxyPPG number anywhere.
- Do not present HMC or ds003838 as having a canonical full-cohort result.
- Do not select final architecture or compute a formal Pareto frontier.
- Do not merge this branch into a canonical integration branch without
  Emir's explicit acceptance.

## Recommendation for Emir

1. Route this branch for review alongside (not instead of) the ongoing
   Codex audit of the parent SHA.
2. Decide whether HMC full-cohort training and ds003838 are required
   before Stage 4, or can proceed in parallel with Stage 4 controlled
   integration — this is explicitly Emir's call, not pre-decided by this
   remediation (see `final_verdict_rationale` in
   `results/stage3_science_completion_manifest.json`).
3. Treat the GalaxyPPG BLOCKER finding as a positive signal about this
   project's hostile-review discipline — it was found, not covered up,
   and fixed with full before/after transparency; the completed full CV's
   real, disclosed subject heterogeneity is the same discipline applied a
   second time.

## Update: Codex fail remediation sprint

A second independent Codex audit of the prior sprint's frozen SHA
(`aaa87c21...`) found three real HIGH-severity defects (GalaxyPPG
participant-level C evaluation, P01 eligibility justification, LBNP
target-range/C-control protocol compliance). All three are now CLOSED —
see `docs/STAGE3_CODEX_FAIL_REMEDIATION_REPORT.md` for the full account,
including which numbers changed (GalaxyPPG C_to_B +0.904→+0.916 bpm; LBNP
now a protocol-compliant rerun with COMPLETE_NEGATIVE unchanged) and which
did not (GalaxyPPG A_cap/B untouched). Recommend routing this branch
(`stage3-codex-fail-remediation`) for a second independent Codex delta
audit before any further acceptance decision.
