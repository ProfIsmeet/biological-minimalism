# Manual Acceptance Checklist — Stage 2-3

For a human operator to run once a browser/projector/Docker environment is
available. Every item below was implemented and structurally verified on
`ismet/frontend-stage2-3-hardening`, but NOT executed live from this
environment (see `KNOWN_LIMITATIONS.md` §1-3) — check each box for real
before treating Stage 2-3 as behaviorally accepted, not just
implementation-complete.

## A1 — Live-region announcement boundaries

- [ ] With a screen reader running, load `/mission-overview` and wait 30+
      seconds without interacting: confirm the mission status clock and
      "last confirmed frame" age are **not** announced repeatedly.
- [ ] Trigger a real connection loss/recovery, source switch, or replay
      start/stop: confirm each of those **is** announced once, as a discrete
      event.
- [ ] Open `/digital-twin` with the figure auto-rotating: confirm the
      rotation angle is never announced, but the architecture-only
      disclaimer is announced once on load.

## A2 — Reduced motion

- [ ] Enable the OS `prefers-reduced-motion` setting alone (leave the
      in-app Settings toggle off): confirm all CSS/Framer Motion/WebGL
      motion stops app-wide.
- [ ] Disable the OS setting, enable only the in-app Settings toggle:
      confirm the same — this is the case that was broken before Stage 2 A2.
- [ ] With the app open in two tabs, toggle Settings in one tab: confirm the
      other tab's motion state does **not** change (per-tab, but each tab's
      own toggle write propagates live within that tab without a reload).
- [ ] Toggle Settings, then immediately navigate to `/digital-twin` and
      `/mission-overview`: confirm every animated surface (gauges, orbit
      rings, rotation) respects the new setting without a reload.

## A3 — Mobile "More" dialog

- [ ] On a narrow viewport, open the "More" menu: confirm focus lands on the
      first focusable item automatically.
- [ ] Press Tab repeatedly: confirm focus cycles within the dialog and wraps
      from the last item back to the first (never escapes to the page
      behind it).
- [ ] Press Shift+Tab from the first item: confirm it wraps to the last item.
- [ ] Press Escape: confirm the dialog closes and focus returns to the
      "More" button.
- [ ] With the dialog open, try to scroll the page behind it (touch/trackpad):
      confirm the background does not scroll.
- [ ] With a screen reader's virtual cursor, try to read past the dialog into
      the page behind it: confirm the background is not reachable.
- [ ] Open the dialog, then use the browser back button: confirm the dialog
      closes cleanly (no stuck scroll-lock, no stuck inert background).

## A4 — WebGL/Digital Twin fallback

- [ ] On a device/browser with WebGL disabled, load `/mission-overview` and
      `/digital-twin`: confirm each shows its accessible fallback (sensor
      buttons still work for the operational avatar; the architecture-only
      text panel shows for the conceptual twin) — never a blank panel.
- [ ] Using devtools, simulate a lost WebGL context (`WEBGL_lose_context`
      extension) on either surface: confirm the fallback appears and the
      "Try 3D view again" button successfully restores the 3D view.
- [ ] Confirm the fallback for either surface never displays an invented
      number, confidence value, or scientific claim.

## Stage 3A — deployment hardening

- [ ] `docker compose up --build` on a genuinely clean machine (no cached
      `node_modules`): confirm it succeeds and both services become healthy.
- [ ] Confirm the frontend served by the container calls the correct API/WS
      origin (check Network tab / WS connection) matching the configured
      build args.
- [ ] Attempt a cross-origin request from a page not in
      `BIOMIN_ALLOWED_ORIGINS`: confirm it is rejected by CORS.

## Stage 3B — canonical jury demo

- [ ] From an arbitrary starting state (synthetic active, a different replay
      subject, non-1× speed, an active fault), click "Load canonical demo":
      confirm the result is recorded replay, subject S14, paused at the
      start, 1×, no fault — regardless of the starting state.
- [ ] Click "Load canonical demo" twice in quick succession: confirm the
      final visible state is consistent (not a partial mix of two runs) and
      no error is shown for the mere act of double-clicking.
- [ ] With the dataset intentionally unavailable (or the subject list
      empty), click "Load canonical demo": confirm it reports the exact
      missing prerequisite and does **not** silently switch to synthetic.

## Projector / visual

- [ ] Confirm 1080p (or target projector) rendering; smallest labels remain
      readable at presentation distance.
- [ ] Confirm 200% browser zoom still lays out correctly.
