# Scientific Integrity Review — Stage 6 Fresh-Session Audit & Closure

## Mandatory rules — re-verified against real populated data

| Rule | Verification | Result |
|---|---|---|
| Missing ≠ zero | Real withheld HR during the captured fault renders as a line gap, never 0; `wrist_temperature_light` shows "Not measured" text, never 0 | PASS |
| Unavailable ≠ nominal | HR ring shows "Unavailable" with a red/warning tone during the real fault, never a nominal-looking state | PASS |
| Pending ≠ failure | No candidate is shown red/failed for a pending (TIER_P) result; `evidenceBurdenMatrix.ts` bundled data confirmed unchanged | PASS |
| Fault-cleared ≠ recovered | Directly fixed and demonstrated in this audit (S6A-FIND-03/04/05) — distinct table rows/markers | PASS |
| Rebuilding ≠ valid current inference | During the shaded fault-interval region (which visually spans through the re-warm-up), the pipeline strip correctly shows `HR output: UNAVAILABLE`, never a stale/interpolated value | PASS |
| Recorded ≠ inferred | Unchanged from Stage 6 source; not touched by this audit's fixes | PASS (inherited) |
| Inferred ≠ conceptual | Unchanged | PASS (inherited) |
| Experimental ≠ selected | Unchanged; `CandidateDispositionMatrix` disposition badges untouched by this audit | PASS (inherited) |
| Engineering estimate ≠ measured hardware | Unchanged; `ArchitectureDeltaMatrix`'s footer text untouched | PASS (inherited) |
| Seed variability ≠ population uncertainty | Unchanged; `uncertaintyLabel()` calls untouched | PASS (inherited) |
| Architecture selection ≠ replay coverage | `CoverageFreshnessMatrix`'s static-vs-live column separation untouched in structure; its "as of" timestamp was fixed (S6A-FIND-01) but this does not affect the selection-vs-coverage distinction itself | PASS |
| Historical/superseded ≠ governing | Unchanged; no bundled data file was modified by this audit | PASS (inherited) |

## Non-finite/edge-case handling — re-verified via new pure-logic tests

`null`/`undefined`/`NaN`/`±Infinity`/finite-zero/valid-negative-delta/
valid-positive-delta classification was already covered by the Stage 6
source's own tests (`dataToMark.ts` checks, unchanged by this audit).
This audit added coverage for the specific new edge cases its own fixes
introduced: a recovery marker with no real HR sample yet (correctly
produces zero markers, not a fabricated one), an ongoing/never-cleared
fault (correctly produces no recovery marker), and a plain
`prediction_available` event with no fault ever active (correctly
produces zero fault-timeline events).

## No scientific behavior changed

None of this audit's 5 corrections touch any scientific model, dataset,
checkpoint, HR inference logic, selected architecture, or Digital Twin
scientific boundary. All 5 fixes are confined to: (1) which existing,
already-correct backend field a display value reads from (never which
value the backend itself computes), (2) a CSS layout property, and (3)
which existing event-log entries a chart's own presentation layer
surfaces. `SCIENTIFIC_BEHAVIOR_CHANGED: false`.

## No duplicate monitoring owner introduced

This audit added no new network call, no new store, no new WebSocket
subscription. `view.replayPositionSeconds` and
`snapshot.source.replay_position_seconds` are pre-existing fields on the
already-single-owner `useOperationalViewModel()`/`useConfirmedHistory()`
data flow — this audit changed which *already-available* field three
call sites read, not the ownership of any data source.
`DUPLICATE_MONITORING_OWNER_INTRODUCED: false`.
