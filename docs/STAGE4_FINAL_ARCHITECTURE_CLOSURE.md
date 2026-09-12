# Stage 4 Final Architecture Closure

For Emir/Project Coordinator and independent audit. This memo records the
**actual final decision** — as distinct from
`docs/STAGE4_FINAL_ARCHITECTURE_DECISION_PREP.md`, which is preserved
verbatim as the historical pre-closure input record. Machine-readable
source of truth: `results/final_wearable_architecture.json`,
`results/stage4_formal_pareto_analysis.json`,
`results/stage4_gate_e_coordinator_decisions.json`,
`results/stage4_final_closure_manifest.json`.

This is a closure candidate, reported complete pending independent audit —
see Section 8. Stage 5 (paper/jury) is explicitly **not** started here.

## 1. Final architecture

**Selected: `CORE_PLUS_CONTEXT`** — wrist PPG + wrist IMU, chest ECG,
frontal EEG, EOG (sharing the EEG module's AFE/reference/ground).

| Body region | Module | Contents |
|---|---|---|
| Wrist | `wrist_module` | PPG, IMU |
| Chest | `chest_module` | ECG |
| Head | `head_module` | Frontal EEG, EOG (shared AFE) |

**Module topology: `DISTRIBUTED_BODY_MODULE_TOPOLOGY`** — each module keeps
its own local battery + MCU/radio domain (no cross-body shared hub). This
is the higher-power interpretation (per-module MCU/radio, not a single
system-wide one) and is accepted/disclosed as such, not hidden behind the
cheaper single-shared figure.

## 2. Contact model (~9 total)

| Modality | Total contacts (min–max, most likely) | Confidence |
|---|---|---|
| Wrist PPG + IMU | 1–1, most likely 1 | CLOSED |
| Chest ECG | 3–5, most likely 3 | BOUNDED_ENGINEERING_ESTIMATE |
| Frontal EEG | 3–6, most likely 3 | BOUNDED_ENGINEERING_ESTIMATE |
| EOG (incremental only, shares EEG reference/ground) | 2–2, most likely 2 | CLOSED |
| **Sum (most likely)** | **9** | matches `results/stage4_candidate_burden_matrix.json` CORE_PLUS_CONTEXT `total_contacts.most_likely` |

## 3. Burden (accepted, disclosed)

- Power (battery-side, selected distributed/per-module topology): **9.937 mW** — vs. 5.645 mW under the alternative single-shared-MCU/radio interpretation (not selected; source power assumptions unchanged, only the topology interpretation differs).
- Mass: 8.763 g battery-only (distributed topology avoids the shared-hub wiring-harness penalty entirely).
- Raw data rate: wrist PPG 1216 bps + wrist IMU 1536 bps + ECG 12000 bps + EEG/EOG 4800 bps.
- Every figure is a **bounded** engineering estimate (Gate D `CONDITIONALLY_READY`), not a final/exact BOM.

## 4. Excluded-sensor rationale table

| Excluded modality | Reason | Prohibited claim |
|---|---|---|
| Thoracic BioZ/EIS | Corrected protocol-compliant LBNP evidence is `COMPLETE_MIXED`, negative-leaning, heterogeneous | "BioZ is useless" — not the finding; preserved in scientific history |
| Leg BioZ | QDE V2 aggregate-negative, heterogeneous, sensitivity-fragile; adds new body region + contact/attachment burden | Generalization beyond the tested terrestrial endpoint |
| Second-site PPG | Negative/deprioritized PTT evidence; adds the single largest sensor power (9.018 mW) and data rate (28,500 bps) in the whole burden model | "Second PPG never helps" as a permanent claim |
| Wrist temperature/light | No governing experiment exists (`TIER_P_PENDING`) | Labeling as negative — correct status is insufficient/pending evidence |

None of these are erased from the scientific record — see
`results/stage4_science_consumption_manifest.json` and
`results/stage4_science_claim_ledger.json` for the full negative/mixed
evidence, preserved unchanged.

## 5. Gate D — burden completeness

`CONDITIONALLY_READY` → **`CLOSED_FOR_STAGE4_BY_COORDINATOR_ACCEPTANCE_OF_BOUNDED_ENGINEERING_UNCERTAINTY`**
(`results/stage4_gate_d_burden_completeness.json` schema v3.0.0,
`coordinator_acceptance` field). State history preserved append-only:
`NOT_READY` (v1.0.0) → `CONDITIONALLY_READY` (v2.0.0) →
`COORDINATOR_ACCEPTED_BOUNDED_UNCERTAINTY` (v3.0.0). **Not** silently
relabeled `READY` — the residual disclosure list (exact montages, vendor
parts, final topology freeze) remains open and is carried forward, not
hidden.

## 6. Gate E — pending-science sensitivity (Coordinator decisions)

| Item | Decision | Revision trigger |
|---|---|---|
| EOG external validity (HMC full-cohort) | `FREEZE_CONDITIONALLY` — EOG included | A stable, majority-consistent **HMC-3**-equivalent external-negative result reopens inclusion. A near-zero/inconclusive result (HMC-2) may trigger review but is not automatic. |
| Sparse-vs-full EEG channel count (ds003838 full cohort) | `FREEZE_CONDITIONALLY` — current sparse/minimal montage retained | A **DS-2** (materially worse) or **DS-3** (strong subject heterogeneity) full-cohort result reopens the channel-count architecture. |

HMC full and ds003838 full remain `LOWER_PRIORITY_EXTERNAL_WORK_PENDING` —
**not run, not marked complete**, and not required for this closure.

## 7. Formal Pareto result

`formal_pareto_status = COMPLETE`. **No single numeric score computed.**
No unique winner asserted.

| Class | Status |
|---|---|
| `MINIMAL_CORE` | Pareto-relevant (non-dominated) — not selected |
| `CORE_PLUS_CONTEXT` | Pareto-relevant (non-dominated) — **Coordinator selected** |
| `EVIDENCE_EXTENDED` | Potentially dominated (not formally proven dominated — see methodology below) |
| `EXPERIMENTAL_EXTENDED` | Potentially dominated (not formally proven dominated) |

> Coordinator selected `CORE_PLUS_CONTEXT` from the Pareto-relevant set
> because the EOG increment adds controlled sleep-staging evidence at low
> incremental physical burden without adding a new body region or full
> module, while accepting conditional external-validation uncertainty.

`CORE_PLUS_CONTEXT` does **not** mathematically dominate `MINIMAL_CORE` —
`MINIMAL_CORE` dominates on every burden axis; `CORE_PLUS_CONTEXT` dominates
on science breadth; neither dominates on both, so both remain Pareto-relevant.
`EVIDENCE_EXTENDED`/`EXPERIMENTAL_EXTENDED` are not formally proven
dominated either, because their added modalities target physiological
information `CORE_PLUS_CONTEXT` structurally cannot capture at all — a
breadth axis on which they are not weakly dominated, regardless of current
evidence quality. Full methodology and pairwise analysis:
`results/stage4_formal_pareto_analysis.json`.

## 8. Acceptance gates A–H

| Gate | Final state |
|---|---|
| A — Scientific provenance | PASS |
| B — Excluded-sensor rationale | PASS |
| C — Evidence status honesty | PASS |
| D — Burden completeness | `CONDITIONALLY_READY`, coordinator-accepted (Section 5) |
| E — Pending-science sensitivity | Closed by Coordinator decision (Section 6) |
| F — Negative-result preservation | PASS |
| G — Claim consistency | PASS (`ml/validate_stage4_science_claim_consistency.py`, `ml/validate_stage4_final_architecture_closure.py`) |
| H — Digital Twin separation | PASS (Digital Twin untouched, unreferenced by this closure) |

Full record: `results/stage4_final_closure_manifest.json`.

## 9. Claim migration — what may now be said

- A final Stage-4 wearable architecture has been selected: `CORE_PLUS_CONTEXT`.
- Selection is evidence-driven and burden-aware.
- EOG inclusion is conditional on pending external replication (HMC full-cohort).
- Sparse EEG channel choice is conditional on pending full-cohort evidence (ds003838).

## 10. Prohibited claims (unchanged, still enforced)

"Four sensors are proven sufficient" · "EOG is externally validated" ·
"Sparse EEG is population validated" · "BioZ is useless" · "Second PPG
never helps" · "Digital Twin is validated" · "Astronaut validation has been
achieved" · "`CORE_PLUS_CONTEXT` mathematically dominates every
architecture".

## 11. Status and next action

`STAGE4_FINAL_CLOSURE_CANDIDATE_REPORTED_COMPLETE_PENDING_INDEPENDENT_AUDIT`.
Not `STAGE4_VERIFIED_COMPLETE` — that requires independent audit. Stage 5
(paper/jury) is explicitly not authorized by this closure.
