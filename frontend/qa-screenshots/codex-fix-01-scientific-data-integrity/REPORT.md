# Corrective package 01 — scientific data integrity

> **Independent-review correction notice (2026-09-23):** The original self-assessment below was challenged by an independent review that found three residual defects. Its earlier `COMPLETE` language is superseded. The correction addendum and final verdict at the end of this report are authoritative.

> **Second independent-review correction notice (2026-09-24):** A later cross-route review proved that the first addendum's pending-convergence boundary could still be bypassed on legacy live-feed routes. That addendum's final verdict is also superseded. The second independent-review correction and cross-route verdict at the end of this report are authoritative.

> **Third independent-review correction notice (2026-09-24):** Event-order review subsequently identified a third-authority convergence deadlock and duplicate/stale source-state request risk. Every earlier `COMPLETE` verdict is superseded. The third independent-review correction and event-ordering verdict at the end of this report are authoritative.

## Executive outcome

F-01, F-02, F-03, and F-23 are corrected within the requested frontend-only scope. Live Monitoring now consumes the same authoritative availability-gated operational model as Mission Overview; missing AI confidence and synthetic HR no longer become zero or nominal; Mission Timeline suppresses the scientifically unsafe legacy adaptation percentage and narrative; and dataset identity now participates in both source confirmation and mission-history segmentation.

The final deterministic monitoring suite passes 601/601, lint and TypeScript pass, and the production build completes successfully. No commit, push, staging, backend mutation, dependency installation, navigation change, or visual pass was performed.

## Starting repository state

- Branch: `stage5-dashboard-canonical-sync`
- HEAD: `c99ed8f14a2d9605c0059fd3a1444cf0b31fbe19`
- Latest commit: `c99ed8f feat(frontend): complete operational experience and delivery hardening`
- Starting `git status --short`:

```text
?? .site-preview-mission-overview-local.png
?? .site-preview-mission-overview.png
?? .site-preview-research.png
?? edit_haydarpasa.mjs
?? frontend/public/models/
?? frontend/qa-screenshots/
?? frontend/src/components/visualization/human/HolographicHumanModel.tsx
?? help_table_rows.mjs
?? inspect_basliksiz.mjs
?? inspect_haydarpasa.mjs
?? inspect_workbook.mjs
?? node_modules
?? qa-screenshots/
```

All of these untracked paths pre-dated this package. They were preserved. The new report was added inside the already-untracked `frontend/qa-screenshots/` tree as required.

## Ending repository state

- Branch: `stage5-dashboard-canonical-sync`
- HEAD: `c99ed8f14a2d9605c0059fd3a1444cf0b31fbe19`
- Latest commit: `c99ed8f feat(frontend): complete operational experience and delivery hardening`
- Ending `git status --short`:

```text
 M frontend/scripts/verify-monitoring-state.ts
 M frontend/src/app/mission-timeline/page.tsx
 M frontend/src/components/layout/LiveFeedProvider.tsx
 M frontend/src/components/monitoring/FinalSignalStack.tsx
 M frontend/src/components/monitoring/HrInferencePanel.tsx
 M frontend/src/components/monitoring/MonitoringSourceStrip.tsx
 M frontend/src/components/monitoring/ScopeProvenanceFooter.tsx
 M frontend/src/components/panels/AIConfidencePanel.tsx
 M frontend/src/components/panels/PrimaryVitalsPanel.tsx
 M frontend/src/lib/monitoring/operationalViewModel.ts
 M frontend/src/lib/monitoring/sourceIdentity.ts
 M frontend/src/lib/monitoring/telemetryAvailability.ts
 M frontend/src/store/missionStore.ts
?? .site-preview-mission-overview-local.png
?? .site-preview-mission-overview.png
?? .site-preview-research.png
?? edit_haydarpasa.mjs
?? frontend/public/models/
?? frontend/qa-screenshots/
?? frontend/src/components/visualization/human/HolographicHumanModel.tsx
?? frontend/src/lib/monitoring/insightDisplay.ts
?? frontend/src/lib/monitoring/liveMonitoringPresentation.ts
?? help_table_rows.mjs
?? inspect_basliksiz.mjs
?? inspect_haydarpasa.mjs
?? inspect_workbook.mjs
?? node_modules
?? qa-screenshots/
```

## Files changed by this package

- `frontend/scripts/verify-monitoring-state.ts`
- `frontend/src/app/mission-timeline/page.tsx`
- `frontend/src/components/layout/LiveFeedProvider.tsx`
- `frontend/src/components/monitoring/FinalSignalStack.tsx`
- `frontend/src/components/monitoring/HrInferencePanel.tsx`
- `frontend/src/components/monitoring/MonitoringSourceStrip.tsx`
- `frontend/src/components/monitoring/ScopeProvenanceFooter.tsx`
- `frontend/src/components/panels/AIConfidencePanel.tsx`
- `frontend/src/components/panels/PrimaryVitalsPanel.tsx`
- `frontend/src/lib/monitoring/insightDisplay.ts` (new)
- `frontend/src/lib/monitoring/liveMonitoringPresentation.ts` (new)
- `frontend/src/lib/monitoring/operationalViewModel.ts`
- `frontend/src/lib/monitoring/sourceIdentity.ts`
- `frontend/src/lib/monitoring/telemetryAvailability.ts`
- `frontend/src/store/missionStore.ts`
- `frontend/qa-screenshots/codex-fix-01-scientific-data-integrity/REPORT.md` (new)

No independent-audit file was edited.

## F-01 — authoritative Live Monitoring availability

### Before

Mission Overview derived current data through `useOperationalViewModel()` and `deriveTelemetryAvailability()`, while four Live Monitoring value surfaces independently combined confirmed snapshots and retained REST status. A WebSocket-connected/REST-error state could therefore continue to expose retained identity, replay state, HR, model status, or signal data as current. A REST state still loading also counted as active when a WebSocket frame existed.

### After

- `MonitoringSourceStrip`, `FinalSignalStack`, `HrInferencePanel`, and `ScopeProvenanceFooter` consume `useOperationalViewModel()` for semantic values.
- `deriveTelemetryAvailability()` now requires REST source state to be `available`; `loading` fails closed as `awaiting_confirmation`.
- REST/status fallback during `awaiting_confirmation` is allowed only after REST availability is authoritative.
- `source_error`, disconnect, and unconfirmed states expose no current plots, HR, prediction, inference status, replay position, fault status, model identity, or channel list.
- Retained source/dataset/subject values are shown only as `Source/Dataset/Subject context` and explicitly marked `retained configuration` / `not current telemetry`.
- PPG and IMU simulated faults continue to suppress their observations and HR remains unavailable until a new valid PPG+IMU window produces a prediction.

State-machine change:

```text
Before: connected + snapshot + REST loading/error-prone local fallbacks -> route-dependent current display
After:  REST error -> source_error
        transport closed -> disconnected
        REST not available OR no confirmed matching frame -> awaiting_confirmation
        connected + REST available + full-identity-matched frame -> active
```

## F-02 — AI Insights missing-data safety

- Added a discriminated confidence display derivation where null, undefined, and non-finite values become an explicit offline `Unavailable` state.
- The radial gauge is not mounted without a real numeric value and receives no invented zero.
- A genuine numeric zero remains an available numeric zero and retains the existing confidence-level behavior.
- Missing synthetic HR now receives the offline tone rather than nominal styling; present HR, including a genuine zero, retains existing numeric behavior.
- The confidence empty state includes `aria-label="Overall Confidence: Unavailable"` and visible unavailability copy.
- Recorded replay, PPG+IMU inferred output, synthetic vitals, and unavailable states remain explicitly distinguishable.

## F-03 — Mission Timeline Digital Twin boundary

- Removed all rendering of `overall_adaptation`, `% Adapted`, backend milestone labels, backend narratives, and success/health badges derived from the legacy payload.
- Replaced the unsafe section with neutral conceptual scenario markers that are explicitly not measured outcomes.
- Added a persistent visible boundary: `Architecture only · untrained · unvalidated · not personalized` plus explicit exclusion of physiological-change, prediction, clinical-readiness, and flight-qualification claims.
- Valid payload, loading, replay, and unavailable/error paths all render without converting absent legacy fields to zero or success.
- The endpoint dependency remains intact, but its scientifically uninterpretable quantitative fields are suppressed.

## F-23 — dataset-aware mission history identity

- Canonical source identity now includes a tagged dataset identity in addition to source type and subject.
- Missing dataset identity uses a structured `{ kind: "unconfirmed" }` representation rather than a string sentinel; it cannot collide with a real dataset named `unconfirmed` or any other real name.
- Store history segmentation uses the same canonical identity as source confirmation.
- Frames that disagree with authoritative REST dataset/source/subject are rejected before they can replace `latest`, enter `history`, or advance the confirmed timestamp.
- A separate raw observed-identity key preserves the existing REST-convergence trigger without exposing the mismatched frame to product telemetry.
- Same dataset/source/subject frames retain rolling history; dataset, source, subject, and existing fault transitions retain their reset behavior.
- No persisted store migration was needed because `missionStore` is session-memory only.

## Tests added or changed

The deterministic harness gained 67 checks (534 baseline to 601 final), covering:

- connected authoritative availability;
- WebSocket connected with REST source failure;
- disconnect with prior data;
- REST loading and missing confirmed snapshot;
- PPG and IMU fault overrides;
- rebuilding without HR and recovery with a valid prediction;
- retained identity wording;
- structural enforcement that all four Live Monitoring value surfaces use the shared operational model;
- null/undefined confidence, genuine zero confidence, and present confidence;
- missing, zero, and present synthetic HR tone behavior;
- gauge suppression and screen-reader unavailability text;
- Timeline claim suppression, persistent scope boundary, conceptual marker semantics, valid-payload suppression, and unavailable/error behavior;
- same subject/source across different datasets;
- same full identity history retention;
- missing-dataset collision resistance;
- dataset-change history reset;
- late prior-dataset frame rejection;
- valid new-dataset recovery;
- existing disconnect, fault, and source/subject lifecycle behavior.

No test was deleted or weakened.

## Commands and results

Repository/audit inspection:

```text
git branch --show-current
git rev-parse HEAD
git log -1 --oneline
git status --short
sed / rg / find inspection of the three audit files and required runtime paths
git diff --check
git diff --stat
git diff --name-only
```

Verification sequence:

```text
npm run verify:monitoring
  Baseline: 534/534 passed; consumer guard passed (20 protected files)

npx tsc --noEmit
  PASS (exit 0)

npm run verify:monitoring
  Intermediate expected red run: 592/597 passed, 5 failed
  Repaired before continuing

npm run verify:monitoring
  Intermediate: 597/597 passed

npm run lint
  PASS (exit 0)

npx tsc --noEmit
  PASS (exit 0)

npm run verify:monitoring
  Intermediate: 598/598 passed; consumer guard passed

npm run build
  PASS; compiled, type/lint validation completed, 14/14 static pages generated

npm run lint
  Final: PASS (exit 0)

npx tsc --noEmit
  Final: PASS (exit 0)

npm run verify:monitoring
  Final: 601/601 passed, 0 failed
  Consumer guard: PASS, 20 protected files
  Retry-independence check: PASS

npm run build
  Final: PASS; compiled successfully, 14/14 static pages generated
```

`frontend/package.json` defines no separate Jest/Vitest test command; `verify:monitoring` is the repository's complete existing frontend verification suite.

Build contention check:

- Process enumeration was unavailable in the managed environment.
- `.next/lock` did not exist before either build.
- Both production builds completed successfully.

## Browser verification and screenshots

Read-only probes to `127.0.0.1:3000`, `127.0.0.1:3100`, and backend health candidates on `127.0.0.1:8000` returned no connection (`000`). The application/backend were therefore not already available for safe read-only browser verification.

No backend source, subject, replay position, or fault state was changed. No screenshots were captured or fabricated. Adverse states were verified with deterministic fixtures and semantic/source-contract tests.

## Known limitations

- No live browser evidence was captured because the frontend and backend were not running.
- The repository uses a plain Node deterministic harness rather than a component-rendering test framework. Pure semantic derivations, source-contract assertions, lint, TypeScript, and two production builds provide the available automated evidence.
- Existing unrelated audit findings, visual debt, accessibility packages, deployment work, route/navigation decisions, and backend behavior remain intentionally untouched.

## Scope and scientific-truth confirmation

- Visual-design work was not started.
- No global typography, spacing, color, border, card, or layout redesign was made.
- No human-model, WebGL, navigation/archive, deployment, modal, or reduced-motion work was performed.
- Backend calculations and behavior were not changed.
- `CORE_PLUS_CONTEXT`, the three-region/five-modality architecture, MINIMAL_CORE composition, EOG-only delta, BioZ/EIS exclusion, PPG-DaLiA recorded-data boundary, S14 single-participant limitation, dashboard-versus-Results boundary, and simulated-fault boundary remain unchanged.
- Digital Twin is now consistently presented as `ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED`, not trained, adapting, personalized, clinically validated, or spaceflight validated.
- Missing data is never converted to zero, nominal, healthy, confirmed, adapted, or available in the corrected paths.

## Superseded original verdict

The original package reported all gates complete at 601/601. Independent review subsequently demonstrated that a pre-REST identity mismatch could retain stale current telemetry, two Live Monitoring control surfaces still bypassed the complete gate, the HR panel could make an unconfirmed no-fault assertion, and secondary missing vitals inherited nominal styling. That earlier verdict is not the current verdict.

## Independent-review correction addendum

### Continuation starting state

- Branch: `stage5-dashboard-canonical-sync`
- HEAD: `c99ed8f14a2d9605c0059fd3a1444cf0b31fbe19`
- Latest commit: `c99ed8f feat(frontend): complete operational experience and delivery hardening`
- The corrective package was already uncommitted and was continued rather than replaced.
- Starting continuation `git status --short`:

```text
 M frontend/scripts/verify-monitoring-state.ts
 M frontend/src/app/mission-timeline/page.tsx
 M frontend/src/components/layout/LiveFeedProvider.tsx
 M frontend/src/components/monitoring/FinalSignalStack.tsx
 M frontend/src/components/monitoring/HrInferencePanel.tsx
 M frontend/src/components/monitoring/MonitoringSourceStrip.tsx
 M frontend/src/components/monitoring/ScopeProvenanceFooter.tsx
 M frontend/src/components/panels/AIConfidencePanel.tsx
 M frontend/src/components/panels/PrimaryVitalsPanel.tsx
 M frontend/src/lib/monitoring/operationalViewModel.ts
 M frontend/src/lib/monitoring/sourceIdentity.ts
 M frontend/src/lib/monitoring/telemetryAvailability.ts
 M frontend/src/store/missionStore.ts
?? .site-preview-mission-overview-local.png
?? .site-preview-mission-overview.png
?? .site-preview-research.png
?? edit_haydarpasa.mjs
?? frontend/public/models/
?? frontend/qa-screenshots/
?? frontend/src/components/visualization/human/HolographicHumanModel.tsx
?? frontend/src/lib/monitoring/insightDisplay.ts
?? frontend/src/lib/monitoring/liveMonitoringPresentation.ts
?? help_table_rows.mjs
?? inspect_basliksiz.mjs
?? inspect_haydarpasa.mjs
?? inspect_workbook.mjs
?? node_modules
?? qa-screenshots/
```

### Exact files changed in the continuation

- `frontend/scripts/verify-monitoring-consumers.mjs`
- `frontend/scripts/verify-monitoring-state.ts`
- `frontend/src/components/monitoring/HrInferencePanel.tsx`
- `frontend/src/components/monitoring/InferenceResponseTimeline.tsx`
- `frontend/src/components/monitoring/MonitoringSessionContext.tsx`
- `frontend/src/components/monitoring/MonitoringSourceStrip.tsx`
- `frontend/src/components/monitoring/ReplaySessionControl.tsx`
- `frontend/src/components/monitoring/ScopeProvenanceFooter.tsx`
- `frontend/src/components/monitoring/SimulatedFaultControl.tsx`
- `frontend/src/components/panels/PrimaryVitalsPanel.tsx`
- `frontend/src/lib/monitoring/controlPresentation.ts` (new)
- `frontend/src/lib/monitoring/insightDisplay.ts`
- `frontend/src/lib/monitoring/liveMonitoringPresentation.ts`
- `frontend/src/lib/monitoring/operationalViewModel.ts`
- `frontend/src/lib/monitoring/sourceConvergence.ts` (new)
- `frontend/src/store/missionStore.ts`
- `frontend/qa-screenshots/codex-fix-01-scientific-data-integrity/REPORT.md`

The continuation did not modify Mission Timeline, AI Confidence, Final Signal Stack, Digital Twin presentation, backend code, global styling, navigation, deployment, or the human visualization.

### Residual finding 1 — mismatch before REST convergence

Root cause: the mismatch branch recorded only `observedSourceIdentityKey`, leaving the prior `latest` and `history` active. Full operational routes set `seedDataSourceState={false}`, so `LiveFeedProvider` did not own convergence there and no other owner observed the identity transition.

Correction:

- A mismatched frame now immediately clears `latest` and current-session `history` while preserving only noncurrent historical timestamp metadata.
- The store records one `sourceConvergenceKey` for the mismatched full identity.
- `MonitoringSessionProvider`, already the single REST owner on full operational routes, observes that key and makes one convergence request through a pure dedupe planner.
- Repeated frames with the same mismatched identity retain the same key and do not produce one request per frame.
- Failed requests and authoritative results that do not match the observed identity remain fail-closed and do not loop automatically.
- A genuinely new mismatch identity produces one new request.
- When REST confirms the pending identity, the key clears; the next matching frame becomes current and starts a history containing only that session.
- Status-derived display fallback is disabled while identity convergence is pending.
- Live-feed-only routes retain `LiveFeedProvider` as their REST owner; full routes use `MonitoringSessionProvider`. No route mounts two convergence owners.

Behavioral evidence exercises the real Zustand store and the same pure request planner used by the provider:

```text
REST A -> frame A active
frame B while REST A -> A latest/history cleared immediately
repeated B -> one request plan total
REST still A / request failure -> A not restored, history empty, no retry loop
REST B -> convergence key cleared
next B frame -> active, B-only history
normal B frames -> no convergence polling
```

### Residual finding 2 — control surfaces bypassed availability

Root cause: replay and fault controls independently combined confirmed snapshots with retained REST status, and the HR panel always called the no-fault formatter even when current source state was unavailable.

Correction:

- Added shared pure replay/fault controller derivations driven by `TelemetryAvailability`.
- `ReplaySessionControl` consumes the operational view model, withholds current subject/playback/speed/position/duration under unavailable states, explicitly labels retained subject selection as configuration, and disables source, playback, and speed mutations.
- `SimulatedFaultControl` consumes the same model, withholds stale fault details, disables apply/clear/config inputs, and reports the fault state as not currently confirmed.
- `HrInferencePanel` uses the tested fault derivation and cannot claim no fault while the source is unconfirmed.
- `InferenceResponseTimeline` now limits its current-window statement to active authoritative availability.
- Active confirmed replay and fault behavior remains operational.

Behavioral controller tests cover active confirmed, source loading, REST error, disconnected, no confirmed frame, and identity mismatch awaiting convergence. For every unavailable state they assert null current values, explicit unavailable messaging, disabled mutations, absent retained subject/playback details, withheld stale fault detail, and absence of the false `No simulated fault is active` claim.

### Residual finding 3 — secondary missing vitals nominal

Root cause: `MetricTile` defaults to nominal and HRV, respiration, and blood-pressure tiles did not pass an explicit level. Their display predicates also accepted `NaN` and infinities because they checked only nullishness.

Correction:

- Added shared finite-value and grouped-availability helpers.
- HRV and respiration now pass scalar availability-derived levels.
- Blood pressure requires both systolic and diastolic to be finite and passes a grouped availability-derived level.
- Null, undefined, `NaN`, and positive/negative infinity render unavailable/offline.
- Genuine finite zero remains present rather than being treated as missing; valid finite values retain existing nominal presentation.
- Heart-rate display also uses the finite-value predicate, preserving the earlier missing-HR correction.

### Tests and command results

The monitoring suite increased from the reviewed 601-check baseline to 744 behavioral/structural checks without removing a prior check.

```text
npm run verify:monitoring
  First targeted run: 735/736 passed, 1 failed
  Diagnosis: expected text did not match the existing canonical active-fault formatter
  Repaired expectation to the actual semantic label

npm run verify:monitoring
  736/736 passed; consumer guard passed

npm run lint
  PASS (exit 0)

npx tsc --noEmit
  PASS (exit 0)

npm run verify:monitoring
  736/736 passed; consumer guard passed

npm run verify:monitoring
  741/741 passed after provider/component integration assertions

npm run lint
  Final: PASS (exit 0)

npx tsc --noEmit
  Final: PASS (exit 0)

npm run verify:monitoring
  Final: 744/744 passed, 0 failed
  Consumer guard: PASS, 20 protected files
  Source-state / subject-list retry independence: PASS

npm run build
  Final: PASS; compiled successfully and generated 14/14 static pages

git diff --check
  PASS
```

### Browser/runtime evidence

Read-only probes after the correction returned no connection (`000`) at frontend candidates `127.0.0.1:3000` and `127.0.0.1:3100`, and backend health candidates on `127.0.0.1:8000`. Browser adverse-state verification was therefore unavailable. No service was started and no backend source, subject, replay position, fault state, or screenshot evidence was mutated or fabricated.

### Continuation ending state

- Branch: `stage5-dashboard-canonical-sync`
- HEAD: `c99ed8f14a2d9605c0059fd3a1444cf0b31fbe19`
- Latest commit unchanged: `c99ed8f feat(frontend): complete operational experience and delivery hardening`
- Ending `git status --short`:

```text
 M frontend/scripts/verify-monitoring-consumers.mjs
 M frontend/scripts/verify-monitoring-state.ts
 M frontend/src/app/mission-timeline/page.tsx
 M frontend/src/components/layout/LiveFeedProvider.tsx
 M frontend/src/components/monitoring/FinalSignalStack.tsx
 M frontend/src/components/monitoring/HrInferencePanel.tsx
 M frontend/src/components/monitoring/InferenceResponseTimeline.tsx
 M frontend/src/components/monitoring/MonitoringSessionContext.tsx
 M frontend/src/components/monitoring/MonitoringSourceStrip.tsx
 M frontend/src/components/monitoring/ReplaySessionControl.tsx
 M frontend/src/components/monitoring/ScopeProvenanceFooter.tsx
 M frontend/src/components/monitoring/SimulatedFaultControl.tsx
 M frontend/src/components/panels/AIConfidencePanel.tsx
 M frontend/src/components/panels/PrimaryVitalsPanel.tsx
 M frontend/src/lib/monitoring/operationalViewModel.ts
 M frontend/src/lib/monitoring/sourceIdentity.ts
 M frontend/src/lib/monitoring/telemetryAvailability.ts
 M frontend/src/store/missionStore.ts
?? .site-preview-mission-overview-local.png
?? .site-preview-mission-overview.png
?? .site-preview-research.png
?? edit_haydarpasa.mjs
?? frontend/public/models/
?? frontend/qa-screenshots/
?? frontend/src/components/visualization/human/HolographicHumanModel.tsx
?? frontend/src/lib/monitoring/controlPresentation.ts
?? frontend/src/lib/monitoring/insightDisplay.ts
?? frontend/src/lib/monitoring/liveMonitoringPresentation.ts
?? frontend/src/lib/monitoring/sourceConvergence.ts
?? help_table_rows.mjs
?? inspect_basliksiz.mjs
?? inspect_haydarpasa.mjs
?? inspect_workbook.mjs
?? node_modules
?? qa-screenshots/
```

No stage, commit, push, amend, reset, restore, clean, stash, branch switch, merge, rebase, backend mutation, or user-artifact deletion occurred.

### Remaining limitations and final verdict

- Browser verification remains unavailable because the services were not running.
- Component mounting is not available in the repository's test stack. The components consume pure controller derivations that are behaviorally exercised across every required state; source wiring checks complement rather than replace those behavioral tests.
- F-03 remains unchanged and protected by its passing tests: no adaptation percentage, score, narrative, or success badge has returned, and the visible architecture-only/untrained/unvalidated/not-personalized boundary remains.

All three independent-review residuals are corrected with passing behavioral evidence. The uncommitted package is ready for another independent review, but not committed.

`CODEX_FIX_01_CORRECTIVE_REVIEW_STATUS: COMPLETE`

`MISMATCH_BEFORE_REST_FAILS_CLOSED: YES`

`FULL_ROUTE_IDENTITY_CONVERGENCE: YES`

`LIVE_CONTROL_SURFACES_AUTHORITATIVELY_GATED: YES`

`ALL_MISSING_VITALS_NON_NOMINAL: YES`

`F03_PRESERVED: YES`

`READY_FOR_INDEPENDENT_REVIEW: YES`

`READY_TO_COMMIT: NO`

## Fourth independent-review correction — physical request single-flight

This addendum is the final authoritative terminus for owner-transfer request behavior. It supersedes the third-review claim `FULL_LEGACY_OWNER_TRANSFER_SINGLE_FLIGHT: YES`. That earlier claim was incorrect because the tests counted destination request tickets, not total invocations of the physical request factory. The accepted A/B/C authoritative-transition correction is unchanged.

### Repository identity and preservation

- Starting branch: `stage5-dashboard-canonical-sync`
- Starting HEAD: `c99ed8f14a2d9605c0059fd3a1444cf0b31fbe19`
- Ending branch: `stage5-dashboard-canonical-sync`
- Ending HEAD: `c99ed8f14a2d9605c0059fd3a1444cf0b31fbe19`
- No stage, commit, push, pull, fetch, merge, rebase, stash, reset, restore, clean, branch switch, worktree creation, artifact deletion, or Claude-worktree edit was performed.

Starting `git status --short`:

```text
 M frontend/scripts/verify-monitoring-consumers.mjs
 M frontend/scripts/verify-monitoring-state.ts
 M frontend/src/app/mission-timeline/page.tsx
 M frontend/src/components/layout/LiveFeedProvider.tsx
 M frontend/src/components/monitoring/FinalSignalStack.tsx
 M frontend/src/components/monitoring/HrInferencePanel.tsx
 M frontend/src/components/monitoring/InferenceResponseTimeline.tsx
 M frontend/src/components/monitoring/MonitoringSessionContext.tsx
 M frontend/src/components/monitoring/MonitoringSourceStrip.tsx
 M frontend/src/components/monitoring/ReplaySessionControl.tsx
 M frontend/src/components/monitoring/ScopeProvenanceFooter.tsx
 M frontend/src/components/monitoring/SimulatedFaultControl.tsx
 M frontend/src/components/panels/AIConfidencePanel.tsx
 M frontend/src/components/panels/PrimaryVitalsPanel.tsx
 M frontend/src/lib/monitoring/operationalViewModel.ts
 M frontend/src/lib/monitoring/sourceIdentity.ts
 M frontend/src/lib/monitoring/telemetryAvailability.ts
 M frontend/src/lib/monitoring/useConfirmedSnapshot.ts
 M frontend/src/store/missionStore.ts
?? .site-preview-mission-overview-local.png
?? .site-preview-mission-overview.png
?? .site-preview-research.png
?? edit_haydarpasa.mjs
?? frontend/public/models/
?? frontend/qa-screenshots/
?? frontend/src/components/visualization/human/HolographicHumanModel.tsx
?? frontend/src/lib/monitoring/controlPresentation.ts
?? frontend/src/lib/monitoring/insightDisplay.ts
?? frontend/src/lib/monitoring/liveMonitoringPresentation.ts
?? frontend/src/lib/monitoring/sourceConvergence.ts
?? help_table_rows.mjs
?? inspect_basliksiz.mjs
?? inspect_haydarpasa.mjs
?? inspect_workbook.mjs
?? node_modules
?? qa-screenshots/
```

The fourth correction changed only:

- `frontend/src/lib/monitoring/sourceConvergence.ts`
- `frontend/src/components/layout/LiveFeedProvider.tsx`
- `frontend/src/components/monitoring/MonitoringSessionContext.tsx`
- `frontend/scripts/verify-monitoring-state.ts`
- `frontend/qa-screenshots/codex-fix-01-scientific-data-integrity/REPORT.md`

All other pre-existing tracked modifications and untracked user artifacts were preserved.

### Root cause and corrected lifecycle

Before:

```text
full B factory invocation #1 -> unresolved
full releases -> activateOwner clears inFlight
legacy activates -> legacy B factory invocation #2
old response is stale, but two physical REST requests exist
```

After:

```text
full B factory invocation #1 -> central physical promise remains unresolved
full releases -> full subscriber is detached
legacy activates -> subscribes to the existing B promise; no factory invocation
original promise settles -> only legacy's current callbacks receive B/error
total physical B request count: 1
```

`SourceStateRequestCoordinator` now separates three concerns:

- the centrally owned physical request and its underlying promise;
- the replaceable active owner/subscriber and its local callbacks;
- the monotonic response generation used to reject a superseded B after C starts.

The physical request survives owner replacement and same-owner Strict Mode replay. A settlement that occurs in the gap between release and replacement is retained without writing and is delivered only after a matching destination subscribes. With no replacement, settlement performs zero store writes and zero component-local callbacks. A genuinely different key starts one new generation and one new physical request; the older generation cannot write in either completion order. A completed failure remains deduped until an explicit forced retry, which creates exactly one new physical request.

Both `LiveFeedProvider` and `MonitoringSessionProvider` now call `startOrAdoptRequest` and register their current result/error callbacks with this same shared lifecycle.

### Behavioral request counts and callback evidence

Production-controller tests use deferred promises and increment counters inside the actual request factory:

```text
full -> legacy, pending B:              1 physical request
legacy -> full, pending B:              1 physical request
initial-seed owner transfer:            1 physical request
same-owner Strict Mode release/replay:  1 physical request
settlement during owner-transfer gap:   1 physical request
no replacement:                         1 physical request, 0 writes/callbacks
B -> C different identity:              2 total (1 B + exactly 1 C)
adopted failure:                         1 physical request
explicit retry after failure:           +1 physical request
```

In both same-key transfer directions, the destination callback receives and applies the original promise's B result exactly once and the superseded owner's local callback count remains zero. The same callback routing is proven for an adopted error. Both B-first and C-first completion orders prove that B cannot overwrite C.

### Verification

```text
npm run verify:monitoring (required pre-edit baseline)
  848/848 passed, 0 failed
  consumer guard passed
  source-state / subject-list retry independence passed

npm run verify:monitoring (final)
  888/888 passed, 0 failed
  consumer guard passed across 20 protected files
  source-state / subject-list retry independence passed

npm run lint
  PASS (exit 0)

npx tsc --noEmit
  PASS (exit 0)

npm run build
  PASS; compiled successfully and generated 14/14 static pages

git diff --check
  PASS
```

The final suite is greater than 848 and preserves the prior checks, including the accepted A -> pending B -> REST A fail-closed path, REST B recovery, REST C then frame C recovery, global pending-convergence gate, stale-response rejection, dataset/history isolation, missing-vital semantics, replay/fault/HR inference gating, Digital Twin boundary, and retry independence.

Ending `git status --short` is identical to the starting status shown above. The ending tracked changed-file list remains the same 19 pre-existing tracked paths; the five fourth-correction files are contained within that preserved package (with `sourceConvergence.ts` and this report under pre-existing untracked paths).

`CODEX_FIX_01_PHYSICAL_SINGLE_FLIGHT_STATUS: COMPLETE`

`FULL_TO_LEGACY_SAME_KEY_PHYSICAL_REQUEST_COUNT: 1`

`LEGACY_TO_FULL_SAME_KEY_PHYSICAL_REQUEST_COUNT: 1`

`INITIAL_SEED_TRANSFER_PHYSICAL_REQUEST_COUNT: 1`

`DESTINATION_OWNER_ADOPTS_IN_FLIGHT_RESULT: YES`

`SUPERSEDED_OWNER_LOCAL_CALLBACKS_BLOCKED: YES`

`STALE_RESPONSE_PROTECTION_PRESERVED: YES`

`PHYSICAL_REQUEST_FACTORY_BEHAVIORALLY_TESTED: YES`

`ALL_PREVIOUS_848_CHECKS_PRESERVED: YES`

`READY_FOR_INDEPENDENT_REVIEW: YES`

`READY_TO_COMMIT: NO`

## Third independent-review correction — authoritative event ordering

### Starting repository state

- Branch: `stage5-dashboard-canonical-sync`
- HEAD: `c99ed8f14a2d9605c0059fd3a1444cf0b31fbe19`
- Pre-edit monitoring baseline: `777/777`, consumer guard passed for 20 protected files, retry-independence guard passed.
- The existing uncommitted package was continued rather than replaced.
- Starting `git status --short`:

```text
 M frontend/scripts/verify-monitoring-consumers.mjs
 M frontend/scripts/verify-monitoring-state.ts
 M frontend/src/app/mission-timeline/page.tsx
 M frontend/src/components/layout/LiveFeedProvider.tsx
 M frontend/src/components/monitoring/FinalSignalStack.tsx
 M frontend/src/components/monitoring/HrInferencePanel.tsx
 M frontend/src/components/monitoring/InferenceResponseTimeline.tsx
 M frontend/src/components/monitoring/MonitoringSessionContext.tsx
 M frontend/src/components/monitoring/MonitoringSourceStrip.tsx
 M frontend/src/components/monitoring/ReplaySessionControl.tsx
 M frontend/src/components/monitoring/ScopeProvenanceFooter.tsx
 M frontend/src/components/monitoring/SimulatedFaultControl.tsx
 M frontend/src/components/panels/AIConfidencePanel.tsx
 M frontend/src/components/panels/PrimaryVitalsPanel.tsx
 M frontend/src/lib/monitoring/operationalViewModel.ts
 M frontend/src/lib/monitoring/sourceIdentity.ts
 M frontend/src/lib/monitoring/telemetryAvailability.ts
 M frontend/src/lib/monitoring/useConfirmedSnapshot.ts
 M frontend/src/store/missionStore.ts
?? .site-preview-mission-overview-local.png
?? .site-preview-mission-overview.png
?? .site-preview-research.png
?? edit_haydarpasa.mjs
?? frontend/public/models/
?? frontend/qa-screenshots/
?? frontend/src/components/visualization/human/HolographicHumanModel.tsx
?? frontend/src/lib/monitoring/controlPresentation.ts
?? frontend/src/lib/monitoring/insightDisplay.ts
?? frontend/src/lib/monitoring/liveMonitoringPresentation.ts
?? frontend/src/lib/monitoring/sourceConvergence.ts
?? help_table_rows.mjs
?? inspect_basliksiz.mjs
?? inspect_haydarpasa.mjs
?? inspect_workbook.mjs
?? node_modules
?? qa-screenshots/
```

### Root causes

#### Finding A — third authoritative identity deadlock

The store retained only the pending identity B and the latest REST status. After `A -> pending B -> REST C`, it could not distinguish unchanged pre-convergence A from a genuine authoritative transition to C. Pending B therefore survived REST C, and the global pending boundary correctly but permanently rejected C frames.

The store also needed an explicit record of superseded and retired identities. Without it, frame C could replace pending B and a later B frame could flip the target back, or abandoned B could reopen convergence after REST had advanced to C.

#### Finding B — duplicate and stale source-state requests

Both route owners had separate initial-seed and convergence effects. Mounting with a pre-existing pending identity could start both requests. Local cancellation flags prevented some unmounted writes but did not provide a shared owner epoch or request generation, so a stale A response could arrive after a newer B/C response and roll the authoritative store backward.

### Exact files changed in this third continuation

- `frontend/src/store/missionStore.ts` — explicit convergence base, superseded identities, and retired identities; deterministic REST A/B/C treatment.
- `frontend/src/lib/monitoring/sourceConvergence.ts` — shared REST disposition classifier and source-state owner/generation coordinator.
- `frontend/src/components/layout/LiveFeedProvider.tsx` — one coordinated legacy-owner lifecycle instead of separate seed and convergence requests.
- `frontend/src/components/monitoring/MonitoringSessionContext.tsx` — one coordinated full-owner lifecycle, stale-response rejection, and preserved independent retry behavior.
- `frontend/scripts/verify-monitoring-state.ts` — real-store and behavioral request-ordering regressions.
- `frontend/qa-screenshots/codex-fix-01-scientific-data-integrity/REPORT.md` — this third-review record.

No visual component, style, backend, model, asset, route definition, navigation, deployment file, Claude worktree, or unrelated artifact was changed.

### Authoritative transition semantics

| Transition | Before | Final behavior |
|---|---|---|
| `A -> pending B -> REST A` | Pending could remain but later ordering was underspecified. | REST A is classified as unchanged pre-convergence authority. Pending B and base A remain; telemetry stays unavailable; late A is rejected. |
| `A -> pending B -> REST B -> frame B` | B could clear pending. | REST B is explicitly classified as confirming pending B. Pending/base clear; A retires; next B becomes current with B-only history. |
| `A -> pending B -> REST C -> frame C` | Pending B remained and C deadlocked. | REST C is classified as a third authoritative transition. Pending/base clear; A and abandoned B retire; next C becomes current with C-only history; no C request is opened. |
| `pending B -> frame C -> repeated B/C` | B and C could alternate pending targets. | First C supersedes B once. B is recorded as superseded; repeated B or C cannot retarget or create request loops. |
| Retired A/B frame after C is current | A retired frame could reopen or clear state. | Retired frame is ignored: it cannot overwrite C, enter C history, advance the confirmed timestamp, or reopen convergence. REST may still authoritatively select that identity in a future transition. |

REST remains authoritative. The deterministic disposition values are `unchanged_pre_convergence_authority`, `confirmed_pending_identity`, and `advanced_to_third_authority`; non-B responses are not blindly treated as success.

### Request ownership and stale-response rules

`SourceStateRequestCoordinator` is the single definition used by both route owners.

- An owner token plus monotonically increasing owner epoch defines the active full or legacy route owner.
- A monotonically increasing request generation defines the only response currently eligible to write.
- A response is accepted only if the owner is active, its owner token and epoch still match, and its generation is still the current in-flight generation.
- Changing owners invalidates the previous owner independently of promise cancellation.
- Starting a newer pending identity invalidates the older generation independently of response order.
- Releasing an owner makes later success and failure responses stale; they perform no callbacks or store writes.
- Re-activating the same owner token, including React Strict Mode effect replay, adopts its existing lifecycle and does not duplicate the in-flight request.
- The first active-owner request is either the initial seed or pending convergence, never both.
- Repeated pending identities remain deduplicated after success or failure; only an explicit source-state retry may force another request.
- A non-fetch authoritative action response supersedes an older source-state fetch before writing.
- Source-state retry and subject-list retry remain separate effects and tokens.
- No timer, polling interval, automatic retry loop, or hidden global poll was introduced.

### Behavioral tests and assertions

The deterministic suite increased from 777 to 848 checks. New evidence exercises the production Zustand store, REST disposition classifier, coordinator, executor, and route-owner wiring.

Third-authority store tests prove:

```text
REST A -> A1 current -> B1 pending
REST A -> pending B/base A retained; late A remains unavailable
REST B -> pending/base clear -> B frame current -> B-only history
REST C -> obsolete B clears -> no stale A/B restoration
C1 -> current C -> C-only history -> no redundant C request
late retired A -> C remains current; no new pending; timestamp unchanged
frame C supersedes pending B once
repeated C and superseded B -> request count remains 2
```

Request-controller tests prove:

```text
owner starts without pending -> exactly one initial-seed ticket
owner starts with pending B -> exactly one convergence ticket, no seed ticket
same-owner Strict Mode replay -> original ticket retained, no duplicate
full -> legacy transfer with pending B -> one destination-owner ticket
legacy -> full transfer with pending B -> one destination-owner ticket
repeated B while in flight -> no additional ticket
B -> C -> exactly one additional C ticket; repeated C -> none
newer B response accepted before older A -> real store remains B
older A resolving first after newer C was planned -> A stale, then C accepted
unmounted owner response -> stale, zero writes
superseded owner response -> stale, cannot roll C back
current-owner error -> one error callback, no automatic retry
explicit retry -> one retry ticket and remains single-flight
```

### Verification chronology and final results

```text
npm run verify:monitoring
  Pre-edit baseline: 777/777 passed
  Consumer guard: PASS, 20 protected files
  Retry-independence guard: PASS

npm run verify:monitoring
  First integration run: 775/777 passed
  Two failures were obsolete structural expectations that named the prior
  planner directly; product behavior was not weakened. They were replaced
  with stronger wiring checks for the shared coordinator/executor.

npm run verify:monitoring
  Intermediate behavioral expansions: 836/836, 842/842, 846/846 passed

npm run verify:monitoring
  Final: 848/848 passed, 0 failed
  Consumer guard: PASS, 20 protected files
  Source-state / subject-list retry independence: PASS

npm run lint
  PASS (exit 0)

npx tsc --noEmit
  PASS (exit 0)

npm run build
  PASS; compiled successfully and generated 14/14 static pages

git diff --check
  PASS
```

### Limitations and runtime evidence

Read-only probes returned `000` at frontend candidates `127.0.0.1:3000` and `127.0.0.1:3100`, plus backend health candidates `127.0.0.1:8000/health` and `127.0.0.1:8000/api/health`. Services were not running, so browser evidence was unavailable. No service or backend was started or mutated, and no screenshot/runtime evidence was fabricated.

The repository has no safe component-mounting test framework for these providers. The shared request lifecycle was therefore extracted as a production pure controller and tested behaviorally with deferred promises, real request counts, real Zustand transitions, both completion orders, owner transfers, cleanup, and errors. Source wiring assertions only supplement that behavioral proof.

### Ending repository state and preservation

- Branch: `stage5-dashboard-canonical-sync`
- HEAD: `c99ed8f14a2d9605c0059fd3a1444cf0b31fbe19`
- Ending `git status --short`:

```text
 M frontend/scripts/verify-monitoring-consumers.mjs
 M frontend/scripts/verify-monitoring-state.ts
 M frontend/src/app/mission-timeline/page.tsx
 M frontend/src/components/layout/LiveFeedProvider.tsx
 M frontend/src/components/monitoring/FinalSignalStack.tsx
 M frontend/src/components/monitoring/HrInferencePanel.tsx
 M frontend/src/components/monitoring/InferenceResponseTimeline.tsx
 M frontend/src/components/monitoring/MonitoringSessionContext.tsx
 M frontend/src/components/monitoring/MonitoringSourceStrip.tsx
 M frontend/src/components/monitoring/ReplaySessionControl.tsx
 M frontend/src/components/monitoring/ScopeProvenanceFooter.tsx
 M frontend/src/components/monitoring/SimulatedFaultControl.tsx
 M frontend/src/components/panels/AIConfidencePanel.tsx
 M frontend/src/components/panels/PrimaryVitalsPanel.tsx
 M frontend/src/lib/monitoring/operationalViewModel.ts
 M frontend/src/lib/monitoring/sourceIdentity.ts
 M frontend/src/lib/monitoring/telemetryAvailability.ts
 M frontend/src/lib/monitoring/useConfirmedSnapshot.ts
 M frontend/src/store/missionStore.ts
?? .site-preview-mission-overview-local.png
?? .site-preview-mission-overview.png
?? .site-preview-research.png
?? edit_haydarpasa.mjs
?? frontend/public/models/
?? frontend/qa-screenshots/
?? frontend/src/components/visualization/human/HolographicHumanModel.tsx
?? frontend/src/lib/monitoring/controlPresentation.ts
?? frontend/src/lib/monitoring/insightDisplay.ts
?? frontend/src/lib/monitoring/liveMonitoringPresentation.ts
?? frontend/src/lib/monitoring/sourceConvergence.ts
?? help_table_rows.mjs
?? inspect_basliksiz.mjs
?? inspect_haydarpasa.mjs
?? inspect_workbook.mjs
?? node_modules
?? qa-screenshots/
```

No stage, commit, amend, push, pull, fetch, merge, rebase, cherry-pick, stash, reset, restore, clean, branch/worktree creation or switch, Claude-worktree modification, backend mutation, unrelated cleanup, or artifact deletion occurred.

`CODEX_FIX_01_EVENT_ORDERING_STATUS: COMPLETE`

`THIRD_AUTHORITATIVE_IDENTITY_RECOVERS: YES`

`UNCHANGED_OLD_REST_REMAINS_FAIL_CLOSED: YES`

`INITIAL_SEED_AND_CONVERGENCE_SINGLE_FLIGHT: YES`

`FULL_LEGACY_OWNER_TRANSFER_SINGLE_FLIGHT: YES`

`STALE_RESPONSE_CANNOT_ROLL_BACK_AUTHORITY: YES`

`SUPERSEDED_OWNER_CANNOT_WRITE: YES`

`REQUEST_ORCHESTRATION_BEHAVIORALLY_TESTED: YES`

`ALL_PREVIOUS_777_CHECKS_PRESERVED: YES`

`READY_FOR_INDEPENDENT_REVIEW: YES`

`READY_TO_COMMIT: NO`

## Fourth independent-review verdict — accepted historical terminus

The third-review owner-transfer COMPLETE claim immediately above is superseded. The detailed fourth-review correction and evidence earlier in this report are authoritative; they count physical request-factory invocations rather than destination tickets.

`CODEX_FIX_01_PHYSICAL_SINGLE_FLIGHT_STATUS: COMPLETE`

`FULL_TO_LEGACY_SAME_KEY_PHYSICAL_REQUEST_COUNT: 1`

`LEGACY_TO_FULL_SAME_KEY_PHYSICAL_REQUEST_COUNT: 1`

`INITIAL_SEED_TRANSFER_PHYSICAL_REQUEST_COUNT: 1`

`DESTINATION_OWNER_ADOPTS_IN_FLIGHT_RESULT: YES`

`SUPERSEDED_OWNER_LOCAL_CALLBACKS_BLOCKED: YES`

`STALE_RESPONSE_PROTECTION_PRESERVED: YES`

`PHYSICAL_REQUEST_FACTORY_BEHAVIORALLY_TESTED: YES`

`ALL_PREVIOUS_848_CHECKS_PRESERVED: YES`

`READY_FOR_INDEPENDENT_REVIEW: YES`

`READY_TO_COMMIT: NO`

## Fifth independent-review correction — final report terminus

The fourth-review physical single-flight correction is accepted and preserved: same-key full/legacy transfers, initial-seed transfer, Strict Mode replay, callback adoption, and stale-generation rejection still use one physical GET. The prior overall COMPLETE verdict is superseded because legacy `DataSourceControl` mutations wrote authoritative `DataSourceStatus` directly and therefore bypassed the shared request generation.

### Repository identity and preservation

- Starting branch: `stage5-dashboard-canonical-sync`
- Starting HEAD: `c99ed8f14a2d9605c0059fd3a1444cf0b31fbe19`
- Ending branch: `stage5-dashboard-canonical-sync`
- Ending HEAD: `c99ed8f14a2d9605c0059fd3a1444cf0b31fbe19`
- No stage, commit, push, pull, fetch, merge, rebase, stash, reset, restore, clean, branch switch, worktree creation, artifact deletion, or Claude-worktree edit occurred.

Starting `git status --short` contained the preserved 19 tracked modifications from the existing package and these untracked entries:

```text
 M frontend/scripts/verify-monitoring-consumers.mjs
 M frontend/scripts/verify-monitoring-state.ts
 M frontend/src/app/mission-timeline/page.tsx
 M frontend/src/components/layout/LiveFeedProvider.tsx
 M frontend/src/components/monitoring/FinalSignalStack.tsx
 M frontend/src/components/monitoring/HrInferencePanel.tsx
 M frontend/src/components/monitoring/InferenceResponseTimeline.tsx
 M frontend/src/components/monitoring/MonitoringSessionContext.tsx
 M frontend/src/components/monitoring/MonitoringSourceStrip.tsx
 M frontend/src/components/monitoring/ReplaySessionControl.tsx
 M frontend/src/components/monitoring/ScopeProvenanceFooter.tsx
 M frontend/src/components/monitoring/SimulatedFaultControl.tsx
 M frontend/src/components/panels/AIConfidencePanel.tsx
 M frontend/src/components/panels/PrimaryVitalsPanel.tsx
 M frontend/src/lib/monitoring/operationalViewModel.ts
 M frontend/src/lib/monitoring/sourceIdentity.ts
 M frontend/src/lib/monitoring/telemetryAvailability.ts
 M frontend/src/lib/monitoring/useConfirmedSnapshot.ts
 M frontend/src/store/missionStore.ts
?? .site-preview-mission-overview-local.png
?? .site-preview-mission-overview.png
?? .site-preview-research.png
?? edit_haydarpasa.mjs
?? frontend/public/models/
?? frontend/qa-screenshots/
?? frontend/src/components/visualization/human/HolographicHumanModel.tsx
?? frontend/src/lib/monitoring/controlPresentation.ts
?? frontend/src/lib/monitoring/insightDisplay.ts
?? frontend/src/lib/monitoring/liveMonitoringPresentation.ts
?? frontend/src/lib/monitoring/sourceConvergence.ts
?? help_table_rows.mjs
?? inspect_basliksiz.mjs
?? inspect_haydarpasa.mjs
?? inspect_workbook.mjs
?? node_modules
?? qa-screenshots/
```

The fifth correction changed only:

- `frontend/src/lib/monitoring/sourceConvergence.ts`
- `frontend/src/components/demos/DataSourceControl.tsx`
- `frontend/src/components/layout/LiveFeedProvider.tsx`
- `frontend/src/components/monitoring/MonitoringSessionContext.tsx`
- `frontend/scripts/verify-monitoring-state.ts`
- `frontend/qa-screenshots/codex-fix-01-scientific-data-integrity/REPORT.md`

The ending status adds only `M frontend/src/components/demos/DataSourceControl.tsx` to the starting status above. The ending tracked changed-file list is therefore the same 19 starting paths plus `frontend/src/components/demos/DataSourceControl.tsx`; every existing untracked artifact remains present.

### Before and after event ordering

Before:

```text
legacy seed GET A starts and remains unresolved
DataSourceControl mutation returns B
DataSourceControl directly writes B
older seed GET resolves A and coordinator still accepts it
store rolls backward B -> A
```

After:

```text
legacy seed GET A starts at generation 1
legacy mutation starts at generation 2 and invalidates generation 1 before any mutation write
mutation B resolves; current owner/epoch/generation callback writes B
older GET A resolves; outcome is stale and performs no callback/write
store remains B
```

The production coordinator now issues owner- and epoch-scoped authoritative mutation tickets. A mutation advances the same monotonic generation used by physical GETs before invoking its request factory. Success and error callbacks run only if that owner, epoch, and generation are still current. A second mutation advances the generation again, and route transfer advances the owner epoch. No unscoped cancel operation, timer, polling loop, or render-driven retry was added.

`LiveFeedProvider` exposes only a legacy-provider-scoped mutation starter bound to its private owner token. `DataSourceControl` routes every synthetic/load/play/pause/reset/speed/fault operation through it. `MonitoringSessionProvider` uses the same production coordinator for full-route actions and its compound reset generation.

### Behavioral operation and write counts

All cases use deferred promises with the production coordinator:

```text
seed GET A -> mutation B -> late A:
  GET factories 1; mutation factories 1; accepted writes 1; final B

inverse completion (GET settles physically before mutation):
  accepted writes 1; final B

pending convergence GET B -> mutation C -> late B:
  accepted store writes 1; pending cleared; final C; C telemetry recovers

legacy mutation resolves after unmount:
  mutation factories 1; store writes 0; component-local callbacks 0

legacy mutation resolves after transfer to full owner:
  obsolete legacy callbacks 0; final authority C from full owner

two mutations with reversed completion:
  accepted writes 1; newer C wins; older B is stale

active mutation failure:
  authority writes 0; active error callbacks 1

obsolete mutation failure:
  authority writes 0; obsolete callbacks 0
```

The pre-existing fourth-review deferred tests remain intact and continue to prove one physical GET for full -> legacy B, legacy -> full B, initial-seed transfer, Strict Mode replay, and settlement during the transfer gap.

### Verification

```text
npm run verify:monitoring (required pre-edit baseline)
  888/888 passed, 0 failed
  consumer guard passed
  source-state / subject-list retry independence passed

npm run verify:monitoring (final)
  932/932 passed, 0 failed
  consumer guard passed across 20 protected files
  source-state / subject-list retry independence passed

npm run lint
  PASS (exit 0)

npx tsc --noEmit
  PASS (exit 0)

npm run build
  PASS; compiled successfully and generated 14/14 static pages

git diff --check
  PASS
```

`CODEX_FIX_01_AUTHORITATIVE_MUTATION_ORDERING_STATUS: COMPLETE`

`LEGACY_MUTATION_SUPERSEDES_OLDER_GET: YES`

`LATE_GET_CANNOT_ROLL_BACK_MUTATION: YES`

`UNMOUNTED_LEGACY_CONTROL_CANNOT_WRITE: YES`

`OBSOLETE_LEGACY_OWNER_CANNOT_WRITE: YES`

`MUTATION_GENERATION_BEHAVIORALLY_TESTED: YES`

`PHYSICAL_SINGLE_FLIGHT_PRESERVED: YES`

`ALL_PREVIOUS_888_CHECKS_PRESERVED: YES`

`READY_FOR_INDEPENDENT_REVIEW: YES`

`READY_TO_COMMIT: NO`

## Second independent-review correction — global pending-convergence boundary

### Root cause and affected route tiers

The first correction cleared `latest` and `history` when a mismatched identity was first observed, but `missionStore.ingest()` still evaluated later frames only against the old authoritative `dataSourceStatus`. If REST convergence failed or continued to report A, another A frame matched that old status and could repopulate current telemetry while `sourceConvergenceKey` still represented pending B. `useConfirmedSnapshot()` and `useConfirmedHistory()` did not independently check the pending key.

This was globally relevant but directly bypassed the intended boundary on the legacy live-feed tier, where `LiveFeedProvider` is the only REST owner and silently catches request failure:

- `/ai-insights`
- `/mission-timeline`
- `/settings`

The full operational tier remains `/mission-overview` and `/live-monitoring`, where `MonitoringSessionProvider` continues to report failed or non-confirming convergence as a source error.

### Starting state for the second continuation

- Branch: `stage5-dashboard-canonical-sync`
- HEAD: `c99ed8f14a2d9605c0059fd3a1444cf0b31fbe19`
- Baseline: `744/744` monitoring checks passed before editing.
- Starting `git status --short`:

```text
 M frontend/scripts/verify-monitoring-consumers.mjs
 M frontend/scripts/verify-monitoring-state.ts
 M frontend/src/app/mission-timeline/page.tsx
 M frontend/src/components/layout/LiveFeedProvider.tsx
 M frontend/src/components/monitoring/FinalSignalStack.tsx
 M frontend/src/components/monitoring/HrInferencePanel.tsx
 M frontend/src/components/monitoring/InferenceResponseTimeline.tsx
 M frontend/src/components/monitoring/MonitoringSessionContext.tsx
 M frontend/src/components/monitoring/MonitoringSourceStrip.tsx
 M frontend/src/components/monitoring/ReplaySessionControl.tsx
 M frontend/src/components/monitoring/ScopeProvenanceFooter.tsx
 M frontend/src/components/monitoring/SimulatedFaultControl.tsx
 M frontend/src/components/panels/AIConfidencePanel.tsx
 M frontend/src/components/panels/PrimaryVitalsPanel.tsx
 M frontend/src/lib/monitoring/operationalViewModel.ts
 M frontend/src/lib/monitoring/sourceIdentity.ts
 M frontend/src/lib/monitoring/telemetryAvailability.ts
 M frontend/src/store/missionStore.ts
?? .site-preview-mission-overview-local.png
?? .site-preview-mission-overview.png
?? .site-preview-research.png
?? edit_haydarpasa.mjs
?? frontend/public/models/
?? frontend/qa-screenshots/
?? frontend/src/components/visualization/human/HolographicHumanModel.tsx
?? frontend/src/lib/monitoring/controlPresentation.ts
?? frontend/src/lib/monitoring/insightDisplay.ts
?? frontend/src/lib/monitoring/liveMonitoringPresentation.ts
?? frontend/src/lib/monitoring/sourceConvergence.ts
?? help_table_rows.mjs
?? inspect_basliksiz.mjs
?? inspect_haydarpasa.mjs
?? inspect_workbook.mjs
?? node_modules
?? qa-screenshots/
```

### Exact files changed in the second continuation

- `frontend/src/store/missionStore.ts`
- `frontend/src/lib/monitoring/useConfirmedSnapshot.ts`
- `frontend/src/components/layout/LiveFeedProvider.tsx`
- `frontend/scripts/verify-monitoring-state.ts`
- `frontend/scripts/verify-monitoring-consumers.mjs`
- `frontend/qa-screenshots/codex-fix-01-scientific-data-integrity/REPORT.md`

No visual component, backend file, route definition, layout, navigation, accessibility package, or deployment file was changed in this continuation.

### Real-store reproduction before the fix

The reproduced failing transition was:

```text
REST A -> ingest A1 -> A current
ingest mismatched B1 -> latest/history cleared, pending B
convergence fails or REST still reports A
ingest A2 -> A2 became latest/history even though pending B remained
```

Observed invalid state:

```json
{
  "latest": "A",
  "history": ["A"],
  "pending": "[\"dataset_replay\",\"reported\",\"B\",\"S14\"]",
  "status": "A"
}
```

### Final behavior after the fix

- `sourceConvergenceKey !== null` is now a store-level fail-closed boundary evaluated before ordinary authoritative-status matching.
- Old-authoritative A frames and repeated pending B frames cannot enter `latest` or `history`, cannot replace the pending B target, and cannot advance `lastConfirmedTimestampSeconds`.
- A genuinely new non-authoritative C identity may replace pending B and produces one new convergence request.
- A known late frame from an identity retired by an already-authoritative REST transition is rejected without reopening convergence to the retired session. This preserves late-frame rejection and the existing authoritative A -> REST B -> valid B recovery contract.
- `useConfirmedSnapshot()` and `useConfirmedHistory()` now apply defense-in-depth pending-key gates. Even deliberately injected stale A residue is not exposed while B is pending.
- `LiveFeedProvider` separates its one-time initial seed from pending convergence and uses `planSourceConvergenceRequest`, the same tested one-request-per-identity planner used by the full-route owner.
- REST confirmation of B clears the pending boundary; the next B frame becomes current, creates B-only history, and normal B traffic does not poll.
- Pre-REST startup retains its existing provisional-telemetry behavior.

### Behavioral regression evidence and request counts

The production Zustand store, production confirmed-read helpers, production route classifier, and production convergence planner are exercised directly.

```text
REST A -> A1 current/history
B1 mismatch -> latest null, history empty, pending B, timestamp remains A1
REST still A -> pending B retained
A2 -> rejected; latest null; history empty; timestamp unchanged
confirmed snapshot/history -> unavailable, including injected stale-A defense test
request count after B1: 1
request count after repeated A2/B2: 1
REST B -> pending clears
B3 -> current; history contains only B; confirmed readers recover
normal B traffic -> request count remains 1

Separate replacement sequence:
B mismatch -> request count 1
new C mismatch -> request count 2
repeated C -> request count remains 2
all rejected frames -> confirmed timestamp unchanged

Pre-REST startup:
provisional frame -> latest/history available under the existing contract
```

Existing route-tier tests continue to prove `/ai-insights`, `/mission-timeline`, and `/settings` use the legacy live-feed owner, while `/mission-overview` and `/live-monitoring` use the full owner. Structural wiring assertions supplement, rather than replace, the real-store and pure-helper behavior tests.

### Complete verification results

```text
npm run verify:monitoring
  Pre-edit baseline: 744/744 passed

npm run verify:monitoring
  First targeted run: 769/771 passed, 2 failed
  Diagnosis: the stronger pending gate correctly exposed that a known late A
  frame after authoritative REST B was opening a stale A convergence target.
  Repair: reject the already-observed retired identity without opening pending
  convergence; preserve later genuine transitions after the first valid B.

npm run verify:monitoring
  Intermediate: 771/771 passed

npm run verify:monitoring
  Final: 777/777 passed, 0 failed
  Consumer guard: PASS, 20 protected files
  Source-state / subject-list retry independence: PASS

npm run lint
  PASS (exit 0)

npx tsc --noEmit
  PASS (exit 0)

npm run build
  PASS; compiled successfully and generated 14/14 static pages

git diff --check
  PASS
```

### Runtime evidence and limitations

Read-only probes returned `000` at `127.0.0.1:3000`, `127.0.0.1:3100`, `127.0.0.1:8000/health`, and `127.0.0.1:8000/api/health`. No service was started and no browser, backend, or screenshot evidence was fabricated. Component mounting remains unavailable in the repository's test stack; the global store and pure confirmed-read/request-planning helpers are exercised directly instead.

### Ending state for the second continuation

- Branch: `stage5-dashboard-canonical-sync`
- HEAD: `c99ed8f14a2d9605c0059fd3a1444cf0b31fbe19`
- Ending `git status --short`:

```text
 M frontend/scripts/verify-monitoring-consumers.mjs
 M frontend/scripts/verify-monitoring-state.ts
 M frontend/src/app/mission-timeline/page.tsx
 M frontend/src/components/layout/LiveFeedProvider.tsx
 M frontend/src/components/monitoring/FinalSignalStack.tsx
 M frontend/src/components/monitoring/HrInferencePanel.tsx
 M frontend/src/components/monitoring/InferenceResponseTimeline.tsx
 M frontend/src/components/monitoring/MonitoringSessionContext.tsx
 M frontend/src/components/monitoring/MonitoringSourceStrip.tsx
 M frontend/src/components/monitoring/ReplaySessionControl.tsx
 M frontend/src/components/monitoring/ScopeProvenanceFooter.tsx
 M frontend/src/components/monitoring/SimulatedFaultControl.tsx
 M frontend/src/components/panels/AIConfidencePanel.tsx
 M frontend/src/components/panels/PrimaryVitalsPanel.tsx
 M frontend/src/lib/monitoring/operationalViewModel.ts
 M frontend/src/lib/monitoring/sourceIdentity.ts
 M frontend/src/lib/monitoring/telemetryAvailability.ts
 M frontend/src/lib/monitoring/useConfirmedSnapshot.ts
 M frontend/src/store/missionStore.ts
?? .site-preview-mission-overview-local.png
?? .site-preview-mission-overview.png
?? .site-preview-research.png
?? edit_haydarpasa.mjs
?? frontend/public/models/
?? frontend/qa-screenshots/
?? frontend/src/components/visualization/human/HolographicHumanModel.tsx
?? frontend/src/lib/monitoring/controlPresentation.ts
?? frontend/src/lib/monitoring/insightDisplay.ts
?? frontend/src/lib/monitoring/liveMonitoringPresentation.ts
?? frontend/src/lib/monitoring/sourceConvergence.ts
?? help_table_rows.mjs
?? inspect_basliksiz.mjs
?? inspect_haydarpasa.mjs
?? inspect_workbook.mjs
?? node_modules
?? qa-screenshots/
```

No stage, commit, push, amend, merge, rebase, reset, restore, clean, stash, branch switch, backend mutation, unrelated editing, or user-artifact deletion occurred.

`CODEX_FIX_01_FINAL_CROSS_ROUTE_STATUS: COMPLETE`

`PENDING_CONVERGENCE_IS_GLOBAL_FAIL_CLOSED_GATE: YES`

`OLD_AUTHORITATIVE_FRAMES_REJECTED_WHILE_PENDING: YES`

`LEGACY_LIVE_FEED_ROUTES_FAIL_CLOSED: YES`

`FULL_OPERATIONAL_ROUTE_BEHAVIOR_PRESERVED: YES`

`CONVERGENCE_REQUESTS_DEDUPLICATED: YES`

`ALL_PREVIOUS_744_CHECKS_PRESERVED: YES`

`READY_FOR_INDEPENDENT_REVIEW: YES`

`READY_TO_COMMIT: NO`

## Third independent-review verdict — superseded historical terminus

The second-review section immediately above is retained only as a superseded historical record. The detailed third-review correction section and the following event-ordering verdict are the final authoritative result for this report.

`CODEX_FIX_01_EVENT_ORDERING_STATUS: COMPLETE`

`THIRD_AUTHORITATIVE_IDENTITY_RECOVERS: YES`

`UNCHANGED_OLD_REST_REMAINS_FAIL_CLOSED: YES`

`INITIAL_SEED_AND_CONVERGENCE_SINGLE_FLIGHT: YES`

`FULL_LEGACY_OWNER_TRANSFER_SINGLE_FLIGHT: YES`

`STALE_RESPONSE_CANNOT_ROLL_BACK_AUTHORITY: YES`

`SUPERSEDED_OWNER_CANNOT_WRITE: YES`

`REQUEST_ORCHESTRATION_BEHAVIORALLY_TESTED: YES`

`ALL_PREVIOUS_777_CHECKS_PRESERVED: YES`

`READY_FOR_INDEPENDENT_REVIEW: YES`

`READY_TO_COMMIT: NO`

## Fourth independent-review verdict — accepted historical terminus

The third-review owner-transfer COMPLETE claim immediately above is superseded. The detailed fourth-review correction and evidence earlier in this report are authoritative; they count physical request-factory invocations rather than destination tickets.

`CODEX_FIX_01_PHYSICAL_SINGLE_FLIGHT_STATUS: COMPLETE`

`FULL_TO_LEGACY_SAME_KEY_PHYSICAL_REQUEST_COUNT: 1`

`LEGACY_TO_FULL_SAME_KEY_PHYSICAL_REQUEST_COUNT: 1`

`INITIAL_SEED_TRANSFER_PHYSICAL_REQUEST_COUNT: 1`

`DESTINATION_OWNER_ADOPTS_IN_FLIGHT_RESULT: YES`

`SUPERSEDED_OWNER_LOCAL_CALLBACKS_BLOCKED: YES`

`STALE_RESPONSE_PROTECTION_PRESERVED: YES`

`PHYSICAL_REQUEST_FACTORY_BEHAVIORALLY_TESTED: YES`

`ALL_PREVIOUS_848_CHECKS_PRESERVED: YES`

`READY_FOR_INDEPENDENT_REVIEW: YES`

`READY_TO_COMMIT: NO`

## Fifth independent-review verdict — final report terminus

The fourth-review physical single-flight correction immediately above is accepted. The detailed fifth-review correction and evidence earlier in this report are authoritative for mutation ordering and supersede the prior overall COMPLETE verdict.

`CODEX_FIX_01_AUTHORITATIVE_MUTATION_ORDERING_STATUS: COMPLETE`

`LEGACY_MUTATION_SUPERSEDES_OLDER_GET: YES`

`LATE_GET_CANNOT_ROLL_BACK_MUTATION: YES`

`UNMOUNTED_LEGACY_CONTROL_CANNOT_WRITE: YES`

`OBSOLETE_LEGACY_OWNER_CANNOT_WRITE: YES`

`MUTATION_GENERATION_BEHAVIORALLY_TESTED: YES`

`PHYSICAL_SINGLE_FLIGHT_PRESERVED: YES`

`ALL_PREVIOUS_888_CHECKS_PRESERVED: YES`

`READY_FOR_INDEPENDENT_REVIEW: YES`

`READY_TO_COMMIT: NO`
