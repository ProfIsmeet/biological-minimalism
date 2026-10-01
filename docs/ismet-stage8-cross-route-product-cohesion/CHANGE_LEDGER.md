# Change ledger

91 files changed, 2185 insertions, 1128 deletions, against
`dc2039d53773ebfad763e0716f51876fb8185058`.

The large majority of those lines are two mechanical migrations — the retired
palettes and the typography floor — applied across 72 component files. The
substantive work is in the files listed individually below.

## Files created

| File | Purpose |
|---|---|
| `src/app/ai-insights/AIInsightsClient.tsx` | Source-aware rebuild of `/ai-insights` (§13). The route now branches on the confirmed source, so it never asks about a score that does not exist for that source. |
| `src/app/digital-twin/DigitalTwinClient.tsx` | The `/digital-twin` view, moved out of `page.tsx` so a server shell can own `metadata`. A client component cannot export it, which is why the route had none. |
| `src/components/layout/RouteHeader.tsx` | The one page-header treatment for a standard route (§16/§17). Fixes three competing title scales, two of them out of the §9.1 band. |
| `src/lib/monitoring/timelinePresentation.ts` | Pure §14 presentation: event origin and time basis. JSX-free so the mapping is asserted behaviourally, not inspected. |
| `scripts/verify-rendered-routes.mjs` | HTTP acceptance against a running server: 146 assertions over 10 routes. |

## Files deleted

| File | Why |
|---|---|
| `src/components/panels/DigitalTwinPanel.tsx` | Dead, but rendered `overall_adaptation` as "% Overall Adaptation" plus per-system percentage scores — one import from reintroducing the claim §7.4 forbids. §6 permits removing dead code whose presence is itself a scientific-integrity risk. Backed by an existence guard. |

## Files with substantive edits

### Shared shell and design system

| File | Change |
|---|---|
| `src/app/globals.css` | Removed the `!important` sub-12px override (the floor is now a build-time guard, not a silent runtime patch). Added the single global `:focus-visible` rule inside `@layer base`. De-glassed `.mission-panel`. Deleted `.text-shadow-glow`. |
| `tailwind.config.ts` | Added the `focus-ring` token, set to the `#A1D2CC` already hard-coded at ~20 sites. |
| `src/components/layout/Sidebar.tsx` | 10-11px all-caps labels to 12px sentence case; group labels off `ink-disabled`; 40px rows to 44px; active row gains weight + a leading rule so selection is not background-colour alone; removed the `max-h-[72px]` clamp that truncated the wordmark; `aria-hidden` on decorative icons. |
| `src/components/layout/MobileNav.tsx` | Group-label contrast and tracking only. Audited in full and found already correct. |
| `src/components/layout/PresentationHeader.tsx` | `/settings` no longer renders a live CONNECTED/CONNECTING badge; it gets a static APPLICATION PREFERENCES scope badge. |
| `src/components/layout/MotionConfigProvider.tsx` | Comment only — it named the deleted panel as an example consumer. |

### Routes

| File | Change |
|---|---|
| `src/app/live-monitoring/page.tsx` | Title 28/34px to the shared `RouteHeader`; metadata description added. |
| `src/app/digital-twin/page.tsx` | Became a thin server shell owning `metadata`. |
| `src/app/mission-overview/page.tsx` | Metadata description added. Composition untouched. |
| `src/app/mission-timeline/MissionTimelineClient.tsx` | Real session event chronology as a semantic table, read-only from the shared event store; conceptual markers moved behind a hard rule and a "Not session data" badge; removed a synthetic-only trend that drew an empty 0-100 chart in replay; `RouteHeader`. |
| `src/app/mission-timeline/page.tsx` | Metadata description added. |
| `src/app/settings/SettingsClient.tsx` | Removed the duplicated operational data-source control; reduce-motion switch rebuilt as a 24px track inside a 44px button; `RouteHeader`. |
| `src/app/settings/page.tsx` | Metadata description added. |
| `src/app/ai-insights/page.tsx` | Became a thin server shell owning `metadata`. |

### Panels and controls

| File | Change |
|---|---|
| `src/components/panels/AIConfidencePanel.tsx` | Title/subtitle now source-conditional; "Sensor Contribution" to "Synthetic sensor contribution". The scientific logic was already correct. |
| `src/components/panels/ExplanationPanel.tsx` | Refresh genuinely disabled during replay, with the reason in the accessible name and the tooltip. |
| `src/components/monitoring/ReplaySessionControl.tsx` | Every button, select and number input to 44px / 14px; speed buttons gain `aria-pressed` and a weight change so selection is not colour-only. |
| `src/components/monitoring/SimulatedFaultControl.tsx` | Same. |
| `src/components/monitoring/MonitoringSourceStrip.tsx` | Retry control to 44px. |
| `src/components/demos/DataSourceControl.tsx` | Same, plus the heaviest single-file palette migration outside the research tree. Still mounted in the Demo controls drawer, where it belongs. |
| `src/components/ui/DataStateError.tsx` | Retry control to 44px. |
| `src/components/operations/SensorConstellation.tsx` | Hub labels: two at 9/10px to one at 12px; connection state relocated to the caption with a word-plus-colour treatment. Circle geometry unchanged. |
| `src/components/operations/FaultRecoveryTimeline.tsx` | "SIMULATED" from 10px/`ink-disabled` to the floor on `jury-warning`. |

### Runtime

| File | Change |
|---|---|
| `src/lib/runtime/operationalRuntimeTier.ts` | `/settings` dropped from `LEGACY_LIVE_FEED_ROUTES`, with the §15 rationale recorded in the doc comment. |

### Tests

| File | Change |
|---|---|
| `scripts/verify-monitoring-state.ts` | +434 lines, -9. The §22 tree-wide guards, the §16/§17/§18 guards, and the six `C-01` floor assertions rewritten in place. Digital-twin assertions now read both halves of the split route. |
| `scripts/verify-stage7-digital-twin.mjs` | Points at the view and also checks the shell, so the split cannot weaken it. |
| `package.json` | Added `verify:rendered`, kept separate from `verify:monitoring` because it needs a running server. |

## Mechanical migrations

| Migration | Files | Occurrences |
|---|---|---|
| `slate-*` / `space-*` to semantic tokens | across components | 470 |
| Raw default palette + alpha-over-white to semantic tokens | 20 | 528 |
| Sub-12px classes to the 12px floor | across components | ~400 |
| `outline-[#A1D2CC]` to `outline-focus-ring` | 16 | 22 |

The largest single mechanical file is `components/research/ResearchMode.tsx`
(168 lines rewritten), which is mounted — reachable through a collapsed
`<details>` on `/research/experimental`. Collapsed is not unreachable.

## Explicitly not changed

- `/mission-overview` composition, the five-section narrative, the four-ring
  fixed-sweep orbit, the coverage-radar semantics, the HR trend and signal
  lanes, the fault/rebuilding/recovery timeline structure.
- Stage 7 human geometry, anatomical joints, camera/focus/keyboard behaviour,
  WebGL fallback, single-canvas ownership.
- `JuryHero` and `ExperimentalHero` display type.
- Evidence-selection policy, canonical dataset/checkpoint handling, model and
  scientific constants.
- Any backend file. Any ML file. Any dataset.
- `main`, the source branch, and the Furkan presentation snapshot.
