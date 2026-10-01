# Responsive acceptance matrix

## Status: BLOCKED_EXTERNAL

The §23 browser matrix was **not performed**. No Chrome browser extension was
connected to this environment: `mcp__claude-in-chrome__tabs_context_mcp`
returned an extension-not-connected error, and `list_connected_browsers`
returned an empty list. There was no browser to drive.

The required matrix is therefore entirely unverified:

| Viewport | Class | Status |
|---|---|---|
| 1440x900 | desktop | **NOT VERIFIED** |
| 1366x768 | desktop, short | **NOT VERIFIED** |
| 1280x800 | desktop, narrow | **NOT VERIFIED** |
| 1024x768 | tablet landscape | **NOT VERIFIED** |
| 768x1024 | tablet portrait | **NOT VERIFIED** |
| 390x844 | mobile | **NOT VERIFIED** |

No screenshots exist. `frontend/qa-screenshots/ismet-stage8-cross-route-product-cohesion/`
is created and empty, and its manifest records zero canonical artifacts.
Screenshots from an earlier stage were **not** reused: §23 forbids reuse, and
copying them forward would have made the evidence package actively misleading.
Fabricating manifest entries was never an option.

## What was verified instead

A real HTTP acceptance pass against a running Next.js server:
`frontend/scripts/verify-rendered-routes.mjs`, 146 assertions over 10 routes,
all passing. Per route it proves:

- the route responds 200;
- it renders its own `<title>` naming that route;
- it renders a `<meta name="description">` that **differs from the layout
  default** — the weaker "a description tag exists" form is vacuous here, since
  the root layout supplies one for every route, and that is exactly how
  `/digital-twin` shipped with no metadata at all and still looked correct;
- it renders exactly one `h1`, so the document outline is sound;
- its expected copy is present in **visible** text (script payloads and tags
  stripped first);
- none of the §7 forbidden claims appear in visible text;
- no retired palette class and no sub-12px text class reaches the browser —
  which also catches a stale build or a dynamically composed class that a
  source scan cannot see.

Plus: the four static routes deliver no `/ws/live-feed` reference in their
payload, and `/research` redirects to `/research/experimental` preserving its
query string.

## What this substitute cannot tell you

It is HTML, not a rendered page. It cannot detect:

- horizontal overflow at any width, which is the single most likely responsive
  regression from this stage's work, because raising ~40 type sizes and ~26
  control heights makes content wider and taller;
- whether the two-column grids on `/live-monitoring` and `/digital-twin`
  collapse correctly at 1024x768 and below;
- whether the `mission-grid` breakpoints still hold at 1366px;
- whether the sidebar-to-mobile-nav transition behaves;
- whether the 44px control minimums are actually achieved once rendered;
- whether the global focus ring is visible against every surface token;
- any measured contrast ratio.

## The specific risk a reviewer should check first

This stage raised roughly 40 text sizes to the 12px floor and roughly 26
interactive controls to a 44px minimum, and §9.1 explicitly forbids resolving
overflow by shrinking text back down. Three changes are the most likely to have
introduced a layout regression and should be looked at before anything else:

1. **`SensorConstellation` hub** — two labels at 9px/10px became one label at
   12px inside the same 56px (compact) / 68px circle. The second label moved to
   the caption below. Check the compact variant in the `/live-monitoring` right
   rail at 1280x800 and narrower.
2. **`ReplaySessionControl` and `SimulatedFaultControl`** — every button, select
   and number input grew from ~28-32px to 44px and from 12px to 14px text, in
   `flex-wrap` rows. Check the right rail at 1024x768, where that column is
   narrowest.
3. **`OperationalAvatarOverlay` and `StaticAvatarFallback`** — anchor labels
   went from 8-11px to 12px, positioned absolutely over the figure. Check for
   overlapping labels on `/mission-overview` and `/digital-twin`.

A reviewer with a browser can complete this matrix in minutes;
`INDEPENDENT_REVIEW_ENTRYPOINT.md` gives the exact commands to bring the stack
up on the same ports.
