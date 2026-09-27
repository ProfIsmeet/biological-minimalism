# Prompt 5 Dossier — Hostile / Adversarial Audit

This is the adversarial self-review record for `claude/stage2-3-final-acceptance`.
Full narrative: `../AUDIT.md` section 10. This file records the specific
attack attempts and their outcomes in dossier form.

## Attacks attempted and outcomes

| Attack | Method | Outcome |
|---|---|---|
| Force a false canonical-bootstrap success | Rapid 3x click of "Load Canonical Jury Demo" against real backend with no dataset configured | No false success at any point; identical honest fail-closed message every time; source identity never drifted from `SYNTHETIC DEMO` |
| Break the reduced-motion OR-contract | Full truth table (OS x app, all 4 combinations) plus explicit "remove one input while the other remains active" test | Contract held in all cases; removing one input alone never re-enabled motion while the other was still active |
| Break user pause intent across reduction toggles | Manually paused rotation, then cycled OS-reduce on/off | Pause state survived; button never silently flipped back to "Pause rotation" (playing) |
| Break cross-tab consistency | Genuine second tab, toggled the persisted setting from the second tab | First tab picked up the change via the native `storage` event in both directions, no stale state |
| Force a full-motion hydration flash | Set persisted reduction, hard-navigate/reload, measure class+angle at first script execution | `reduce-motion` class and frozen angle already present at first measurement; structural boot-script inspection confirms synchronous pre-hydration application |
| Force WebGL fallback to leak an invented number | Forced unsupported path via `getContext` override, forced context loss via `WEBGL_lose_context` | Fallback text contained architecture-only/untrained/unvalidated boundary language only; no confidence/adaptation/telemetry value found by regex scan of fallback body text |
| Force the WebGL "recovery offered" rule to violate its own contract | Compared unsupported path (no retry offered) vs. context-loss/render-error paths (retry offered) | Rule held: retry control absent precisely and only on the hard-unsupported path |
| Force a stale/leaked backend config into the jury UI | Ran `verify_jury_environment.py`'s `public-env-leak` check directly against this checkout | PASSED -- no backend env var name found in the rendered frontend copy |
| Mislabel controlled evidence as real | Deliberately constructed a controlled REST-interception `source_error` screenshot for the required `state-fault` evidence slot | Filename explicitly contains `CONTROLLED`; `../AUDIT.md` section 11 documents the interception and why the real dataset-gated path is unreachable in this environment |
| Fabricate real-S14 or Docker-runtime success | Searched the host filesystem for the dataset/checkpoint; checked for `docker` on PATH | Both confirmed genuinely absent; both recorded as `BLOCKED_EXTERNAL`, not attempted, not simulated as real |

## Residual risk not closed by this session

- Actual screen-reader announcement wording/cadence is unverified (deferred
  by the repository owner) -- a hostile reviewer should still independently
  run VoiceOver/NVDA before treating Stage 2 as fully closed.
- Container-runtime CORS/WS behavior inside an actual Docker network
  namespace is unverified (Docker unavailable) -- the static CORS logic is
  proven correct in isolation, but a hostile reviewer should still run the
  full container matrix on a Docker-capable host.
