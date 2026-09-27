# Superseded Stage 2-3 evidence

These two files are preserved, byte-for-byte unmodified, from
`frontend/qa-screenshots/claude-stage2-3-final-acceptance/` purely as an
honest audit trail. They are **not** part of the release evidence bundle
(this directory is intentionally outside `frontend/qa-screenshots/`, which
is the only tree `scripts/verify_jury_release_evidence.py` globs), and they
must never be copied back into that tree or re-labeled as current evidence.

- `state-recovered-signals-INCORRECT-shows-active-error.png` — originally
  `frontend/qa-screenshots/claude-stage2-3-final-acceptance/state-recovered-signals.png`.
  Its filename, evidence-index.json entry, and AUDIT.md both described this
  as a "recovered, CONNECTED after real backend restart" state. Visual
  inspection during the `claude/stage4-5-visual-command-deck` independent
  re-audit found it actually shows an ACTIVE red "Source state could not be
  loaded — Failed to fetch" error banner on `/live-monitoring` — the
  opposite of recovered. Replaced by
  `frontend/qa-screenshots/claude-stage2-3-final-acceptance/live-signals-synthetic-demo-post-restart-connected.png`.

- `mission-overview-zoom-INCORRECT-used-css-zoom-property.png` — originally
  `frontend/qa-screenshots/claude-stage2-3-final-acceptance/mission-overview-200-zoom-accessibility.png`.
  Its own evidence-index.json entry recorded the viewport as
  `"1280x800 CSS px, document.documentElement.style.zoom=2"` — a CSS
  property mutation, not a genuine browser zoom mechanism. Replaced by
  `frontend/qa-screenshots/claude-stage2-3-final-acceptance/mission-overview-200-zoom-real-devicemetrics.png`,
  captured via a genuine CDP device-metrics-override viewport halving.

Full detail: `frontend/qa-screenshots/claude-stage2-3-final-acceptance/AUDIT.md`
section 12, and `docs/claude-stage4-5-visual-command-deck/MASTER_HANDOFF_REPORT.md`.
