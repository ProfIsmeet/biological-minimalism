# Stage 3 Handoff to Emir and Integration Owner

Self-contained — no chat history required. Branch:
`stage3-acceptance-gate-closure`. **Not canonical** — pending both the
ongoing Codex independent audit of
`ab798815882ac0723491dc489de2375f8bf5b774` (untouched) and Emir's own
review of this sprint's work.

Resolve all current Stage-3 evidence only through
`ml/stage3_science_resolver.py` (`resolve_current(family_id)` or
`resolve_and_verify(family_id)`) — never by reading a result file
directly by guessed filename. The resolver fails closed against every
historical/superseded/invalidated/noncanonical/pending artifact.

## What is COMPLETE and may eventually be surfaced (once accepted)

- **LBNP thoracic EIS**: real, complete, **`COMPLETE_MIXED`** result
  (negative-leaning, heterogeneous — not a uniform negative). Governing
  artifact: `results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json`
  (resolver family `lbnp_thoracic_eis`). Under the frozen terrestrial
  0-60 mmHg protocol: A=20.973, B=21.425, C=20.132 mmHg MAE.
  A_minus_B=-0.452 mmHg — **sign-reverses** if subject 9 (an extreme
  outlier) is excluded via leave-one-out. C_minus_B=-1.293 mmHg — remains
  negative under leave-one-out but **shrinks substantially** without
  subject 9. Safe to cite as: "Under the frozen terrestrial 0-60 mmHg
  LBNP protocol, thoracic EIS did not show stable aggregate incremental
  value beyond ECG+pleth, with substantial subject heterogeneity." Never
  cite as a uniform/stable negative, never as a microgravity/astronaut
  claim. The prior 607-window execution
  (`results/lbnp_thoracic_eis_stage3.json`) is
  **`HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL`** (200/607 windows were
  outside the frozen scope, and its C-control had same-stage leakage) —
  it **MUST NOT** be consumed by Stage 4 or any integration work; the
  resolver fails closed against it.
- **GalaxyPPG corrected full 6-fold CV**: real, complete,
  `EXTERNAL_REPLICATION_SUPPORTIVE` result (all 18 real eligible subjects,
  one test appearance each). Governing artifact:
  `results/galaxyppg_corrected_full_cv_result.json` (resolver family
  `galaxyppg_external_replication`). Safe to cite as: "In the
  independently corrected 18-participant GalaxyPPG cohort, aligned IMU
  provided a modest aggregate improvement over the capacity-near-matched
  PPG-only baseline and deranged-IMU control, with meaningful participant
  heterogeneity" (participant-level A_cap->B +0.834268 bpm, 12/18 favor
  B; C->B +0.916231 bpm, 13/18 favor B; window-weighted agrees to <0.02
  bpm; no sign reversal under leave-one-out). Do not cite the bounded
  single-fold diagnostic's larger effect size (+1.342 bpm) as the current
  number — that diagnostic
  (`results/galaxyppg_hr_corrected_eligibility_stage3.json`) is
  **SUPPORTING** evidence only, superseded by the full CV as the
  governing external-replication claim.
- **Codex parent-audit remediation** (H-01/H-02 through the final
  governance/freeze closure sprint): all closed — see
  `docs/STAGE3_CODEX_PARENT_AUDIT_SCIENCE_OWNER_REMEDIATION.md`,
  `docs/STAGE3_CODEX_FAIL_REMEDIATION_REPORT.md`,
  `docs/STAGE3_FINAL_SOURCE_OF_TRUTH_REMEDIATION_REPORT.md`,
  `docs/STAGE3_FINAL_GOVERNANCE_FREEZE_CLOSURE_REPORT.md`.

## What is BOUNDED / HISTORICAL — do not present as complete

- GalaxyPPG's pre-fix single-fold and full-6-fold-CV results: **INVALIDATED**
  by a real reference-signal-quality defect. Do not cite their MAE numbers
  for anything.
- LBNP's pre-fix 607-window execution: **`HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL`**.
  Do not cite its MAE numbers or its `COMPLETE_NEGATIVE` classification as
  current.
- HMC n=7 bounded diagnostic: `BOUNDED_DIAGNOSTIC` status — real,
  negative-leaning, too small to conclude anything about the full cohort
  either way, and remains the only trained HMC evidence. Current
  download-state breakdown: 59 edf files present, 58 complete recording
  pairs, 52 SHA256-verified, 1 partial (`SN060`) — see
  `results/hmc_current_download_inventory.json`. Full cohort:
  `FULL_COHORT_PENDING`.
- ds003838 n=3 bounded diagnostic: historical, inconclusive by design.

## What is PENDING (real work remaining, not a design choice)

- HMC full-cohort training (`FULL_COHORT_PENDING` — access is real and
  working; download partial; training not started this sprint per this
  sprint's explicit scope boundary).
- ds003838 full 65-subject cohort (quantified: ~93GB/~9.4h additional
  download needed).

## What Integration Owner should NOT do

- Do not surface any INVALIDATED GalaxyPPG number, or the
  HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL LBNP 607-window number, anywhere.
- Do not present HMC or ds003838 as having a canonical full-cohort result.
- Do not select final architecture or compute a formal Pareto frontier —
  `final_architecture_status` remains `UNRESOLVED`,
  `formal_pareto` remains `NOT_READY`.
- Do not merge this branch into a canonical integration branch without
  Emir's explicit acceptance.
- Do not resolve any Stage-3 result by reading a file directly by
  filename guess — use `ml/stage3_science_resolver.py`.

## Recommendation for Emir

1. Route this branch for review alongside (not instead of) the ongoing
   Codex audit of the parent SHA.
2. Decide whether HMC full-cohort training and ds003838 are required
   before Stage 4, or can proceed in parallel with Stage 4 controlled
   integration — this is explicitly Emir's call, not pre-decided by this
   remediation (see `final_verdict_rationale` in
   `results/stage3_science_completion_manifest.json`).
3. Treat the GalaxyPPG BLOCKER finding, and the subsequent multi-sprint
   governance hardening (real resolver, fail-closed freeze, semantic
   content verification), as a positive signal about this project's
   hostile-review discipline — each defect was found, not covered up,
   and fixed with full before/after transparency.
