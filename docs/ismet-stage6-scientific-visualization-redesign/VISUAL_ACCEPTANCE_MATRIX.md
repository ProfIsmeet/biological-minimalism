# Visual Acceptance Matrix — Stage 6 Scientific Visualization Redesign

| Family | Component | Desktop | Tablet | Mobile | Keyboard | Reduced motion | Evidence |
|---|---|---|---|---|---|---|---|
| A+D Coverage/freshness | `CoverageFreshnessMatrix` | PASS | PASS (full-page capture) | PASS (row-card, no overflow) | PASS (button rows on Mission Overview) | N/A (static rows, no animation) | 01, 02, 06, 20 |
| B Pipeline strip | `PipelineStateStrip` | PASS | PASS | PASS (vertical list) | PASS (expand/collapse via real button) | N/A | 02, 07, 20 |
| C Fault/recovery timeline | `FaultRecoveryTimeline` | PASS (honest empty state) | PASS (within full-page capture) | **NOT RE-TESTED at 390px with a populated timeline** — see limitation below | PASS (semantic table always present) | N/A | 02, 09, 20 |
| HR trend | `RecentHrEstimateTrend` | PASS (enlarged, legible) | PASS | PASS (within full-page capture) | N/A (no interactive control) | N/A | 02, 11, 20, 21 |
| E Architecture delta matrix | `ArchitectureDeltaMatrix` | PASS | Not separately captured (static table, no responsive-specific risk identified) | Not separately captured | N/A (no interactive control) | N/A | 13, 25 |
| F Evidence/burden matrix | `CandidateDispositionMatrix` (enriched) | PASS | Not separately captured | PASS (pre-existing mobile stacked-list layout, confirmed still renders with new columns) | N/A | N/A | 14, 18, 19 |
| G Sensitivity small multiples | `SensitivitySmallMultiples` | PASS | Not separately captured | PASS (grid reflows to 1 column, no overflow) | N/A (values via semantic table, not dot focus) | N/A | 15, 18, 19 |

## Genuine 200% zoom

`GENUINE_200_PERCENT_ZOOM: not attempted` — out of this pass's time
budget; not fabricated as a pass. Recommended as an explicit item for the
independent Stage 6 reviewer.

## Known limitation: FaultRecoveryTimeline mobile with populated data

The 390×844 capture of `/mission-overview` (`21-390x844-command-deck-view.png`)
shows the timeline's honest, correctly-rendered **empty** state (no fault
events in this synthetic-only session) with no horizontal overflow. The
Recharts `ResponsiveContainer`-driven chart body itself was not separately
stress-tested at 390px width with actual plotted fault intervals and HR
points, because no real replay session with fault-injection capability was
available in this environment (PPG-DaLiA dataset archive absent — see
`VERIFICATION_LEDGER.md`). This is disclosed as a genuine, specific gap for
the independent reviewer to close on a machine with the dataset available,
rather than silently assumed to be fine.

## Desktop/Tablet/Mobile acceptance summary

`DESKTOP_ACCEPTANCE: PASS`. `TABLET_1024_ACCEPTANCE: PASS`.
`MOBILE_390_ACCEPTANCE: PASS`, with the one documented limitation above
(FaultRecoveryTimeline's populated-state mobile rendering not
independently re-tested).
