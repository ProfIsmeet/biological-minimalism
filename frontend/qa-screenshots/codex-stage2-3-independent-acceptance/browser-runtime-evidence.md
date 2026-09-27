# Browser runtime evidence

Browser observations were made on 2026-09-26/27 with the Codex in-app Chromium browser. The controller exposed rendered DOM, keyboard, accessibility-tree, and JavaScript state but not a durable screenshot-export API. These selected records preserve the observations without copying a giant or duplicate screenshot tree.

## Artifact BR-01 — Live-region stability and connection recovery

- Route: `/mission-overview`, `/digital-twin`
- Viewport: desktop browser viewport
- Browser: Codex in-app Chromium
- Frontend port: 3001
- Backend mode: isolated repository backend on port 8001
- Source state: real synthetic source, then disconnected, then recovered synthetic
- Responses: real backend; no interception
- Purpose: confirm ticking mission time and Digital Twin rotation remain visually available outside announced regions while meaningful disconnect/recovery transitions are announced.
- Observation: over 15 one-second samples the Mission live-region text stayed stable while visible time advanced. Digital Twin angle advanced 143°→178° without per-frame live-region mutation. Backend stop produced one disconnected/unavailable update; restart produced a connected/recovery update. Identical states did not storm.

## Artifact BR-02 — Reduced-motion cross-tab and persisted reload

- Route: `/digital-twin` in tab A, `/settings` in tab B
- Viewport: desktop browser viewport
- Browser: Codex in-app Chromium
- Frontend port: 3001
- Backend mode: isolated repository backend on port 8001
- Source state: real synthetic source
- Responses: real backend; no interception
- Purpose: reproduce and retest live persisted-setting propagation, user pause preservation, and reload behavior.
- Observation after correction: cross-tab enable changed tab A to `html.dark.reduce-motion` and held the figure at 24°. Cross-tab disable under normal OS preference removed the class and resumed a previously playing figure (33°→38°). A manually paused figure remained paused across the same preference cycle. Reload with the persisted setting showed the reduction class at first observation and subsequently rendered a stable 24° canvas; no full-motion frame was observed.
- Limitation: OS media-feature emulation was unavailable; this record covers the application preference only.

## Artifact BR-03 — Mobile More dialog

- Route: `/mission-overview`
- Viewport: 390 × 844 CSS pixels
- Browser: Codex in-app Chromium
- Frontend port: 3001
- Backend mode: isolated repository backend on port 8001
- Source state: real synthetic source
- Responses: real backend; no interception
- Purpose: verify focus trap, accessible name, scroll lock, inert background, close paths, restoration, and navigation cleanup.
- Observation: dialog name came from `mobile-more-heading`; focus began at Close; Tab/Shift+Tab wrapped between Close and Settings; body overflow was hidden; 18 background direct children became inert and aria-hidden and were restored exactly. Escape restored More focus, backdrop closed, three cycles were clean, and route/back/forward cleanup left no stale state.

## Artifact BR-04 — Demo Control Drawer

- Route: `/mission-overview`
- Viewport: 390 × 844 CSS pixels
- Browser: Codex in-app Chromium
- Frontend port: 3001
- Backend mode: isolated repository backend on port 8001
- Source state: real synthetic source
- Responses: real backend; no interception
- Purpose: independently exercise the second modal implementation.
- Observation: `demo-control-drawer-heading` supplied the name; initial focus was Close; focus wrapped Reset↔Close; scroll lock and inert/hidden background were applied and restored; Escape restored Demo controls focus; backdrop, repeated cycles, route cleanup, history navigation, and trigger unmount all passed.
