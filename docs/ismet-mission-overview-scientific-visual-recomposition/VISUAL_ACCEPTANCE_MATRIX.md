# Visual Acceptance Matrix — Mission Overview Scientific Visual Recomposition

All rows verified against **real PPG-DaLiA S14 replay** with the accepted HR
checkpoint. Horizontal-overflow results are programmatic
(`scrollWidth > clientWidth`), not eyeballed.

| Viewport | Layout verified | Overflow | Evidence |
|---|---|---|---|
| 1440x900 | Human stage (1-5) + orbit (6-8) + HR trend (9-12) aligned in one hero row | none | 01, 02 |
| 1366x768 | Desktop split active, same three-part hero | none | 14 |
| 1280x800 | Orbit (4) + trend (8) row 1, stage row 2 | none | 15 |
| 1024x768 | Orbit + trend precede the human stage; affected-region above | none | 16, 17 |
| 768x1024 | Same tablet behaviour at the breakpoint edge | none | 18 |
| 390x844 | Single column in required order: status, affected region, orbit, trend, stage | none | 19, 25 |
| 390x844 + active fault | Fault banner untruncated, output withheld | none | 27 |
| Genuine 200% zoom | NOT_RUN / BLOCKED_EXTERNAL - see VERIFICATION_LEDGER.md | n/a | none (discarded rather than mislabelled) |

## Component acceptance

| Component | Desktop | Mobile | Notes |
|---|---|---|---|
| Concentric integrity orbit | PASS (320px, 13-10px strokes) | PASS (288px, >=9px strokes) | Fixed equal sweeps; legend >=13px; value no longer overlaps arcs |
| Architecture coverage radar | PASS (320px) | PASS (280px) | Binary 0-1; EEG/EOG member-but-unobserved rendered correctly |
| Recent HR estimate trend | PASS (330px plot) | PASS (250px plot) | Axis titles, gridlines, real gaps, linear segments |
| Signal ribbon lanes | PASS (88px lanes) | PASS | Independent domains; adaptive-precision gutters |
| Pipeline state strip | PASS (68px nodes) | PASS (58px nodes) | Converging PPG/IMU; keyboard-expandable |
| Fault & recovery timeline | PASS (340-380px) | PASS | Real replay-second axis |
| Status strip | PASS | PASS | Frame-age ticker removed; stable phase language |

## Operational-state acceptance

Every state in the mandatory matrix was exercised against real data; see
VERIFICATION_LEDGER.md for the full table and the stale-HR probe transcript.
No state produced a stale HR, a false red startup error, a fabricated
EEG/EOG trace, a zero-for-missing value, or a visible frame-age ticker.
