# Finding Ledger

| ID | Severity | Evidence | Resolution | Status |
|---|---|---|---|---|
| MO-AUD-01 | High | A successful Pause changed authoritative REST state while the last WebSocket frame remained `playing`; UI preferred the stale frame. | Added REST-first `resolveAuthoritativePlaybackState` and behavioral tests; browser Pause/Resume now changes the visible state correctly. | Closed |
| MO-AUD-02 | Medium | Radar labeled “current-source observation” and rendered a faulted/warming but physically provided channel as `0`, conflating absence with temporary unusability. | Split source provision from current node state; plot is binary provision, exact table carries usability. Added fault/warm-up tests. | Closed |
| MO-AUD-03 | Medium | 768/1024 layouts placed a fixed 320 px orbit beside the HR plot, causing compression/intrusion. | Moved the analytical split breakpoint from 768 to 1180 px and recaptured both tablet sizes. | Closed |
| MO-AUD-04 | Medium | Fixed-sweep protection was an exact source-string check, not a geometry test. | Extracted a pure geometry helper and asserted 300 degrees, uniform arc flags, and one arc command for all rings. | Closed |
| MO-AUD-05 | Medium | Source’s claimed release-evidence verifier exit zero was not reproducible; source images collided with canonical slots. | Preserved canonical evidence and explicitly classified source and Codex images as audit-only. Final verifier: exit 0, zero ambiguity. | Closed |
| MO-AUD-06 | Medium | During first frontend-before-backend establishment, status bar was neutral but the radar said `DISCONNECTED`. | Added initial-establishment input to the pure radar model, mapped it to `AWAITING CONFIRMED SOURCE`, and added a behavioral test. | Closed |
| MO-AUD-07 | Low | `Unavailable` at 20 px crowded the inner ring. | Reduced to 16 px with tighter tracking/leading; recaptured fault state. | Closed |
| MO-AUD-08 | Low | Timeline recovery label was 11 px. | Raised to 12 px. | Closed |

Remaining critical: 0. Remaining high: 0. Remaining medium: 0.
