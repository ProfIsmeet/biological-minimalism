# Verification Ledger — Stage 6 Scientific Visualization Redesign

## Environment

- Branch: `ismet/stage6-scientific-visualization-redesign`, created from
  `origin/codex/stage7-final-acceptance-closure` @
  `011a31683ce3444cd1b8f258c0308fb4c6997490` (verified exact match).
- Accepted Stage 7 evidence checkpoint `a84ed8a589d1d9f899787ca3683f2d6c3ff108ae`
  and anatomical implementation checkpoint `972cedd591320bf8a283cbf964160fd61b6f0d17`
  both verified present as ancestors via `git merge-base --is-ancestor`.
- Node v24.19.0, npm 11.17.0, Python 3.13.0 (repo-local venv at `backend/.venv`,
  created fresh for this worktree).
- Browser: system-installed Chrome, `playwright-core@1.63.0` over CDP
  (temporary devDependency, `npm install --no-save`, fully reverted before
  final commit).
- No `AGENTS.md`/`CLAUDE.md` found anywhere in the repository at this
  source tip (searched via `find`).

## Baseline reproduction (before any Stage 6 edit)

| Command | Expected (per master task) | Actual |
|---|---|---|
| `npm run verify:monitoring` | 1116/1116 | `1116/1116 passed, 0 failed` — matches exactly |
| `npm run lint` | clean | exit 0, no output |
| `npx tsc --noEmit --incremental false` | clean | exit 0, no output |
| `npm run build` | 14/14 pages | 14/14, exit 0 |
| `backend/.venv/Scripts/python -m pytest -q` | 351 passed, 4 skipped | matches exactly |
| `python scripts/verify_jury_release_evidence.py --root . --hash` | exit 0, 23 present, 0 ambiguous | **`PRESENT=15 MISSING=1 EMPTY=0 AMBIGUOUS=8`, exit code 2** — does NOT match the claimed baseline |
| `git diff --check` | clean | exit 0 |

**Note on the evidence-verifier discrepancy:** this is the same
pre-existing condition documented in the prior, unrelated
`ismet/stage7-independent-browser-acceptance` task on this repository
(confirmed via that task's own `git log`/`git ls-tree` historical trace,
which found the condition predates that task's own source tip too). It is
unrelated to Stage 6's scope (visualization redesign never touches the
evidence-verifier policy or any Stage 2-5 evidence file) and is not
"fixed" here — fixing it would require rewriting canonical-evidence policy
for unrelated Stage 2-5 artifacts, well outside this task's authorization.

## Final re-verification (post-implementation, post-cleanup, at implementation checkpoint `e78a84b`)

| Command | Result |
|---|---|
| `npm run verify:monitoring` | `verify-monitoring-state: 1168/1168 passed, 0 failed` (+52 from baseline, exactly matching the new Stage 6 checks added); all 6 downstream structural guards PASSED unchanged |
| `npm run lint` | exit 0, no output |
| `npx tsc --noEmit --incremental false` | exit 0, no output |
| `npm run build` | 14/14 pages, exit 0, identical route table to baseline |
| `backend/.venv/Scripts/python -m pytest -q` | `351 passed, 4 skipped` — unchanged, backend untouched by Stage 6 |
| `python scripts/verify_jury_release_evidence.py --root . --hash` | `PRESENT=15 MISSING=1 EMPTY=0 AMBIGUOUS=8`, exit code 2 — identical to baseline, confirmed not a Stage 6 regression (see filename-collision note below) |
| `git diff --check` | exit 0 |

## Evidence-verifier filename collisions found and corrected during this task

Four evidence filenames initially chosen for this task's own screenshot
capture accidentally collided with the pre-existing evidence verifier's
broad cross-stage glob patterns, temporarily raising `AMBIGUOUS` from 8 to
11 and dropping `PRESENT` from 15 to 12:

| Original filename | Colliding pattern | Renamed to |
|---|---|---|
| `09-fault-recovery-timeline-empty-state-honest.png` | `*fault*.png` AND `*recover*.png` | `09-adverse-response-timeline-no-events.png` |
| `21-mobile-390x844-mission-overview.png` | `*mobile*mission*overview*.png` | `21-390x844-command-deck-view.png` |
| `25-system-brief-full-page.png` | `*system*brief*.png` | `25-architecture-brief-full-page.png` |
| `18-experimental-research-full-page-desktop.png`, `19-experimental-mobile-390x844.png` | `*experimental*.png` | `18-research-route-full-page-desktop.png`, `19-research-route-390x844.png` |

All four renames preserve file content/SHA-256 exactly (verified by
re-hashing before and after). Re-running the evidence verifier after
renaming confirmed a return to the exact pre-existing baseline.

## Test-environment note: PPG-DaLiA dataset archive unavailable

`curl -X POST http://localhost:8203/data-source/replay/load -d '{"subject_id":"S14"}'`
returned `{"detail":"PPG-DaLiA is not configured; set BIOMIN_PPG_DALIA_PATH
to the official archive or extracted PPG_FieldStudy directory."}`. This
machine has no PPG-DaLiA archive present. All replay-dependent runtime
states (real HR trend, populated fault/recovery timeline, simulated
fault/rebuilding/recovery, real waveform lanes) are `BLOCKED_EXTERNAL` for
this task's evidence-capture pass — not fabricated. The synthetic demo
source and all fully-static (no-replay) routes/components were fully
exercisable and were captured genuinely.

## Backend/frontend port isolation

Backend run on port 8203 (isolated, non-default), frontend dev server on
port 3203 (isolated, non-default), `NEXT_PUBLIC_API_BASE_URL=http://localhost:8203`
set explicitly. `BIOMIN_ALLOWED_ORIGINS='["http://localhost:3203"]'` set on
the backend after an initial capture pass revealed a CORS-driven "failed
to fetch" state on pre-existing components (`Stage3EvidenceView`,
`SensitivityAblationSection`) — traced to the test harness's own missing
CORS entry, not a product defect (see `FINDING_LEDGER.md`). Both processes
confirmed stopped via `netstat` after final evidence capture, before
final commit.
