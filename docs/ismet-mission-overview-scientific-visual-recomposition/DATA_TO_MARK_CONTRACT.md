# Data-to-Mark Contract — Mission Overview Scientific Visual Recomposition

Every visual mark rendered by this recomposition, with its exact source,
encoding, missing-value behaviour and — critically — what it explicitly
does **not** mean. No visualization was implemented before its row existed.

---

## 1. Concentric Inference Integrity Orbit (4 rings)

| Field | Value |
|---|---|
| Question answered | Which parts of the signal path are currently intact? |
| Source | `deriveIntegrityRings()` (`lib/monitoring/integrityRings.ts`, **unchanged** by this task) fed from `useOperationalViewModel()` |
| Fact class | Live, replay- or synthetic-derived, gated by `telemetryAvailability` |
| Visual mark | Four concentric arcs, outside-in: Source authority, PPG input, IMU input, HR output |
| Unit | **None — categorical.** There is no unit because there is no quantity |
| Domain / scale | **No scale.** Every ring draws an identical fixed 300° sweep with a shared 60° gap in every state |
| Missing-value behaviour | `unavailable` → gray, dash `2 7`, word "No channel in current source" |
| Fault behaviour | `fault` → coral `#D46F70`, dash `8 6`, word "Simulated fault" |
| Awaiting behaviour | `awaiting` → amber, dash `10 7`, word "Awaiting confirmation" |
| Source-error behaviour | `source_error` → coral, dash `2 6`, word "Source error" |
| Accessibility equivalent | `aria-describedby` paragraph naming all four states in words + a 4-row visible legend at 13px with matching line swatches |
| Why this grammar is valid | Concentric categorical bands express *nesting/dependency* (source encloses inputs, inputs enclose output) without implying magnitude — appropriate precisely because there is no magnitude to show |
| **What it does NOT mean** | **Not a percentage, confidence, probability, reliability, readiness, accuracy or health score.** Arc length is constant and carries no information. A structural test forbids any numeric-percent token in this file |

## 2. Orbit centre value

| Field | Value |
|---|---|
| Question answered | What is the current AI-estimated HR, if one is authoritative right now? |
| Source | `view.prediction.value` (authoritative view model) |
| Fact class | Live, replay-only |
| Visual mark | 46px tabular-numeral value + "bpm" inside the innermost ring |
| Unit | bpm |
| Missing behaviour | Renders the word **"Unavailable"** plus the exact reason. **Never** renders a retained previous value and **never** renders `0 bpm` — verified in a real fault cycle: value → `null` during fault AND during rebuilding → fresh value only on genuine recovery |
| Accessibility equivalent | Value, label, status and scope note are all real DOM text |
| **What it does NOT mean** | Adjacent text states **"Not model confidence"**. No accuracy or ground-truth claim; there is no reference HR channel in this runtime |

## 3. Architecture Coverage Radar (binary)

| Field | Value |
|---|---|
| Question answered | Which modalities does the selected architecture contain, and which are actually observed in the current source? |
| Source | Series A: `FINAL_SENSOR_INVENTORY` + `CORE_PLUS_CONTEXT` membership (**static**). Series B: `modalityStates[].nodeState` from the live view model |
| Fact class | A = static architecture fact; B = live observation |
| Visual mark | Two closed polygons on five axes (PPG, IMU, ECG, EEG, EOG) |
| Unit | **Dimensionless binary** |
| Domain / scale | **Exactly [0, 1]**, enforced by the `BinaryCoverage = 0 \| 1` type |
| Missing behaviour | A channel absent from the source is `0` **with its exact reason** in the semantic table ("Not provided by this replay") |
| Fault behaviour | A faulted channel is `0` with reason "Simulated fault — channel withheld" — never collapsed into generic absence |
| Awaiting / source-error / disconnected | **Observation series WITHHELD entirely** (`observed: null`, polygon not drawn) with a visible `AWAITING CONFIRMED SOURCE` notice. An all-zero polygon would falsely claim "we looked and found nothing" rather than "we cannot yet say" |
| Accessibility equivalent | `aria-describedby` summary + a full semantic table of modality / architecture / current-source state and reason |
| Why this grammar is valid | All five axes share **one identical dimensionless binary meaning**, which is the precondition Reference C's radar form requires. Unlike a typical radar, no axis carries a different unit or range |
| **What it does NOT mean** | A visible note states **"Binary coverage only — not model performance."** Not quality, reliability, sensitivity, accuracy or confidence. No percentage is printed anywhere |

## 4. Recent HR Estimate Trend

| Field | Value |
|---|---|
| Question answered | How has the AI-estimated HR moved recently, and where was it unavailable? |
| Source | `useConfirmedHistory()` → `deriveHrTrend()` (**derivation unchanged**) |
| Fact class | Live, replay-derived |
| Visual mark | Linear area/line, 2.5px, over a ~90 s relative window |
| Unit | bpm (y, labelled "HR (bpm)"); seconds relative to now (x, labelled "Replay time (s, relative)") |
| Missing behaviour | `connectNulls={false}` — withheld intervals are **real visible breaks**; a caption states gaps mean unavailable/withheld output |
| Fault behaviour | An explicit amber banner: "Current HR unavailable · plot retains confirmed historical estimates only" |
| Accessibility equivalent | Heading, current value as DOM text, scope and gap captions |
| Why linear, not monotone | Monotone smoothing would draw curvature implying intermediate samples that were **never observed**. Changed to `type="linear"` in this task |
| **What it does NOT mean** | No confidence band (no genuine uncertainty exists), no clinical normal range, no reference/ground-truth comparison |

## 5. Signal Ribbon lanes (PPG / IMU / ECG)

| Field | Value |
|---|---|
| Question answered | What does each real channel's waveform look like right now? |
| Source | `view.modalities[].plot` (real channel samples, sample rate, start timestamp) |
| Fact class | Live, replay-derived |
| Visual mark | One 88px lane per channel, each with its **own independent y-domain** |
| Unit | Per-channel device units, with real sample rate (64/32/700 Hz) always visible |
| Missing behaviour | No channel → explicit architecture-only row, **never a fabricated flat line** |
| Fault behaviour | Explicit dashed "Simulated fault — waveform withheld" panel replacing the trace |
| Accessibility equivalent | Per-lane identity, region, Hz, and min/max gutter as DOM text; shared time range printed |
| **What it does NOT mean** | Unlike units are **never** combined on one axis — PPG amplitude, accelerometer g and ECG amplitude each keep a separate domain and gutter |

## 6. EEG / EOG rows

| Field | Value |
|---|---|
| Question answered | Are EEG and EOG part of the architecture, and are they present in this source? |
| Source | `FINAL_SENSOR_INVENTORY` (member) + live observation (absent in S14) |
| Visual mark | Text row: "Final architecture modality · no waveform channel in current source"; radar vertex at 0 |
| **What it does NOT mean** | **No fabricated waveform, no partial reliability, no percentage.** Absence is never converted to zero-as-a-measurement; it is stated as absence |

## 7. Pipeline State Strip

| Field | Value |
|---|---|
| Question answered | In what order does the HR result become valid, and where is it blocked? |
| Source | `deriveHexFlow()` (**unchanged**) |
| Visual mark | Linear process flow with PPG/IMU converging into Window assembly |
| Unit | None — categorical |
| Accessibility equivalent | Ordered list semantics; every node keyboard-focusable with expandable explanation; nothing hover-only |
| **What it does NOT mean** | Not a percent funnel, not a readiness score. No invented sample counts or readiness percentages |

## 8. Fault & Recovery Timeline

| Field | Value |
|---|---|
| Question answered | When did adverse events occur against real replay time, and when did output return? |
| Source | Session event log with authoritative `replay_position_seconds` |
| Unit | Replay seconds (x), HR bpm (y) |
| Missing behaviour | Null HR intervals remain breaks; the y-domain includes zero, which **prevents** exaggerating small fluctuations |
| **What it does NOT mean** | No clinical "normal" inference; simulated control events are labelled distinctly from source-reported state |

## 9. Status phase language

| Field | Value |
|---|---|
| Question answered | What is the connection/source state right now, stably? |
| Source | `deriveOperationalPhase()` from `connectionLabel` + `telemetryAvailability` |
| Visual mark | One categorical word, amber for establishing/awaiting, red only for genuine failure |
| **What it does NOT mean** | **Replaces the removed per-second "Last confirmed frame" ticker.** The underlying `confirmedTimestampSeconds` is retained in the view model for guards, freshness and history isolation — only its unstable visible presentation was removed |
