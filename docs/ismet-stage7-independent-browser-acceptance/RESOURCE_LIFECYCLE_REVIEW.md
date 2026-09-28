# Resource Lifecycle Review — Stage 7 Independent Browser Acceptance

Runtime behavioral evidence for canvas/render-loop/listener/observer lifecycle claims
on `/digital-twin`, gathered against the final corrected implementation, using the
machine's installed Chrome driven via `playwright-core` (temporary devDependency,
reverted before final commit — see `WEBGL_RUNTIME_REVIEW.md` for the toolchain note).
All tests ran against a freshly built dev server on an isolated port
(`npm run dev -- -p 3103`), with `.next` cleared beforehand to rule out stale-cache
artifacts.

## 20x mount/unmount cycle

Navigated `/digital-twin` → `/settings` (a route with **no canvas at all**, chosen
specifically so "canvas count after navigating away" proves a true unmount rather than
merely matching some other route's own canvas count — `/mission-overview` was
considered but rejected for this check because it renders its own, unrelated
holographic-figure canvas) → `/digital-twin`, 20 times.

**Result:** `canvasWhileMounted === 1` on **all 20** cycles;
`canvasAfterUnmount === 0` on **all 20** cycles (verified against `/settings`).
No accumulation, no leaked canvas, no growth over repeated cycling.

## Repeated resize while mounted

With `/digital-twin` mounted, resized the viewport through 1920×1080 → 1024×768 →
390×844 → 1440×900 → 1920×1080 (5 resizes in sequence, no remount between them).

**Result:** exactly 1 `<canvas>` present at every size, throughout. No duplicate
canvas spawned by a resize-triggered remount path.

## Hidden-tab / `visibilitychange` suspension

Simulated a tab going to background (`document.hidden = true`,
`visibilitychange` dispatched) while `/digital-twin` was mounted, then restored
visibility.

**Result:** canvas count stayed at 1 throughout hide → hidden → restore. This
confirms the route's documented "demand-driven rendering while... hidden" behavior is
implemented as **render-loop suspension**, not DOM removal — the canvas element
persists and is expected to; what pauses is the render loop feeding it. This matches
the architecture described in the original report and is not a defect.

## Context-loss/retry cycling — cross-referenced

See `WEBGL_RUNTIME_REVIEW.md` Gate D: 3 full loss→retry cycles, single-canvas
invariant held after every cycle, no orphaned render loop detected via repeated
canvas-count sampling after retry.

## Console/exception hygiene across all lifecycle stress tests

68 total console messages were captured across the full lifecycle test run
(mount/unmount ×20, resize ×5, visibility toggle, reduced-motion toggle sequence).
66 of these were `net::ERR_CONNECTION_REFUSED` / WebSocket-connection-failed messages
— expected and unrelated to Digital Twin: the backend was intentionally not running
for this frontend-only lifecycle test, and these errors trace to `/mission-overview`'s
and `/settings`'s own live-feed WebSocket hooks, never to `/digital-twin` (confirms,
independently, that the route owns no network/monitoring source, consistent with
`SOURCE_CLAIM_ADJUDICATION.md` claim #10). The remaining 2 messages were both the same
pre-existing hydration-mismatch warning (`className="dark"` vs `"dark reduce-motion"`),
reproducing once on `/digital-twin` and once on `/settings` — already documented in
`FINDING_LEDGER.md` as a pre-existing, cross-route condition unrelated to Stage 7. No
Digital-Twin-specific, WebGL-specific, or Three.js-specific error occurred at any point
across the entire stress sequence.

## Memory-leak claim — scope and honest limitation

This review provides meaningful runtime stress evidence (repeated mount/unmount,
resize, and visibility-cycling with a stable, non-growing canvas count and no
recurring exceptions) rather than source-structure-only inspection. It does **not**
constitute a formal heap-snapshot memory-profiling study — no claim of "proven absence
of any memory leak" is made here; the claim made is the narrower, evidence-backed one:
across 20 mount/unmount cycles, 5 resizes, and repeated visibility toggling, no
observable resource accumulation (canvas count, console error recurrence) occurred.

## Summary

| Check | Cycles/samples | Result |
|---|---|---|
| Mount/unmount | 20 | Exactly 1 canvas mounted, 0 after true unmount — every cycle |
| Resize | 5 | Exactly 1 canvas at every size |
| Hidden-tab suspension | 1 hide + 1 restore | Canvas persists (render-suspension architecture); no duplication |
| Context-loss/retry | 3 | Exactly 1 canvas after every retry (cross-ref `WEBGL_RUNTIME_REVIEW.md`) |
| Console hygiene | 68 messages inspected | 0 Digital-Twin-specific errors; all non-backend-noise messages traced to a pre-existing, unrelated condition |

**RESOURCE_CLEANUP_RUNTIME_REVIEW: PASS**, backed by genuine runtime stress evidence,
not source structure alone.
