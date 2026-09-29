# Scientific Source Adjudication — Stage 6 Scientific Visualization Redesign

## What Stage 6 means

Stage 6 turns the frontend's scientific/operational visualization layer from
a mixture of small charts, decorative geometry (rings/orbits/pentagons/hex
flows), and text-heavy evidence into a coherent, legible, traceable
visualization layer — without touching any scientific model, dataset,
checkpoint, HR inference logic, selected architecture, or the Stage 7
Digital Twin. This report identifies exactly which data artifacts govern
each new/redesigned chart and why.

## The cited authoritative spec directory does not exist at the source tip

The master task instructed reading
`frontend/qa-screenshots/codex-independent-final-frontend-audit/DEFERRED_VISUAL_IMPLEMENTATION_SPEC.md`,
`AUDIT.md`, and `JURY_DEMO_RECOMMENDATION.md` as the primary visualization
requirements ("Visual Package V3", families A–G). **This directory does not
exist** in the repository at the verified source SHA
`011a31683ce3444cd1b8f258c0308fb4c6997490`, nor anywhere else in the repo's
history reachable from this branch (confirmed via `find` across the full
worktree). A grep for "Visual Package V3" / "VISUAL_PACKAGE_V3" across
`docs/` found no match either.

This is reported honestly rather than silently substituted or fabricated.
It did not block implementation: the master task's own body (sections
10–17) fully specifies each visualization family's required rows, columns,
rules, and prohibitions in exhaustive detail — sufficient to implement
without the missing directory. Families A–G were implemented directly
against those inline specifications.

## Governing data sources actually used

| Family | Governing artifact(s) | Governing status |
|---|---|---|
| A + D (Coverage & freshness) | `frontend/src/lib/monitoring/operationalViewModel.ts` (live, real-time) | Live authoritative view model — not a results/ artifact |
| B (Pipeline strip) | `frontend/src/lib/monitoring/inferenceHexFlow.ts` (unmodified, reused) | Live authoritative pure derivation |
| C (Fault/recovery timeline) | `frontend/src/lib/monitoring/operationalEvents.ts` + `store/operationalEventStore.ts` (unmodified, reused) | Live authoritative session event log with real replay-time timestamps |
| E (Architecture delta matrix) | `results/stage4_architecture_candidate_classes.json`, `results/final_wearable_architecture.json` (live-fetched via existing `api.getFinalWearableArchitecture()`) | `results/final_figure_manifest.json` and this artifact's own `coordinator_decision_status` mark `CORE_PLUS_CONTEXT`/`final_architecture_status` as the accepted Stage 4 closure — GOVERNING |
| F (Evidence/burden matrix) | `results/final_tables/table_d_negative_mixed_results.json` (bundled excerpt) + `results/final_wearable_architecture.json`'s `exclusion_rationale` (live-fetched, pre-existing) | `provenance.source: results/final_claim_ledger.json` — GOVERNING |
| G (Sensitivity small multiples) | `results/final_figure_manifest.json` figures A, B, C, D (bundled excerpts of their cited provenance files) | Manifest status: `STAGE5_FIGURE_MANIFEST_REPORTED_COMPLETE_PENDING_INDEPENDENT_AUDIT` — the current best-available governing source, not itself marked superseded by anything newer; reported with that exact pending-audit qualifier, not overclaimed as fully audited |

## Resolver/governance layer used

`results/final_figure_manifest.json` and `results/final_tables/*.json` are
the project's own existing resolver layer — a synthesis pass that already
identifies, for every figure/table, which underlying `results/*.json`
artifact is EXISTING_STAGE4_FIGURE_REUSED_VERBATIM vs.
NEW_STAGE5_FIGURE_DERIVED_FROM_ACCEPTED_DATA. Stage 6 consumed this layer
directly rather than re-deriving governance from raw per-experiment JSON,
consistent with the master task's instruction to "use the current
resolver/governance layer where one exists."

No older, individually-attractive `results/*.json` file was read directly
in place of its manifest-cited governing figure/table export. Every number
appearing in a Stage 6 chart traces to a `figure_sources/` or
`final_tables/` entry, which in turn cites its own upstream provenance file
— confirmed by direct reading of each cited file before bundling (see
`DATA_TO_MARK_CONTRACT.md`).

## No governing data was found unavailable for a required family

All seven families (A–G) had governing data available; none required a
`BLOCKED_BY_MISSING_AUTHORITATIVE_DATA` disposition. The one area where
this runtime genuinely lacks data — per-channel last-confirmed freshness
age/threshold (Family D's literal "age" requirement) — is documented
honestly in `CoverageFreshnessMatrix.tsx` and shown categorically rather
than with an invented numeric age bar (see `OPERATIONAL_VISUALIZATION_REPORT.md`).
