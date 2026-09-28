# VERIFICATION_LEDGER — claude/stage4-5-real-visual-implementation

IMPLEMENTATION_CHECKPOINT_SHA: 6d169c4abe6d68a7758f515bad5df39b8d851727
REPORT_COMMIT: this commit — resolve with `git rev-parse HEAD`

All commands below were run from this worktree at IMPLEMENTATION_CHECKPOINT_SHA
against a real, isolated backend (127.0.0.1:8004) with the real PPG-DaLiA S14
dataset and HR checkpoint configured via `BIOMIN_PPG_DALIA_PATH` /
`BIOMIN_PPG_DALIA_HR_CHECKPOINT_PATH` env vars (never copied into the repo),
and a production frontend build (localhost:3004).

## 1. Static/structural verification

| Check | Command | Result |
|---|---|---|
| Lint | `npm run lint` | PASS — 0 errors |
| Typecheck | `npx tsc --noEmit` | PASS — 0 errors |
| Monitoring-state regression harness | `node --experimental-strip-types scripts/run-verify-monitoring-state.mjs` | PASS — 1042/1042 checks (13 new this run) |
| Single-source-of-truth consumer guard | `node scripts/verify-monitoring-consumers.mjs` | PASS — 20 protected files, no direct `missionStore.latest/.history` reads |
| Live-region boundaries | `node scripts/verify-live-region-boundaries.mjs` | PASS — 3 protected files, no ticking value inside an announced live region |
| Reduced-motion single source of truth | `node scripts/verify-reduced-motion-unification.mjs` | PASS |
| Modal dialog primitive reuse | `node scripts/verify-modal-dialog-primitives.mjs` | PASS — 2 known consumers, one shared hook |
| WebGL fallback coverage | `node scripts/verify-webgl-fallback.mjs` | PASS — 2 Canvas consumers, real unsupported/error/context-loss coverage |
| Production build | `npm run build` | PASS — 14/14 routes compiled, `/mission-overview` 17.9 kB / 250 kB First Load JS |
| Backend test suite | `.venv312/bin/python -m pytest -q` | PASS — 348 passed, 4 skipped (pre-existing) |
| Release-evidence verifier | `python scripts/verify_jury_release_evidence.py --root .` | PASS — **exit 0**, PRESENT=23, MISSING=1 (optional `rejected-cesiumman`), EMPTY=0, AMBIGUOUS=0 |
| Repo hygiene | `git diff --check` on every commit | PASS — no whitespace errors |

## 2. Real-backend timing probe (C-06 root-cause verification)

A standalone diagnostic script (`probe_warmup.py`, scratchpad-only, never
committed) connected to the real `/ws/live-feed` WebSocket and used only the
existing public `POST`/`DELETE /data-source/replay/fault` REST endpoints to
measure the actual wall-clock duration of `heart_rate_inference.status ==
"warming_up"` after a fault clears:

```
[0.000] fault cleared (t_clear=0 reference)
[0.503] status -> warming_up value=None
[10.091] status -> available value=None
```

This confirmed the backend's own documented contract
(`backend/app/ml/replay_hr.py`: "Heart Rate AI waiting for an 8 s synchronized
PPG + IMU window") — the window is genuinely ~8-10 real seconds, not the
sub-150ms the original failed capture attempts implied. The actual constraint
was tool round-trip latency (a `wait_for` confirmation plus a 2x-DPI screenshot
together consumed nearly the whole window); the fix was procedural (1x DPI,
screenshot as the very next action after `DELETE`), not a timing assumption.

## 3. Real browser evidence capture (C-05/C-06/C-07)

One continuous real fault cycle (packet-loss, target=ppg, severity=0.9,
seed=7272) against the real S14 replay, captured via Chrome DevTools MCP on
`localhost:3004/mission-overview`:

| Time (UTC) | Event | Screenshot |
|---|---|---|
| 17:35:10 | Fault applied | — |
| 17:35:14 | Fault confirmed in UI (full untruncated text) | `state-fault-real-s14-packet-loss.png` |
| 17:35:27 | Fault cleared | — |
| 17:35:32 | Rebuilding state captured (pixel-verified: no numeric HR) | `state-rebuilding-real-s14-hr-warmup-v2.png` |
| 17:35:36 | Prediction became available (fresh window completed) | — |
| 17:35:50 | Recovered state captured (96.3 bpm, pixel-verified) | `state-recovered-real-s14-v2.png` |

Every screenshot above was opened with the `Read` tool immediately after
capture and its visible pixels were compared against the intended state
**before** being accepted into `EVIDENCE_INDEX.json` — this is the same check
that originally surfaced C-06, applied prospectively this time.

## 4. First-viewport acceptance (C-03/C-04, regression checks for desktop)

| Viewport | Result |
|---|---|
| 390x844 (mobile, dpr 3) | PASS — status bar, affected-region summary, and HR (79.6 bpm) all visible with zero scroll |
| 1024x768 | PASS — status bar, affected-region summary, and HR (57.2 bpm, full SRC/PPG/IMU/OUT breakdown) all visible with zero scroll |
| 1440x900 | PASS (regression) — physiology stage and HR column render side by side as before `order-*` had no effect at `xl` |
| 1920x1080 | PASS (regression) — full Section 1 fits with generous margins, enlarged typography, visible chart axes, no clipping |

## 5. Design-review loop (hostile pass)

Screenshotted Sections 2 and 4 of `/mission-overview` at 1920x1080 after the
full Stage 4 typography sweep and rebuild. Finding: `OperationalPhysiologyStage.tsx`
retained one `text-[11px]` instance the initial Stage 4 pass missed (caught by
the new automated typography guard, not manual inspection alone) — fixed and
re-verified (`verify:monitoring` re-run: 1042/1042). No other material
findings (no remaining card-wall, no low-contrast text, no clipped/overlapping
elements) at 1920, 1440, 1024, or 390.

## 6. Operational adversarial review

Exercised via the real fault-cycle capture in §3 plus static inspection:

- **Stale values shown as current**: not observed — every event carries its
  own real UTC timestamp; the HR trend/current value updates every tick.
- **Rebuilding shown as recovered**: fixed (C-06); the two states are now
  visually distinct (partial vs. full ring, "Unavailable"/"warming up" vs. a
  numeric bpm value) and pixel-verified as distinct.
- **Hidden or truncated fault text**: fixed (C-05).
- **Identity mismatch**: dataset (PPG-DaLiA), subject (S14), and model
  identity (`PPGDaliaHRModelB:PPGPlusIMUHRModel`) are consistent across every
  captured state, including through the fault cycle.
- **Missing channels appearing healthy**: EEG/EOG continue to render "No
  channel in current source" explicitly, never fabricated as confirmed.
- **Presenter controls mistaken for operational state**: "Demo controls" is a
  clearly separate, distinctly labeled button; unaffected by this run's changes.
- **Duplicate subscriptions**: `verify-monitoring-consumers.mjs` confirms no
  new component reads `missionStore` directly — `AffectedRegionSummary` (new)
  and every modified component read the same shared `useOperationalViewModel()`.
- **Focus regressions**: no `focus-visible` outline class was removed; lint's
  `eslint-plugin-react-hooks`/`jsx-a11y` rules (bundled in `eslint-config-next`)
  passed clean.

## 7. Explicitly not re-run this session

- 200% browser-zoom acceptance and VoiceOver walkthroughs (no code touched
  this run plausibly regresses either; prior stage2-3 evidence stands).
