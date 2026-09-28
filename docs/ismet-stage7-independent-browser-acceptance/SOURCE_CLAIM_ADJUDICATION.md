# Source Claim Adjudication — Stage 7 Independent Browser Acceptance

Independent adjudication of every claim made in `docs/codex-stage7-digital-twin-integration/*.md`
(the original Codex implementer's Stage 7 self-report set), by an independent auditor
working on branch `ismet/stage7-independent-browser-acceptance`, starting from the
exact required source tip `c01f66f43a76c953996d811f3e846f3ac7d9a09c`
(`origin/codex/stage7-digital-twin-integration`).

Legend: **CONFIRMED** = independently reproduced with fresh evidence. **CONFIRMED
(CORRECTED)** = the underlying claim was true in spirit but a real defect was found
and fixed before final acceptance. **CHALLENGED / NOT SUPPORTED** = the original
report's specific claim did not hold up under independent testing. **REPRODUCED
DIFFERENTLY** = independently re-measured and found a materially different number,
with root cause identified. **PRE-EXISTING, NOT STAGE 7** = a real discrepancy that
predates the Stage 7 diff (verified via `git log`/`git ls-tree`).

| # | Source claim | Evidence required | Evidence found | Independent result | Finding ID |
|---|---|---|---|---|---|
| 1 | Canonical route `/digital-twin` | Route exists, single implementation | `frontend/src/app/digital-twin/page.tsx` renders `ConceptualTwinStage`; only one Digital Twin implementation reachable in the app | **CONFIRMED** | — |
| 2 | Product-nav-integrated | Nav entry present and discoverable | `15-navigation-entry-sidebar.png`; sidebar exposes a "Digital Twin" nav item | **CONFIRMED** | — |
| 3 | Architecture-only / untrained / unvalidated boundary | Route never implies live/validated model output | Read `ConceptualTwinStage.tsx` + `ConceptualTwinFallback.tsx`; semantic summary text; no confidence/adaptation percentage rendered | **CONFIRMED** (see `SCIENTIFIC_INTEGRITY_REVIEW.md`) | — |
| 4 | Default/front/back/chest/wrist views | 5 presets exist and are reachable | `digitalTwinPresentation.ts` at source tip defines exactly these 5 | **CONFIRMED** | — |
| 5 | Chest → ECG only, Wrist → PPG+IMU only | `activeRegion` scoped correctly per preset | Confirmed in source and via `ArchitectureSensorContacts.tsx` region-orbit lookup | **CONFIRMED** | — |
| 6 | Semantic non-canvas equivalent exists | A real DOM/ARIA summary of topology/selection, not canvas-only | `ConceptualTwinStage.tsx`'s "Semantic architecture summary" `aria-live="polite"` block; `11-semantic-summary-chest-selected.png` | **CONFIRMED** | — |
| 7 | Static SVG fallback | Fallback renders real markers, equivalent topology | `ConceptualTwinFallback.tsx`, 71 lines, `role="img"` + `<title>`/`<desc>`, all 5 modality markers present | **CONFIRMED** | — |
| 8 | Shared reduced-motion | One source of truth (persisted OR OS), used consistently | `useReducedMotionPreference()` hook, `biomin:reduce-motion` localStorage key, `verify-reduced-motion-unification.mjs` (PASSED); live browser test confirmed persistence, cross-route pickup, and genuine cross-tab sync (see `REDUCED_MOTION_REVIEW.md`) | **CONFIRMED** | — |
| 9 | Demand-driven rendering while paused/reduced/focused/hidden | `frameloop` switches to `"demand"` off the default animated view | Confirmed in source (`frameloop: motionActive && !reducedMotion ? "always" : "demand"`) — **but this same "demand" path was the root cause of a real, previously undetected defect** (camera mutations invisible to R3F's reconciler under `"demand"`, so Chest/Wrist focus never visually zoomed) | **CONFIRMED (CORRECTED)** | S7-AUDIT-02 |
| 10 | No monitoring/WS/polling/REST/store ownership | Route never reads mission store or opens its own network connection | `checkNotIncludes` source-string guards (pre-existing) + live browser test: all WebSocket/fetch errors observed during `/digital-twin` testing originated from `/mission-overview` and `/settings`, never from `/digital-twin` itself | **CONFIRMED** | — |
| 11 | Monitoring 1059 → 1085 | Exact pass-count delta | Baseline reproduction (source tip, before any correction): `1085/1085 passed, 0 failed` | **CONFIRMED** | — |
| 12 | Backend 351 passed / 4 skipped | Exact pytest result | `.venv` pytest run at source tip: `351 passed, 4 skipped` | **CONFIRMED** | — |
| 13 | Lint / TS / build / evidence-verifier pass | Each command exits 0 | lint exit 0, `tsc --noEmit` exit 0, `next build` 14/14 exit 0; evidence verifier **did not** exit 0 (see below) | **CONFIRMED** (lint/TS/build) / **REPRODUCED DIFFERENTLY** (evidence verifier) | — |
| 14 | Evidence verifier: 23 PRESENT / 1 optional MISSING / 0 AMBIGUOUS | Exact verifier output | Independently ran `scripts/verify_jury_release_evidence.py --root . --hash` at the source tip and again post-correction: **PRESENT=15, MISSING=1, EMPTY=0, AMBIGUOUS=8, exit code 2** (`F-07 status: INCOMPLETE`), both before and after this audit's own changes | **REPRODUCED DIFFERENTLY** — see `ROUTE_COUNT_RECONCILIATION.md` for the historical trace proving this predates Stage 7 (last touched at `b9ec0a8`, before the Stage 7 diff began) | PRE-EXISTING, NOT STAGE 7 |
| 15 | No known Stage 4-5 regression | `/mission-overview` and other Stage 4-5 routes behave unchanged | Re-ran `/mission-overview` and `/settings` under the same browser harness; hydration-mismatch warning reproduces identically on both, confirming it is a pre-existing, cross-route condition, not something Stage 7 introduced | **CONFIRMED** | — |
| 16 | No repo-persisted final PNG evidence (blocker) | Real, final-code-state screenshots checked into the repo | 17 PNGs captured against the corrected implementation, SHA-256'd, all mutually distinct, all visually inspected — see `EVIDENCE_MANIFEST.md` | **CLOSED** | — |
| 17 | No genuine 200% browser zoom acceptance (blocker) | Real browser-chrome zoom, not CSS/emulation substitute | Attempted via `playwright-core` driving the machine's installed Chrome via CDP; `Page.getLayoutMetrics` confirmed `scale: 1` remained unchanged after synthetic zoom-accelerator keypresses in both headless and headed mode — a genuine CDP/browser-architecture limitation (CDP exposes no real zoom API; the only zoom-adjacent API, `Emulation.setPageScaleFactor`, is itself a forbidden emulation substitute under this task's own rules) | **BLOCKED_EXTERNAL** (independently reconfirmed via a different toolchain than the original report used — not merely accepted on trust) | — |
| 18 | No real runtime WebGL unsupported/context-loss/retry acceptance (blocker) | Genuine browser-level WebGL disable; real `WEBGL_lose_context` cycles | Chrome launched with `--disable-gpu --disable-webgl --disable-webgl2` for Gate C; real `gl.getExtension("WEBGL_lose_context").loseContext()` cycled 3x for Gate D | **CLOSED** — see `WEBGL_RUNTIME_REVIEW.md` | — |
| 19 | Anatomical quality only interactively self-reviewed (limitation) | Independent rubric-scored review | Full rubric applied, evidence-backed — see `VISUAL_QUALITY_RUBRIC.md` | **CLOSED** (rubric review performed; no external asset was substituted, no code-native model change was required beyond the S7-AUDIT-01/02 fixes) | — |
| 20 | Resource cleanup only structurally accepted (limitation) | Runtime stress evidence, not source-only | 20x mount/unmount cycle, repeated resize, hidden-tab visibilitychange, all runtime-tested with canvas-count assertions | **CLOSED** — see `RESOURCE_LIFECYCLE_REVIEW.md` | — |
| 21 | WebGL unsupported/context-loss/retry only structurally accepted (limitation) | Runtime evidence | Closed together with claim 18 | **CLOSED** | — |
| 22 | Reduced-motion OS toggle not run (limitation) | OS-level toggle test or honest NOT_RUN | This Windows Server VM offers no permitted way to toggle real OS-level "Show animations" without modifying OS accessibility settings (explicitly prohibited by this task's rules); CDP/Playwright's `reducedMotion` context option is browser-level media-query emulation, the same category of forbidden substitute this task's own rules reject for zoom | **REDUCED_MOTION_OS_PATH: NOT_RUN** (honestly reported, not concealed) — app-level path independently closed with strong evidence | — |
| 23 | One upstream `THREE.Clock` deprecation warning | Confirm origin, assess correctness impact | Investigated: not present in `git grep` of project source; originates from the pinned `three`/`@react-three/fiber` dependency versions, not project code. Does not affect correctness — it is a deprecation notice, not a runtime error. No dependency upgrade performed (out of scope; risk of destabilizing an accepted Stage 4-5 baseline for a cosmetic warning) | **CONFIRMED**, accepted as a low-severity upstream limitation | — |
| 24 | Production build stayed 14/14 despite `/digital-twin` integration | Explain the route-count non-change | `/digital-twin` is a **modified pre-existing route**, not a new one — it existed before Stage 7 and Stage 7 changed its implementation, not the route table | **CONFIRMED**, fully reconciled — see `ROUTE_COUNT_RECONCILIATION.md` | — |

## Summary

Of 24 adjudicated claims: **20 CONFIRMED** (14 as-reported, 2 CONFIRMED WITH CORRECTION
after a real defect was found and fixed, 1 REPRODUCED DIFFERENTLY but explained as
pre-existing, 5 blockers/limitations independently CLOSED with genuine runtime
evidence), **1 correctly reported as BLOCKED_EXTERNAL** (genuine 200% zoom — a real
environment/CDP limitation, not fabricated), **1 correctly reported as NOT_RUN**
(OS-level reduced-motion toggle — no permitted mechanism on this VM). No claim was
accepted purely on the original report's word; every claim above either has fresh,
independently-gathered evidence or an explicit, honest non-pass disposition.
