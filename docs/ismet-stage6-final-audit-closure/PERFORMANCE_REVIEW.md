# Performance Review — Stage 6 Fresh-Session Audit & Closure

## Bundle impact of this audit's own fixes

No new dependency added (`playwright-core` remains a temporary,
fully-reverted devDependency, confirmed absent from `package.json`/
`package-lock.json` after final commit). All 5 code fixes are small,
targeted edits to existing files:

| File | Change size |
|---|---|
| `OperationalEventLogWatcher.tsx` | ~10 lines (field swap + comment) |
| `FaultRecoveryTimeline.tsx` | ~30 lines (field swap, recovery-marker rendering, dedup) |
| `CoverageFreshnessMatrix.tsx` | ~8 lines (field swap + comment) |
| `ChartFrame.tsx` | ~10 lines (prop rename + comment) |
| `faultRecoveryTimeline.ts` | ~40 lines (recovery-marker derivation, event-class map correction) |

Final build route sizes essentially unchanged from the Stage 6 source
(`mission-overview`: 19.4kB → 19.6kB, a ~0.2kB delta from the added
recovery-marker rendering logic).

## Correctness-relevant performance findings

- **S6A-FIND-02's root cause (min-height vs. definite height) has a
  performance dimension worth noting**: before the fix, Recharts was
  silently attempting to render into a 0×0 container on every relevant
  page load — not a crash, but wasted render work producing an invisible
  result. The fix eliminates this wasted work as a side effect of fixing
  correctness.
- **Recovery-marker derivation** (`recoveryMarkers` computation in
  `faultRecoveryTimeline.ts`) runs a `.find()` over `hrPoints` once per
  closed interval — bounded by the same `useConfirmedHistory()` history
  buffer this audit confirmed is already bounded (pre-existing
  `MAX_HISTORY` slice in `missionStore.ts`), and by the small number of
  fault intervals realistically present in one session. No unbounded
  growth risk introduced.
- **Deduplication** (`seenRecoveryTimes` Set) adds O(1) amortized
  overhead per interval — negligible.

## No new console errors or hydration mismatches introduced

Verified via real browser console capture across the full populated-
replay exercise (multiple fresh dev-server restarts, multiple fault/
clear/recovery cycles): zero pageerrors, zero React hydration-mismatch
warnings attributable to this audit's changes. The pre-existing `THREE.Clock`
deprecation warning and headless-GPU `ReadPixels` performance messages
(a software-rendering artifact of this test environment, unrelated to any
2D chart) remain, both already documented as pre-existing/environmental in
prior work on this repository.

## No regression in the underlying data-fetching/render cadence

This audit's fixes change *which field* three call sites read and *which
CSS class* one shared component uses — they do not change render
frequency, subscription structure, or update cadence. The pre-existing
`verify-monitoring-consumers.mjs` structural guard (single-owner data
access) continues to pass unchanged, confirming no new duplicate data
path was introduced.
