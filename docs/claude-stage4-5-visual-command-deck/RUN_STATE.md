# RUN_STATE — Claude Stage 4-5 Visual Command Deck

This file is the durable execution checkpoint for this mission. If context is
compacted or the session restarts, re-read this file, run `git status` /
`git log`, and continue from "Next concrete action" below. Do not restart
completed work.

## Identity

- Repository: `https://github.com/ProfIsmeet/biological-minimalism.git`
- Anchor checkout (untouched by this task): `/Users/emirharunsunbul/Documents/ChatGPT/IAC` (branch `codex/stage1-scientific-data-integrity`, substantial unrelated untracked work — never edited by this task)
- Isolated worktree for this task: `/Users/emirharunsunbul/Documents/ChatGPT/IAC-claude-stage4-5-visual-command-deck`
- Branch: `claude/stage4-5-visual-command-deck` (new, created this task)
- Required starting SHA: `98b73c168f95c91e7f5f5e8e4beef9ca79136d53` (`claude/stage2-3-final-acceptance`) — verified exact via `git rev-parse` before any edit
- `main` SHA at start: `3efb49a02e4c824a82410793d245d3141a5942f1` (untouched)
- Source branch (`claude/stage2-3-final-acceptance`) SHA: `98b73c168f95c91e7f5f5e8e4beef9ca79136d53` (untouched — this task branches from it, never writes back to it)
- Other relevant ancestor: `codex/stage2-3-independent-acceptance` @ `779c265ca4f3d9f24c15994b8d301e68fc02ea3c`
- Target branch existed on remote before this task: NO (verified via `git ls-remote`)

## Environment

- OS: macOS (Darwin 25.5.0)
- Node: v22.23.1 / npm 10.9.8
- System Python: 3.14.5 (backend requires 3.12 for `torch==2.6.0`; prior Stage2-3 session installed `python@3.12` via Homebrew user-space — reused if present, else reinstalled the same way)
- Docker CLI: **not installed** (`docker: command not found`) — Docker gate is `BLOCKED_EXTERNAL` for the entire mission, confirmed independently
- Browser automation: Chrome DevTools MCP (`mcp__plugin_ecc_chrome-devtools__*`) / claude-in-chrome
- VoiceOver: not enabled, per explicit owner deferral (`ACTUAL_SCREEN_READER_STATUS: DEFERRED_BY_OWNER_UNTIL_AFTER_STAGE7`)

## Dataset / checkpoint discovery (major finding — overrides prior BLOCKED_EXTERNAL)

The prior `claude-stage2-3-final-acceptance` audit reported the PPG-DaLiA dataset
and HR checkpoint as genuinely absent on this host. Independent re-discovery
this session found **both assets present as git-ignored files in the anchor
worktree** (`/Users/emirharunsunbul/Documents/ChatGPT/IAC`), not in this
task's isolated worktree (which only carries the tracked `.gitkeep` / README
placeholders):

- Checkpoint: `<anchor>/ml/checkpoints/model_b_ppg_plus_imu_ppg_dalia.pt` — size `138086` bytes, SHA-256
  `c53a34586d2d6baf68aae4441b6c15a0f5f623f0ea70c023c7371c2dbded0e77` — **exact match** to the expected values.
- Dataset archive: `<anchor>/datasets/ppg-dalia/raw_uci/ppg_dalia_uci.zip` — outer zip contains a nested
  `data.zip`, which contains `PPG_FieldStudy/S14/S14.pkl` — **confirmed present** by listing (not extracted into the repo; the backend adapter (`backend/app/data/ppg_dalia.py`) natively handles this nested-zip layout, no manual extraction needed).

Plan: configure `BIOMIN_PPG_DALIA_PATH` and `BIOMIN_PPG_DALIA_HR_CHECKPOINT_PATH`
to point read-only at these anchor-worktree paths (never copied into this
worktree, never staged, never committed, never written verbatim into
committed reports — reports say "anchor worktree ignored asset path"
generically). This unblocks real S14 acceptance testing that Stage 2-3 had
marked `BLOCKED_EXTERNAL`.

## Confirmed Stage 2-3 evidence defects (from independent re-audit, before any fix)

1. **`state-recovered-signals.png` is mislabeled.** Visual inspection shows the
   Live Signals page displaying an active red "Source state could not be
   loaded — Failed to fetch" banner, "REPLAY STATE: Unavailable — source
   error", "SIMULATED FAULT: Not currently confirmed" — this is an active
   fault/error view, not a recovered view. Confirmed defect, must be replaced
   with a genuinely recovered capture (no error banner, channels confirmed).
2. **`mission-overview-200-zoom-accessibility.png` used `document.documentElement.style.zoom = 2`**
   (confirmed via evidence-index.json's own viewport field and AUDIT.md §6)
   — this is explicitly disallowed as "real browser zoom" per this mission's
   rules. Must be recaptured using a genuine browser zoom mechanism (CDP page
   scale / native zoom keystroke), not CSS zoom.
3. **`state-rebuilding-webgl-contextloss-retry.png`** — investigated and
   RESOLVED AS NOT A DEFECT. Read `ConceptualTwinFallback.tsx` and
   `WebglStage.tsx` in full: the fallback component intentionally shows
   identical body text ("3D rendering unavailable on this device or browser")
   for both the hard-unsupported case and the context-lost/retryable case —
   the only differentiator is whether the "Try 3D view again" button is
   rendered at all (`onRetry` present vs. `undefined`, per `WebglStage.tsx`'s
   `renderFallback(retry)` vs `renderFallback(null)`). The captured screenshot
   shows the button present, which only occurs on the context-loss/retry
   path — so the evidence is correctly captured for that state. The only
   real limitation is the one already disclosed in AUDIT.md §11 (this is a
   WebGL rebuild substituted for the absent HR/connection-rebuilding state,
   because the app has no distinct "reconnecting" UI text) — already honest,
   no correction needed.
4. **`state-fault-source-error-CONTROLLED.png`**: already correctly labeled
   `CONTROLLED` in filename and evidence-index; visual inspection matches
   (source_error state, all modalities showing "Source error"). Not a defect.
5. **`docs/claude-stage2-3-final-acceptance/STATUS.md` is stale.** It says
   "Working branch ... not yet pushed" and lists "push to origin" / "stop the
   two test services" as *remaining* tasks, even though the branch is
   verifiably pushed (its own tip commit is `origin/claude/stage2-3-final-acceptance`)
   and ports 3003/8003 have no active listeners (confirmed via `lsof`). This
   is the kind of stale self-referential status text the mission asks to
   correct. Will not edit the historical `claude/stage2-3-final-acceptance`
   branch itself (never modify a source branch) — will add a corrective note
   in this task's own Phase 1 report instead, since the file lives in
   inherited history now baked into this branch's ancestry.

## Completed so far

1. Bootstrapped: verified origin URL, fetched, confirmed exact base SHA and ancestor SHAs, confirmed no prior `claude/stage4-5-visual-command-deck` existed locally or remotely, created isolated sibling worktree + branch.
2. Read required docs: `docs/claude-stage2-3-final-acceptance/STATUS.md`, `FINAL_REPORT.md`; `frontend/qa-screenshots/claude-stage2-3-final-acceptance/AUDIT.md`, `FIVE_STAGE_COMPLETENESS_MATRIX.md`, `JURY_DEMO_RECOMMENDATION.md`, `evidence-index.json`; `docs/MODEL_CONTRACT_PPG_DALIA_HR.md`; `docs/DATASET_REPLAY.md`. Confirmed no `AGENTS.md`/`CLAUDE.md` and no `DEFERRED_VISUAL_IMPLEMENTATION_SPEC.md` exist at this SHA (not present in this ancestry — noted as absent, not fabricated).
3. Visually inspected the 4 highest-risk inherited screenshots (see defects above).
4. Discovered real dataset/checkpoint assets in the anchor worktree (see above) — overrides prior BLOCKED_EXTERNAL for real S14.
5. Inventoried frontend route/component architecture: `mission-overview` is a thin server wrapper around `components/operations/MissionOverviewExperience.tsx`, which composes `MissionStatusBar`, `OperationalPhysiologyStage`, `HRInferenceCore`, `InferenceHexFlow`, `InferenceIntegrityOrbit`, `ModalityPentagon`, `SensorConstellation`, `SignalRibbonMatrix`, `RecentHrEstimateTrend`, `FaultRecoverySpine`, `OperationalProvenanceChain`, `PresenterPreflight`, `DemoControlDrawer`, `OperationalEventRail`/`Watcher`. Names map directly onto the mission's Stage 5 "demote ornamental orbit/hex/pentagon" and "consolidate duplicate inference summaries" language.

## Phase 0 — clean baseline (COMPLETE, unmodified worktree)

All numbers reproduced independently and match the inherited Stage 2-3 claims exactly:

| Check | Result |
|---|---|
| `npm ci` (frontend) | 452 packages installed, 0 errors (2 pre-existing npm audit advisories, unrelated to this task) |
| `npm run verify:monitoring` | 1021/1021 passed, 5/5 structural verifiers PASSED |
| `npm run lint` | clean |
| `npx tsc --noEmit` | clean |
| `npm run build` | 14/14 pages |
| Backend venv | Python 3.12.14 (`backend/.venv312`, user-space, reused from prior Homebrew install), `pip install -r requirements.txt` clean |
| Backend full suite (`pytest -q`) | 347 passed, 4 skipped, 104s |
| Targeted CORS/deployment/jury tests (`pytest -k "cors or deploy or jury"`) | 30 passed |
| `scripts/verify_jury_environment.py --root .` | 19 PASS / 7 WARN / 0 FAIL (WARNs: docker absent, HR checkpoint/PPG-DaLiA env vars not yet set — expected pre-Phase-1) |
| `scripts/verify_jury_release_evidence.py` (default/`--hash`/`--json`) | 23 PRESENT / 1 MISSING (optional `rejected-cesiumman`, honestly absent) / 0 AMBIGUOUS / 0 EMPTY, `f07_status: COMPLETE` in JSON mode |
| `git diff --check` | clean (exit 0) |

No regressions from the unmodified base. No source files changed in Phase 0.

## Phase 1 — COMPLETE (commit `6ea2d05`)

Real S14 acceptance ran end-to-end (backend discovery, checkpoint hash match,
`AI_ESTIMATED` HR, real fault injection, HR-rebuilding, recovery, 3x
idempotent reload). 2 confirmed Stage 2-3 evidence defects corrected
(mislabeled recovery screenshot, CSS-zoom evidence); 1 suspected defect
(WebGL rebuild substitute) investigated and cleared as already honest.

## Phase 2 — Stage 4/V1 — COMPLETE (commit `ec655e9`)

Hostile-audited all 8 routes. 4 material defects found and fixed: legacy
disconnected header on 3 routes (V1-01), MetricTile text overlap (V1-02),
distorted/clipped orbit SVG (V1-03), wrong browser tab title on 2 routes
(V1-04). One self-caught regression during this phase (verifier path
literals) found and fixed without weakening any test.

## Phase 3 — Stage 5/V2 — COMPLETE (no source changes; verification only)

Found the command-deck architecture already substantially built. Verified
the first-viewport contract, the full required viewport matrix
(1920x1080/1440x900/1280x800/1024x768/390x844/real-200%-zoom), and
regression-tested the reduce-motion toggle and mobile dialog after the
Stage 4 refactors. One finding (duplicate-looking inference summaries)
reviewed and documented as an intentional, non-contradictory dual framing —
not changed.

## Final phase — reports, final verification, commit, push — IN PROGRESS

All 8 mandated reports written. One more self-caught regression found and
fixed during final verification (evidence-verifier `audit-main` glob
narrowing broke 2 backend unit tests; reverted, documented instead as an
accepted AMBIGUOUS). Final clean-tree verification suite green except for
that one documented, understood evidence-verifier AMBIGUOUS.

## Next concrete action

Stage the final docs/evidence commit, run `git diff --check`, commit, push
`claude/stage4-5-visual-command-deck` (non-force), verify local/remote SHA
equality, stop task-created services (backend 8003, frontend 3003), and
deliver the final chat response with the required YAML verdict block.

## Services/processes started by this task (to stop at the end)

(none yet — will record ports/PIDs here as Phase 0/1 services are started)

## Commits created by this task

(none yet)

## Pushed

NO (not yet)
