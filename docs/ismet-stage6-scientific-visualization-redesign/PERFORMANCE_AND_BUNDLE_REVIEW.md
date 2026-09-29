# Performance & Bundle Review — Stage 6 Scientific Visualization Redesign

## Bundle-size impact

No new dependency was added — every new chart reuses the pre-existing
`recharts@^2.15.0` dependency (already in `package.json` before this task).
`npm run build` route sizes, baseline vs. final:

| Route | Baseline First Load JS | Final First Load JS | Delta |
|---|---|---|---|
| `/mission-overview` | 255 kB (18.8 kB route) | 255 kB (19.4 kB route) | +0.6 kB route-local, shared bundle unchanged |
| `/system-brief` | 116 kB (5.22 kB route) | 116 kB (5.81 kB route) | +0.59 kB route-local |
| `/research/experimental` | 246 kB (33.6 kB route) | 246 kB (38.1 kB route) | +4.5 kB route-local |
| Shared chunk (`103 kB`) | unchanged | unchanged | 0 |

All growth is route-local JS (the new component code + bundled data
excerpts), not a shared-chunk increase — confirmed via the build output's
own per-route breakdown. `data/stage6/sensitivitySmallMultiples.ts` and
`evidenceBurdenMatrix.ts` are the largest new additions in raw source size
(bundled numeric data), but both are small, hand-trimmed excerpts (only
the fields actually consumed — e.g. `macro_f1` per seed, not full
confusion matrices or per-epoch training history, which the source
`figure_D_sleep_primary_abc.json`-equivalent artifact also contains but
this bundle deliberately omits).

## Render cost / update frequency

- `PipelineStateStrip`, `CoverageFreshnessMatrix`: derive their state from
  `useOperationalViewModel()` in the same render pass as every other
  operational component already on the page — no new subscription, no new
  polling interval.
- `FaultRecoveryTimeline`: `useMemo`-wraps both `hrSamples` mapping and
  `deriveFaultRecoveryTimeline()` itself, re-computed only when `events`,
  `hrSamples`, or `confirmedTimestampSeconds` actually change — not on
  every render.
- `SensitivitySmallMultiples`: all data is static (bundled at build time,
  never re-fetched or re-computed per render); `seriesMeanSd()` runs once
  per render pass over small fixed-size objects (5 or fewer entries each)
  — negligible cost, no memoization needed at this scale.

## Bounded history — no new unbounded growth

`FaultRecoveryTimeline` reads `useOperationalEventStore()` (pre-existing,
bounded to `MAX_EVENTS = 40` via `.slice(-MAX_EVENTS)`) and
`useConfirmedHistory()` (pre-existing, bounded via `missionStore.ts`'s
`.slice(-MAX_HISTORY)`) — both confirmed by direct source read. No new
unbounded array was introduced.

## Hidden-tab / DOM node count

Not independently re-measured for Stage 6's specific new components in
this pass (time-constrained) — inherited from the pre-existing app-wide
behavior, which the prior Stage 7 independent audit already verified
stops/reduces render work when hidden (canvas-specific, not directly
applicable to these SVG/DOM charts, which do not run a `requestAnimationFrame`
loop at all — Recharts renders once per prop change, not per frame).
`isAnimationActive={false}` on every Recharts element means there is no
continuous per-frame render cost to begin with, hidden or visible.

## Downsampling

Not applicable to any new Stage 6 chart — `SensitivitySmallMultiples`
plots small, fixed-size datasets (≤5 points per series) in full;
`FaultRecoveryTimeline` plots the bounded, already-small confirmed-history
buffer in full. No extrema/null-gap/fault-boundary information is at risk
of being downsampled away, since no downsampling occurs.

## No recurring console error or hydration mismatch introduced

Verified via real browser console capture before and after the
`PipelineStateStrip` fix (S6-FIND-01) — the hydration-mismatch error this
task itself introduced was found and fixed before this report was written;
final capture is clean of any Stage-6-attributable console error (see
`FINDING_LEDGER.md` for the full before/after trace).
