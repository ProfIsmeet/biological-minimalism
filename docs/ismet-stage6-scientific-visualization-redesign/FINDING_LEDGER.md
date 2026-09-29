# Finding Ledger — Stage 6 Scientific Visualization Redesign

Adversarial self-review of this task's own Stage 6 implementation, performed
after the first implementation pass and before final evidence capture. **This
is the implementation author's own self-review, not the later independent
Codex Stage 6 review** — stated explicitly per this task's own instruction.

---

## S6-FIND-01 — HIGH — Invalid `<li>`-inside-`<li>` nesting in PipelineStateStrip causes a real hydration mismatch

**Evidence:** Real browser console capture (Chrome via `playwright-core`)
against `/mission-overview` showed:
```
[error] In HTML, %s cannot be a descendant of <%s>. This will cause a hydration error. <li> li
[pageerror] Hydration failed because the server rendered HTML didn't match the client.
```
Root cause: `PipelineStateStrip.tsx`'s `Chip` sub-component rendered `<li>`
as its root element, and both the desktop and mobile `<ol>` layouts wrapped
the PPG/IMU input pair in an *additional* `<li>` containing two `<Chip>`s —
producing `<li><div><li>...</li><li>...</li></div></li>`, invalid HTML (an
`<li>` cannot validly contain another `<li>` without an intervening
`<ol>`/`<ul>`).

**Affected file:** `frontend/src/components/operations/PipelineStateStrip.tsx`.

**Correction:** `Chip` now renders a plain `<div>` as its root; every
standalone `Chip` usage is wrapped in its own explicit `<li>` at the call
site instead.

**Browser retest:** Re-ran the same console capture against a fresh dev
server after the fix — the hydration-mismatch error and the two nesting
errors are gone; only pre-existing, unrelated messages remain (409 from
`/data-source/subjects`, confirmed to reproduce identically on `/settings`,
a route Stage 6 never touched; the pre-existing `THREE.Clock` deprecation
warning; headless-GPU `ReadPixels` stall messages, a software-rendering
artifact of this test environment, not a production defect).

**Final disposition:** **FIXED and verified.**

---

## S6-FIND-02 — MEDIUM — Unrounded floating-point X-axis tick labels in SensitivitySmallMultiples

**Evidence:** Visual inspection of the initial browser capture of
`15-sensitivity-small-multiples-desktop.png` showed X-axis tick labels like
`6.783962655067444` — full floating-point precision, violating the
"tabular numerals for aligned quantitative values" / general readability
requirement.

**Root cause:** `SeriesPanel`'s Recharts `<XAxis>` had no `tickFormatter`
for the numeric value axis (only the categorical Y-axis had one).

**Affected file:** `frontend/src/components/experimental/SensitivitySmallMultiples.tsx`.

**Correction:** Added `tickFormatter={(v) => v.toFixed(2)}` to the X-axis.

**Browser retest:** Re-captured; tick labels now read `6.78`, `7.28`,
`7.78`, `8.77` etc.

**Final disposition:** **FIXED and verified.**

---

## Investigated, no defect found

### SignalLaneChart / SignalRibbonMatrix — suspected hover-only waveform data

**Concern:** `SignalLaneChart.tsx` hides both axes (`<XAxis hide />`,
`<YAxis hide />`) and exposes exact `t`/`value` only via a Recharts
`<Tooltip>`, which read as a possible "no hover-only information" violation.

**Investigation:** Read `SignalRibbonMatrix.tsx` in full. Found: (1) a
real, always-visible per-lane numeric gutter showing `domain[1]`/`domain[0]`
(the value range) without hovering; (2) a real, always-visible shared
time-range label (`t=X.XXs` … `t=Y.YYs`) below all lanes; (3) modality
identity, region, and sample rate (Hz) always visible per lane. Only the
single instantaneous point value at a specific cursor position is
tooltip-gated — the critical facts (identity, units/Hz, value range, time
range) are all already accessible without hovering.

**Disposition: NO DEFECT.** Not corrected — correcting would mean adding a
visible per-lane value table for marginal benefit at real implementation
risk, not justified by an actual violation.

### Pre-existing "Stage-3 evidence unavailable" errors during evidence capture

**Concern:** Initial browser capture screenshots showed
`SensitivityAblationSection`/`Stage3EvidenceView` rendering "Failed to
fetch" error states instead of real content.

**Investigation:** Traced to a CORS misconfiguration in this task's own
test backend instance (started on a non-default port without
`BIOMIN_ALLOWED_ORIGINS` including that origin) — confirmed via a direct
`curl` to the backend endpoint succeeding, and via re-starting the backend
with the correct origin resolving the issue in the browser.

**Disposition: NOT A PRODUCT DEFECT — test-environment configuration only.**
Corrected in the test harness (backend restarted with the right CORS
origin) before final evidence capture; no application code changed.

### `409 Conflict` from `/data-source/subjects`

**Concern:** Console capture showed a `409` response.

**Investigation:** Reproduced identically on `/settings`, a route Stage 6
never touched, and confirmed via direct `curl` that
`/data-source/replay/load` returns `"PPG-DaLiA is not configured"` — this
machine has no PPG-DaLiA dataset archive present (`BIOMIN_PPG_DALIA_PATH`
unset). A genuine, pre-existing environment limitation.

**Disposition: PRE-EXISTING, NOT A STAGE 6 REGRESSION.** Documented in
`VERIFICATION_LEDGER.md`; no code change made or warranted.

### Cross-component consistency (MINIMAL_CORE/CORE_PLUS_CONTEXT facts)

**Concern:** `ArchitectureDeltaMatrix.tsx` (new) and `MinimalCoreComparison.tsx`
(pre-existing, both on `/system-brief`) both render MINIMAL_CORE/CORE_PLUS_CONTEXT
facts — checked for possible divergence.

**Investigation:** Both consume the exact same `lib/architecture.ts` static
constants (`MINIMAL_CORE_SUMMARY`, `CORE_PLUS_CONTEXT_SUMMARY`, `EOG_DELTA_NOTE`)
— consistency is structural (same source, not independently re-derived
strings), not merely visually similar.

**Disposition: NO DEFECT.**

---

## Summary

| Severity | Count | Disposition |
|---|---|---|
| CRITICAL | 0 | — |
| HIGH | 1 (S6-FIND-01) | Fixed, browser-retested |
| MEDIUM | 1 (S6-FIND-02) | Fixed, browser-retested |
| LOW | 0 | — |
| INFORMATIONAL | 4 (hover-only waveform check, CORS test-env issue, 409 pre-existing, cross-component check) | No code change needed — either no defect, or genuinely out of application scope |

No finding remains unfixed that was within this task's authority to fix.
No test was weakened and no acceptance criterion was redefined to obtain a
pass.
