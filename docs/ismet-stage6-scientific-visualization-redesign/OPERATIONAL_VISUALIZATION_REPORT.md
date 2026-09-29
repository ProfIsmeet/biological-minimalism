# Operational Visualization Report — Stage 6 Scientific Visualization Redesign

Covers Families A, B, C, D and the HR trend/waveform redesign — all on
`/mission-overview` (and, for waveforms, `/live-monitoring` via the
unmodified `SignalRibbonMatrix`).

## A + D — Coverage & freshness matrix (`CoverageFreshnessMatrix.tsx`)

Merged into one component (see `VISUALIZATION_INVENTORY.md` for the
rationale). Rows: PPG, IMU, ECG, EEG, EOG (from `FINAL_SENSOR_INVENTORY`).
Each row shows: modality color key, region, a coverage sentence
(`coverageText()`: "Currently observed" / "Awaiting confirmation" / "Not
provided by this replay" / "Not reported by current telemetry"), and a
`StatusPill` with the exact `OperationalStateWord` vocabulary already
established elsewhere in the app (Confirmed / Replay warm-up / Unavailable
/ Disconnected / Simulated fault / Connected — awaiting confirmed frame /
Source error). The non-compact form adds a full semantic table (modality,
region, selected-architecture membership, current observation, inference
role, absence/fault reason).

**"Selected" ≠ "currently observed" rule:** enforced structurally — the
component never conflates the static `FINAL_SENSOR_INVENTORY` membership
(all 5 modalities, always shown as rows) with the live `nodeState`/
`observation` per row. A replay carrying only PPG/EEG genuinely shows IMU/
ECG/EOG as "Not provided by this replay" rather than omitting the rows or
implying they left the architecture.

**Freshness limitation, disclosed honestly:** this runtime exposes no
per-channel last-confirmed age or backend-defined staleness threshold
(confirmed by reading `lib/monitoring/modalityObservation.ts` in full — no
timestamp field exists per channel). Rather than invent an age/threshold
bar, the component shows the one authoritative session-level "as of" time
(`view.confirmedTimestampSeconds`) once, with explicit footer text
disclosing why no per-row age is shown.

## B — Pipeline state strip (`PipelineStateStrip.tsx`)

Reuses `deriveHexFlow()` unmodified. Stages: Source → {PPG input, IMU
input} → Window assembly → HR model → HR output — exactly the required
Family B stage list. Desktop renders a horizontal `<ol>`; mobile (`sm:hidden`)
renders a vertical ordered list. Selecting any stage (a real `<button
aria-expanded>`) reveals its provenance/requirement text — never
hover-only. No fabricated readiness percentage or sample count is
rendered anywhere; the strip is purely categorical, and the header text
says so explicitly ("Categorical pipeline state · not a confidence score").

## C — Fault & recovery timeline (`FaultRecoveryTimeline.tsx`)

See `DATA_TO_MARK_CONTRACT.md` for the exact data contract. Key acceptance
points, verified:

- Real replay-time X-axis, never evenly-spaced-by-index, never wall-clock
  arrival order.
- Real null gaps in the HR line (`connectNulls={false}`).
- An ongoing (uncleared) fault extends only to the current confirmed
  replay position, never to an invented future clear time.
- `SIMULATED` label carried verbatim from the source event — this
  runtime's only fault mechanism is the simulated-fault control, so no
  organic/source fault is ever at risk of being mislabeled.
- Exact onset/clear/duration available in a real `<table>`, not
  hover-only.
- When ANY relevant event lacks a real timestamp, the entire chart falls
  back to a text-only chronology — verified by a dedicated behavioral test
  (`verify-monitoring-state.ts`, "Stage 6 fault timeline: axisAvailable is
  false when a relevant event lacks a real timestamp").

**Evidence capture limitation:** the PPG-DaLiA dataset archive is not
present on this test machine, so no real fault-injection cycle could be
captured live in-browser for this pass — the captured evidence shows the
honest, correct **empty state** ("No fault or recovery events in this
interface session"), not a fabricated populated one. The pure-logic
behavioral tests independently prove the interval-pairing/axis-availability/
ongoing-extension/null-gap contracts without needing a live replay session.

## HR trend (`RecentHrEstimateTrend.tsx`)

`deriveHrTrend()` (the pure logic) was already scientifically sound before
this task — real gap detection via a median-interval-based threshold, no
fabricated interpolation, domain padding proportional to the visible
range. The only defect was presentational: a 120-140px container. Enlarged
to 220-260px, added a "bpm" y-axis label and increased tick count from 2
to 4. No change to `hrTrend.ts` itself.

## Waveforms (`SignalRibbonMatrix.tsx` / `SignalLaneChart.tsx`)

Investigated for the "hover-only information" defect pattern (per-lane
axes are `hide`-d) and found NOT to qualify — see `FINDING_LEDGER.md`
"Investigated, no defect found". Per-lane min/max value range, shared
visible time range, modality identity, region, and sample rate (Hz) are
all always visible without hovering. No change made; this component was
already legible and honest (own y-domain per lane, no shared axis across
unlike physical units, real "withheld" state for faulted lanes, EEG/EOG
shown as explicit architecture-coverage lanes never synthesized).
