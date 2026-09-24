# STATUS

**Active milestone**: Milestone A (Stage 2 accessibility) — A1, A2, A3, A4 complete. A5 (Stage 2 verification checkpoint) passed on the same gate below. Next up: Milestone B (Stage 3A deployment hardening).

**Completed work**:
- Hard-stop gate verified: both required remotes present, deployment branch SHA matches exactly.
- Branch `ismet/frontend-stage2-3-hardening` created from `origin/codex/stage1-scientific-data-integrity @ cfd4935ee264cdeb3953c8b437c3936cd9e2f0ae`.
- Baseline gate passed: verify:monitoring 932/932, lint clean, tsc clean, build 14/14 pages, git diff --check clean.
- Durable work-record docs created (this directory).
- **A1 (continuous live-region announcements) complete.** Audited all 16 files in `src/` referencing `aria-live`/`role="status"`/`role="alert"`. Found and fixed 3 real violations (a continuously-changing value living inside an announced live region, structurally — not throttled):
  - `components/operations/MissionStatusBar.tsx` — "Session time" (1s clock tick) and "Last confirmed frame" age were inside the whole-strip `role="status"`. Split into a dedicated `sr-only` live-summary `<span>` built only from the 5 meaningful fields (session, source, connection, replay state, fault); the visible field grid carries no live role.
  - `components/monitoring/MonitoringSourceStrip.tsx` — "Replay position" (updates every telemetry tick during playback) was inside the whole-grid `role="status"`. Same fix: sr-only live summary excludes it; visible grid carries no live role.
  - `components/visualization/human/ConceptualTwinStage.tsx` — the `useFrame`-driven rotation angle (up to 60/s) shared a `role="status"` paragraph with the static architecture-boundary disclaimer. Split into two paragraphs: the disclaimer keeps `role="status"` (static, never changes), the angle text is a plain non-live `sr-only` paragraph.
  - The other 13 files with live-region usage (`AIConfidencePanel.tsx`, `DataStateError.tsx`, `DemoControlDrawer.tsx`, `SimulatedFaultControl.tsx`, `ReplaySessionControl.tsx`, `HrInferencePanel.tsx`, `FinalSignalStack.tsx`, `SourceStatusStrip.tsx`, `mission-timeline/page.tsx`, `ResearchMode.tsx`, `Stage4ArchitectureDecisionPanel.tsx`, `Stage4FinalArchitecturePanel.tsx`, `FutureScienceHandoffCard.tsx`) were individually inspected — every one wraps only a discrete/static message (error, "unavailable", "waiting for confirmation", a fixed statement) that changes on a real state transition, not a per-second/per-frame tick. No changes needed there.
  - Added `frontend/scripts/verify-live-region-boundaries.mjs` — a deterministic structural check (same zero-dependency Node convention as `verify-monitoring-consumers.mjs`) proving the 3 fixed files' live-region elements never re-embed the ticking identifier/label, and that the ticking value still exists elsewhere in the file (proving it was moved, not deleted). Wired into `npm run verify:monitoring` as a third stage.
  - Re-ran full baseline gate after all A1 edits: `verify:monitoring` 932/932 + new check PASSED, lint clean, `tsc --noEmit` clean, `next build` 14/14 pages, `git diff --check` clean. No regressions.

**Tests already passed**: full baseline gate (932/932 monitoring + verify-live-region-boundaries + verify-reduced-motion-unification + lint + tsc + build 14/14 + git diff --check) after both A1 and A2 edits.

**Current blockers**: none.

**Exact next action**: commit the A4 changes (files listed below, staged explicitly) as the Stage 2 checkpoint commit, then move to Milestone B (Stage 3A) — inspect the complete diff of `origin/claude/deployment-hardening` and port only valid changes (Docker/npm ci install, `NEXT_PUBLIC_WS_URL` config, exact-origin CORS, env examples, jury runbook, read-only env verifier, release-evidence manifest/verifier, Presenter Preflight wording correction).

**A4 summary (WebGL/Digital Twin failure fallback)**:
- Audit found `ConceptualTwinStage.tsx` (the `/digital-twin` reference figure) had **no WebGL detection or error handling at all** — an unsupported device, a renderer init failure, a lost context, or any render-time error would leave a blank/broken panel. `PhysiologyAvatar3D.tsx` (the operational avatar) only handled the up-front "unsupported" case via a private `detectWebgl()`; it had no handling for a runtime render error or a lost context either.
- Added `components/visualization/human/detectWebgl.ts` — the one shared WebGL-support check (previously duplicated only in `PhysiologyAvatar3D.tsx`).
- Added `components/visualization/human/WebglErrorBoundary.tsx` — a real React class-component error boundary (`getDerivedStateFromError`/`componentDidCatch`), since render-time throws inside a `react-three-fiber` scene tree have no hook-based equivalent.
- Added `components/visualization/human/WebglStage.tsx` — the shared wrapper combining all three failure paths (unsupported, render-time error via the boundary, lost context via a `webglcontextlost` listener registered in `onCreated`) behind one `renderFallback(retry | null)` API. `retry` is `null` (no recovery control offered) only for the hard-unsupported case, per A4's "recovery action only when technically possible" rule; for a render error or lost context, `retry` remounts the Canvas with a fresh WebGL context via a `key` bump.
- `PhysiologyAvatar3D.tsx` now renders `<WebglStage>` instead of a raw `<Canvas>`; its fallback is the existing `StaticAvatarFallback` (now accepting an optional `onRetry`), and the interactive `OperationalAvatarOverlay` column stays mounted regardless — only the volumetric rendering itself is ever replaced, so the operator never loses the sensor panel.
- Added `components/visualization/human/ConceptualTwinFallback.tsx` for `ConceptualTwinStage.tsx` (no sensor anchors, so a static text panel rather than an anchor map) — preserves the exact same architecture-only/untrained/unvalidated scientific-boundary language the live disclaimer carries, reports no rotation angle or any other invented quantity, and includes the same conditional retry button.
- Added `frontend/scripts/verify-webgl-fallback.mjs`, wired into `verify:monitoring`, asserting: `WebglStage` covers all three failure paths and the null-vs-retry rule; `WebglErrorBoundary` is a genuine React error boundary; both `PhysiologyAvatar3D.tsx` and `ConceptualTwinStage.tsx` render `<WebglStage>` and never a raw `<Canvas>`; both fallback components declare an optional `onRetry` and render it conditionally.
- No pre-existing Stage 1 check referenced the old WebGL/Canvas structure, so no existing check needed updating this time.
- Full gate re-verified: `verify:monitoring` 933/933 (unchanged — A4 added no new monitoring-state checks) + all five structural checks PASSED, lint clean, `tsc --noEmit` clean, `next build` 14/14 pages, `git diff --check` clean. This also serves as the A5 Stage 2 verification checkpoint — no regressions found across the full A1–A4 change set; keyboard-only and adversarial screen-reader review were not performed live (no browser automation available in this environment) and are reported as `NOT_RUN_DOCKER_UNAVAILABLE`-style gaps in the final report, not claimed as passed.

**A3 summary (mobile "More" dialog focus containment)**:
- Audit of the pre-existing `MobileNav.tsx` sheet found it had only Escape-to-close and a first-focusable-child focus-on-open — no Tab/Shift+Tab containment (focus could escape to the page behind the sheet), no scroll lock, and no background inert/aria-hidden (a screen reader's virtual cursor and Tab could still reach content behind the open sheet).
- `DemoControlDrawer.tsx` already had a fully correct, previously-shipped implementation of exactly this (Prompt-4 §10 / Prompt-4A MEDIUM-1): portal to `document.body`, full Tab/Shift+Tab trap, Escape, scroll lock with restoration, background `inert`+`aria-hidden` with exact restoration, and focus restoration to the trigger. Per the master prompt's instruction to prefer an existing tested primitive over a new dependency, this was extracted verbatim (no behavior change) into a shared hook, `frontend/src/lib/runtime/useModalDialog.ts`.
- Added one new capability to the shared hook beyond what either dialog had before: route-change-safe close (a `usePathname()` watcher that calls `onClose` if the route changes while still marked open — covers browser back/forward, which never goes through an in-dialog `Link`'s `onClick`).
- `DemoControlDrawer.tsx` now calls `useModalDialog(...)` instead of carrying its own effects — verified behaviorally identical (same portal target, same panel/trigger/overlay refs).
- `MobileNav.tsx`'s sheet is now portaled to `document.body` (required by the hook's background-inert step, which walks `document.body.children`) and calls the same shared hook — it now gets the Tab trap, scroll lock, and background inert it was missing, for free.
- Updated the pre-existing Stage 1 "modal: ..." block of checks in `scripts/verify-monitoring-state.ts` (6 checks) to assert against the shared hook file instead of the now-refactored `DemoControlDrawer.tsx` inline code, and added one new check ("modal: drawer uses the shared useModalDialog() hook") — guarantees preserved and strengthened, not weakened; documented inline at the check site. Total check count increased from 932 to 933.
- Added `frontend/scripts/verify-modal-dialog-primitives.mjs`, wired into `verify:monitoring`, asserting: the shared hook implements the Tab trap (both directions), Escape, scroll lock+restore, inert+aria-hidden+restore, trigger-focus-restore, and route-change-close; both `DemoControlDrawer.tsx` and `MobileNav.tsx` call the shared hook and portal to `document.body` with correct `role="dialog"`/`aria-modal="true"`; neither consumer reimplements its own inert/keydown logic.
- Full gate re-verified: `verify:monitoring` 933/933 + all four structural checks PASSED, lint clean, `tsc --noEmit` clean, `next build` 14/14 pages, `git diff --check` clean.

**A2 summary (reduced-motion unification)**:
- Added `useReducedMotionPreference()` to `frontend/src/lib/runtime/reduceMotion.ts` — the single shared source of truth, OR-combining the persisted `/settings` localStorage toggle with the OS `prefers-reduced-motion` media query (see DECISIONS.md D3 for the precedence rule). SSR-safe (starts `false`, resolves post-mount); listens for OS change, cross-tab `storage`, and a new same-tab `REDUCE_MOTION_CHANGE_EVENT` so it propagates live without a reload.
- `/settings` toggle now dispatches `REDUCE_MOTION_CHANGE_EVENT` after writing localStorage.
- New `components/layout/MotionConfigProvider.tsx`, mounted once in `app/layout.tsx`, wraps the whole app in Framer Motion's `<MotionConfig reducedMotion="always"|"never">` driven by the shared hook — fixes a real bug where `DigitalTwinPanel.tsx`'s infinitely-repeating orbit/glow animations (Framer Motion's own JS animation engine, not CSS) never respected either reduced-motion source before this change.
- `OperationalPhysiologyStage.tsx` and `ConceptualTwinStage.tsx` each previously ran their own private OS-only `matchMedia` check (ignoring the persisted setting) — both now read the shared hook. `ConceptualTwinStage.tsx`'s existing effect (freeze angle + pause playback under reduced motion) now re-runs on every hook change, not just at mount.
- `HumanScanRings.tsx` and `RegionOrbit.tsx` already correctly received `reducedMotion` as a prop and needed no change.
- Updated one pre-existing Stage 1 check in `scripts/verify-monitoring-state.ts` ("conceptual twin stage: checks prefers-reduced-motion") to assert the component uses the shared hook instead of the now-removed literal OS-query string — the guarantee is preserved (and strengthened, since the persisted setting is now also honored), not weakened; documented inline at the check site.
- Added `frontend/scripts/verify-reduced-motion-unification.mjs`, wired into `verify:monitoring`, asserting: the shared hook combines both sources and all three live-update listeners exist; Settings dispatches the same-tab event; `MotionConfigProvider` wraps `layout.tsx` and is driven by the hook; the two former OS-only offenders now use the hook and contain no local `matchMedia` call; all three `useFrame` loops still gate on `reducedMotion`.
- Full gate re-verified after the change: `verify:monitoring` 932/932 + both new checks PASSED, lint clean, `tsc --noEmit` clean, `next build` 14/14 pages, `git diff --check` clean.

**Files intentionally changed so far (cumulative, A1+A2+A3+A4)**:
- `frontend/src/lib/runtime/useModalDialog.ts` (new — A3 shared focus/scroll/inert primitive)
- `frontend/src/components/operations/DemoControlDrawer.tsx` (A3 — refactored to use shared hook, no behavior change)
- `frontend/src/components/layout/MobileNav.tsx` (A3 — portaled + uses shared hook, gains Tab trap/scroll lock/inert it lacked)
- `frontend/scripts/verify-modal-dialog-primitives.mjs` (new — A3 structural test)
- `frontend/scripts/verify-monitoring-state.ts` (A3 — updated "modal: ..." checks to match new architecture, +1 new check, guarantees preserved)
- `frontend/src/components/visualization/human/detectWebgl.ts` (new — A4 shared WebGL support check)
- `frontend/src/components/visualization/human/WebglErrorBoundary.tsx` (new — A4 real React error boundary)
- `frontend/src/components/visualization/human/WebglStage.tsx` (new — A4 shared unsupported/error/context-loss wrapper)
- `frontend/src/components/visualization/human/ConceptualTwinFallback.tsx` (new — A4 fallback for the Digital Twin reference figure)
- `frontend/src/components/visualization/human/StaticAvatarFallback.tsx` (A4 — added optional conditional `onRetry`)
- `frontend/src/components/visualization/human/PhysiologyAvatar3D.tsx` (A4 — uses WebglStage instead of raw Canvas)
- `frontend/src/components/visualization/human/ConceptualTwinStage.tsx` (A4 — uses WebglStage instead of raw Canvas, previously had zero WebGL handling)
- `frontend/scripts/verify-webgl-fallback.mjs` (new — A4 structural test)
- `frontend/package.json` (wired all Stage 2 verification scripts into `verify:monitoring`)
- `frontend/src/components/operations/MissionStatusBar.tsx` (A1 fix)
- `frontend/src/components/monitoring/MonitoringSourceStrip.tsx` (A1 fix)
- `frontend/src/components/visualization/human/ConceptualTwinStage.tsx` (A1 fix, A2 fix)
- `frontend/scripts/verify-live-region-boundaries.mjs` (new — A1 structural test)
- `frontend/src/lib/runtime/reduceMotion.ts` (A2 — added shared hook + change event)
- `frontend/src/app/settings/page.tsx` (A2 — dispatch same-tab change event)
- `frontend/src/components/layout/MotionConfigProvider.tsx` (new — A2)
- `frontend/src/app/layout.tsx` (A2 — mount MotionConfigProvider)
- `frontend/src/components/operations/OperationalPhysiologyStage.tsx` (A2 — use shared hook)
- `frontend/scripts/verify-monitoring-state.ts` (A2 — updated one check to match new architecture, guarantee preserved)
- `frontend/scripts/verify-reduced-motion-unification.mjs` (new — A2 structural test)
- `frontend/package.json` (wired both new scripts into `verify:monitoring`)
- `docs/ismet-stage2-3/STATUS.md`, `docs/ismet-stage2-3/DECISIONS.md` (this update)

**Note on prior session work**: a separate, unrelated small hardening pass (`PrimaryVitalsPanel.tsx`, `researchStore.ts`) from a *different* task on branch `stage5-runtime-honesty-hardening` was stashed (`git stash list` on that branch) before switching to this Stage-1 base — it is out of scope for this assignment and was not brought over.
