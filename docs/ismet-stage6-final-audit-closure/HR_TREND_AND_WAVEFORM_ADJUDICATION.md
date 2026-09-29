# HR Trend & Waveform Adjudication — Stage 6 Fresh-Session Audit & Closure

Hostile visual/scientific re-audit, performed against real populated data
(the same real S14 replay + real checkpoint exercise as
`POPULATED_TIMELINE_ACCEPTANCE.md`), not accepted from the source's
`ENLARGED_LOGIC_UNCHANGED` / `REVIEWED_NO_CHANGE_NEEDED` self-report alone.

## HR trend (`RecentHrEstimateTrend.tsx`)

Evidence: `11-hr-trend-desktop-populated.png` (captured **during an active
real fault**), `12-hr-trend-mobile-populated.png`.

| Requirement | Result |
|---|---|
| Sufficient plot height | PASS — 220-260px, not a sparkline |
| Visible replay-time axis | PASS — `-90s` to `now`, real elapsed-time window (this chart intentionally uses wall-clock elapsed time, "recent trend," a different and legitimate use case than the fault-timeline's replay-position axis — see note below) |
| Visible BPM axis/unit | PASS — "bpm" label, real ticks (61/66/75 in the captured frame) |
| Source/evidence classification | PASS — "Replay HR estimate · no reference HR channel in the current runtime" |
| Null gaps | PASS — real gap logic in `hrTrend.ts`, unchanged, already correct |
| Freshness | PASS — "Current HR unavailable · plot retains confirmed historical estimates only" banner shown during the captured fault |
| Stable, truthful y-domain | PASS — domain padded proportional to visible range, not exaggerating tiny fluctuations |
| No stale HR during fault/pending/rebuilding | PASS — during the captured active fault, the HR ring shows "Unavailable", the trend shows the warning banner and a real truncated line, never a frozen "last good" value presented as current |
| Missing/non-finite values withheld | PASS |
| Desktop/tablet/mobile legibility | PASS — confirmed at 1920px and 390px, no overflow |
| Exact semantic summary | PASS — the same banner/scope text serves as the non-visual equivalent |
| No tooltip-only critical value | PASS — the numeric current value is always rendered as text next to the heading, not tooltip-gated |

**Note on the two different "time" axes in this app**, clarified by this
audit's own S6A-FIND-01 investigation: `RecentHrEstimateTrend`'s "-90s to
now" axis is genuine *recent elapsed wall-clock time* (an intentional,
correct use of the wall-clock field this audit found being misused
elsewhere) — appropriate for "how has HR trended in roughly the last
minute and a half," a different, legitimate question from
`FaultRecoveryTimeline`'s "where in this replay session did this fault
happen," which requires the replay-position field. No defect was found
here; this is called out explicitly so a future reviewer does not
mistakenly "fix" this correct usage by analogy to S6A-FIND-01.

**Disposition: `HR_TREND_STATUS: PASS`, no correction needed.** The prior
implementation's "enlarged, logic unchanged" characterization holds up
under a hostile, real-data re-audit.

## Waveforms (`SignalRibbonMatrix.tsx` / `SignalLaneChart.tsx`)

Evidence: `13-waveforms-desktop-populated.png`, `14-waveforms-mobile-populated.png`
(both captured against real S14 PPG/IMU/ECG channel data).

| Requirement | Result |
|---|---|
| Time basis | PASS — real shared time-range label (`t=24.22s` to `t=24.75s` in the captured frame), drawn from the confirmed source's own sample rate/start time |
| Unit or honest normalized label | PASS — real sample rates shown per lane (64 Hz / 32 Hz / 700 Hz); per-lane value ranges shown (e.g. PPG 40.7/-96.1) |
| Per-lane modality identity | PASS — modality + region labeled per lane |
| Independent domains for unlike units | PASS — each lane computes its own y-domain (`computeDynamicDomain`), never a shared axis across PPG/IMU/ECG |
| Scale visibility | PASS — real min/max gutter, always visible, not hover-gated |
| Freshness | Implicit via the shared time-range label; no separate per-lane freshness age is exposed, consistent with the same limitation already disclosed for the coverage matrix (this runtime has no per-channel age field) |
| Missing intervals | PASS — EEG/EOG lanes explicitly show "Final architecture modality · no waveform channel in current source" rather than a fabricated flat line |
| Source-error state | Not separately re-exercised in this pass (would require a genuine source-error condition, not reproduced here); pre-existing structural guard (`verify-webgl-fallback.mjs`, unrelated Canvas-only guard) does not cover this specific case — noted as a limitation, not claimed as tested |
| No smoothing across missing data | PASS by construction — faulted lanes render an explicit dashed "Simulated fault — waveform withheld" panel, never an interpolated line |
| No stale continuation | PASS |
| Bounded history | PASS — `DISPLAY_POINT_BUDGET = 300`, downsampled via `downsampleExtremaPreserving` (extrema-preserving, confirmed by name and by the visibly jagged real ECG trace in the evidence, not over-smoothed) |
| Reduced-motion-safe | PASS — no animation on these charts (`isAnimationActive={false}` pattern used throughout this codebase) |
| Semantic summary | PASS — the architecture-coverage lanes' text and the shared caption serve this role |
| Mobile legibility | PASS — confirmed at 390px, no overflow |
| 200% zoom legibility | `NOT_ATTEMPTED — zoom itself is BLOCKED_EXTERNAL` (see the responsive/zoom section), so this specific sub-check could not be completed |

**Disposition: `WAVEFORM_STATUS: PASS`, no correction needed.** Re-confirms
the source implementation's self-review finding (documented in the source's
own `FINDING_LEDGER.md` as "investigated, no defect found") — this audit
independently re-derived the same conclusion against genuinely populated,
real-fault data rather than accepting the prior finding on trust.
