# Accessibility & Responsive Review — Stage 6 Scientific Visualization Redesign

`ACTUAL_SCREEN_READER_STATUS: DEFERRED_BY_OWNER_UNTIL_STAGE9`. VoiceOver
was not run; no OS accessibility settings were altered.

## Accessibility

- **Semantic tables/summaries:** every new chart (`FaultRecoveryTimeline`,
  `SensitivitySmallMultiples`, `ArchitectureDeltaMatrix`,
  `CoverageFreshnessMatrix`'s non-compact form) has a real `<table>`/`<ul>`
  with exact values, via the shared `SemanticTable`/`ChartFrame` primitives
  (`aria-describedby` linking each chart's heading to a plain-language
  summary sentence, read before the plot by assistive tech).
- **No hover-only information:** verified per-component in
  `FINDING_LEDGER.md` and `OPERATIONAL_VISUALIZATION_REPORT.md`. Confirmed
  the one suspected case (`SignalLaneChart`'s tooltip) is not a violation
  — critical facts are already visible without hovering.
- **Keyboard access:** `PipelineStateStrip`'s stage blocks are real
  `<button aria-expanded>` elements; `CoverageFreshnessMatrix`'s rows are
  real `<button aria-pressed>` when `onSelect` is provided (Mission
  Overview usage) or plain `<div>` rows otherwise (System Brief/Live
  Monitoring full form, where selection is not applicable). Browser
  evidence `22-keyboard-focus-visible.png` confirms a visible focus ring
  after 2 Tab presses from page load.
- **No excessive tab stops:** `SensitivitySmallMultiples`' scatter-plot
  dots are deliberately NOT individually focusable — the exact-value
  semantic table beneath each panel is the keyboard/screen-reader path,
  avoiding dozens of per-dot tab stops for a 5-seed/4-subject dataset. This
  is the "sensible grouped/roving interaction... not hundreds of individual
  tab stops" pattern the master task itself requires.
- **No announcement storm:** no new `aria-live` region was added by Stage
  6; the pre-existing `verify-live-region-boundaries.mjs` structural guard
  continues to pass unchanged.
- **Color-independent status:** every `StatusPill` carries a text label,
  never color alone; modality color (`MODALITY_COLOR`) identifies modality
  only, never severity — unchanged, reused convention.
- **Accessible names:** `PipelineStateStrip` chips expose their label text
  directly inside the button; `CoverageFreshnessMatrix` rows include
  modality + region + state in visible text (no `aria-label` needed beyond
  what's already visible, consistent with the project's existing pattern
  on `ModalityPentagon`, which did need `aria-label` because its buttons
  were icon-only — Stage 6's rows are not).

## Responsive

Verified via real browser capture at 1920×1080, 1024×768 (tablet), and
390×844 (mobile) — see `EVIDENCE_MANIFEST.md`.

- **No horizontal overflow:** confirmed programmatically
  (`document.documentElement.scrollWidth > clientWidth === false`) at
  390×844 on both `/mission-overview` and `/research/experimental` — not
  merely eyeballed.
- **Genuine mobile transformation, not squeeze:**
  - `CoverageFreshnessMatrix`: row-card layout, unchanged between desktop
    and mobile (it was already a stacked list — no squeeze risk by
    construction).
  - `PipelineStateStrip`: distinct desktop (horizontal `<ol>`, `sm:hidden`
    guard) vs. mobile (vertical `<ol>`) layouts, matching the explicit
    "desktop uses a linear strip / mobile uses a vertical ordered process
    list" requirement.
  - `SensitivitySmallMultiples`: `grid-cols-1 lg:grid-cols-2` — genuinely
    reflows to one column per row on mobile, not a shrunk 2-column grid.
  - `FaultRecoveryTimeline`: relies on Recharts' `ResponsiveContainer` for
    width reflow; no bespoke mobile layout beyond that. **Documented
    limitation, LOW severity** — not adversarially re-tested against a
    populated (non-empty) timeline at 390px in this pass, since no real
    fault-injection session was capturable in this environment (see
    `VERIFICATION_LEDGER.md`).
- **First-viewport contract preserved:** Section 1 ("Command Deck") of
  `MissionOverviewExperience.tsx` — `MissionStatusBar`, the physiology
  stage, `AffectedRegionSummary`, `HRInferenceCore`, `RecentHrEstimateTrend`
  — was not touched by any Stage 6 change beyond `RecentHrEstimateTrend`'s
  container height increase (which stays within the same section, does not
  push Section 1's other content below the fold — confirmed in
  `01-mission-overview-initial-view-desktop.png`).

## Reduced motion

No new reduced-motion preference system was introduced. All new Recharts
elements set `isAnimationActive={false}` explicitly, matching the existing
codebase-wide convention (confirmed by grep — every pre-existing chart in
this codebase already does this). `23-reduced-motion-state.png` captures
`/mission-overview` with the app-level reduced-motion preference persisted
ON via the real `/settings` toggle. The pre-existing
`verify-reduced-motion-unification.mjs` structural guard (single shared
source of truth) continues to pass unchanged.

## Genuine 200% zoom

Not attempted in this pass. Stage 6's scope is chart legibility and data
integrity, not a new zoom-acceptance claim; this is documented as
`GENUINE_200_PERCENT_ZOOM: not attempted` rather than fabricated as a pass.
