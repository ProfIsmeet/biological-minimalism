# Network and provider audit

## Runtime tiers

`lib/runtime/operationalRuntimeTier.ts` is a pure string classifier — no React,
no browser APIs — precisely so the isolation guarantee is proven by test rather
than by a Network-panel screenshot. That mattered this stage, because no
Network panel was available.

| Tier | Mounts | Routes |
|---|---|---|
| `full` | LiveFeed WebSocket + `MonitoringSessionProvider` + `OperationalEventLogWatcher` | `/mission-overview`, `/live-monitoring` |
| `live-feed` | LiveFeed WebSocket only | `/ai-insights`, `/mission-timeline` |
| `static` | nothing | everything else, and any unknown route |

Unknown routes fall through to `static`, so a new explanatory route cannot
accidentally open a background socket.

## The one tier change this stage

**`/settings` moved from `live-feed` to `static`.**

It only ever qualified for `live-feed` because it mounted the operational
data-source control — synthetic/replay source switching plus subject selection
— which duplicated the Demo controls drawer the operational routes already own.
That is an ownership problem, not a convenience: two independent places could
change the confirmed source, and the preferences page could mutate what the
monitoring routes were displaying while showing none of the resulting state.
§15 asks for no duplicated operational controls without a justified workflow;
there is no such workflow here, so the control was removed rather than
restyled.

With it gone, Settings reads no live telemetry at all: no WebSocket, no
`/data-source/state`, no `/data-source/subjects`. Its "Test connection" button
is a single user-initiated fetch, not a subscription, and needs no tier.

The existing assertion was **strengthened, not relaxed**. It previously said
`/settings` *is* `live-feed`; it now says `/settings` is `static`, and two
assertions were added proving the route opens no socket and mounts no
monitoring session.

## Monitoring ownership (§20)

The §14 requirement — show a real event chronology on `/mission-timeline` —
could have been met by promoting that route to the `full` tier so it owned an
event-log watcher. That would have created a **second monitoring owner**, which
§20 forbids.

Instead the route reads the module-level Zustand `useOperationalEventStore`
**read-only**. The store is a session log populated by the operational routes,
so events recorded there stay readable after navigating to the timeline without
any new provider, socket, or watcher. `/mission-timeline` keeps its existing
tier.

Asserted: the timeline source contains `useOperationalEventStore` and contains
none of `MonitoringSessionProvider`, `OperationalEventLogWatcher`, or
`LiveFeedProvider`.

## Provider boundary

`OperationalRuntime` wraps only routed page content; the shell renders outside
it. So the sidebar, header and mobile nav never depend on operational providers
and render identically on a static route.

Continuing assertions (all passing):

- the root layout does not mount the operational providers globally;
- `OperationalRuntime` mounts the socket on `full` and `live-feed`, the session
  provider only on `full`, and passes `seedDataSourceState={false}` on `full` to
  avoid a duplicate fetch;
- the static routes (`/system-brief`, `/research/experimental`, and **both
  halves** of `/digital-twin`) call no `useLiveFeed`, no
  `useMonitoringSession`, and mount no `LiveFeedProvider`.

That last list now includes `DigitalTwinClient.tsx`. When `/digital-twin` was
split into a server shell plus a client component, three protected assertions
that read `app/digital-twin/page.tsx` would have silently emptied — the body
they were inspecting had moved. Rather than repoint them, every digital-twin
source assertion now reads **both halves concatenated**, so neither this split
nor a future one can hollow out a protected check.

## Delivered-payload verification

The pure classifier proves intent. `verify-rendered-routes.mjs` adds the
server-side half: the four static routes deliver no `/ws/live-feed` reference
in their HTML payload at all.

This is weaker than a Network panel — it cannot prove the browser opens no
socket at runtime, only that the delivered payload contains no socket URL to
open. Both layers together are reasonable evidence; neither alone is proof.

## §15 exposure review

Re-checked on `/settings`, and now asserted tree-wide rather than for that one
route, since the exposure risk is not route-specific:

| Must not appear | Status |
|---|---|
| Private filesystem paths | guarded tree-wide, zero occurrences |
| Backend environment variable names (`API_BASE_URL`, `WS_URL`) | asserted absent from `/settings` |
| Raw infrastructure instructions (`uvicorn`, `app.main`) | asserted absent |
| `localhost` URLs | asserted absent |
| Secret or token fields | none exist |
| Internal model paths | none exist |

The reachability check reports "reachable" or "unavailable" in product
language and never echoes a URL.

The private-path guard initially produced a false positive: its pattern matched
the word run "PageDown/Space/Home/End" inside a keyboard-handling comment. It
is now anchored to a real path shape, with the reason recorded at the guard.

## Fail-closed telemetry

Unchanged and preserved. Missing telemetry reports as unavailable, never as
zero or nominal. Three places where a missing value was rendering as an empty
chart axis — which reads as a measured zero — were fixed this stage; see
`SCIENTIFIC_CONSISTENCY_MATRIX.md`.

## Not verified

- No runtime Network-panel capture, so no proof of actual socket counts, request
  counts, or cleanup on route unmount.
- No measurement of whether a socket is correctly torn down when navigating
  from an operational route to a static one. The provider structure makes it
  the expected behaviour; nothing here observed it.
