# Stage 4 — Architecture Decision Framework & Pareto Science Inputs

For Emir/Project Coordinator, Claude/Integration Owner, and future Stage-5
synthesis. This is the SECOND, parallel Science Owner Stage-4 package —
it does not replace or duplicate `stage4-science-handoff`, it references
it. No new science was performed; no final architecture is selected here.

Accepted Stage-3 base: `stage3-gate3-final-resolver-closure @ 5c381014af61e5d10d41223963831b25b9ff23e6`.
Prior Stage-4 science package: `stage4-science-handoff @ 5730efd246df8a898d77ea60a32d04235078c215` (unmodified).

## Part I — Evidence confidence framework

See `results/stage4_architecture_science_decision_framework.json` for the
full mechanical definitions. Six tiers, each with an explicit,
evidence-field-driven rule (never assigned by impression):
`TIER_A_REPLICATED_SUPPORT` → `TIER_B_CONTROLLED_SUPPORT` →
`TIER_C_BOUNDED_SUPPORT` → `TIER_D_MIXED_OR_FRAGILE` →
`TIER_E_NEGATIVE_OR_DEPRIORITIZED` → `TIER_P_PENDING`. Current occupants:

- **Tier A**: wrist PPG+IMU (two independent datasets, capacity-controlled).
- **Tier B**: EOG same-dataset (Sleep-EDF corrected A/B/C).
- **Tier C**: HMC bounded, ds003838 bounded (both inconclusive by design).
- **Tier D**: thoracic EIS, leg BioZ, sleep interaction (mixed/fragile).
- **Tier E**: second-site PPG (consistently negative).
- **Tier P**: wrist temperature, wrist light (no governing experiment exists).

## Part II — Sensor-by-sensor decision status

| Modality | Status | Confidence Tier |
|---|---|---|
| wrist PPG + IMU | `CORE_CANDIDATE` | TIER_A |
| EOG (with EEG) | `SUPPORTED_CANDIDATE` | TIER_B (same-dataset) / TIER_C (external) |
| thoracic BioZ/EIS | `CONDITIONAL_CANDIDATE` | TIER_D |
| leg BioZ | `EXPERIMENTAL_CANDIDATE` | TIER_D |
| second-site PPG | `DEPRIORITIZED_CANDIDATE` | TIER_E |
| wrist temperature/light | `PENDING_DECISION_EVIDENCE` | TIER_P |
| sparse-vs-full EEG (ds003838) | `PENDING_DECISION_EVIDENCE` | TIER_C |

Full detail (proposed role, strongest evidence/counter-evidence, what
future evidence could change the conclusion) is in
`results/stage4_science_consumption_manifest.json` and
`results/stage4_sensor_decision_sensitivity.json`.

## Part III — Decision-flip thresholds

The two HIGH-sensitivity items and their explicit flip conditions (full
detail in `results/stage4_sensor_decision_sensitivity.json`):

- **EOG / HMC full-cohort** (Scenarios HMC-1/2/3): strong external
  replication → promotable toward Tier A; near-zero effect → stays Tier C
  "inconclusive," not negative; stable external negative → downgrade
  toward `EXPERIMENTAL_CANDIDATE`.
- **Sparse-vs-full EEG / ds003838 full cohort** (Scenarios DS-1/2/3):
  approximate equality → supports minimization; materially worse →
  weakens minimization; strong subject heterogeneity → may justify a
  conditional/adaptive architecture class rather than one universal
  configuration.

All other fragile/mixed modalities (second-site PPG, leg BioZ, thoracic
EIS, sleep interaction) are rated LOW decision sensitivity — no
currently-planned Stage-3 experiment would resolve their ambiguity
further; new experimental design would be required, which is out of
current scope.

## Part IV — Scientific Pareto inputs

Eight axes (full detail in `results/stage4_scientific_pareto_inputs.json`):
incremental value, breadth, evidence maturity, robustness, uniqueness,
dependency, decision fragility, mission relevance. **No arbitrary
weighted composite score is computed** — this is deliberate multi-
objective preparation, not a pre-baked ranking. Engineering burden axes
remain Integration Owner's responsibility.

## Part V — Shared-resource science interpretation

- **PPG + IMU**: IMU's replicated, modest incremental value is
  wrist-co-locatable with PPG — its architecture burden case may be
  justified even for a modest effect size *because* physical marginal
  burden may be low (subject to Integration Owner's engineering
  confirmation).
- **EEG + EOG**: EOG has bounded same-dataset support with pending
  external replication. If shared AFE/reference infrastructure is
  engineering-feasible, its marginal hardware burden may differ
  substantially from treating it as an independent module — a real
  science/engineering interface point, not yet engineering-confirmed.
- **ECG + thoracic BioZ/EIS**: shared chest placement may reduce some
  physical burden, but current EIS scientific incremental value remains
  mixed/negative-leaning for the tested target. **Shared location alone
  must not manufacture scientific value that the data does not show.**
- **Trunk + leg BioZ**: leg BioZ introduces real additional
  attachment/body-region burden and did not demonstrate stable aggregate
  value — a genuine burden-without-clear-benefit case per current
  evidence.

**Governing rule, stated explicitly**: low burden does not transform weak
evidence into strong evidence, and strong evidence does not automatically
justify extreme burden. Both dimensions are preserved independently.

## Part VI — Architecture configuration framework

Four candidate classes defined in
`results/stage4_architecture_candidate_classes.json` (no winner
selected): `MINIMAL_CORE` (Tier-A sensors only) →
`CORE_PLUS_CONTEXT` (+ EOG, assuming shared-infrastructure feasibility) →
`EVIDENCE_EXTENDED` (+ thoracic EIS, leg BioZ, on mission-relevance
grounds despite mixed evidence) → `EXPERIMENTAL_EXTENDED` (+ second-site
PPG, wrist temp/light, explicitly exploratory).

## Part VII — Architecture acceptance gates

Eight gates in `results/stage4_architecture_acceptance_gates.json`,
classified by severity:

- **HARD_BLOCK** (must pass, no exception): provenance (A), excluded-
  sensor rationale (B), evidence-status honesty (C), burden completeness
  (D), negative-result preservation (F), claim consistency (G), Digital
  Twin separation (H).
- **COORDINATOR_DECISION_REQUIRED**: pending-science sensitivity (E) —
  for every current HIGH-sensitivity item (EOG/HMC, sparse-EEG/ds003838),
  Emir must explicitly choose WAIT / FREEZE_CONDITIONALLY /
  FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE before freeze.

Gate D (burden completeness) is explicitly `NOT_READY` — it is
Integration Owner's deliverable, not produced by this package.

## Part VIII — Configuration dominance rules

A configuration may be flagged `POTENTIALLY_DOMINATED` (never
`DOMINATED` outright — that requires Integration Owner's confirmed
burden data) when it adds a new body region, substantial contacts, or
real power/data burden, while providing no stable incremental evidence
and no unique validated endpoint. Conversely, a small co-located sensor
with replicated incremental value (e.g. wrist IMU) may survive Pareto
analysis even with a modest effect size, because its marginal burden is
plausibly near-zero. Both determinations require Integration Owner's
engineering burden confirmation before being called `PARETO_RELEVANT`
with confidence — this package only flags candidates for that analysis.

## Part IX — Claim / jury decision traceability

Reusable conditional template per modality (tested question → key result
→ replication → heterogeneity → burden context → architecture
implication → safe jury wording), populated for every modality in
`results/stage4_science_consumption_manifest.json`. Two worked examples:

> **If retained** (wrist IMU): the strongest justification is that
> synchronized IMU showed modest, capacity-controlled incremental
> HR-estimation value in PPG-DaLiA, and this direction externally
> replicated in the corrected GalaxyPPG cohort, while adding no new body
> region in a wrist-co-located design.

> **If excluded or deprioritized** (thoracic EIS): the evidence basis is
> that protocol-compliant LBNP testing did not show stable aggregate
> incremental value beyond ECG+pleth for the tested central-hypovolemic-
> stress target, and remained substantially subject-9-influenced.

Architecture-dependent wording (which class was actually chosen) is left
as a template slot — not finalized here.

## Part X — Paper table schemas (not populated final prose)

Six table schemas prepared, with currently-known science fields
populated and architecture-dependent fields left `UNRESOLVED`:

- **Table A** — Modality evidence summary (one row per modality, from
  the sensor-value matrix).
- **Table B** — Controlled ablation results (A/A_cap/B/C per family,
  from the consumption manifest).
- **Table C** — External replication (GalaxyPPG vs PPG-DaLiA; HMC bounded
  vs Sleep-EDF, explicitly marked inconclusive not negative).
- **Table D** — Negative/mixed experiments (thoracic EIS, leg BioZ,
  second-site PPG, sleep interaction).
- **Table E** — Final architecture rationale — **all fields UNRESOLVED**,
  to be populated only after Coordinator freeze.
- **Table F** — Science vs. burden tradeoff — science-side columns
  populated from `results/stage4_scientific_pareto_inputs.json`;
  burden-side columns left for Integration Owner.

These schemas are not separately materialized as a new artifact file in
this sprint — populate them directly from `results/stage4_science_consumption_manifest.json`,
`results/stage4_scientific_sensor_value_matrix.json`, and
`results/stage4_scientific_pareto_inputs.json` when the actual paper
draft is prepared, to avoid a third, potentially-drifting copy of the
same numbers.

## Coordinator decisions still required

1. For EOG (HMC-dependent) and sparse-vs-full EEG (ds003838-dependent):
   explicitly choose WAIT / FREEZE_CONDITIONALLY /
   FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE (Gate E).
2. Whether HMC full-cohort and/or ds003838 full-cohort work should be
   resumed before Stage 5, given their HIGH decision sensitivity — this
   remains explicitly Emir's call (unchanged from the prior Stage-3
   handoff).
3. The actual final architecture selection itself — this package
   provides inputs, never a selection.

## What Claude/Integration Owner may consume

The confidence-tier system, sensitivity map, scientific Pareto axes,
acceptance gates, and candidate classes (all five new artifacts plus
this document) — for rendering, implementing, or feeding into an
engineering burden analysis. Claude may NOT reinterpret any tier
assignment, sensitivity rating, or gate readiness without Coordinator
authorization, and may not select a final architecture from these inputs
alone.
