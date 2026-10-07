# Stage 2–3 Independent Browser Acceptance and Adversarial Review

Audit window: 2026-09-26 through 2026-09-27 (Europe/Istanbul)

## 1. Executive verdict

**Overall: PARTIAL.** The audited target was the required SHA. Baseline gates were reproduced independently. Real-browser DOM, accessibility-tree, keyboard, live-region, controlled WebGL-failure, and canonical-bootstrap failure/interception tests passed after two reduced-motion defects were corrected on the successor branch. Stage 2 remains PARTIAL because OS/browser reduced-motion emulation and an actual screen reader were unavailable. Stage 3A is COMPLETE_STATIC_ONLY because Docker was unavailable. Stage 3B is CONDITIONALLY_ACCEPTED because the local S14 dataset and checkpoint were unavailable, so a real canonical success run could not be performed. Release evidence remains incomplete.

Merge is not recommended and Stage 4 is not ready until the higher-level runtime and evidence gaps listed below are closed.

## 2. Repository and worktree identity

| Item | Verified value |
| --- | --- |
| Remote | `https://github.com/ProfIsmeet/biological-minimalism.git` |
| Isolated worktree | `<local-stage2-3-audit-worktree>` |
| Successor branch | `codex/stage2-3-independent-acceptance` |
| Audit target | `origin/ismet/frontend-stage2-3-hardening` at `50233e882cdead9643f53ca3b9ba93f785990951` |
| Stage 1 comparison base | `origin/codex/stage1-scientific-data-integrity` at `cfd4935ee264cdeb3953c8b437c3936cd9e2f0ae` |
| Deployment source | `origin/claude/deployment-hardening` at `ef747182353560d6355931310a08bcce5d3a949d` |
| Starting cleanliness | Clean isolated worktree |
| Primary checkout | Not switched or edited; its pre-existing untracked files were left untouched |
| Existing port 3000 runtime | Not reused or terminated |

The required target SHA matched exactly; no hard-stop condition was encountered.

## 3. Baseline reproduction

The unmodified audit target produced:

- `npm run verify:monitoring`: **1021/1021 passed, 0 failed**, followed by all five structural verifier scripts passing.
- `npm run lint`: pass.
- `npx tsc --noEmit`: pass when run independently.
- `npm run build`: pass; 14/14 static pages generated and one dynamic route reported.
- Full backend suite: **347 passed, 4 skipped**.
- Environment verifier: **19 PASS, 7 WARN, 0 FAIL**.
- Release-evidence verifier: exit 2; **0 PRESENT, 24 MISSING**, including 23 required artifacts; F-07 `INCOMPLETE`.
- `git diff --check`: pass.

The known supersession regression was reproduced in the executable monitoring suite: `load-subject` and `reset` ran, the sequence became superseded, `speed-1x` and `clear-fault` did not run, the outcome was `"superseded"`, `ok` was `false`, `lastStatus` was `null`, and no success announcement was produced.

## 4. Browser and runtime environment

| Component | Audit environment |
| --- | --- |
| Node | `v22.23.1` |
| npm | `10.9.8` |
| System Python | `3.14.5` |
| Browser backend runtime Python | Isolated Python 3.12 virtual environment |
| Final backend test Python | Python 3.14 integration virtual environment |
| Browser automation | Codex in-app Chromium browser with rendered DOM, keyboard, accessibility-tree, and JavaScript evaluation |
| Frontend | Audited checkout on `localhost:3001` |
| Real isolated backend | Repository backend on `localhost:8001`, synthetic state; no dataset/checkpoint |
| Controlled frontend/backend | `localhost:3002` / `localhost:8002` for explicitly intercepted scenarios |
| Mobile viewport | 390 × 844 CSS pixels |
| Docker | Not available on PATH |
| PPG-DaLiA / S14 | Not configured locally |
| HR checkpoint | Not present locally |

No service was exposed publicly. No dataset or checkpoint was downloaded.

## 5. Stage 2A — live-region results

**Verdict: YES for browser DOM/accessibility-tree acceptance; actual screen reader NOT RUN.**

- Mission status was sampled once per second for 15 seconds against the real isolated backend. The single live-region text remained stable while visible session time continued to advance.
- Controlled replay samples advanced visible position from 14.8 s to 17.3 s while the live region remained unchanged.
- Digital Twin angle advanced from 143° to 178° while its live region retained only the stable scientific-boundary announcement.
- Stopping the real backend changed the announcement once to disconnected/unavailable and made visual controls unavailable. Restarting it produced a connected/recovery announcement and matching event-log transition.
- A controlled replay-to-synthetic source transition produced one meaningful announcement.
- A controlled source error announced the unavailable fault and displayed `Source error`; recovery returned to connected synthetic state and removed source-error visuals.
- Repeated identical states did not produce an announcement storm.
- Canonical failure and controlled-success announcements were both visible in their intended live region.

The test inspected rendered DOM and browser accessibility information. It did not enable an operating-system screen reader and does not claim screen-reader equivalence.

## 6. Stage 2B — reduced-motion results

**Verdict: PARTIAL.** The persisted application preference and live cross-tab behavior passed after correction. OS/browser emulation was not available, so the OR contract could not be exercised from both inputs independently.

### Reproduced defects

Before product edits, enabling Reduce Motion in a second tab stopped WebGL rotation but did not add `reduce-motion` to the already-mounted first tab's document. Disabling it again left the Digital Twin permanently paused because the accessibility override overwrote the user's playback state.

### Post-correction browser results

- Cross-tab enable: the first tab's `<html>` became `dark reduce-motion`; the angle snapped to and remained at 24°; the control reported `Resume rotation`.
- Cross-tab disable under normal OS preference: `<html>` returned to `dark`; a previously playing model resumed (33° to 38° in the observation window).
- User-paused state was preserved across enable/disable: the angle stayed fixed and the control remained `Resume rotation`.
- Persisted-setting reload: `reduce-motion` was present on the first observation; the canvas subsequently rendered at a stable 24°. No full-motion flash was observed in DOM/canvas snapshots.
- Meaningful telemetry continued: controlled replay position advanced from 15.3 s to 16.3 s while the announcement remained stable.
- The production Digital Twin remained reduced after an induced context loss and retry.
- Repeated navigation did not reveal multiplying listeners or stale class state.

The browser reported normal OS motion preference. OS reduce, both-input enablement, live OS preference change, and the “turn app setting off while OS reduce remains active” case were NOT RUN because the available browser controller had no media-feature emulation. Animation-object enumeration was also unavailable in the restricted browser evaluator; hydration evidence is therefore limited to rendered document/canvas observation.

## 7. Stage 2C — mobile dialog keyboard results

**Verdict: YES.** Both dialogs were exercised at 390 × 844 with real keyboard events and live DOM inspection.

### Mobile More dialog

- `role="dialog"` was named by `mobile-more-heading`; initial focus landed on `Close menu`.
- Tab wrapped from the last Settings link to Close; Shift+Tab wrapped from Close to Settings.
- Body overflow became `hidden`; all 18 background direct children became inert and `aria-hidden="true"`; their exact prior states were restored on close.
- Escape restored focus to the More trigger. Backdrop activation closed the dialog.
- Three repeated cycles left no stale focus, overflow, inert, or listener state.
- Route navigation and browser back/forward cleaned up the modal state. Unmounting the trigger did not throw.

### Demo Control Drawer

- `role="dialog"` was named by `demo-control-drawer-heading`; initial focus landed on its close control.
- Tab wrapped Reset to Close and Shift+Tab wrapped Close to Reset.
- Scroll lock, inert/hidden background, Escape focus restoration, and backdrop close all passed.
- Repeated cycles, route cleanup, browser history navigation, and trigger unmount all passed without stale state or errors.

## 8. Stage 2D — WebGL fallback results

**Verdict: YES for exercised browser paths.** Normal production rendering was checked first. A temporary browser-local route used the production `WebglStage`, `ConceptualTwinFallback`, and `StaticAvatarFallback`; the route was removed afterward and is not tracked.

For both operational physiology and conceptual Digital Twin:

- Normal support rendered a canvas.
- Forced unsupported initialization rendered the fallback, no canvas, and no useless retry.
- Controlled render error rendered the fallback and retry; retry restored the canvas.
- Actual `WEBGL_lose_context` / `forceContextLoss` triggered the context-loss fallback; retry restored the canvas.
- The operational fallback control `PPG — Wrist — Confirmed` was keyboard focusable and activated with Enter.
- The conceptual fallback retained the architecture-only, untrained, unvalidated boundary and contained no confidence, adaptation percentage, measured telemetry, or invented values.
- With application reduced motion active, context loss followed by retry restored the canvas at a stable 24° with `Resume rotation` and the document reduction class intact.

These are genuine production-component fallback executions under controlled browser failure injection, not evidence of a real hardware/driver failure.

## 9. Stage 3A — deployment results

**Verdict: COMPLETE_STATIC_ONLY; Docker runtime NOT RUN.**

- Frontend Dockerfile copies both package manifest and lockfile and uses `npm ci`; no `npm install` directive is present.
- The target lockfile SHA-256 is `fe872a4c639b23df5911fb78f023b15b8246749cb6c3b601dc76e58e1b3cf3b5`, matching the deployment-source content; the audit did not alter it.
- Frontend configuration trims values, handles empty values, strips trailing slashes, and derives `ws:`/`wss:` consistently from the API URL.
- Backend CORS accepts exact configured origins and rejects wildcard, blank, and empty unsafe configuration.
- Frontend and backend example environment files agree with the implementation.
- Presenter Preflight remained read-only and the jury-facing UI did not expose private backend environment variable names.
- The jury runbook agreed with observed configuration and fail-closed behavior.
- Targeted deployment/configuration tests: **30 passed**.
- Environment verifier: **19 PASS, 7 WARN, 0 FAIL**.

Docker, Compose validation, image builds, container startup, and container REST/WebSocket smoke tests are `NOT_RUN_DOCKER_UNAVAILABLE`. Static acceptance is not presented as a container-runtime pass.

## 10. Stage 3B — canonical-bootstrap results

**Verdict: CONDITIONALLY_ACCEPTED.** The real missing-prerequisite path and controlled UI sequence passed; real S14 success was not runnable.

### Real backend

With no configured dataset/checkpoint, `Load Canonical Jury Demo` named the missing dataset, remained synthetic, emitted no false success, and stayed fail-closed on retry. The action remained separate from Reset.

### Controlled successful sequence

Starting from hostile replay state S7, non-zero position, 5× speed, and an active PPG fault, the UI finished at S14, paused, 0.0 s, 1×, fault none. The recorded request sequence was exactly:

`state → subjects → load-subject → reset → speed-1x → clear-fault`

A second invocation repeated the same bounded four mutation calls and ended in the same state. A separate S7 / 22 s / 10× / pass-fault start also converged to canonical state. Visible telemetry/history contained no prior S7 source identity, fabricated EEG/EOG, or astronaut/live-data claim; the only remaining S7 text was the subject dropdown option.

### Controlled fail-closed matrix

- Subject list loading: named that loading had not finished.
- Subject list error: named that the list could not be loaded.
- Empty list and S14 absent: named the precise prerequisite.
- Load, reset, speed, and clear-fault failures: each named the failed step, stopped at that step, and produced no false success.
- Explicit retry after clear-fault failure succeeded without a page reload.
- A delayed subject request superseded by a newer UI action announced that the load was superseded and no state was applied; reset/speed/clear did not run.
- Route change/unmount during a delayed load applied no stale canonical status and cleaned dialog/overflow/inert state.
- Pending controls disabled/deduplicated a second competing click; the exact concurrent supersession behavior was additionally covered by the 1021-check suite.
- Request logs were bounded; no request storm was observed.

All successful S14 behavior above was produced by an explicitly controlled backend/interception. It is not claimed as real dataset evidence.

## 11. Real backend versus controlled/intercepted tests

| Evidence | Backend classification | What it proves |
| --- | --- | --- |
| Synthetic connected, disconnect, restart/recovery | Real isolated repository backend | Runtime connection announcements and fail-safe UI |
| Dataset missing canonical action | Real isolated repository backend | Real local prerequisite failure is explicit and fail-closed |
| S14 success/idempotency/adversarial starting states | Controlled backend/intercepted | UI orchestration, ordering, final presentation, and bounded requests only |
| Loading/error/empty/S14-absent and step failures | Controlled backend/intercepted | UI failure semantics and retry behavior only |
| Supersession and unmount delay | Controlled backend/intercepted plus executable suite | Stale result suppression and bounded mutation sequence |
| WebGL unsupported/render/context loss | Controlled browser failure injection | Production fallback behavior, not real GPU failure |

No intercepted response is presented as a real backend or real S14 success.

## 12. Findings by severity

### M-01 — Cross-tab Reduce Motion did not update the CSS boundary (MEDIUM, corrected)

- **Reproduction:** Keep `/digital-twin` open in tab A; enable Reduce Motion from `/settings` in tab B.
- **Expected:** Tab A stops nonessential motion and gains the document `reduce-motion` class without reload.
- **Actual before fix:** WebGL stopped at 24°, but tab A remained `class="dark"`; CSS motion stayed enabled.
- **Affected code:** `frontend/src/lib/runtime/reduceMotion.ts`, `useReducedMotionPreference()` recomputation.
- **Impact:** The advertised app-preference accessibility boundary was inconsistent across already-open jury tabs.
- **Required before Stage 4:** Yes; corrected and browser-retested.

### M-02 — Leaving Reduce Motion could not resume a mounted Digital Twin (MEDIUM, corrected)

- **Reproduction:** With OS preference normal, enable then disable Reduce Motion from another tab while `/digital-twin` remains mounted.
- **Expected:** The accessibility override temporarily gates rotation; disabling it restores a previously playing state while preserving a user pause.
- **Actual before fix:** The reduction effect set `playing=false`, so disabling reduction left the figure paused indefinitely.
- **Affected code:** `frontend/src/components/visualization/human/ConceptualTwinStage.tsx`, reduced-motion effect.
- **Impact:** Live preference changes produced stale control and motion state in the jury view.
- **Required before Stage 4:** Yes; corrected and browser-retested.

### Evidence gaps

- Actual screen reader: not run.
- OS/browser reduced-motion emulation and live OS changes: not run.
- Docker/Compose/container runtime: unavailable.
- Real S14 dataset/checkpoint success: unavailable.
- Release manifest: 23 required artifacts absent.
- Real GPU/driver failure, physical mobile/touch device, projector, and assistive-technology hardware: not run.

No BLOCKER, HIGH, or LOW code finding remained after the corrections.

## 13. Corrections made

The correction commit is intentionally narrow:

1. The shared reduced-motion hook now synchronizes the document `reduce-motion` class whenever the effective persisted-or-OS value recomputes, including cross-tab storage changes.
2. Conceptual Twin reduction now gates playback through `playing && !reducedMotion` without overwriting the user's underlying play/pause choice.
3. Regression guards require document-class synchronization and reject a future `setPlaying(false)` override in the conceptual stage.
4. The existing 1021-check source assertion was updated to enforce preservation rather than the defective state overwrite.

No scientific metric, model, sensor set, telemetry calculation, art direction, navigation structure, or Stage 4 behavior changed.

## 14. Tests and exact counts

Final post-correction verification:

| Gate | Result |
| --- | --- |
| Monitoring state | **1021/1021 passed, 0 failed** |
| Monitoring structural verifiers | 5/5 scripts passed |
| ESLint | Pass, 0 errors |
| TypeScript | Pass, 0 errors |
| Next.js production build | Pass; 14/14 static generation steps completed |
| Backend full suite | **347 passed, 4 skipped** |
| Targeted deployment/config tests | **30 passed** |
| Environment verifier | **19 PASS, 7 WARN, 0 FAIL** |
| Release-evidence verifier | Exit 2; **0 present, 24 missing; 23 required missing** |
| `git diff --check` | Pass |

An initial parallel TypeScript invocation raced the production build over `.next/types` and reported transient missing generated files. The build itself passed, and a subsequent standalone `npx tsc --noEmit` passed with exit 0. This was tooling-directory concurrency, not a product failure.

## 15. Evidence captured

Selected textual browser evidence is stored in:

- `frontend/qa-screenshots/codex-stage2-3-independent-acceptance/browser-runtime-evidence.md`
- `frontend/qa-screenshots/codex-stage2-3-independent-acceptance/controlled-path-evidence.md`

Each artifact records route, viewport, browser, frontend port, backend mode, source state, real/intercepted classification, and purpose. No giant prior screenshot tree, browser cache, temporary route, or failed capture was copied. The available browser controller did not expose a filesystem screenshot export, so the selected durable artifacts are observation records rather than images.

The release-evidence verifier was run after evidence preparation and remained incomplete; these audit records do not masquerade as the manifest's missing jury screenshot bundle.

## 16. Explicit NOT RUN items

- Actual OS screen reader.
- OS/browser `prefers-reduced-motion: reduce` emulation, both preference sources enabled, and live OS preference change.
- Docker Compose configuration, container builds, startup, REST, and WebSocket smoke tests.
- Real S14 canonical success and idempotency with a local PPG-DaLiA dataset and checkpoint.
- Real GPU/driver WebGL failure.
- Physical mobile/touch hardware and projector presentation.

## 17. Remaining human and hardware actions

Before Stage 4, a qualified operator should:

1. Run the Stage 2A scenarios with VoiceOver, NVDA, or an equivalent screen reader and confirm announcement wording and cadence.
2. Repeat the complete reduced-motion matrix with actual media-feature emulation or OS preference changes, including app-off/OS-on and initial hydration.
3. Build and smoke-test both containers on a Docker-capable host, including REST and WebSocket connectivity through the documented topology.
4. Configure the approved PPG-DaLiA dataset and checkpoint, then run the canonical S14 action twice from hostile starting states against the real backend.
5. Capture and approve the required F-07 release-evidence bundle on the intended mobile, desktop, projector, and assistive-technology setup.

## 18. Commit list and final SHA

- `eb292c121158cd1697f6d878054ea355b5c45c94` — `fix(frontend): synchronize reduced-motion state`
- A second scoped report/evidence commit records this review; its final SHA is the branch tip reported by Git delivery and the final response.

The branch is pushed without force, and local/remote tip equality is verified after the report commit.

## 19. Stage 4, main, source branches, and temporary artifacts

Stage 4 was not started. `main`, both source branches, the Stage 1 comparison branch, the existing primary checkout, and its port-3000 server were not modified. The temporary WebGL harness existed only for browser testing and was removed. No local environment file, dataset, checkpoint, browser cache, or temporary runtime artifact is tracked.

## 20. Merge recommendation

**NO.** The corrected product behavior is materially stronger and all executable gates pass, but the acceptance rules prohibit lower-level passes from overriding missing OS reduced-motion, actual screen-reader, Docker-runtime, real-S14, and release-evidence verification. The successor branch should remain an audit/correction candidate until those higher-level gaps are closed.

`CODEX_STAGE2_3_INDEPENDENT_REVIEW: PARTIAL`
`AUDIT_TARGET_SHA_VERIFIED: YES`
`MONITORING_1021_PRESERVED: YES`
`LIVE_REGION_BROWSER_ACCEPTANCE: YES`
`REDUCED_MOTION_BROWSER_ACCEPTANCE: PARTIAL`
`MOBILE_DIALOG_KEYBOARD_ACCEPTANCE: YES`
`WEBGL_FAILURE_BROWSER_ACCEPTANCE: YES`
`ACTUAL_SCREEN_READER_VERIFIED: NO`
`DEPLOYMENT_STATIC_ACCEPTANCE: YES`
`DOCKER_RUNTIME_VERIFIED: NO`
`CANONICAL_BOOTSTRAP_UI_ACCEPTANCE: YES`
`REAL_S14_SUCCESS_PATH_VERIFIED: NO`
`SUPERSESSION_CORRECTION_PRESERVED: YES`
`RELEASE_EVIDENCE_COMPLETE: PARTIAL`
`SCIENTIFIC_BEHAVIOR_CHANGED: NO`
`STAGE4_STARTED: NO`
`MAIN_MODIFIED: NO`
`MERGE_RECOMMENDED: NO`
`READY_FOR_STAGE4: NO`
