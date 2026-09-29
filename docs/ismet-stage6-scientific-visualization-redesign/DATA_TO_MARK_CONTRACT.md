# Data-to-Mark Contract — Stage 6 Scientific Visualization Redesign

Every quantitative/categorical mark rendered by a new or redesigned Stage 6
visualization, with exact source, transformation, missing-value behavior,
and evidence class.

## Family A + D — `CoverageFreshnessMatrix.tsx`

| Field | Value |
|---|---|
| Source | `useOperationalViewModel().modalities[]` (live hook, `frontend/src/lib/monitoring/operationalViewModel.ts`) |
| Source field path | `OperationalModalityState.{modality, region, observation, nodeState, stateLabel}` |
| Transformation | None beyond selecting a display string per `nodeState`/`observation.state` via `coverageText()` |
| Aggregation | None — one row per modality |
| Filtering | None — all 5 `FINAL_SENSOR_INVENTORY` modalities always shown |
| Missing-value behavior | `observation.state === "unavailable"` renders "Not provided by this replay" / "Not reported by current telemetry" — never a blank cell, never 0 |
| Metric | Categorical state, not numeric |
| Evidence class | N/A (operational state, not a scientific result) |
| Caveat | This runtime exposes no per-channel last-confirmed age; shown as categorical state, not an invented freshness bar — stated explicitly in the component's own footer text |
| Cross-component consumers | None new — this is the sole consumer of this presentation |

## Family B — `PipelineStateStrip.tsx`

| Field | Value |
|---|---|
| Source | `deriveHexFlow()` (`lib/monitoring/inferenceHexFlow.ts`, unmodified) |
| Source field path | `HexNode.{id, label, state}` |
| Transformation | None — rendering only; the pure derivation is reused byte-for-byte |
| Missing-value behavior | N/A — always categorical, never numeric |
| Evidence class | N/A (operational state) |
| Caveat | Explicitly labeled "not a confidence score" in the component header |

## Family C — `FaultRecoveryTimeline.tsx`

| Field | Value |
|---|---|
| Source | `useOperationalEventStore().events` (`OperationalEvent[]`) + `useConfirmedHistory()` (HR samples) |
| Source field path | `OperationalEvent.sourceTimestampSeconds` (x-axis), `snapshot.heart_rate_prediction?.value` (y-axis) |
| Transformation | `deriveFaultRecoveryTimeline()` (new, pure, `lib/monitoring/faultRecoveryTimeline.ts`) pairs `fault_applied`→`fault_cleared` events per modality into intervals; sorts HR samples by timestamp |
| Missing-value behavior | A null `heart_rate_prediction` stays `null` in `hrPoints`, rendered via `connectNulls={false}` (real gap, never 0 or interpolated) |
| Axis availability rule | `axisAvailable = events.length > 0 && events.every(e => e.timeSeconds !== null)` — a single event lacking a real timestamp disables the entire time axis for that render, falling back to a text chronology |
| Ongoing-fault rule | An unclosed interval sets `clearSeconds: null, ongoing: true` and is visually extended only up to `nowSeconds` (the current confirmed replay position) — never to an invented future clear time |
| Simulated flag | Carried through verbatim from `OperationalEvent.simulated` — this runtime's only fault-injection mechanism is the simulated-fault control, so this is always `true` for `fault_applied`/`fault_cleared` events; never mislabels an organic fault |
| Evidence class | N/A (operational event log) |
| Cross-component consumers | None new |

## Family E — `ArchitectureDeltaMatrix.tsx`

| Field | Value |
|---|---|
| Source (rows) | `FINAL_SENSOR_INVENTORY` (`lib/architecture.ts`, static, unmodified) |
| Source (MINIMAL_CORE membership) | Hardcoded `MINIMAL_CORE_MODALITIES = ["PPG","IMU","ECG","EEG"]`, copied from `results/stage4_architecture_candidate_classes.json` `classes[0].sensors` (verified by direct read before writing) |
| Source (burden) | `api.getFinalWearableArchitecture()` live fetch → `architecture.contact_model.per_modality_breakdown[key].most_likely` |
| Governing status | GOVERNING (`results/final_wearable_architecture.json`, the Stage 4 closure's one canonical architecture artifact) |
| Transformation | None beyond table row construction; burden text formats `${most_likely} ${unit}`.trim() |
| Missing-value behavior | `contacts?.most_likely != null ? ... : "Not available"` — never renders 0 for an unresolved live fetch |
| Metric | Contact count (electrodes/optical sites), a bounded engineering estimate, not a measured value — labeled as such in the footer |
| Evidence class | Tier B/C for EOG (from `results/final_wearable_architecture.json` `science_rationale.evidence_confidence`, copied verbatim); Tier A framing for MINIMAL_CORE modalities ("foundation signal, not under incremental-value test", from `stage4_architecture_candidate_classes.json`) |
| Directionality | N/A (membership table, not a comparative metric) |
| Caveat | Footer states explicitly: static facts do not depend on live replay coverage; burden figures are bounded engineering estimates, not measured/flight-qualified hardware |
| Cross-component consumers | `MinimalCoreComparison.tsx` (pre-existing, unmodified) renders the same `MINIMAL_CORE_SUMMARY`/`CORE_PLUS_CONTEXT_SUMMARY`/`EOG_DELTA_NOTE` constants — verified consistent by construction (same source constants, not independently re-derived) |

## Family F — `CandidateDispositionMatrix.tsx` (enriched)

| Field | Value |
|---|---|
| Source (existing columns) | `useResearchStore().finalWearableArchitecture.exclusion_rationale` (live fetch, pre-existing, unmodified) |
| Source (new columns) | `NEGATIVE_MIXED_EVIDENCE` (`data/stage6/evidenceBurdenMatrix.ts`), bundled verbatim excerpt of `results/final_tables/table_d_negative_mixed_results.json` |
| Governing status | GOVERNING (`provenance.source: results/final_claim_ledger.json`) |
| Join key | `exclusion_rationale`'s object key (`thoracic_bioz_eis`, `leg_bioz`, `second_site_ppg`, `wrist_temperature_light`), matched 1:1 against `table_d`'s `claim_id` (note: `table_d` spells the BioZ key `thoracic_eis`, the exclusion artifact spells it `thoracic_bioz_eis` — the bundled data file keys on the exclusion artifact's spelling to match the existing component's join, confirmed correct by inspection) |
| Missing-value behavior | `evidence?.numericSupport ?? "Not measured"` — `wrist_temperature_light` genuinely has no numeric result (TIER_P_PENDING, no governing experiment) and correctly shows "Not measured", never a fabricated number or 0 |
| Metric | Free-text numeric result string (verbatim from the source artifact, e.g. `"B_minus_A = +1.462 MAE (worse); n=4 held-out test subjects"`) — not re-parsed into a separate number/unit pair, since the source artifact itself expresses direction and population scope inline |
| Participant count | Embedded in `numericSupport`/`populationScope` text, verbatim from source |
| Evidence class | Disposition badge unchanged (pre-existing "Not selected for CORE_PLUS_CONTEXT" / "Disposition pending") — new columns add the quantitative backing without altering the existing disposition classification |
| Caveat | `limitation` field (not rendered as a separate column in this pass, available in the bundled data for a future enhancement) preserves e.g. "sign-sensitive to exclusion" text |

## Family G — `SensitivitySmallMultiples.tsx`

| Field | Value |
|---|---|
| Source | `data/stage6/sensitivitySmallMultiples.ts`, bundled verbatim excerpts of 4 figures from `results/final_figure_manifest.json` |
| Governing status | GOVERNING per the manifest (status: `STAGE5_FIGURE_MANIFEST_REPORTED_COMPLETE_PENDING_INDEPENDENT_AUDIT` — reported with that exact qualifier, not overclaimed) |
| Panel 1 | `PPG_DALIA_CAPACITY_CONTROL` — provenance `results/ppg_dalia_capacity_control.json`, `results/ppg_dalia_imu_multiseed_replication.json`; metric MAE (bpm), lower-is-better, n=5 seeds |
| Panel 2 | `PTT_SUBJECT_HETEROGENEITY` — provenance `results/ptt_sensitivity_day11.json`; metric delta MAE (bpm), lower-is-better, n=4 subjects; sign-flip-on-s2-exclusion carried verbatim (`aggregateWithS2`/`aggregateWithoutS2`/`signFlipsWhenS2Excluded: true`) |
| Panel 3 | `SLEEP_EDF_PRIMARY_ABC` — provenance `results/sleep_edf_eeg_eog_ablation.json`, `results/sleep_edf_eeg_eog_control_analysis.json`; metric macro-F1, higher-is-better, n=5 seeds, n=3 test subjects |
| Panel 4 | `PPG_DALIA_SUBJECT_HETEROGENEITY` — provenance `results/ppg_dalia_sensitivity_day11.json`; metric delta MAE (bpm), higher-is-better (positive = candidate better), n=3 subjects |
| Transformation | `seriesMeanSd()` (new, pure, `data/stage6/sensitivitySmallMultiples.ts`) computes `{mean, sd, n}` per series — real sample statistics (`ddof=1` semantics matching the source artifact's own stated uncertainty meaning), never fabricated |
| Missing-value behavior | No pending/missing values exist in these 4 governing families; N/A for this pass |
| Uncertainty type | Sample SD across seeds/subjects — every panel's footer explicitly states "not a population confidence interval" via `uncertaintyLabel()`, matching each source figure's own `uncertainty_meaning` field verbatim |
| Directionality | Explicit per panel via `directionalityLabel()`; MAE panels are lower-is-better, macro-F1 panel is higher-is-better — never mixed on one axis (one `ChartFrame` per metric family, enforced structurally by one `SeriesPanel` per `ChartFrame`) |
| Participant/seed count | Rendered in both the summary sentence and the semantic table (`n seeds` column) |
| X-axis tick formatting | `v.toFixed(2)` — fixed during this task's own adversarial self-review after finding unrounded floating-point tick labels in initial browser evidence (see `FINDING_LEDGER.md`) |
| Cross-component consumers | None — new, standalone |

## Missing/non-finite guard layer — `lib/visualization/dataToMark.ts`

`classifyValue()`/`formatMetric()` are available to every Stage 6 chart for
raw numeric formatting; `SeriesPanel`/`ArchitectureDeltaMatrix`/`CandidateDispositionMatrix`
use direct nullish-coalescing (`?? "Not measured"`/`?? "Not available"`)
against already-typed source fields instead, since their source data is
already string-typed or has a clear domain-specific missing sentinel. The
shared guard layer is exercised directly by 13 new behavioral tests (see
`docs/ismet-stage6-scientific-visualization-redesign/../frontend/scripts/verify-monitoring-state.ts`)
covering `undefined`/`null`/`NaN`/`±Infinity`/real-zero classification.
