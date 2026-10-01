# Evidence manifest

## Screenshot evidence: none exists

`frontend/qa-screenshots/ismet-stage8-cross-route-product-cohesion/` contains
`manifest.json` and no images.

**Why:** no Chrome browser extension was connected to this environment.
`tabs_context_mcp` returned an extension-not-connected error and
`list_connected_browsers` returned an empty list. There was no browser to
drive.

**Two things that were deliberately not done:**

1. **Earlier stages' screenshots were not copied forward.** §23 requires fresh
   evidence and forbids reuse. Copying stale images into a Stage 8 directory
   would have made this package actively misleading about what was observed at
   this SHA — worse than an empty directory.
2. **No manifest entry was fabricated.** The required fields (filename, route,
   viewport, runtime source, operational state, expected visual facts, visual
   inspection status, SHA-256, canonical/audit/superseded classification) are
   all fields *about an artifact*. With no artifacts, inventing rows would be
   inventing observations. `artifacts` is `[]` and all three classification
   counts are `0`.

The manifest records the block, the reason, both policies above, the six
unverified viewports, and what the substitute evidence does and does not prove
— so the gap is machine-readable rather than only described in prose.

## Evidence that does exist

| Evidence | Location | Result |
|---|---|---|
| Rendered-route acceptance | `frontend/scripts/verify-rendered-routes.mjs` | 146/146 |
| Monitoring state suite | `frontend/scripts/verify-monitoring-state.ts` | 1327/1327 |
| Monitoring consumers | `verify-monitoring-consumers.mjs` | pass, 20 protected files |
| Live-region boundaries | `verify-live-region-boundaries.mjs` | pass, 3 protected files |
| Reduced-motion unification | `verify-reduced-motion-unification.mjs` | pass |
| Modal dialog primitives | `verify-modal-dialog-primitives.mjs` | pass, 2 consumers |
| WebGL fallback | `verify-webgl-fallback.mjs` | pass |
| Stage 7 digital twin | `verify-stage7-digital-twin.mjs` | pass |
| TypeScript | `npx tsc --noEmit` | clean |
| ESLint | `npm run lint` | clean |
| Production build | `npm run build` | 12 routes prerendering |

All of this is re-runnable; `VERIFICATION_LEDGER.md` has the exact commands and
the two ports used.

## Rendered payload sizes

Captured during the final `verify:rendered` run. Not evidence of correctness —
recorded because a sudden change in these numbers is a cheap signal that
something structural moved.

| Route | Status | Bytes |
|---|---|---|
| `/mission-overview` | 200 | 96,908 |
| `/system-brief` | 200 | 79,167 |
| `/live-monitoring` | 200 | 58,016 |
| `/research/experimental` | 200 | 55,104 |
| `/digital-twin` | 200 | 46,710 |
| `/ai-insights` | 200 | 39,123 |
| `/mission-timeline` | 200 | 35,002 |
| `/settings` | 200 | 33,918 |

`/` and `/research` are redirects and return no body of their own.

## Real S14 assets (§24)

Not required for this stage's scope and not accessed. Nothing was downloaded,
nothing was copied into the repository, nothing was committed, and no private
absolute path appears in any report — the last of which is additionally
enforced by a tree-wide guard over the source.

## One transient worth recording

During the final gate sweep, `verify:rendered` briefly reported three failures
on `/mission-overview` (no title, no description, zero `h1`). This was not a
defect: `npm run build` had just overwritten `.next` underneath the running
`next dev` server. Re-running after the dev server recovered gave 146/146. It
is recorded here because a reviewer running the gates in that order will see
the same thing, and should not read it as a real finding.
