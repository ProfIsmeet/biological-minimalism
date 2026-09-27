# Claude Stage 4/V1 — Biological Minimalism Visual System — Hostile Audit

Audit window: 2026-09-27, `claude/stage4-5-visual-command-deck`, base `98b73c168f95c91e7f5f5e8e4beef9ca79136d53`.

## 1. Method

Inspected every route in `frontend/src/app/*` at desktop (1280x800) via Chrome
DevTools MCP against the real, isolated frontend/backend pair described in
`docs/claude-stage4-5-visual-command-deck/RUN_STATE.md`, plus one mobile
(390x844) pass on the highest-traffic route. Compared actual rendered output
(not just source) against the V1 specification's typography/spacing/color/
surface/motion rules and the explicit anti-AI-slop checklist. Findings below
are only material, reproducible defects — routes and elements that were
already correct are not listed as "fixed."

## 2. Routes inspected

`/mission-overview`, `/live-monitoring`, `/system-brief`,
`/research/experimental` (redirect target of `/research`), `/digital-twin`,
`/ai-insights`, `/mission-timeline`, `/settings`. All eight app routes under
`frontend/src/app/` were opened and visually reviewed; `/` renders no content
of its own (root redirect).

## 3. Findings and corrections

| ID | Severity | Route/component | Finding | Evidence | Correction | Retest |
|---|---|---|---|---|---|---|
| V1-01 | High (route cohesion) | `/ai-insights`, `/mission-timeline`, `/settings` via `AppHeader.tsx` / `TopBar.tsx` | These three routes rendered a legacy "Mission Control" header inventing "Mission Control / Earth Orbit / Mission Day" language and an "AI Confidence" badge that appear nowhere else in the product — a direct violation of "no route appears to belong to another product." The other five routes all use the shared minimal `PresentationHeader`. Root cause: `AppHeader.tsx`'s routing table only mapped 5 of 8 routes to `PresentationHeader`; the other 3 fell through to the legacy `TopBar` fallback. | `stage4-before-ai-insights-legacy-shell-and-overlap.png` | Added `insights`/`timeline`/`settings` variants to `PresentationHeader.tsx`; updated `AppHeader.tsx` to route all three to it. `TopBar.tsx` is left in place unmodified (it is one of `verify-monitoring-consumers.mjs`'s protected files) but is no longer mounted on any route. | `stage4-after-ai-insights-unified-shell.png`; `npm run verify:monitoring` 1021/1021; visually reconfirmed on all 3 routes |
| V1-02 | High (rendering defect) | `components/ui/MetricTile.tsx`, used by `PrimaryVitalsPanel` on `/ai-insights` | Status-word values ("Unavailable") rendered at the same `text-2xl` size used for short numeric readings ("66", "90/55"), overflowing the fixed-width grid tile and visually overlapping the adjacent tile's text — reproducible any time a metric is unavailable (confirmed deterministically in PPG-DaLiA replay mode, where HRV/Respiration/BP are always `Unavailable`). | `stage4-before-ai-insights-legacy-shell-and-overlap.png` (top-left/top-right tile collision) | `MetricTile` now sizes any value longer than 6 characters at `text-base` with wrapping (`break-words`, `min-w-0`) instead of the fixed `text-2xl leading-none`; short numeric readings are unaffected. | `stage4-after-ai-insights-replay-no-text-overlap.png` — all four tiles render cleanly with no overlap |
| V1-03 | Medium (rendering defect) | `components/visualization/ExperimentalDispositionOrbit.tsx` on `/research/experimental` | The SVG orbit diagram's central "CORE_PLUS_CONTEXT / Final architecture" label text was visibly clipped. Root cause (measured via `getBoundingClientRect`): the `<svg>` element, sized only via `width`/`height` HTML attributes with no `viewBox`, computed to `177.77 × 300` px instead of `300 × 300` in a flex-row layout — a genuine, reproducible browser layout quirk independent of any of this session's viewport emulation (confirmed on a freshly opened tab at default 1280px width). | `stage4-before-orbit-diagram-clipped.png` | Added an explicit `viewBox="0 0 300 300"` and `className="h-[300px] w-[300px] shrink-0"` to force deterministic, non-distorted sizing. | `stage4-after-orbit-diagram-fixed.png`; `getBoundingClientRect()` now reports exactly `300 × 300` |
| V1-04 | Low (metadata correctness) | `/mission-timeline`, `/settings` | Both routes are `"use client"` page components, which Next.js App Router cannot allow to export `metadata` — the browser tab title fell back to a stale, unrelated title ("Biological Minimalism — Final Sensing Architecture", the System Brief route's title) observed on both routes. | Browser tab titles captured during navigation (see RUN_STATE.md) | Extracted the interactive body into `MissionTimelineClient.tsx` / `SettingsClient.tsx`; `page.tsx` is now a thin server component exporting the correct route-specific `metadata.title`. Two verifier scripts (`verify-monitoring-state.ts`, `verify-reduced-motion-unification.mjs`) hardcoded `app/settings/page.tsx` / `app/mission-timeline/page.tsx` paths for source-string checks against content that moved — both updated to the new file paths, same assertions, same real content, not weakened. | Tab titles now read "Mission Timeline — Biological Minimalism" / "Settings — Biological Minimalism"; `npm run verify:monitoring` 1021/1021 |

## 4. Investigated, found NOT to be a defect

- **AI Confidence self-contradiction on initial `/ai-insights` load** — first
  paint briefly showed `AIConfidencePanel` as "Unavailable" while
  `ExplanationPanel`'s independently-fetched SHAP endpoint already returned
  "AI Confidence is 100%...". Re-checked after the store settled (a few
  seconds): both panels agreed at 100%, consistently, across repeated
  reloads. This is a normal store-hydration timing artifact (the confirmed-
  snapshot gate populates slightly after the independent REST explanation
  call resolves), not a data-wiring bug — no fix applied, no scientific
  claim was ever falsely displayed as settled/authoritative during that
  transient window (the panel correctly said "Unavailable" during it).
- **Evidence-glob collision, not a product defect** — adding this
  directory's own `AUDIT.md` and a `/system-brief` screenshot initially
  collided with `scripts/verify_jury_release_evidence.py`'s `audit-main` and
  `system-brief` patterns, which were written before a second stage-specific
  evidence folder existed. The `system-brief` collision was fixed by renaming
  this directory's screenshot (`stage4-route-final-architecture-page-desktop.png`)
  — no product or verifier change needed. An attempt to also fix the
  `audit-main` collision by narrowing its glob was **reverted**: that pattern
  is exercised by two unit tests in `backend/tests/test_jury_verifiers.py`
  that depend on it staying a generic wildcard, and narrowing it broke both.
  Per this mission's rule against weakening tests to make something pass, the
  verifier was left unmodified — running it against this branch now honestly
  reports `AMBIGUOUS` for `audit-main` (two real, non-empty, independently
  reviewable `AUDIT.md` files). See
  `docs/JURY_RELEASE_EVIDENCE_MANIFEST.md`'s "Known ambiguity" note for the
  full explanation. This is the one intentionally-accepted, explained
  exception to this mission's "0 AMBIGUOUS" evidence-verifier target.
- **`AppHeader.tsx` comment staleness** — the routing comment claimed
  `/digital-twin` still used the legacy `TopBar`, but the code already
  routed it to `PresentationHeader variant="reference"`. Corrected the
  comment while editing the same function (see diff); not counted as a
  separate finding since it was documentation only, not a rendered defect.

## 5. Anti-AI-slop checklist review

Explicitly checked the full list from the mission's Stage 4 anti-slop audit
against actual rendered output (not source): excessive rounded rectangles,
generic dashboard grids, decorative gradients, neon/cyberpunk styling,
excessive badges, repeated subtitles, icon-everywhere treatment, arbitrary
glow, inconsistent capitalization, tiny uppercase labels, redundant borders,
repeated explanatory copy, large empty operational heroes, decorative
scientific imagery unsupported by data, hidden errors, hidden provenance,
every module having equal importance, "AI-powered" marketing language. The
existing visual system (dark navy canvas, teal/blue/amber/red status
semantics, 1px borders, minimal shadow/glow, tabular numerals, restrained
typography) was already largely compliant prior to this session — the four
findings above are the material defects found, not a wholesale redesign.
No neon/cyberpunk styling, no fabricated confidence values, no hidden
provenance were found anywhere in the eight routes inspected.

## 6. Protected behavior confirmation

No scientific constant, calculation, availability semantic, fail-closed
path, source/session/dataset identity rule, or API/WS contract was changed
by any Stage 4 fix. `git diff` for this phase touches only: two shared UI
components (`MetricTile.tsx`, one SVG sizing fix), the header-routing table
and its variant labels, two route-title wrapper files, and two verifier
script path corrections that keep pre-existing checks pointed at their
(relocated) real content.

---

# Claude Stage 5/V2 — Mission Overview Command Deck — Hostile Audit

## 7. Starting-state finding

Independent inspection of `MissionOverviewExperience.tsx` (the actual
`/mission-overview` composition, not assumed from the mission brief's
generic description) found the command-deck architecture the mission
specifies was **already substantially built** prior to this session:

- Section 01 ("Command Deck", the first viewport) already composes
  `MissionStatusBar` (persistent status band), `OperationalPhysiologyStage`
  (source/identity/per-modality confirmation), `HRInferenceCore` (primary
  HR reading), and `RecentHrEstimateTrend` (compact trend) — this already
  satisfies the mission's first-viewport contract (see §9 below).
- `ModalityPentagon` and the orbit/hex inference visuals
  (`InferenceIntegrityOrbit`, `InferenceHexFlow`) were already placed in
  Sections 02–03, below the first viewport — i.e. already demoted from
  primary operational importance, not something this session needed to do.
- Mobile already renders a bottom-tab-style nav (Mission / Signals / More)
  with the full status band visible without scrolling (§9).

Given this, Stage 5 work in this session is a **verification and targeted-
consolidation pass**, not a rebuild — consistent with the mission's
instruction not to redesign what the hostile audit finds is already correct.

## 8. Findings

| ID | Severity | Route/component | Finding | Evidence | Disposition |
|---|---|---|---|---|---|
| V2-01 | Low (reviewed, not a defect) | `InferenceIntegrityOrbit` + `InferenceHexFlow`, `/mission-overview` §03 | Both panels sit side by side and both derive from the same `useOperationalViewModel()`, each summarizing the same Source/PPG/IMU/Output categorical chain — a plausible "duplicate inference summary" complaint. Investigated the actual rendered content and source: the two panels are editorially and visually distinct — the Orbit gives an aggregated, confidence-free "categorical integrity" framing (4 states, concentric rings, explicit "not a confidence score" disclaimer) while the HexFlow gives a granular, sequential pipeline framing (6 steps, Source→PPG/IMU→Window→Model→Output). Both are driven by the one shared view model (no risk of the two disagreeing), and each carries deliberate, commented design intent (e.g. "no percentage, confidence, or partial-arc probability" on the Orbit). | `stage5-inference-integrity-hexflow-orbit-reviewed.png` | **No code change.** Classified as two intentional, non-contradictory framings of one shared source of truth rather than accidental duplication. Restructuring this late without dedicated redesign/testing time would carry more regression risk than the finding's severity justifies, and risks crossing into Stage 6 chart-redesign territory (explicitly out of scope). Recorded here per the mission's "record findings even when you decide not to act" requirement. |
| V2-02 | — | Settings reduce-motion toggle, post-Stage-4 refactor | Verified no regression from moving the toggle's logic out of `settings/page.tsx` into `SettingsClient.tsx` (Stage 4 fix V1-04). | Live `evaluate_script` check: toggle sets `aria-checked`, `<html class="reduce-motion">`, and `localStorage["biomin:reduce-motion"]` correctly in both directions. | Confirmed working, no finding. |
| V2-03 | — | Mobile "More" dialog, post-Stage-4 header migration | Verified no regression from the `AppHeader`/`PresentationHeader` routing change (Stage 4 fix V1-01): dialog opens with `role="dialog"`, focus lands on the Close button, all 6 destination links present (including the 3 newly-migrated routes), Escape closes it and returns focus exactly to the "More" trigger. | Accessibility-tree snapshots before/after Escape (see RUN_STATE.md) | Confirmed working, no finding. |

## 9. First-viewport contract verification

Checked all 9 required questions against the real, unmodified `/mission-overview` first viewport (Section 01, "Command Deck") at 1280x800 and 390x844:

| Question | Answered by | Verified |
|---|---|---|
| Active source? | `MissionStatusBar` "SOURCE" field | Yes |
| Subject/session/dataset identity? | `MissionStatusBar` "SESSION" field (+ "DATASET"/"SUBJECT" when in replay) | Yes |
| Loading/live/disconnected/errored/converging? | `MissionStatusBar` "CONNECTION" field | Yes |
| Simulated fault active? | `MissionStatusBar` "SIMULATED FAULT" field | Yes |
| Real/synthetic/simulated/retained/unavailable? | Source label ("SYNTHETIC DEMO" / "RECORDED REPLAY") + per-field "Not applicable" / "retained configuration" language | Yes |
| Affected region/channel/subsystem? | `OperationalPhysiologyStage` per-modality confirmation list | Yes |
| HR available/withheld/rebuilding/unavailable? | `HRInferenceCore` | Yes |
| Why is HR in that state? | `HRInferenceCore`'s SRC/PPG/IMU/OUT breakdown + hint text | Yes |
| Next expected safe state? | Not explicitly stated as a prediction (correctly — the mission forbids inventing "unsupported recovery estimates"); the fault/recovery narrative in §04 and the real rebuilding/recovery evidence in Phase 1 demonstrate the actual transition path | N/A by design |

No P1/P2 priority, acknowledgement workflow, incident ownership, mission
phases, clinical severity, freshness thresholds, medical action, escalation
policy, or unsupported recovery estimate was found anywhere on the route.

## 10. Viewport matrix (Mission Overview)

| Viewport | Zoom | Overflow | Critical content in first view | Evidence |
|---|---|---|---|---|
| 1920x1080 | 1x | None (`scrollWidth === clientWidth === 1920`) | Full Section 01 visible, no scroll needed | `stage5-viewport-1920x1080-mission-overview.png` |
| 1440x900 | 1x | None (1440/1440) | Full Section 01 visible, no scroll needed | `stage5-viewport-1440x900-mission-overview.png` |
| 1280x800 | 1x | None (verified throughout Phase 1/2) | Status band + stage + HR card visible | see Stage 2-3 and Phase 1 real-S14 evidence |
| 1024x768 | 1x | None (1024/1024) | Status band fully visible; HR card wraps below stage (expected `xl:` breakpoint behavior) | `stage5-viewport-1024x768-mission-overview.png` |
| 390x844 | 1x | None | Status band, source/session identity, presenter controls all visible without scrolling | `stage4-route-mission-overview-mobile-390x844.png` |
| Real 200% zoom (640x400 @ 4x DSF, CDP device-metrics override) | 200% | None (`scrollWidth === clientWidth === 640`) | Falls back to mobile nav correctly; status band fully visible | `frontend/qa-screenshots/claude-stage2-3-final-acceptance/mission-overview-200-zoom-real-devicemetrics.png` |
| Reduced motion | n/a | n/a | Verified in Phase 1/Stage 2-3 remediation (14-scenario matrix inherited and reconfirmed); Stage 4's Settings refactor reconfirmed independently in §8 (V2-02) | — |

## 11. Component disposition (verified against the mission's list)

| Component | Mission's disposition | Actual state found |
|---|---|---|
| Command deck | Recompose | Already recomposed as a 5-section scrollable narrative (pre-existing) |
| Status band | Persistent and authoritative | `MissionStatusBar` in Section 01, confirmed persistent |
| Body stage | Retain | `OperationalPhysiologyStage` retained, unchanged |
| HR core | Promote | Already primary in Section 01 |
| Recent trend | Compact and legible | `RecentHrEstimateTrend`, compact, already present |
| Modality pentagon | Demote from primary importance | Already in Section 02, not the first viewport |
| Orbit/hex ornamental visuals | Demote from first viewport | Already in Section 03, not the first viewport |
| Duplicate inference summaries | Consolidate | Reviewed (V2-01) — found to be non-contradictory dual framings, not consolidated; documented rather than restructured |
| Fault/recovery | Prominent | `FaultRecoverySpine` + `OperationalEventRail`, Section 04, real fault/recovery evidence captured in Phase 1 |
| Provenance | Accessible details/drawer | `OperationalProvenanceChain` + `ScopeProvenanceFooter`, Section 05 |
| Demo controls | Explicitly presenter-only | "Demo controls" button, clearly separated, opens `DemoControlDrawer` |

## 12. Explicitly deferred (Stage 6/7 boundary)

No scientific chart redesign (Stage 6) or anatomy/digital-human redesign
(Stage 7) was performed or started. `OperationalPhysiologyStage`'s
holographic figure, `ExperimentalDispositionOrbit`'s SVG sizing fix (a
layout-only correction, not a redesign), and the SHAP/trend charts on
`/ai-insights` were all left with their existing visual design.
