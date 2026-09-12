# Stage 4 Final Architecture Decision Preparation

> **Superseded-for-the-decision note (Stage 4 Final Architecture Closure sprint):**
> The Coordinator has since made every decision this memo lists as open in
> Section 8. This document is preserved verbatim as the historical
> pre-closure record — it is **not rewritten**. See
> `docs/STAGE4_FINAL_ARCHITECTURE_CLOSURE.md` and
> `results/final_wearable_architecture.json` for the actual final decision.

For Emir/Project Coordinator. This memo is understandable without reading
the rest of the repo. It is **decision preparation, not a decision** — no
final architecture, no Pareto winner, and no Gate-E choice is made here.

Machine-readable companion: `results/stage4_final_architecture_decision_packet.json`.

**Update (Gate D Burden Closure sprint):** Gate D moved from `NOT_READY` to
`CONDITIONALLY_READY` — contact/electrode counts and battery/MCU-radio
topology are now bounded (not exact) and candidate-ordering is confirmed
robust across every tested bound. See Section 6.

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

Full per-class sensor lists, power/data-rate sums, and module requirements: `results/stage4_candidate_class_burden_comparison.json`. Bounded contact counts, battery-topology scenarios, and robustness-tested burden ranges: `results/stage4_candidate_burden_matrix.json`.

## 3. Science differences between candidates

- `MINIMAL_CORE → CORE_PLUS_CONTEXT`: adds EOG on same-dataset controlled evidence (Sleep-EDF, +0.028 macro-F1) with external validity still open (HMC bounded n=7 is statistically underpowered in either direction).
- `CORE_PLUS_CONTEXT → EVIDENCE_EXTENDED`: adds thoracic BioZ (MIXED, negative-leaning, subject-9-dominated) and leg BioZ (MIXED, single-outlier-dominated) — included on mission-relevance grounds, not evidence strength; the Science Owner is explicit that this is a scope argument, not an evidence-strength argument.
- `EVIDENCE_EXTENDED → EXPERIMENTAL_EXTENDED`: adds second-site PPG (consistently NEGATIVE result) and wrist temp/light (no governing experiment exists at all) — explicitly exploratory, never evidence-supported.

Per-decision-unit detail (confidence tier, external replication, heterogeneity, decision-flip conditions): `results/stage4_architecture_decision_projection.json`.

## 4. Burden differences between candidates

Power and raw data-rate are additive and summed per class from already-published component values (`results/stage4_engineering_readiness.json`); mass is **module-granular only** — the chest module (ECG+thoracic BioZ) cannot currently be decomposed into per-sensor submasses (now bounded to a **0.21–0.53 g** delta, see `chest_module_decomposition` in `results/stage4_gate_d_burden_completeness.json`). Key deltas:

- EOG's isolated incremental cost is small and well-characterized: **+0.375 mW, +0.4 g** (shares the head module's AFE/battery/enclosure) — shared-AFE co-location is now **engineering-confirmed** (standard ADS1299-family multi-channel architecture), not just assumed.
- Thoracic BioZ contributes **1.335 mW** — one of the single largest power contributors in the system — for evidence that is mixed/negative-leaning.
- Leg BioZ adds a genuinely new body region: its own module, **8.431 g** (per-leg reference), excluded from every system total. **New this sprint:** the Science Owner scopes leg BioZ as *bilateral* (both legs), but the engineering model never stated whether this means 1 shared multiplexed module or 2 independent ones — bounded at **4–8 contacts**, most likely 8 (bilateral).
- Second-site PPG adds **~6.0–9.0 mW** (scenario-dependent) and 28,500 bps raw — both larger than several already-included modalities — for a negative result.
- **New this sprint:** the hardware topology contract lists a separate MCU + radio per body-worn module, but the authoritative power total only charges one MCU + one radio system-wide. Bounding both interpretations, `EVIDENCE_EXTENDED`'s battery-side power ranges from **8.79 mW** (1 shared MCU/radio) to **15.22 mW** (1 per module) — see `results/stage4_candidate_burden_matrix.json`.

Full dimension-by-dimension audit and shared-resource accounting: `results/stage4_gate_d_burden_completeness.json`. Bounded electrode/contact counts for every modality: `results/stage4_contact_electrode_burden.json`.

## 4a. Which burden conclusions are topology-independent vs. battery-dependent

- **Topology-independent (robust either way):** the relative *ordering* of the four candidate classes by burden — `MINIMAL_CORE ≤ CORE_PLUS_CONTEXT ≤ EVIDENCE_EXTENDED ≤ EXPERIMENTAL_EXTENDED` — holds under every tested combination of contact-count bound, battery topology, and MCU/radio topology (`results/stage4_candidate_burden_matrix.json` `robustness_analysis`), because each class is a strict superset of the last and every addition can only add burden.
- **Battery/electronics-topology-dependent (absolute magnitude only):** battery cell mass itself is scenario-neutral (shared-hub vs. distributed use the same total Wh at the same density), but a shared hub adds an unmodeled cross-body wiring harness (bounded 0.3–1.5 g per remote-module connection); and the MCU/radio single-vs-per-module question can roughly double a multi-module class's power. Neither swing reverses which class is more or less burdensome than another — both only affect *how much* more.

## 4b. Gate D — the four original remediation items, now bounded

| Item | Status | Evidence |
|---|---|---|
| Battery/module-boundary topology | Bounded (both scenarios modeled) | `results/stage4_battery_topology_scenarios.json` |
| Electrode/contact counts | Bounded (ranges + method per modality) | `results/stage4_contact_electrode_burden.json` |
| Chest-module ECG/BioZ mass decomposition | Bounded (0.21–0.53 g delta) | `results/stage4_gate_d_burden_completeness.json#chest_module_decomposition` |
| EEG+EOG shared-AFE feasibility | Engineering-confirmed (standard multi-channel AFE architecture) | `results/stage4_gate_d_burden_completeness.json#eeg_eog_shared_afe_confirmation` |

## 5. HIGH pending-science sensitivities

Two items, both requiring an explicit Gate-E Coordinator choice (`results/stage4_gate_e_coordinator_options.json`):

1. **EOG external validity (HMC full-cohort, 151 recordings)** — current evidence (n=7, 1 held-out recording) is too underpowered to distinguish strong replication from a near-zero or negative result.
2. **Sparse-vs-full EEG channel-count minimization (ds003838 full ~65-subject cohort)** — current evidence (n=3) cannot distinguish approximate equality, material worsening, or strong subject heterogeneity (which could itself justify a subject-adaptive architecture class rather than a fixed channel count).

## 6. Gate D state

**`GATE_D_BURDEN_COMPLETENESS = CONDITIONALLY_READY`** (upgraded from `NOT_READY`; the prior assessment is preserved verbatim in `results/stage4_gate_d_burden_completeness.json#assessment_history`).

All four of the prior sprint's remediation items are now closed to a **bounded** (not exact/final) state — see 4b above. This sprint's own hostile audit of power completeness also surfaced one materially significant new finding (the per-module vs. single-shared MCU/radio question) and bounded it immediately upon discovery. `results/stage4_candidate_burden_matrix.json`'s `robustness_analysis` **computationally confirms** — not merely asserts — that relative candidate-class ordering is preserved across every tested combination of these bounds. This meets the definition of `CONDITIONALLY_READY` ("some absolute values remain uncertain but uncertainties are explicitly bounded, relative ordering is robust"), not full `READY` (several bounds remain ranges, not frozen exact values — final montage/topology decisions are still open engineering choices). Disclosure of that residual approximation is required at freeze time. Full rationale: `results/stage4_gate_d_burden_completeness.json`.

## 7. Gate E options (Coordinator must choose, not this memo)

For **each** of the two HIGH-sensitivity items above, three options exist — WAIT, FREEZE_CONDITIONALLY, or FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE — each with its own benefit/cost, revision trigger, or disclosure language spelled out in `results/stage4_gate_e_coordinator_options.json`. No option is recommended here.

## 8. What the Coordinator must decide

1. EOG/HMC: WAIT / FREEZE_CONDITIONALLY / FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE.
2. Sparse-vs-full EEG/ds003838: WAIT / FREEZE_CONDITIONALLY / FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE.
3. Whether to resume HMC and/or ds003838 full-cohort work before Stage 5 (unchanged from the Stage-3 handoff — remains Emir's call).
4. Battery/electronics topology: shared-hub vs. distributed-per-module, and single-shared vs. per-module MCU/radio — bounded, not resolved; doesn't change candidate ordering but changes absolute burden magnitude for `EVIDENCE_EXTENDED`/`EXPERIMENTAL_EXTENDED`.
5. Final electrode montages for ECG/EEG/thoracic-BioZ/leg-BioZ (bounded ranges exist; not yet frozen to exact counts).
6. Leg BioZ unilateral-vs-bilateral module topology (Science Owner scopes it bilateral; engineering module count not yet confirmed either way).
7. Whether `CONDITIONALLY_READY` (bounded, disclosed uncertainty) is sufficient to proceed to a formal Pareto analysis and final freeze, or whether full `READY` (items 4–6 frozen to exact values) should be required first.
8. The final architecture selection itself.

## 9. What happens after the decision

Gate D is no longer the blocking gate it was — decision item 7 above is now the operative choice: proceed to a formal Pareto analysis under `CONDITIONALLY_READY`'s disclosed bounded uncertainty, or wait for items 4–6 to freeze to exact values first. Either way, Gate E still needs the Coordinator's recorded choices for both HIGH-sensitivity items before a final architecture freeze. A formal Pareto analysis and final architecture selection both remain explicitly out of scope for this sprint.
