# Finding Ledger — Stage 6 Fresh-Session Audit & Closure

All findings from a real, populated fault/recovery replay exercise —
never from an empty-state screenshot alone. Every CRITICAL/HIGH/MEDIUM
finding below was corrected on this audit branch and re-verified with a
fresh browser run after the fix.

---

## S6A-FIND-01 — CRITICAL — Three call sites label a wall-clock timestamp as "replay time"

**Claim challenged:** "Real recorded fault-onset, fault-clear, and
recovery events... plotted against confirmed HR output over replay time"
(FaultRecoveryTimeline's own header copy), and CoverageFreshnessMatrix's
"As of replay t=Ns" footer.

**Evidence:** A real populated-replay run (S14, real fault applied/
cleared via REST) produced a fault-recovery-timeline table showing
`REPLAY TIME (S): 1790703102.9` — a ~2026 Unix-epoch second count, not a
small in-session offset — and a coverage-matrix footer reading
"As of replay t=1790704719.9s". Both are impossible values for "seconds
into an ~9000-second replay session."

**Root cause:** `view.confirmedTimestampSeconds` (`operationalViewModel.ts`)
is backed by `missionStore.lastConfirmedTimestampSeconds`, set from
`snapshot.timestamp` — the server's wall-clock confirmation time, a
legitimate field for computing frame *age* (as `MissionStatusBar.tsx`
correctly does, unaffected by this finding) but not a replay position.
Three Stage 6 call sites treated it as if it were the latter:
`OperationalEventLogWatcher.tsx` (feeding `OperationalEvent.sourceTimestampSeconds`),
`FaultRecoveryTimeline.tsx` (mapping HR history samples), and
`CoverageFreshnessMatrix.tsx` (the "as of" footer).

**Affected files:** `frontend/src/components/operations/OperationalEventLogWatcher.tsx`,
`frontend/src/components/operations/FaultRecoveryTimeline.tsx`,
`frontend/src/components/operations/CoverageFreshnessMatrix.tsx`.

**Correction:** All three switched to `view.replayPositionSeconds` /
`snapshot.source.replay_position_seconds` — the genuine, already-existing
authoritative replay-position field (confirmed present on every historical
snapshot via `TelemetrySourceMetadata.replay_position_seconds`).

**Regression test:** 3 new source guards confirm the corrected field is
used and the wrong one is not, in all three files.

**Browser retest:** Re-ran the full populated-replay exercise after the
fix; table and footer both show correct, small, plausible values (e.g.
`18.5`, `40.5`, `18.8s`).

**Final disposition: FIXED and verified.**

---

## S6A-FIND-02 — CRITICAL — The populated fault/recovery timeline renders nothing

**Claim challenged:** Implicit in "Fault/recovery timeline implemented" —
that the chart actually draws marks once real data exists.

**Evidence:** After fixing S6A-FIND-01, a real populated run still showed
a completely empty chart body (only the X-axis and a shaded fault interval
rendered; no HR line, no Y-axis). Direct DOM inspection during a live
populated session found `<div class="recharts-responsive-container"
style="width: 100%; height: 100%;">` with **zero children** — no `<svg>`
was ever created.

**Root cause:** `ChartFrame`'s chart-body wrapper used Tailwind
`min-h-[Npx]` (CSS `min-height`, leaving `height: auto`). Recharts'
`<ResponsiveContainer>` sets `height: 100%` on itself; CSS percentage
heights do not resolve against an `auto`-height parent, so the container
computed to 0×0 regardless of the visually-rendered `min-height`. It
happened to look correct for `SensitivitySmallMultiples` purely by
coincidence — that component's `ChartFrame`s sit inside a CSS Grid, and
grid-item stretch establishes a *definite* height per the CSS spec, unlike
a plain flex-column section (where `FaultRecoveryTimeline` sits).

**Affected file:** `frontend/src/components/visualization/shared/ChartFrame.tsx`
(shared primitive — this fix also benefits `SensitivitySmallMultiples`,
making its correctness non-coincidental going forward).

**Correction:** Changed the prop/class from `minHeightClassName`/`min-h-[Npx]`
to `heightClassName`/`h-[Npx]` (a definite height), matching the pattern
`RecentHrEstimateTrend.tsx` already used correctly.

**Regression test:** Source guard confirms `heightClassName` is used and
the removed `minHeightClassName` prop is gone.

**Browser retest:** Re-ran the populated exercise; the chart now renders a
real SVG with a visible HR line, Y-axis (0/20/40/60/80 bpm), X-axis
(1s/16s/46s), and the shaded fault-interval region correctly positioned.

**Final disposition: FIXED and verified.**

---

## S6A-FIND-03 — MEDIUM — Fault-clear and recovery were not visually/tabularly distinct

**Claim challenged:** Master task §10: "Fault clear is distinct from
recovery" / "Recovery marker appears only after authoritative recovery."

**Evidence:** The original chart rendered only `model.intervals` (fault
onset→clear pairs); a genuine `prediction_recovered`-class event existed
in the underlying pure module's type system but was never surfaced as its
own chart marker or table row, making the clear-vs-recovery distinction
unverifiable from the rendered evidence.

**Affected file:** `frontend/src/components/operations/FaultRecoveryTimeline.tsx`.

**Correction:** Added a dashed `ReferenceLine` "Recovery" marker and a
dedicated table row, distinct from the fault-interval rows. (Superseded in
its data source by S6A-FIND-05 below, which fixed *how* recovery is
computed; the visual/table distinctness fixed here was kept.)

**Final disposition: FIXED**, then further improved by S6A-FIND-05.

---

## S6A-FIND-04 — MEDIUM — A session's plain initial warm-up was mislabeled "Recovery"

**Claim challenged:** Same as S6A-FIND-03 — a genuine recovery marker
should only ever follow a genuine fault.

**Evidence:** After the S6A-FIND-03 fix, a real run showed **two**
"Recovery" markers — one positioned at 8.5s, chronologically *before* the
fault even started (onset was at 18.5s). A recovery marker before any
fault is a contradiction.

**Root cause:** `faultRecoveryTimeline.ts`'s `EVENT_CLASS` map classified
both `prediction_recovered` (genuine post-fault recovery) and
`prediction_available` (a session's plain first-ever HR value, never a
fault) as `"recovery"`. `operationalEvents.ts`'s own
`deriveEventsFromTransition` (pre-existing, unmodified) already correctly
distinguishes these two kinds at the source — the Stage 6 mapping
re-conflated them.

**Affected file:** `frontend/src/lib/monitoring/faultRecoveryTimeline.ts`.

**Correction:** Removed `prediction_available` (and the equally-imprecise
`prediction_unavailable: "fault_onset"`, which never actually contributed
to any rendered mark since it always has `modality: null`) from the
classification map; only `prediction_recovered` maps to `"recovery"`.

**Final disposition: FIXED**, then further improved by S6A-FIND-05 below
(which found `prediction_recovered` itself essentially never fires).

---

## S6A-FIND-05 — MEDIUM — `prediction_recovered` essentially never fires in the normal recovery sequence

**Claim challenged:** Same recovery-marker requirement.

**Evidence:** After S6A-FIND-04's fix, a real fault-clear-then-recover run
showed the primary HR display genuinely recovering ("65.9 bpm" at t+9s
post-clear, tracked via direct DOM text polling), yet **zero**
`prediction_recovered` events appeared in the session event store across a
30-second post-clear observation window.

**Root cause:** `deriveEventsFromTransition` (pre-existing shared
infrastructure, `operationalEvents.ts`, not modified by this audit — out
of this task's ownership boundary) classifies a `predictionAvailability`
transition to "available" as `prediction_recovered` only if
`previous.faultActive` was `true` at that exact moment. In practice,
`faultActive` flips to `false` the instant the fault-clear REST call
propagates — well before the model's real re-warm-up window elapses and a
new HR value actually appears — so by the time availability returns,
`previous.faultActive` has already become `false`, and the event is always
misclassified as the plain `prediction_available` case instead.

**Affected file:** `frontend/src/lib/monitoring/faultRecoveryTimeline.ts`
(self-contained fix, not touching the pre-existing shared infrastructure
that has the underlying classification bug — that bug is documented here
as a real, but out-of-scope, upstream limitation).

**Correction:** Recovery markers are now derived directly from the
trusted `hrPoints` array itself: for each closed fault interval, the first
real (non-null) HR sample strictly after the interval's `clearSeconds` is
the genuine recovery point — grounded in the same real replay-time axis,
with no dependency on the fragile upstream event classification.
Deduplicated so multiple modalities faulted/cleared together (e.g. a
`target: "both"` fault) produce one recovery marker, not one per modality.

**Regression tests:** 5 new pure-logic tests cover: a real recovery
marker derives correctly from the first real HR sample after clear; no
marker is fabricated before a real value appears; simultaneous multi-
modality recovery deduplicates to one marker; an ongoing (never-cleared)
fault produces no recovery marker; a plain `prediction_available` event
(no fault ever occurred) is excluded from the fault-timeline event set
entirely.

**Browser retest:** Re-ran the populated exercise with an 18-second
post-clear wait; exactly one correctly-positioned "Recovery" marker
appeared (40.1s replay time, 62.8 bpm), matching the real HR line's visual
resumption point exactly.

**Final disposition: FIXED and verified.**

---

## Evidence-verifier exit-2 gate — closed (not a "finding" against Stage 6 per se, but a mandatory closure item)

See `EVIDENCE_VERIFIER_ROOT_CAUSE.md` for the full trace. Root-caused to a
pre-existing (predates Stage 6 entirely — reproduced at the Stage 7 parent
commit before any Stage 6 work existed), environment-level line-ending
checkout artifact, not a Stage 6 defect and not fabricated evidence. Closed
via `.gitattributes` + working-tree renormalization, with zero content
change to any evidence file (verified byte-for-byte).

---

## Evidence-filename collisions — investigated and corrected (this audit's own evidence, not a Stage 6 defect)

Two of this audit's own new screenshot filenames (`*nominal*`, `*rebuild*`)
collided with pre-existing evidence-verifier glob patterns for unrelated
Stage 2-5 slots, temporarily reintroducing `AMBIGUOUS=2`. Renamed before
final commit (content/hash unchanged); verifier reconfirmed at exit 0.

---

## Summary

| Severity | Count | Disposition |
|---|---|---|
| CRITICAL | 2 (S6A-FIND-01, S6A-FIND-02) | Fixed, regression-tested, browser-retested |
| HIGH | 0 | — |
| MEDIUM | 3 (S6A-FIND-03, S6A-FIND-04, S6A-FIND-05) | Fixed, regression-tested, browser-retested |
| LOW | 0 | — |
| INFORMATIONAL | 2 (evidence-verifier root cause; evidence-filename collision) | Both closed as part of this audit's mandatory gates |

No finding remains unfixed that was within this audit's authority to fix.
The one genuine upstream limitation identified (S6A-FIND-05's root cause in
pre-existing `operationalEvents.ts`) was worked around within this audit's
own module rather than modifying shared infrastructure outside its
ownership boundary, and is disclosed explicitly rather than silently
patched over.
