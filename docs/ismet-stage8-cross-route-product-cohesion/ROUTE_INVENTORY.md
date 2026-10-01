# Route inventory

Ten reachable routes. "Runtime tier" is `lib/runtime/operationalRuntimeTier.ts`,
the pure classifier that decides how much operational runtime a pathname gets.

| Route | Kind | Runtime tier | Page title owner | Header | Stage 8 change |
|---|---|---|---|---|---|
| `/` | redirect to `/mission-overview` | static | — | — | none |
| `/mission-overview` | operational | **full** | server page | `MissionOverviewExperience` | metadata description added; typography floor; focus token |
| `/live-monitoring` | operational | **full** | server page | `RouteHeader` | title 34px -> 24/28px band; metadata description; control hit targets |
| `/system-brief` | explanatory walkthrough | static | server page | `JuryHero` (display hero) | palette/typography only; hero deliberately preserved |
| `/research` | redirect, preserves query | static | — | — | none; redirect verified |
| `/research/experimental` | research narrative | static | server page | `ExperimentalHero` (display hero) | largest palette migration; hero preserved |
| `/ai-insights` | model-output reference | live-feed | **new** server shell | `RouteHeader` | rebuilt source-aware (§13) |
| `/mission-timeline` | session record | live-feed | server shell | `RouteHeader` | real event chronology added (§14) |
| `/digital-twin` | system reference | static | **new** server shell | `RouteHeader` | split for metadata; title into band |
| `/settings` | preferences | **static** (was live-feed) | server shell | `RouteHeader` | duplicate operational control removed (§15) |

## Mounted versus dead legacy components

The brief warns against assuming a file is mounted because it exists. Mount
status was traced from `app/**` inward, not inferred.

**Mounted, and therefore in scope** — notably `ResearchMode` (168 lines
rewritten). It is reachable: `/research/experimental` renders
`AdditionalResearchArchive`, which renders `ResearchMode` inside a `<details>`
collapsed by default. Collapsed is not unreachable, so it was treated as live
surface and carried the single largest share of the palette migration.

**`TopBar` is NOT mounted on any real route.** Tracing `AppHeader` showed it
switches to `PresentationHeader` for every known route and falls back to
`TopBar` only for an unknown pathname. An early pass began auditing `TopBar` as
"the header" and was redirected once the switch was read. `PresentationHeader`
is the real header and is where the §8.2 fix landed.

**`DigitalTwinPanel` was dead and is now deleted.** Unreferenced by any route,
but it rendered `overall_adaptation.toFixed(0)` as a large "% Overall
Adaptation" readout plus per-system percentage scores — one import away from
reintroducing exactly the claim §7.4 forbids. Under §6 ("remove dead code only
if its presence creates a real maintenance or scientific-integrity risk") that
qualifies. Deletion is backed by a guard asserting the file does not return.

Ten other components were identified as dead and **left alone**: they carry no
scientific hazard, so removing them would have been scope the brief did not ask
for.
