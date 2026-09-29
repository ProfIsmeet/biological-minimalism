# Visualization Inventory — Stage 6 Scientific Visualization Redesign

Every existing visualization relevant to Stage 6's scope, and the decision
made for each.

| ID | Route | Component | Question answered | Data source | Decision | Notes |
|---|---|---|---|---|---|---|
| V-01 | /mission-overview | `ModalityPentagon.tsx` | Which of the 5 final modalities is currently confirmed? | `useOperationalViewModel()` | **REPLACE** | Replaced by `CoverageFreshnessMatrix` (Family A+D) — a real topology diagram, not fake, but the coverage question is better answered by a direct list separating static-architecture membership from live observation. File kept, unmounted. |
| V-02 | /mission-overview | `InferenceHexFlow.tsx` | What is blocking the HR output right now? | `deriveHexFlow()` (`lib/monitoring/inferenceHexFlow.ts`) | **REDESIGN** | Pure logic reused unmodified; rendering changed from hexagonal geometry to a linear strip (`PipelineStateStrip`) per explicit instruction. File kept, unmounted. |
| V-03 | /mission-overview | `FaultRecoverySpine.tsx` | What faults/recoveries happened this session? | `useOperationalEventStore()` | **REPLACE** | Equal-spaced-by-index layout using client wall-clock, not real replay time — a genuine defect by the master task's own C requirements. Replaced by `FaultRecoveryTimeline` (real time axis). File kept, unmounted. |
| V-04 | /mission-overview | `OperationalEventRail.tsx` | Same event log, alternate list view | `useOperationalEventStore()` | **MERGE** | Duplicate representation of the same event log as V-03; merged into the one `FaultRecoveryTimeline` (chart + accessible table). File kept, unmounted. |
| V-05 | /mission-overview | `RecentHrEstimateTrend.tsx` | What was the recent HR trend? | `deriveHrTrend()` (`lib/monitoring/hrTrend.ts`) | **KEEP + enlarge** | Pure derivation was already scientifically correct (real gap detection, no fabricated values); only the container was sparkline-sized (120-140px). Enlarged to 220-260px, added y-axis unit label and more ticks. Logic untouched. |
| V-06 | /mission-overview | `SignalRibbonMatrix.tsx` / `SignalLaneChart.tsx` | What do the raw waveforms look like? | `useOperationalViewModel().modalities[].plot` | **KEEP** | Investigated for the "hover-only data" defect pattern; found NOT to qualify — modality identity, sample rate, per-lane value range, and a shared visible time-range label are all already visible without hovering; only the exact instantaneous point value is tooltip-gated, a reasonable supplement. No change made. |
| V-07 | /system-brief | `ConditionalSelectionRadial.tsx` | How do MINIMAL_CORE and CORE_PLUS_CONTEXT compare? | `api.getFinalWearableArchitecture()` | **REPLACE** | Decorative SVG wedge diagram (radial rings/spokes), explicitly named in the master task as a required replacement target. Replaced by `ArchitectureDeltaMatrix` (Family E, full per-modality table). File kept, unmounted. |
| V-08 | /system-brief | `MinimalCoreComparison.tsx` | Two-line MINIMAL_CORE vs. CORE_PLUS_CONTEXT summary | `lib/architecture.ts` static constants | **KEEP** | A short, real, non-decorative intro card; complements rather than duplicates the new full matrix. No change made. |
| V-09 | /research/experimental | `ExperimentalDispositionOrbit.tsx` | Which candidates were excluded, and where? | `useResearchStore().finalWearableArchitecture` | **REMOVE (demoted)** | Decorative SVG orbit rendering the exact same `exclusion_rationale` data as `CandidateDispositionMatrix.tsx`, immediately below it — a genuine, confirmed duplicate. Unmounted from the route; file kept. |
| V-10 | /research/experimental | `CandidateDispositionMatrix.tsx` | Candidate disposition, with what evidence? | `useResearchStore()` live fetch | **MERGE (enriched)** | Already real, table-first, mobile-responsive. Enriched in place with two new columns (numeric result & direction, population scope) from Family F's bundled table_d excerpt, rather than building a duplicate component. |
| V-11 | /research/experimental | `SensitivityAblationSection.tsx` | Text summary of ablation/sensitivity families | `/research/stage3-evidence` live fetch | **KEEP** | Real, text-based, already discloses heterogeneity/limitation verbatim from the artifact. Complements, does not duplicate, the new visual small multiples (different families of evidence: this covers 5 stage3-evidence families including some not in the small-multiples set). |
| V-12 | new | *(none existed)* | Selected-vs-observed coverage per modality | `useOperationalViewModel()` | **NEW** (Family A+D) | `CoverageFreshnessMatrix.tsx` |
| V-13 | new | *(none existed)* | Real time-scaled fault/recovery record | `operationalEvents.ts` + `useConfirmedHistory()` | **NEW** (Family C) | `FaultRecoveryTimeline.tsx` |
| V-14 | new | *(none existed)* | Participant/seed-level sensitivity with honest uncertainty | bundled `results/` excerpts | **NEW** (Family G) | `SensitivitySmallMultiples.tsx` |

## Decision summary

| Decision | Count |
|---|---|
| KEEP | 3 (V-05 logic unchanged but enlarged, V-06, V-08, V-11) |
| REDESIGN | 1 (V-02) |
| REPLACE | 2 (V-01, V-07) |
| MERGE | 2 (V-04 into V-13, V-10 enriched in place) |
| REMOVE (demoted, file kept) | 1 (V-09) |
| NEW | 3 (V-12, V-13, V-14) |
| TABLE_IS_BETTER | 0 — no existing chart was judged better replaced by a table alone; tables were added as accessible equivalents alongside every new chart, not as chart replacements |
| BLOCKED_BY_MISSING_AUTHORITATIVE_DATA | 0 |

No component was deleted. Every unmounted legacy component (`ModalityPentagon.tsx`,
`InferenceHexFlow.tsx`, `FaultRecoverySpine.tsx`, `OperationalEventRail.tsx`,
`ConditionalSelectionRadial.tsx`, `ExperimentalDispositionOrbit.tsx`) remains in
the repository, matching the project's own pre-existing precedent
(`InferenceIntegrityOrbit.tsx`, unmounted by an earlier stage).
