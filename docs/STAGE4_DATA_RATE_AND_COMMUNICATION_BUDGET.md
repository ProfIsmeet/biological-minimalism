# Stage 4 Data-Rate and Communication Budget

Source of truth: `results/stage4_engineering_readiness.json` (`data_rate`
block), extending `results/reference_data_rate_budget_day11.json`. All
`DATASHEET_CALCULATED` rows below are reused unchanged, by value, not
recomputed. Only the previously-`NOT_READY` rows (`light_sensor`,
`thoracic_bioz`, `leg_bioz`) and the transmitted/radio rate are newly closed here.

## Rate-class separation (unchanged convention from Day-11)

- **HARDWARE_ACQUISITION_RATE** — AFE ODR (e.g. ADS1299-class ≥250 SPS)
- **SCIENTIFIC_MODEL_STREAM_RATE** — resampled rate fed to the model (e.g. 100 Hz Sleep-EDF)
- **RAW_SENSOR_DATA_RATE** — computed from the stream rate where channels/rate/bits are frozen
- **PROCESSED_DATA_RATE** — **NOT_READY** (no on-device feature-extraction/compression reduction factor is frozen)
- **RADIO_DATA_RATE / TRANSMITTED_RATE** — newly closed by this report, with an explicit protocol-overhead assumption

## Raw acquisition — base topology (excludes optional/experimental branches)

| Modality | Channels | Rate | Bits/sample | Raw bps | Class |
|---|---|---|---|---|---|
| `wrist_ppg` | 1 | 64 Hz | 19 | 1,216 | `DATASHEET_CALCULATED` (frozen) |
| `wrist_imu` | 3 | 32 Hz | 16 | 1,536 | `DATASHEET_CALCULATED` (frozen) |
| `skin_temperature` | 1 | 1 Hz | 16 | 16 | `DATASHEET_CALCULATED` (frozen) |
| `light_sensor` | 1 | 0.1 Hz (1 sample/10s) | 16 | 1.6 | `ENGINEERING_ASSUMPTION` (newly closed) |
| `ecg_chest` | 2 | 250 Hz | 24 | 12,000 | `DATASHEET_CALCULATED` (frozen) |
| `thoracic_bioz` | 1 | 1 Hz | 16 | 16 | `ENGINEERING_ASSUMPTION` (newly closed) |
| `head_eeg_eog` (scientific stream) | 2 (1 EEG + 1 EOG) | 100 Hz | 24 | 4,800 | `DATASHEET_CALCULATED` (frozen; ADS1299-class hardware ODR is ≥250 SPS, distinct from this 100 Hz resampled model-stream figure) |
| **System raw total (base topology)** | | | | **19,585.6 bps (≈19.6 kbps)** | sum of the above |

## Internal processing / on-device rate

**`PROCESSED_DATA_RATE_NOT_READY`.** No on-device feature-extraction or
compression pipeline data-reduction factor is frozen anywhere in this
project. This report deliberately does **not** assume processed rate equals
raw rate, and does **not** assume any particular compression ratio — both
would be invented precision.

## Transmitted (radio) payload assumption

A **20% protocol-overhead** reference assumption (`ENGINEERING_ASSUMPTION`) is
applied to the raw total to approximate BLE ATT/L2CAP/link-layer notification
overhead for small payloads — this is a commonly-cited order-of-magnitude
reference, **not** a specific BLE stack's measured overhead, and does not
account for compression, retransmission, or connection-event scheduling loss.

**System transmitted total (base topology): 19,585.6 × 1.20 = 23,502.72 bps (≈23.5 kbps).**

## Optional / experimental sensor branches — excluded from every base total

| Branch | Raw bps | Status |
|---|---|---|
| `second_ppg_site` (3 ch, 500 Hz, 19 bits) | 28,500 | `OPTIONAL / DEPRIORITIZED_FOR_CURRENT_TARGET` (rule 48) — frozen, unchanged, **not included in any system total** |
| `leg_bioz` (same engineering assumption as thoracic) | ~1 | `EXPERIMENTAL` (rule 47) — **not included in any system total** |

## Historical figure correction (presentation-risk fix)

The previously-cited **48,068 bps (48.068 kbps)** "system raw total" figure
(`results/reference_data_rate_budget_day11.json.system_raw_total`) **included**
`second_ppg_site`'s 28,500 bps — 59% of that total came from a sensor branch
this project has explicitly deprioritized. This was flagged as presentation
risk **HW-1** in `docs/CLAUDE_DAY12_14_SUPPORT_HANDOFF.md`. This report's
**19,585.6 bps base-topology total correctly excludes `second_ppg_site`**,
giving an honest "minimal base system" figure for the first time. The old
48,068 bps figure remains valid as a historical record of what it measured
(base topology + second_ppg_site branch + light/BioZ open) but must not be
cited going forward as "the system data rate" without that qualification.

## System data-rate readiness

| Dimension | Status |
|---|---|
| Raw acquisition (base topology) | `PARTIAL_READY` — datasheet-frozen rows + newly-closed engineering-assumption rows; light/thoracic-BioZ cadence are assumptions, not datasheet facts |
| Internal processing | `NOT_READY` |
| Transmitted/radio | `PARTIAL_READY` — protocol-overhead assumption only, no real BLE stack measurement |
| Optional/experimental branches | Characterized, explicitly excluded from every total |
