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
