# Stage 4 Final Architecture Decision Preparation

For Emir/Project Coordinator. This memo is understandable without reading
the rest of the repo. It is **decision preparation, not a decision** — no
final architecture, no Pareto winner, and no Gate-E choice is made here.

Machine-readable companion: `results/stage4_final_architecture_decision_packet.json`.

## 1. Current project state

- Accepted Stage-3 science: `stage3-gate3-final-resolver-closure @ 5c38101`.
- Stage-4 science handoff (per-family evidence): `stage4-science-handoff @ 5730efd` — consumed.
- Stage-4 architecture decision framework (confidence tiers, sensitivity, Pareto axes, gates, candidate classes): `stage4-architecture-decision-framework @ fa71eec` — consumed in this sprint (`docs/STAGE4_ARCHITECTURE_DECISION_FRAMEWORK_HANDOFF.md`).
- Stage-4 controlled integration (backend/frontend/tests, independently audited PASS): `stage4-controlled-integration @ 05c0ff8` — this sprint's base.
- `final_architecture_status = UNRESOLVED`, `formal_pareto_status = NOT_READY` everywhere in this package, unchanged by this sprint.

## 2. Candidate architectures (no winner)

Four Science-Owner-defined classes, each a strict superset of the prior one for presentation clarity only (`results/stage4_architecture_candidate_classes.json`):

| Class | Adds | Evidence confidence | Pending-science exposure |
|---|---|---|---|
| `MINIMAL_CORE` | wrist PPG+IMU, chest ECG, frontal EEG | TIER_A (PPG+IMU) | NONE |
| `CORE_PLUS_CONTEXT` | + EOG (shared head AFE) | TIER_B same-dataset / TIER_C external | HIGH (HMC full-cohort) |
| `EVIDENCE_EXTENDED` | + thoracic BioZ, leg BioZ | TIER_D (both) | LOW |
| `EXPERIMENTAL_EXTENDED` | + second-site PPG, wrist temp/light | TIER_E / TIER_P | LOW / MEDIUM |

Full per-class sensor lists, power/data-rate sums, and module requirements: `results/stage4_candidate_class_burden_comparison.json`.

## 3. Science differences between candidates

- `MINIMAL_CORE → CORE_PLUS_CONTEXT`: adds EOG on same-dataset controlled evidence (Sleep-EDF, +0.028 macro-F1) with external validity still open (HMC bounded n=7 is statistically underpowered in either direction).
- `CORE_PLUS_CONTEXT → EVIDENCE_EXTENDED`: adds thoracic BioZ (MIXED, negative-leaning, subject-9-dominated) and leg BioZ (MIXED, single-outlier-dominated) — included on mission-relevance grounds, not evidence strength; the Science Owner is explicit that this is a scope argument, not an evidence-strength argument.
- `EVIDENCE_EXTENDED → EXPERIMENTAL_EXTENDED`: adds second-site PPG (consistently NEGATIVE result) and wrist temp/light (no governing experiment exists at all) — explicitly exploratory, never evidence-supported.

Per-decision-unit detail (confidence tier, external replication, heterogeneity, decision-flip conditions): `results/stage4_architecture_decision_projection.json`.

## 4. Burden differences between candidates

Power and raw data-rate are additive and summed per class from already-published component values (`results/stage4_engineering_readiness.json`); mass is **module-granular only** — the chest module (ECG+thoracic BioZ) cannot currently be decomposed into per-sensor submasses, so every class touching that module carries the same `BURDEN_DATA_INCOMPLETE` mass flag. Key deltas:

- EOG's isolated incremental cost is small and well-characterized: **+0.375 mW, +0.4 g** (shares the head module's AFE/battery/enclosure) — *assuming* shared-AFE co-location is engineering-feasible, which is asserted, not yet confirmed.
- Thoracic BioZ contributes **1.335 mW** — one of the single largest power contributors in the system — for evidence that is mixed/negative-leaning.
- Leg BioZ adds a genuinely new body region: its own module, **8.431 g**, excluded from every system total.
- Second-site PPG adds **~6.0–9.0 mW** (scenario-dependent) and 28,500 bps raw — both larger than several already-included modalities — for a negative result.

Full dimension-by-dimension audit and shared-resource accounting: `results/stage4_gate_d_burden_completeness.json`.

## 5. HIGH pending-science sensitivities

Two items, both requiring an explicit Gate-E Coordinator choice (`results/stage4_gate_e_coordinator_options.json`):

1. **EOG external validity (HMC full-cohort, 151 recordings)** — current evidence (n=7, 1 held-out recording) is too underpowered to distinguish strong replication from a near-zero or negative result.
2. **Sparse-vs-full EEG channel-count minimization (ds003838 full ~65-subject cohort)** — current evidence (n=3) cannot distinguish approximate equality, material worsening, or strong subject heterogeneity (which could itself justify a subject-adaptive architecture class rather than a fixed channel count).

## 6. Gate D state

**`GATE_D_BURDEN_COMPLETENESS = NOT_READY`.**

Arithmetic is independently verified correct and every previously-open power/mass/data-rate blocker now has an explicit, labeled value — real progress. But two categories of unknown remain **unbounded** (not merely imprecise): (a) electrode/contact counts for ECG, EEG-main-montage, and thoracic/leg BioZ are literally absent, and (b) the shared-hub-vs-per-module battery/electronics boundary is a fully open topology choice. Both could plausibly change how burden compares across candidates. Full rationale and the 4 concrete remediation items: `results/stage4_gate_d_burden_completeness.json`.

## 7. Gate E options (Coordinator must choose, not this memo)

For **each** of the two HIGH-sensitivity items above, three options exist — WAIT, FREEZE_CONDITIONALLY, or FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE — each with its own benefit/cost, revision trigger, or disclosure language spelled out in `results/stage4_gate_e_coordinator_options.json`. No option is recommended here.

## 8. What the Coordinator must decide

1. EOG/HMC: WAIT / FREEZE_CONDITIONALLY / FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE.
2. Sparse-vs-full EEG/ds003838: WAIT / FREEZE_CONDITIONALLY / FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE.
3. Whether to resume HMC and/or ds003838 full-cohort work before Stage 5 (unchanged from the Stage-3 handoff — remains Emir's call).
4. Which Gate-D remediation item(s) to prioritize before a final freeze (module-boundary decision; electrode/contact count freeze; chest-module decomposition; EOG shared-AFE engineering confirmation).
5. The final architecture selection itself.

## 9. What happens after the decision

Once items 1–4 above are resolved, Gate D can be re-assessed (potentially reaching `CONDITIONALLY_READY` or `READY`) and Gate E closes on the recorded Coordinator choices. Only then can a formal Pareto analysis be authorized and a final architecture selected — both remain explicitly out of scope for this closure-prep sprint.
