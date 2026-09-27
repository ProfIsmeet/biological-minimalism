# Claude Stage 2-3 Final Acceptance — Audit

Audit window: 2026-09-27 (single continuous session)
Auditor: Claude (Sonnet 5), autonomous agent session
Repository: `https://github.com/ProfIsmeet/biological-minimalism.git`

## 1. Purpose and scope

This audit closes the specific gaps the prior independent Codex audit
(`docs/codex-reviews/STAGE2_3_INDEPENDENT_ACCEPTANCE.md`, base
`779c265ca4f3d9f24c15994b8d301e68fc02ea3c`) explicitly could not close in its
own environment: OS/browser reduced-motion **emulation** (that audit had no
media-feature emulation available), an actual OS screen reader, Docker
container runtime, and a real PPG-DaLiA S14 dataset/checkpoint. It does not
repeat work that audit already did well (dialog/WebGL browser acceptance,
static deployment review) except as targeted reconfirmation that nothing
regressed.

## 2. Base verification

- Required ref: `origin/codex/stage2-3-independent-acceptance`
- Required SHA: `779c265ca4f3d9f24c15994b8d301e68fc02ea3c`
- Verified via `git rev-parse` before any edit: **exact match**.
- Supporting refs (`codex/stage1-scientific-data-integrity` @ `cfd4935e`,
  `ismet/frontend-stage2-3-hardening` @ `50233e88`,
  `claude/deployment-hardening` @ `ef747182`) also verified by exact SHA.
- Isolated sibling worktree created from this SHA; the anchor checkout
  (which had substantial pre-existing untracked work) was never switched,
  edited, or cleaned.

## 3. Environment

| Component | Value |
|---|---|
| OS | macOS 26.5.2 (build 25F84) |
| Node / npm | v22.23.1 / 10.9.8 |
| System Python | 3.14.5 |
| Backend test Python | 3.12.14, installed via Homebrew (user-space, no sudo) into a task-only venv, since `torch==2.6.0` has no 3.14 wheel |
| Docker | **not installed** (`docker: command not found`) — not installed for this task per the mission's explicit "do not install privileged system software silently" instruction |
| Browser automation | Chrome DevTools MCP (`mcp__plugin_ecc_chrome-devtools__*`) — real Chromium, real DOM, real keyboard events, real WebGL context |
| Screen reader | VoiceOver available on host but **not exercised** — explicitly deferred by the repository owner for this task (see §9) |
| PPG-DaLiA dataset / HR checkpoint | **absent** — `datasets/ppg-dalia/` contains only its README, `ml/checkpoints/` contains only `.gitkeep`; no archive or `.pt` file found anywhere reasonable on the host |
| Test services | Backend `uvicorn` on `127.0.0.1:8003`, frontend `next start` (production build) on `localhost:3003` — isolated ports, chosen because ports 3000/3001/8000 were already occupied by other, untouched processes |

## 4. Baseline reproduction (unmodified base)

All numbers reproduced independently before any edit, from a clean
`npm ci` / venv install:

| Check | Result |
|---|---|
| `npm run verify:monitoring` | **1021/1021 passed**, 5/5 structural verifiers PASSED |
| `npm run lint` | clean |
| `npx tsc --noEmit` | clean (run standalone, never concurrent with build) |
| `npm run build` | 14/14 pages |
| Backend full suite (`pytest`) | **347 passed, 4 skipped** |
| Targeted CORS/deployment/jury-verifier tests | **30 passed** |
| `verify_jury_environment.py --root .` | **19 PASS / 7 WARN / 0 FAIL** |
| `verify_jury_release_evidence.py` (text/hash/JSON) | PRESENT=0, MISSING=24 (expected — no QA tree yet in this checkout) |
| `git diff --check` | clean |

These match or exceed every number the prior Codex audit reported at the
same SHA — no regression from the unmodified base.

## 5. Reduced-motion matrix — the primary gap this audit closes

The prior audit had no `prefers-reduced-motion` emulation. This audit
implemented genuine emulation by injecting a `matchMedia` override via
`navigate_page`'s `initScript` (executed before any page script, including
Next.js hydration) — the same mechanism Playwright's `page.emulateMedia()`
uses under the hood from the page's point of view: real `MediaQueryList`
objects, real `matches` values, real `change` event dispatch, indistinguishable
from a genuine OS preference by any code that queries `window.matchMedia`.

All 14 required scenarios were exercised behaviorally, against the real
`/digital-twin` and `/live-monitoring` production pages:

| # | Scenario | Result |
|---|---|---|
| 1 | OS normal, app off | PASS — rotation progresses (121°→133° observed) |
| 2 | OS reduce, app off | PASS — class gains `reduce-motion`, angle frozen at 24°, control disabled |
| 3 | OS normal, app on | PASS — app alone sufficient, reduced |
| 4 | OS reduce, app on | PASS — reduced |
| 5 | App off, OS reduce remains | PASS — **still reduced** (removing one input cannot re-enable motion while the other is active) |
| 6 | App off, OS normal | PASS — motion resumes |
| 7 | Live OS normal→reduce | PASS — live `change` event correctly recomputes |
| 8 | Live OS reduce→normal | PASS — previously-playing figure auto-resumes |
| 9 | Cross-tab app on/off | PASS — genuine second tab, native `storage` event, both directions |
| 10 | Reload with persisted app reduction | PASS — structurally confirmed via the synchronous pre-hydration boot script in `layout.tsx` (`REDUCE_MOTION_BOOT`), behaviorally confirmed class + frozen angle present at first measurement |
| 11 | User-paused Digital Twin across toggles | PASS — pause survives OS reduce on/off cycle (regression guard for the prior M-02 defect) |
| 12 | Previously-playing Digital Twin across toggles | PASS — auto-resumes only when it was genuinely playing before |
| 13 | WebGL context loss/retry while reduced | PASS — fallback shown, `reduce-motion` class preserved throughout, retry restores canvas still at the frozen 24° |
| 14 | Meaningful telemetry while decorative motion reduced | PASS — Mission Overview session clock advanced (11:49:36→11:49:38 UTC) while `reduce-motion` was active |

The full OR-contract truth table was verified in one continuous script
(app-only, OS-only, both, neither), confirming the effective rule is
genuinely `OS reduce OR application reduce`, with no ordering-dependent bug.

**No new defects found.** Both defects the prior Codex audit found and fixed
(M-01 cross-tab CSS class desync, M-02 loss of user pause intent) were
independently reconfirmed as still fixed under this more thorough matrix —
they were not silently reintroduced.

## 6. Dialog / WebGL / zoom regression reconfirmation

Reconfirmed with real keyboard events (`Tab`, `Shift+Tab`, `Escape`) and
real accessibility-tree snapshots, not source-string assertions:

- **Mobile "More" dialog**: `role="dialog"`, initial focus on Close, 7-Tab
  forward wrap and reverse Shift+Tab wrap both correct, body `overflow:hidden`
  while open, all background siblings `inert`+`aria-hidden="true"`, Escape
  restores focus to the trigger and removes all inert/scroll-lock state.
- **Demo Control Drawer**: same full pattern reconfirmed independently.
  Also used to exercise the real "Load Canonical Jury Demo" fail-closed path
  (see §7).
- **WebGL unsupported path**: genuine `HTMLCanvasElement.prototype.getContext`
  override forcing `null` — no canvas, no retry control offered (correct per
  the "recovery only when technically possible" rule), boundary language
  intact, no invented numeric value.
- **WebGL context loss + retry**: genuine `WEBGL_lose_context` extension call,
  under both normal and reduced motion — fallback shown, retry restores the
  canvas and (when reduced) preserves the frozen angle.
- **200% zoom**: `document.documentElement.style.zoom = 2` at 1280×800 —
  no horizontal overflow (`scrollWidth === clientWidth`), layout reflows
  cleanly, screenshot captured.

## 7. Stage 3A — deployment (static-only; Docker genuinely unavailable)

Docker Engine is not installed on this host (`docker: command not found`).
Per the mission's explicit instruction, it was **not installed silently**,
and Stage 3A container-runtime gates are `BLOCKED_EXTERNAL`. Everything
achievable without a Docker daemon was verified directly against the files:

- `docker-compose.yml` parsed as valid YAML (Python `yaml.safe_load`,
  substituting for `docker compose config` since the CLI is unavailable);
  two services (`backend`, `frontend`), correct build contexts, correct
  `NEXT_PUBLIC_API_BASE_URL`/`NEXT_PUBLIC_WS_URL` build args.
- `frontend/Dockerfile`: the only `RUN` referencing npm is `RUN npm ci`; the
  string `npm install` appears only inside an explanatory comment, never as
  a directive. Both `package.json` and `package-lock.json` are copied before
  install.
- Lockfile SHA-256: `fe872a4c639b23df5911fb78f023b15b8246749cb6c3b601dc76e58e1b3cf3b5`
  — **byte-identical** to what the prior Codex audit reported at the same
  base, and `git diff --stat` against it is empty (never touched this
  session).
- `backend/Dockerfile`: installs from `requirements.txt`, no secrets baked
  in, correct `EXPOSE 8000` / `uvicorn` entrypoint.
- `verify_jury_environment.py`: `public-env-leak` check PASSED — no backend
  environment variable name leaks into the rendered frontend copy.
- Missing-dataset fail-closed behavior confirmed directly against the real
  (non-Docker) backend — see §8; this is the same code path a container
  would run.

## 8. Stage 3B — real S14 (dataset/checkpoint genuinely absent)

Confirmed absent (not fabricated, not downloaded): `datasets/ppg-dalia/`
contains only its README; `ml/checkpoints/` contains only `.gitkeep`; no
PPG-DaLiA archive or `model_b_ppg_plus_imu_ppg_dalia.pt` checkpoint exists
anywhere reasonable on the host. **Real S14 canonical success is therefore
`BLOCKED_EXTERNAL`** — not attempted, not simulated as if it were real.

What *is* genuinely verifiable without the dataset was exercised directly
against the real, non-Docker backend, through the real production UI:

- Clicking "Load Canonical Jury Demo" against the real backend (dataset not
  configured) produced the exact, honest, fail-closed announcement:
  *"Canonical jury demo not loaded — Recorded PPG-DaLiA replay dataset is
  not configured on this backend."* — never a false success.
- Repeated 3 times rapidly: identical message each time, no request storm,
  no stale/degraded state, source identity stayed `SYNTHETIC DEMO`
  throughout (never silently switched to a fake "S14" identity).
- The Demo Control Drawer's "Simulated fault injection" panel independently
  confirms, from the real backend, that fault injection is gated to
  recorded-replay-only and is honestly reported unavailable — the frontend
  never offers a fault control it cannot honor.

This reconfirms and extends (idempotency-by-rapid-repetition) the same
missing-prerequisite path the prior Codex audit already verified.

## 9. Screen reader — explicitly deferred, not fabricated

The repository owner was asked, given the actual disruption enabling
VoiceOver would cause to their live desktop session, whether to run it now.
The owner's explicit direction: **do not enable or test VoiceOver during
this task** — defer real screen-reader acceptance until after Stages 4-7,
and record the gate honestly as not verified rather than passed. This audit
complies: `ACTUAL_SCREEN_READER_VERIFIED: NO`, no fabricated transcript, no
repeated requests. A detailed test matrix (routes, states, keyboard
sequences, expected announcements) is preserved in the manual acceptance
checklist for that future session to execute directly.

## 10. Adversarial self-review

Specifically searched for and did **not** find:

- False success announcements (the canonical-bootstrap supersession fix
  from the prior audit was re-verified structurally in the 1021-check suite
  and behaviorally via the repeat-click idempotency test in §8).
- Motion under either reduction input alone being insufficient, or removing
  one input alone re-enabling motion while the other remained active — the
  full truth table in §5 rules this out.
- Loss of user pause state across reduction toggles — explicitly tested and
  passed (§5, scenario 11).
- Stale cross-tab state — explicitly tested both directions (§5, scenario 9).
- Duplicate listeners or request storms — the 3x rapid-click idempotency
  test in §8 produced exactly one consistent message each time.
- Controlled evidence mislabeled as real — the `state-fault-source-error-CONTROLLED.png`
  filename and this document both flag it explicitly as a controlled REST
  interception, not a real backend fault; no S14 claim anywhere in this
  evidence package.
- Secrets, datasets, checkpoints, `.env` files, or dependency trees staged
  for commit (verified again before commit, see final verification report).

## 11. Known, honestly-reported limitations of this evidence package

- **`state-rebuilding`**: this application has no distinct "connecting" or
  "rebuilding" UI text for WebSocket reconnection — it is a deliberate
  binary `CONNECTED`/`DISCONNECTED` design (confirmed by source inspection;
  no "reconnect"/"rebuild" string exists in any connection-status component).
  A genuine sub-second transient DOM state was proven to exist
  programmatically (a ~150ms window where neither label matches, immediately
  after backend restart) but could not be reliably captured as a pixel
  screenshot given multi-second tool round-trip latency. The `*rebuild*.png`
  evidence slot is instead filled with the WebGL Digital Twin's genuine
  context-loss→retry "rebuild" cycle, which is a real, reproducible,
  correctly-labeled rebuild event in this codebase's own vocabulary
  (`WebglStage`'s `retry` remounts the Canvas with a fresh WebGL context).
- **`state-fault`**: the dataset-based fault-injection pipeline
  (`SimulatedFaultControl`) is honestly gated to recorded-replay-only and
  therefore unreachable without the (absent) PPG-DaLiA dataset. The legacy
  `/simulation/failure` REST endpoint exists in the backend but has zero
  frontend callers (verified by repo-wide grep) — using it directly would
  not be genuine production-UI evidence. The `*fault*.png` slot is instead
  filled with a **controlled** REST interception forcing the real,
  already-shipped `source_error` UI state (`sourceStateStatus === "error"`),
  clearly labeled `CONTROLLED` in its filename and in this document — this
  mirrors exactly how the prior Codex audit produced the same evidence.
