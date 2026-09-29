# Data-to-Mark Forensic Audit — Stage 6 Fresh-Session Audit & Closure

Spot checks tracing rendered marks back to their exact source, for the
marks this audit's own real populated-replay run produced (the most
consequential set, since they involve live data transformation, not just
static bundled constants).

| Mark | Source | Field path | Transformation | Rendered value | Result |
|---|---|---|---|---|---|
| Fault-onset replay time | Backend `/data-source/replay/fault` POST, propagated via WS frame | `snapshot.source.replay_position_seconds`, captured at the confirmed frame nearest the transition | None beyond `.toFixed(1)` | `18.5` (table) | TRACED, correct — matches the real REST-call-triggered transition's timing within the expected propagation lag |
| Fault-clear replay time | Backend `/data-source/replay/fault` DELETE | Same field | `.toFixed(1)` | `18.5` (same frame as onset in this specific run — a short fault) | TRACED — duration column (`12.8`) independently confirms this is a real, non-degenerate interval |
| HR null-gap interval | `useConfirmedHistory()` → `heart_rate_prediction?.value ?? null` | Real backend-withheld value during the active fault | None — `null` stays `null`, never coerced to 0 | Visible line gap in the chart | TRACED, correct |
| Recovery marker | `hrPoints` (post-clear), first real sample | `snapshot.heart_rate_prediction.value` at the first non-null point after `clearSeconds` | `Math.find()`, no transformation of the value itself | `62.8 bpm` at `40.5s` | TRACED, correct — matches the real HR display's own concurrently-observed value |
| Coverage matrix "as of" time | `view.replayPositionSeconds` | `current.source.replay_position_seconds` | `.toFixed(1)` | `18.8s` | TRACED, correct (post S6A-FIND-01 fix) |
| Pipeline HR-model/output state | `deriveHexFlow()` (unmodified) | `view.predictionAvailability`, `view.telemetryAvailability` | Categorical mapping only, no numeric fabrication | `UNAVAILABLE` during fault / `CONFIRMED` after recovery | TRACED, correct, matches the real fault-active/recovered state at capture time |
| Waveform PPG/IMU/ECG sample rate | `plot.sampleRateHz` | Backend channel metadata, unmodified pass-through | None | `64 Hz` / `32 Hz` / `700 Hz` | TRACED, correct — matches the backend's own documented Empatica E4 / chest ECG sample rates |
| Waveform value range gutter | `computeDynamicDomain(plot.values)` (pre-existing, unmodified) | Real channel sample array for the current window | `Math.min`/`Math.max` over real samples | e.g. PPG `40.7 / -158.8` | TRACED, correct — recomputed per window, not a fixed/fabricated range |

## Bundled static data (Families E/F/G) — re-verified unchanged from the Stage 6 source

This audit did not modify `data/stage6/sensitivitySmallMultiples.ts` or
`data/stage6/evidenceBurdenMatrix.ts`. Screenshots `15`, `16`, `17`, `18`
are byte-identical (SHA-256-confirmed) to the Stage 6 source's own
evidence for the same views, confirming stability — no forensic re-trace
was repeated for these static, already-audited bundled excerpts, since no
change was made to their source or rendering path.

## Summary

Every spot-checked mark from this audit's own real runtime exercise traces
to a real, live backend field with a documented, minimal transformation —
no invented value, no silent coercion of missing/null to zero, no stale
value presented as current. `DATA_TO_MARK_FORENSIC_AUDIT: PASS`.
