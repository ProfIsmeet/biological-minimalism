# Corrective implementation ledger

## S9-F01 — paused first-frame deadlock

Reproduction: start local full-control environment; open Mission Overview; open Demo controls; activate Load canonical demo. The backend correctly becomes dataset replay S14, paused at zero. With no emitted paused frame, telemetry remains awaiting confirmation and Play was disabled.

Root cause: `deriveReplayControlPresentation` used the full authoritative-current telemetry gate for every playback mutation, including the one Play action capable of producing the first frame.

Correction: permit Play only when telemetry is `awaiting_confirmation`, the authoritative REST-derived source is replay, replay session state is paused, and no action is pending. Pause/reset/speed/source/fault mutations remain disabled. The Play control explains that it starts the paused replay to confirm its first frame.

Regression coverage: added explicit positive paused-replay recovery checks and negative already-playing/synthetic checks. Monitoring total increased by four assertions, 1341 → 1345. Exact local UI rerun passed and unlocked controls after the first frame.
