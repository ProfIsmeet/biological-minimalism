# Finding Ledger — Mission Overview Scientific Visual Recomposition

Findings discovered during implementation and the adversarial self-review.
Every high- and medium-severity finding was corrected before finalizing;
none is deferred as future work.

---

## MO-F01 — HIGH — Ordinary startup rendered a false fault-red source state

**Discovered:** source inspection of `MissionStatusBar.tsx` + `sourceLabel.ts`
during archaeology, confirmed in the startup screenshot.

**Evidence:** `deriveSourceLabel()` returns `"UNAVAILABLE"` whenever the
socket is not yet open, and the status bar rendered that value with
`tone: "fault"` (red). During the perfectly ordinary connecting window —
before anything has failed — the operator therefore saw a red UNAVAILABLE
source. §8.1 explicitly forbids this: "Do not display a red `SOURCE ERROR`
during the ordinary connection window."

**Root cause:** presentation conflated "not established yet" with "failed".

**Correction:** added `deriveOperationalPhase()` (`operationalVisualTokens.ts`),
which distinguishes `establishing` / `awaiting_confirmation` (amber, neutral
language) from `disconnected` / `source_error` (red). A genuine
authoritative REST failure (`telemetryAvailability === "source_error"`)
outranks a still-connecting socket, so a real failure is never masked as
startup. `MissionStatusBar` now renders the phase word.

**Regression test:** 10 checks covering every phase combination, including
that `establishing` and `awaiting_confirmation` carry a `warning` tone and
never `fault`, and that a source error still wins over `CONNECTING`.

**Browser retest:** `26-source-establishing-neutral-state.png` — SOURCE and
STATUS both amber `ESTABLISHING SOURCE`, no red anywhere.

**Disposition: FIXED and verified.**

---

## MO-F02 — HIGH — Orbit centre text overlapped the rings and was unreadable

**Discovered:** pixel inspection of the first capture of
`03-desktop-concentric-ring-closeup.png`.

**Evidence:** the innermost ring (r=63, 10px stroke) leaves only ~116px of
clear diameter, but the centre rendered five stacked lines (value, unit,
"AI-estimated HR", status, "Not model confidence") inside a `px-14` box
~208px wide. The value visibly spilled over the inner arc and the three
supporting lines were rendered directly on top of the rings — effectively
illegible.

**Correction:** the centre now holds **only** the value and unit, inside a
112–116px constrained box matched to the real inner clear diameter. The
label, status and required "Not model confidence" note render immediately
**below** the orbit — §9.4 calls for an "explicit *adjacent* note", which
this satisfies without collision.

**Browser retest:** re-captured; value sits cleanly inside the inner ring
and all supporting text is legible beneath.

**Disposition: FIXED and verified.**

---

## MO-F03 — MEDIUM — Signal-lane gutter rendered a varying signal as flat

**Discovered:** pixel inspection of `04-desktop-coverage-radar-closeup.png`,
which also shows the signal lanes.

**Evidence:** the wrist IMU lane's min/max gutter read **"1.0 / 1.0"** while
the plotted trace visibly oscillated. The real accelerometer magnitude spans
roughly 0.96–1.04 g; a fixed `toFixed(1)` collapses both bounds to "1.0",
which reads as a flat, unvarying signal — a false impression of the data.

**Root cause:** display rounding, not the domain derivation
(`computeDynamicDomain` was returning correct values).

**Correction:** added `laneBoundDecimals()` to `waveformDisplay.ts` — a
**display-only** helper that widens precision until the two bounds are
genuinely distinguishable (capped at 4 decimals, after which equal bounds
are the honest answer for a truly flat signal). `computeDynamicDomain`'s
numbers are untouched.

**Regression test:** 5 checks, including that a narrow IMU-like range widens
to 2 decimals, an extremely narrow range widens to 3, a wide PPG-like range
stays at 1, and a genuinely flat signal is still allowed to show equal
bounds rather than inventing spread.

**Browser retest:** gutter now reads **`1.00 / 0.99`** — verified by direct
DOM extraction.

**Disposition: FIXED and verified.**

---

## MO-F04 — MEDIUM — HR trend used smoothing that implied unobserved samples

**Discovered:** source review against §10.

**Evidence:** `RecentHrEstimateTrend` used Recharts `type="monotone"`,
drawing curved interpolation between real samples. §10 requires "linear
segments, not decorative smoothing that implies unobserved intermediate
samples."

**Correction:** changed to `type="linear"`; `connectNulls={false}` preserved
so withheld intervals stay real breaks.

**Regression test:** asserts `type="linear"` is present and `type="monotone"`
is absent from the file.

**Disposition: FIXED and verified.**

---

## MO-F05 — MEDIUM — Three structural guards froze layout strings rather than behaviour

**Discovered:** running the monitoring suite after the recomposition —
5 tests failed.

**Evidence:** `C-04`/`C-03` guards asserted exact Tailwind class strings
(`"order-2 flex min-h-0 flex-col min-[1366px]:order-1"` etc.) from the old
two-column split, and a Stage 6 guard asserted `<CoverageFreshnessMatrix`
specifically. The **behaviour** they protected (HR/affected-region reaching
the first viewport before the physiology stage; the coverage question being
answered) is genuinely preserved by the recomposition, but the frozen
strings no longer describe the layout.

**Correction:** rewritten — **not deleted** — to assert the same behaviour
robustly: DOM-order checks proving the orbit (carrying the HR value) and the
HR trend precede the physiology stage, plus an explicit check that the stage
is re-prioritised only at the ≥1366px split; and a guard that the coverage
*question* is still answered on the route (now by `ArchitectureCoverageRadar`).
The pre-existing DOM-order check on `AffectedRegionSummary` was already
robust and passes unchanged.

**Disposition: FIXED — behaviour coverage preserved, no test removed.**

---

## MO-F06 — MEDIUM (self-inflicted, caught by my own new tests) — two incorrect test premises

**Evidence:** two of the regression tests I added initially failed:
1. "every non-confirmed state is distinguishable by dash or opacity" — but
   §9.3 *deliberately* specifies `recovered` as a **solid** mint stroke with
   a rounded cap, distinguished by colour + its always-rendered word. My
   premise was wrong, not the implementation.
2. `laneBoundDecimals([0.96, 1.04])` expected `1`, but `0.96` and `1.04`
   **both** render as `"1.0"` at one decimal — which is exactly the defect
   the helper exists to fix, so widening to `2` is correct.

**Correction:** both test expectations corrected to match the specified and
correct behaviour, with comments explaining why. No implementation was
weakened to make a test pass.

**Disposition: FIXED.**

---

## Investigated — no change made (documented, not silently ignored)

### Touch targets below 44px — pre-existing, outside scope
`Demo controls` (36px), the five physiology-stage module buttons (36px) and
three inline text links (16px). All are **pre-existing** components this task
did not create. The inline links fall under WCAG 2.5.5's inline-link
exemption. The module buttons belong to the accepted Stage 7 physiology
stage, which this task is explicitly forbidden from altering. My own new
components either have no interactive elements (orbit, radar — informational
SVG plus semantic tables) or exceed the floor (pipeline nodes at 58/68px
minimum). **Reported as a pre-existing LOW finding, not corrected here.**

### Fault-timeline y-axis includes zero
The timeline's HR axis spans 0–60 rather than tightly framing ~55–60. This
compresses the trace toward the top, but including zero **prevents**
exaggerating small fluctuations, which §10 explicitly requires of HR
domains. This is pre-existing derivation behaviour and was deliberately left
unchanged. **No defect.**

### HR trend appears sparse early in a session
The trend's ~90 s window is honest: shortly after start only a few seconds
of confirmed HR exist, so the plot is mostly empty. Auto-zooming the window
to make sparse data look full would be a form of manipulation. **Left as-is
deliberately; no defect.**

### Pre-existing reduced-motion hydration warning
Two console warnings appear only after toggling reduced motion, caused by
the shared root-layout boot script that sets `reduce-motion` on
`<html>` before hydration. Reproduces on untouched routes (`/settings`).
**Pre-existing, cross-route, not introduced by this task.**

---

## Summary

| Severity | Count | Disposition |
|---|---|---|
| CRITICAL | 0 | — |
| HIGH | 2 (MO-F01, MO-F02) | Fixed, regression-tested, browser-retested |
| MEDIUM | 4 (MO-F03, MO-F04, MO-F05, MO-F06) | Fixed, regression-tested |
| LOW | 1 (pre-existing touch targets) | Documented, out of scope (Stage 7 protected) |

**HIGH remaining: 0. MEDIUM remaining: 0.**
