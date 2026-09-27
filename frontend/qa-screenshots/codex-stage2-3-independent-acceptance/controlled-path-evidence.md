# Controlled browser-path evidence

These observations deliberately distinguish controlled/intercepted responses from the real backend. They validate UI orchestration and failure behavior only.

## Artifact CP-01 — Canonical bootstrap success and idempotency

- Route: `/mission-overview`
- Viewport: desktop browser viewport
- Browser: Codex in-app Chromium
- Frontend port: 3002
- Backend mode: controlled local backend on port 8002
- Source state: hostile recorded S7 replay at non-zero position, 5× or 10×, with active simulated fault
- Responses: intercepted/controlled; not real S14 data
- Purpose: verify canonical ordering, final visible state, idempotency, and bounded requests.
- Observation: final visible state was recorded S14, paused, 0.0 s, 1×, fault none. The first request sequence was `state, subjects, load-subject, reset, speed-1x, clear-fault`; repeat invocation issued the same bounded mutation sequence and converged identically. Current telemetry/history contained no prior S7 identity, fabricated EEG/EOG, or astronaut/live-data claim.

## Artifact CP-02 — Canonical failure matrix and recovery

- Route: `/mission-overview`
- Viewport: desktop browser viewport
- Browser: Codex in-app Chromium
- Frontend port: 3002
- Backend mode: controlled local backend on port 8002
- Source state: synthetic or hostile recorded replay, varied by scenario
- Responses: intercepted/controlled failures
- Purpose: verify fail-closed prerequisite and partial-step handling.
- Observation: loading, subject-list error, empty list, absent S14, and load/reset/speed/clear failures each named the relevant missing prerequisite or failed step, stopped subsequent mutation calls, and emitted no success. Explicit retry after clear failure succeeded without reload.

## Artifact CP-03 — Supersession and unmount

- Route: `/mission-overview`, then navigation to `/system-brief`
- Viewport: desktop browser viewport
- Browser: Codex in-app Chromium
- Frontend port: 3002
- Backend mode: controlled local backend on port 8002
- Source state: delayed subject/load response
- Responses: intercepted/controlled delay
- Purpose: verify stale-status suppression, mutation cancellation, and cleanup.
- Observation: a newer UI action superseded the pending sequence and announced `load was superseded` / `No state was applied`; request log stopped before reset/speed/clear. Navigating away during a delayed load applied no canonical status after the delay and left dialog, overflow, and inert state clean.

## Artifact CP-04 — Production WebGL fallback paths

- Route: temporary browser-local audit route rendering production stage/fallback components; route removed after test
- Viewport: desktop browser viewport
- Browser: Codex in-app Chromium
- Frontend port: 3001
- Backend mode: isolated repository backend; fallback triggers were browser-controlled
- Source state: real synthetic telemetry where applicable
- Responses: backend real; WebGL conditions controlled, not backend-intercepted
- Purpose: exercise unsupported initialization, render error, context loss, retry, keyboard fallback, scientific boundary language, and reduced-motion retry.
- Observation: unsupported mode showed no canvas and no retry; controlled render error and actual `WEBGL_lose_context` each showed fallback and recovered on retry. Operational PPG control activated by keyboard. Conceptual fallback retained architecture-only/untrained/unvalidated language and invented no values. Under app reduced motion, context-loss retry restored a stable 24° canvas with reduction still active.
