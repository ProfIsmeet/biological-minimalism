# AUDIT — claude-stage4-5-real-visual-implementation evidence set

## Scope

This directory contains only the evidence that corrects three specific, independently-confirmed
defects inherited from `claude-stage2-3-final-acceptance` and `claude-stage4-5-visual-command-deck`:

- **C-05** — the real-S14 fault description text was truncated with an ellipsis in the status bar.
- **C-06** — `state-rebuilding-real-s14-hr-warmup.png` claimed (in its evidence-index entry) to show
  `heart_rate_inference.status=warming_up` with no numeric HR, but its actual pixels showed a numeric
  HR value and "Model available" — a genuine mismatch between the claimed state and the visible
  screenshot, not a captioning error.
- **C-07** — the recovered-state evidence's recorded bpm value was not verified against the same
  screenshot's own visible pixels.

Plus first-viewport regression evidence for **C-03** (mobile) and **C-04** (1024×768 tablet), and
desktop (1440/1920) regression checks after the Stage 4/5 component changes.

## Rebuilding-state capture methodology (C-06 fix)

The original C-06 defect happened because a screenshot was taken *after* the `warming_up` window had
already elapsed, but was filed under the "rebuilding" evidence slot anyway. To fix this without
repeating the mistake, this run first characterized the real, actual duration of the `warming_up`
window using a small diagnostic WebSocket probe script
(`<ephemeral-scratch>/probe_warmup.py`, run once against the same isolated backend, using only
the existing public `POST`/`DELETE /data-source/replay/fault` endpoints and reading the existing
`heart_rate_inference.status` telemetry field — no DOM freezing, no CSS injection, no response
interception, no fabricated state):

```
[0.000] fault cleared (t_clear=0 reference)
[0.503] status -> warming_up value=None
[10.091] status -> available value=None
```

This confirmed the backend's own stated contract (`app/ml/replay_hr.py`: "Heart Rate AI waiting for an
8 s synchronized PPG + IMU window") — the `warming_up` state genuinely lasts roughly 8-10 real seconds
after any fault clears, regardless of how long the fault itself was held. The previous failed capture
attempts were not caused by an inherently sub-150ms window; they were caused by tool round-trip latency
(an intervening `wait_for` accessibility-tree confirmation plus a full-DPI 2x screenshot together
consumed close to the entire window). The fix was procedural: reduce to 1x device-pixel-ratio, and take
the screenshot as the first and only action immediately after the `DELETE` call (or immediately after a
`wait_for` fault-active confirmation from a prior step), landing solidly inside the window rather than
at its tail.

Every image in this directory was opened with the `Read` tool immediately after capture and its visible
pixels were compared against the intended state **before** it was accepted into this evidence set or
referenced from `EVIDENCE_INDEX.json` — the same check that originally surfaced C-06 in the inherited
evidence, now applied prospectively to new captures instead of only retrospectively.

## Fault/rebuilding/recovered narrative continuity

`state-fault-real-s14-packet-loss.png`, `state-rebuilding-real-s14-hr-warmup-v2.png`, and
`state-recovered-real-s14-v2.png` are three frames of **one continuous fault cycle** (packet-loss fault
applied with seed `7272` at 17:35:10 UTC, cleared at 17:35:27 UTC, recovered at 17:35:36 UTC) against
the same running replay session, subject S14, so the three images form a coherent before/during/after
narrative rather than three unrelated captures stitched together after the fact.

## Superseded evidence

The original `claude-stage2-3-final-acceptance/state-rebuilding-real-s14-hr-warmup.png` and
`state-recovered-real-s14-after-condition-cleared.png` are left unmodified in place, per the established
audit-trail convention — they are superseded for the C-06/C-07 evidence purpose by the files in this
directory, but not deleted, so the defect and its correction both remain inspectable.
