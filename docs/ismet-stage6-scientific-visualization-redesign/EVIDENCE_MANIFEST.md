# Evidence Manifest (companion) — Stage 6 Scientific Visualization Redesign

Authoritative, machine-readable manifest:
`frontend/qa-screenshots/ismet-stage6-scientific-visualization-redesign/EVIDENCE_MANIFEST.json`.
This document is the human-readable companion and canonical-selection-rule
summary.

## Identity

- Implementation checkpoint SHA: `e78a84bd7a6a0e3257b41ebb9e58bb75a4001191`.
- Source: `origin/codex/stage7-final-acceptance-closure` @ `011a31683ce3444cd1b8f258c0308fb4c6997490`.
- Browser: system Chrome via `playwright-core@1.63.0` over CDP (temporary,
  fully reverted).

## Canonical-selection rule

Every file is unique, captured once against the implementation checkpoint
above. No competing/older evidence set exists in this directory, so every
listed file is CANONICAL; none is SUPERSEDED. If a future capture adds a
competing file for an existing conceptual slot in this directory: the file
with the latest capture timestamp recorded in `EVIDENCE_MANIFEST.json`
wins (CANONICAL); the older one is re-marked SUPERSEDED. An unresolvable
timestamp collision is AMBIGUOUS and is treated as not-present until a
human adjudicates it — mirroring the repository's own
`scripts/verify_jury_release_evidence.py` fail-closed policy.

## Coverage vs. the master task's 25-item suggested list

16 files captured. Not all 25 suggested items were captured, in the
interest of finishing a complete implementation + verification + report
cycle within this task's time budget rather than partially completing
implementation to chase exhaustive screenshot coverage. What was
prioritized: at least one piece of evidence per visualization family
(A–G), both responsive breakpoints with a programmatic no-overflow check,
keyboard focus, and reduced motion.

**Not captured, and why (all honestly disclosed, none fabricated):**

- Genuine 200% zoom — not attempted this pass (see `ACCESSIBILITY_AND_RESPONSIVE_REVIEW.md`).
- Mission Overview adverse/rebuilding/restored states, populated fault/recovery
  timeline, real HR trend with data, real waveform lanes — all `BLOCKED_EXTERNAL`:
  the PPG-DaLiA dataset archive is not present on this machine (see
  `VERIFICATION_LEDGER.md`).
- `/live-monitoring` route screenshots — not captured; the route was not
  modified by Stage 6 beyond reusing the already-existing, unmodified
  `SignalRibbonMatrix`.
- Freshness view as a standalone screenshot — Family D is merged into
  Family A's `CoverageFreshnessMatrix` component (see
  `VISUALIZATION_INVENTORY.md`); captured together in files 01/02/06/20.

## File index

| # | File | What it shows |
|---|---|---|
| 1 | `01-mission-overview-initial-view-desktop.png` | First-viewport contract preserved |
| 2 | `02-mission-overview-full-page-desktop.png` | All 5 sections, families A+D/B/C together |
| 3 | `06-coverage-freshness-matrix-mobile.png` | Family A+D, mobile row-cards |
| 4 | `07-pipeline-strip-expanded-block.png` | Family B, click-to-reveal provenance |
| 5 | `09-adverse-response-timeline-no-events.png` | Family C, honest empty state |
| 6 | `11-hr-trend-enlarged.png` | HR trend, enlarged container |
| 7 | `13-architecture-delta-matrix.png` | Family E |
| 8 | `14-evidence-burden-matrix.png` | Family F, enriched columns |
| 9 | `15-sensitivity-small-multiples-desktop.png` | Family G, PPG-DaLiA + PTT panels, rounded axis ticks (post-fix) |
| 10 | `18-research-route-full-page-desktop.png` | Full Experimental Research route |
| 11 | `19-research-route-390x844.png` | Mobile, no horizontal overflow |
| 12 | `20-tablet-1024x768-mission-overview.png` | Tablet breakpoint |
| 13 | `21-390x844-command-deck-view.png` | Mobile, no horizontal overflow |
| 14 | `22-keyboard-focus-visible.png` | Visible focus ring |
| 15 | `23-reduced-motion-state.png` | Persisted reduced-motion preference |
| 16 | `25-architecture-brief-full-page.png` | Full System Brief route |

All 16 SHA-256 hashed (mutually distinct, listed in `EVIDENCE_MANIFEST.json`)
and visually inspected via direct image review before commit — not
accepted on filename alone.
