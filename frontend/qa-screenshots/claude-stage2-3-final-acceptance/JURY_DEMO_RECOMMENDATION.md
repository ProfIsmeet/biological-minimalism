# Jury Demo Recommendation

## Recommendation: run the SYNTHETIC DEMO path, not a claimed S14 replay

As of this audit, no approved local PPG-DaLiA dataset or validated HR
checkpoint is configured anywhere in this environment. The jury-facing
application already handles this correctly and honestly: the "Load
Canonical Jury Demo" control, when clicked against the real backend, names
the missing prerequisite instead of pretending to succeed
("Canonical jury demo not loaded — Recorded PPG-DaLiA replay dataset is not
configured on this backend"). **Do not attempt to present a "recorded
replay" or "S14" demo to a jury until that dataset and checkpoint are
actually configured and independently re-verified** — doing so before that
point is not possible with this build (it fails closed, by design), and
should not be worked around.

For a jury session before that infrastructure exists, the synthetic demo
mode is fully functional, fail-closed-honest, and safe to present:

- Mission Overview, Live Signals, System Brief, Experimental Research, and
  Digital Twin Reference all render correctly and were visually confirmed
  this session (see the route screenshots in this directory).
- Disconnected/recovered transitions were exercised against the real
  backend and are honest (no stale data, explicit "Source disconnected —
  no current samples", `0 of 5 channels confirmed`).
- Reduced-motion behavior is fully correct under every combination of the
  OS preference and the in-app Settings toggle, including cross-tab sync,
  live toggling, and preserving a user's manual pause — see AUDIT.md §5.
- The Digital Twin's architecture-only/untrained/unvalidated boundary
  language is present and correct in every state, including both WebGL
  fallback paths.

## What is NOT ready to demo

- Any claim of "real recorded PPG-DaLiA S14 replay" — the dataset is not
  configured in this environment. If it becomes configured elsewhere before
  a jury session, the missing-prerequisite path this audit already verified
  gives confidence the *failure* mode is safe, but the *success* path must
  still be independently re-verified against the real dataset before a live
  demo — this audit did not and could not do that.
- Any containerized/Docker deployment — not exercised, Docker unavailable
  on this host. Static configuration is verified correct, but an actual
  `docker compose up` has not been run against this exact branch.
- Simulated-fault demonstration — the dataset-backed fault-injection UI is
  honestly disabled without recorded replay. Do not substitute the
  synthetic-only legacy `/simulation/failure` endpoint for this, since it
  has no wired frontend control in this build (verified by repo-wide grep)
  and using it directly would not reflect what a jury actually sees.
- Actual screen-reader-verified accessibility — explicitly deferred this
  session at the repository owner's direction; do not claim VoiceOver/NVDA
  compatibility has been confirmed until that session runs.

## Presenter guidance if demoing today

1. Open on Mission Overview in synthetic demo mode — this is the fully
   verified, honest default.
2. If asked about recorded replay/S14, say plainly that it requires local
   dataset configuration not present in this environment, and that the
   product's own UI will say so rather than fake it — this is a feature,
   not a bug, and is itself worth showing (open the Demo Control Drawer and
   click "Load Canonical Jury Demo" live to demonstrate the honest
   fail-closed message).
3. Avoid the raw REST API console/docs during the demo — several backend
   endpoints (e.g. legacy `/simulation/*`) exist for historical reasons but
   are not part of the current jury-facing experience.
4. See `docs/JURY_DEPLOYMENT_RUNBOOK.md` §26/§27 for the full canonical-demo
   procedure and recovery guidance once a real dataset is configured, and
   the recovery card in this evidence directory for a non-technical
   quick-reference during a live session.
