# Day 9 — Canonical Integration State

Single source of truth for the reconciled Day-8/9 project state on branch
`day8-9-systems-readiness`. Ends cross-machine ambiguity: this branch is the canonical
integration of the Claude systems track and Ismet's Sleep-EDF strengthening + prospective
secondary-holdout track. **This is NOT a final freeze.**

## Merge lineage
- Systems base: `223d6c2` (safety tag `pre-day9-integration-safety`).
- Merged: `origin/day9-sleep-secondary-holdout-ml` @ `a2581ed` (contains Day-8
  `origin/day8-sleep-strengthening-ml` @ `110641c`) via `--no-ff` merge `731c83d`.
- Common ancestor `d1295ac`; semantic merge, 2 real conflicts resolved.
- Follow-on commits: `be01831` (derived-artifact regen + PENDING resolution),
  `b026d2e` (Research API sleep primary/secondary/control), `568bb94` (claim checker,
  traceability, jury/freeze/paper/storyline docs).

## Scientific state (verified from artifacts)
- **PPG-DaLiA / IMU (HR):** positive, capacity-controlled. A_cap→B ~0.605 bpm, C→B ~0.776 bpm
  (5/5 seeds). Raw A→B ~20.6% is capacity-confounded. Decision: CONDITIONAL_FOR_TARGET.
- **PTT / second PPG site (HR):** aggregate negative (~17.540 vs ~19.003 MAE), 5/5 seeds same
  direction, heterogeneous (2/4 subjects each way, s2-sensitive; s2 retained).
  Decision: DEPRIORITIZE_FOR_TARGET. No global removal.
- **Sleep-EDF / EOG (5-class):** primary n=3 (A 0.7473 / B 0.7693 / C 0.7420; C→B 5/5;
  SC4011-dominated) + prospective secondary holdout n=8 (A 0.6530 / B 0.6858 / C 0.6556;
  A→B 5/5, C→B 5/5; 6/8 B>A, 7/8 B>C; zero retraining). Class-level: REM +0.150, **N3 −0.043
  (regression, disclosed; precision effect)**. Evidence: `replicated-with-control` +
  `prospective_secondary_holdout_supported`. Decision: CONDITIONAL_FOR_TARGET (scientific
  blocker resolved; ocular electrode/contact burden unresolved).

## Canonical Sleep claim
> Under a frozen capacity-matched protocol, aligned EOG improved 5-class Sleep-EDF macro-F1 over
> EEG-only in the original primary test and again in a prospectively frozen 8-subject secondary
> holdout. A capacity-identical shuffled-EOG control was consistently worse than aligned EOG in
> both evaluations, supporting a role for temporally aligned ocular information. The evidence
> remains single-dataset, terrestrial, and non-uniform across subjects/classes.

NOT claimed: independent-dataset replication; pooled n=11; EOG necessity; uniform benefit;
astronaut/microgravity validation; trained Digital Twin.

## Global architecture / Pareto
- Final architecture: **UNRESOLVED** (no RETAIN outcome; interaction evidence unavailable).
- Formal Pareto: **NOT_READY** (power/energy, mass, electrode montage, full BOM absent).

## Checkpoint archival
Externally durable + independently re-verified on the integration Mac: GitHub Release
`day8-checkpoint-archive-v1`, SHA256 `5e0661a6d5adcf345dfc86fe4c80138b20df405038a13817c7d97a1189572de4`,
50 checkpoints, 0 raw datasets.

## Verification summary (this integration)
- ML tests: 188 passed, 21 skipped (data/checkpoint-gated), 0 failed.
- Backend tests: 124 passed. Frontend: lint + build clean.
- All deterministic builders re-run: zero-diff (deterministic). No conflict markers.
- Claim consistency checker: 0 issues (extended with stale-pending detectors).
- Live browser validation (CDP): `/research`, `/digital-twin`, `/mission-overview`,
  pareto-readiness — no console errors; sleep primary vs secondary shown separately (no
  pooling), shuffled control + N3 regression visible, Digital Twin untrained/synthetic,
  Pareto NOT_READY.

## Environments (distinct, not conflated)
- Training (frozen): Python 3.13.0 + torch 2.6.0 CPU (`results/environment_manifest.json`).
- Integration/backend (this Mac): Python 3.14 + torch 2.14 (no 2.6.0 wheel for 3.14).
- Frontend: Node/Next.js dev + build.

## Still open before final freeze
Final architecture, formal Pareto, power/mass/BOM, final paper freeze, final dashboard freeze,
final jury rehearsal. See `docs/FINAL_FREEZE_READINESS_CHECKLIST.md`.
