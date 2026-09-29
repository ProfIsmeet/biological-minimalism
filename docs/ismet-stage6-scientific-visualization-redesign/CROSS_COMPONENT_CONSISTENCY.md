# Cross-Component Consistency — Stage 6 Scientific Visualization Redesign

Every fact rendered by more than one Stage 6-touched component, and why it
cannot silently drift.

| Fact | Consumers | Consistency mechanism |
|---|---|---|
| Selected 5-modality architecture (PPG/IMU/ECG/EEG/EOG, order, region) | `CoverageFreshnessMatrix`, `ArchitectureDeltaMatrix`, `MinimalCoreComparison` (pre-existing), `SignalRibbonMatrix` (pre-existing, unmodified) | All read the single `FINAL_SENSOR_INVENTORY` constant (`lib/architecture.ts`) — never independently re-listed |
| MINIMAL_CORE / CORE_PLUS_CONTEXT summary text | `ArchitectureDeltaMatrix`, `MinimalCoreComparison` | Both read `MINIMAL_CORE_SUMMARY`/`CORE_PLUS_CONTEXT_SUMMARY`/`EOG_DELTA_NOTE` from `lib/architecture.ts` — same source constants |
| MINIMAL_CORE modality set (which 4, not 5) | `ArchitectureDeltaMatrix` | Sourced from a direct, verified read of `results/stage4_architecture_candidate_classes.json` at the time of implementation; matches `EOG_DELTA_NOTE`'s existing framing ("EOG is the sole modality added beyond MINIMAL_CORE") by construction — both agree EOG is the only delta |
| Modality → color mapping | `CoverageFreshnessMatrix`, all pre-existing operational components | All read `MODALITY_COLOR` (`lib/architecture.ts`) — never a new color mapping introduced |
| Per-modality current node state (confirmed/fault/unavailable/etc.) | `CoverageFreshnessMatrix`, `PipelineStateStrip` (via PPG/IMU only) | Both derive from the same `useOperationalViewModel()` hook in the same render pass — never two independent fetches |
| Fault-active / faulted-modality state | `PipelineStateStrip`, `FaultRecoveryTimeline`, `MissionStatusBar` (pre-existing, unmodified) | All read `useOperationalViewModel()`'s `faultActive`/`faultedModalities`, or (for the timeline) the `useOperationalEventStore()` log populated from the identical view model by the pre-existing `OperationalEventLogWatcher` — one source of truth |
| Replay time / confirmed timestamp | `CoverageFreshnessMatrix` (footer), `FaultRecoveryTimeline` (x-axis "now" edge), `RecentHrEstimateTrend` (unchanged) | All read `view.confirmedTimestampSeconds` from the same `useOperationalViewModel()` hook |
| HR value / availability | `RecentHrEstimateTrend`, `FaultRecoveryTimeline`, `HRInferenceCore` (pre-existing, unmodified), `PipelineStateStrip`'s "output" stage | All derive from `useConfirmedHistory()` / `useOperationalViewModel().prediction` / `.predictionAvailability` — the same confirmed-snapshot pipeline, never a second HR source |
| Candidate disposition (excluded modalities) | `CandidateDispositionMatrix` (enriched) | `ExperimentalDispositionOrbit`, which rendered the identical `exclusion_rationale` data as a second, decorative representation, is now unmounted — eliminating what was previously a real duplicate-representation risk (both existed simultaneously on the same page before this task) |
| Metric direction (lower/higher-is-better) | `SensitivitySmallMultiples` (4 panels) | Each panel's `direction` field is copied verbatim from its source figure's own metric description; no panel infers direction from data shape |
| Participant/seed count | `SensitivitySmallMultiples` | `seriesMeanSd()`'s `n` field is computed from the actual bundled data object's key count — cannot silently diverge from the number of plotted points, since both come from the same object |

## No new duplicate ownership introduced

- No new WebSocket/REST source was added. `ArchitectureDeltaMatrix` reuses
  the exact `api.getFinalWearableArchitecture()` call the component it
  replaced already made. `CandidateDispositionMatrix`'s enrichment reads
  bundled static data plus the pre-existing `useResearchStore()` fetch —
  no new fetch call added.
- No component under `components/operations/**` added a raw
  `useMissionStore((s) => s.latest)`/`.history` read — confirmed by the
  pre-existing, unmodified `scripts/verify-monitoring-consumers.mjs`
  structural guard, which continues to pass (checked 20 protected files,
  including the two new operational components).

## Verification method

This report is a static/structural analysis (every consumer traced back to
its exact source hook/constant by reading the code), not a live
multi-route comparison screenshot. Combined with the pre-existing
`verify-monitoring-consumers.mjs` guard and the new behavioral tests in
`verify-monitoring-state.ts`, this gives structural (not merely visual)
assurance that no fact has two independent, potentially-diverging sources.
