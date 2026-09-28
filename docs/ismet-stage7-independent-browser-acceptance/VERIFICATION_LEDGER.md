# Verification Ledger — Stage 7 Independent Browser Acceptance

Every automated command run during this audit, with exact results, in chronological
order of the final re-verification pass (baseline reproduction at the source tip
happened earlier in the session and is summarized where it differs from final).

## Environment

- Repo root: this worktree (path omitted — machine-specific; see the branch/SHA
  identity below for reproducibility instead).
- Branch: `ismet/stage7-independent-browser-acceptance`, created from
  `origin/codex/stage7-digital-twin-integration` @ `c01f66f43a76c953996d811f3e846f3ac7d9a09c`
  (verified exact match — no `STAGE7_AUDIT_BLOCKED_SOURCE_SHA_MISMATCH`).
- Node: v24.19.0. npm: 11.17.0.
- Python: 3.13.0 (repo-local venv at `backend/.venv`, created fresh for this
  worktree — venvs are not shared across git worktrees).
- Browser: system-installed Chrome, driven via `playwright-core@1.63.0` over CDP
  (temporary devDependency, `npm install --no-save`, fully reverted — `node_modules`
  and any trace removed — before final commit; never added to `package.json`/
  `package-lock.json`).

## Baseline reproduction (at source tip `c01f66f`, before any correction)

| Command | Result |
|---|---|
| `npm run verify:monitoring` | `verify-monitoring-state: 1085/1085 passed, 0 failed`; all 6 downstream structural guards PASSED |
| `npm run lint` | exit 0, no output |
| `npx tsc --noEmit --incremental false` | exit 0, no output |
| `npm run build` | 14/14 static pages, exit 0 |
| `backend/.venv/Scripts/python -m pytest -q` | `351 passed, 4 skipped, 1 warning` |
| `python scripts/verify_jury_release_evidence.py --root . --hash` | `PRESENT=15 MISSING=1 EMPTY=0 AMBIGUOUS=8`, exit code **2** (`F-07 status: INCOMPLETE`) — see note below |
| `git diff --check` | exit 0 (clean tree at this point) |

**Note on the evidence verifier's exit code:** an earlier note taken during this
session recorded this command's exit code as 0; that was an error in this session's
own documentation, not a change in the script's actual behavior — `required_incomplete()`
in `scripts/verify_jury_release_evidence.py` treats any `AMBIGUOUS` required entry as
not-`PRESENT`, so exit code 2 is what this command has always returned for this
pre-existing condition, confirmed both before and after this audit's own changes (see
`ROUTE_COUNT_RECONCILIATION.md` and `FINDING_LEDGER.md` for the historical trace
proving the condition predates Stage 7).

## Final re-verification (post-correction, post-cleanup, at implementation checkpoint `e513327`)

| Command | Result |
|---|---|
| `npm run verify:monitoring` | `verify-monitoring-state: 1091/1091 passed, 0 failed`; all 6 downstream structural guards PASSED |
| `npm run lint` | exit 0, no output |
| `npx tsc --noEmit --incremental false` | exit 0, no output |
| `npm run build` | 14/14 static pages, exit 0, identical route table to baseline |
| `backend/.venv/Scripts/python -m pytest -q` | `351 passed, 4 skipped, 1 warning` — unchanged, backend untouched by this audit |
| `python scripts/verify_jury_release_evidence.py --root . --hash` | `PRESENT=15 MISSING=1 EMPTY=0 AMBIGUOUS=8`, exit code 2 — identical to baseline, confirmed pre-existing and not a regression introduced by this audit |
| `git diff --check` | exit 0 |

Monitoring count delta: 1085 → 1091 (+6), exactly matching the 6 new assertions added
in the regression-tests commit (`e513327`) — no other count moved, confirming the
existing 1085 checks remain intact and nothing was weakened.

## Runtime/browser verification (this audit's own, real-browser evidence)

| Gate | Result | Report |
|---|---|---|
| WebGL supported (baseline) | PASS | `WEBGL_RUNTIME_REVIEW.md` |
| Gate C — WebGL unsupported | PASS | `WEBGL_RUNTIME_REVIEW.md` |
| Gate D — WebGL context loss + retry (×3 cycles) | PASS | `WEBGL_RUNTIME_REVIEW.md` |
| Gate B — genuine 200% zoom | BLOCKED_EXTERNAL | `RESPONSIVE_AND_ZOOM_MATRIX.md` |
| 20× mount/unmount | PASS | `RESOURCE_LIFECYCLE_REVIEW.md` |
| Repeated resize | PASS | `RESOURCE_LIFECYCLE_REVIEW.md` |
| Hidden-tab visibilitychange | PASS | `RESOURCE_LIFECYCLE_REVIEW.md` |
| Reduced-motion app path + cross-route + cross-tab | PASS | `REDUCED_MOTION_REVIEW.md` |
| Reduced-motion OS path | NOT_RUN | `REDUCED_MOTION_REVIEW.md` |
| Keyboard/accessibility DOM review | PASS | `ACCESSIBILITY_AND_KEYBOARD_REVIEW.md` |
| Desktop/tablet/mobile responsive matrix | PASS | `RESPONSIVE_AND_ZOOM_MATRIX.md` |
| Navigation matrix | PASS | `RESPONSIVE_AND_ZOOM_MATRIX.md` |

## Tooling artifacts encountered and resolved (not app defects)

- `npm run build` run against a still-live `next dev` server corrupted that server's
  webpack module cache (`__webpack_modules__[moduleId] is not a function`); resolved
  by killing the dev server, `rm -rf .next`, and restarting fresh. Encountered twice
  during this session's iterative work; both times correctly diagnosed as a
  build/dev-cache interaction, not a product regression, before proceeding.
- `playwright-core`'s `page.accessibility.snapshot()` was not exposed as expected in
  version 1.63.0; substituted with direct DOM/`getComputedStyle`/`getBoundingClientRect`
  queries for the accessibility review (disclosed in `ACCESSIBILITY_AND_KEYBOARD_REVIEW.md`).
- `browser.newPage()` in this Playwright version creates an isolated browser context
  per call (separate storage), initially producing a false negative in the cross-tab
  reduced-motion test; corrected to use `browser.newContext()` + `context.newPage()`
  for both tabs before trusting the result (disclosed in `REDUCED_MOTION_REVIEW.md`).

## Services

Dev server started on port 3103 (isolated, non-conflicting with any other
session-owned port on this machine) for the runtime test passes; confirmed stopped
(`taskkill`, then `netstat` re-checked with no `LISTENING` entry remaining) before
final commit. No other task-started service was left running.
