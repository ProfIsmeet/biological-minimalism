# VERIFICATION_LEDGER — claude/stage4-5-visual-command-deck

All commands run from `/Users/emirharunsunbul/Documents/ChatGPT/IAC-claude-stage4-5-visual-command-deck` unless noted. "Directory" below is relative to that root.

## Phase 0 — clean baseline (before any edit)

| Command | Directory | Exit | Passed | Failed | Skipped | Duration | Notes |
|---|---|---:|---:|---:|---:|---:|---|
| `npm ci` | `frontend` | 0 | — | — | — | ~6s | 452 packages, 2 pre-existing npm audit advisories (unrelated) |
| `npm run verify:monitoring` | `frontend` | 0 | 1021 + 5/5 structural | 0 | 0 | ~2s | Matches inherited baseline exactly |
| `npm run lint` | `frontend` | 0 | clean | 0 | — | ~3s | |
| `npx tsc --noEmit` | `frontend` | 0 | clean | 0 | — | ~15s | |
| `npm run build` | `frontend` | 0 | 14/14 pages | 0 | — | ~10s | |
| `python3.12 -m venv .venv312 && pip install -r requirements.txt` | `backend` | 0 | — | — | — | ~40s | Reused Python 3.12.14 from prior Stage 2-3 Homebrew install |
| `python -m pytest -q` | `backend` | 0 | 347 | 0 | 4 | 104s | Matches inherited baseline exactly |
| `python -m pytest -q -k "cors or deploy or jury"` | `backend` | 0 | 30 | 0 | 0 | 4.4s | |
| `python scripts/verify_jury_environment.py --root .` | (root) | 0 | 19 PASS | 0 FAIL | 7 WARN | ~1s | WARNs: docker absent, dataset/checkpoint env vars unset (expected pre-discovery) |
| `python scripts/verify_jury_release_evidence.py --root .` | (root) | 0 | 23 PRESENT | 0 | 1 MISSING (optional) | ~1s | 0 AMBIGUOUS, 0 EMPTY; `--hash` and `--json` modes also run, `f07_status: COMPLETE` |
| `git diff --check` | (root) | 0 | clean | — | — | — | |

## Phase 1 — Stage 2-3 remediation + real S14 acceptance

| Command | Directory | Exit | Passed | Failed | Skipped | Duration | Notes |
|---|---|---:|---:|---:|---:|---:|---|
| `unzip -l` / nested `data.zip` inspection | `datasets/ppg-dalia/raw_uci/` (anchor worktree) | 0 | — | — | — | — | Confirmed `PPG_FieldStudy/S14/S14.pkl` present inside nested zip |
| `shasum -a 256` on checkpoint | `ml/checkpoints/` (anchor worktree) | 0 | — | — | — | — | `c53a34586d2d6baf68aae4441b6c15a0f5f623f0ea70c023c7371c2dbded0e77`, 138086 bytes — exact match to expected values |
| `uvicorn app.main:app --port 8003` with `BIOMIN_PPG_DALIA_PATH`/`BIOMIN_PPG_DALIA_HR_CHECKPOINT_PATH` set | `backend` | — (long-running) | — | — | — | — | Real S14 backend session; see MASTER_HANDOFF_REPORT.md §9 for the full REST/UI trace |
| `curl` REST calls: `/data-source/replay/load`, `/play`, `/replay/fault`, `DELETE /replay/fault`, `/replay/reset`, 3x repeat `/replay/load` | `http://127.0.0.1:8003` | 200 each | — | — | — | — | Full fault→rebuilding→recovery cycle and 3x idempotent reload, all genuine |
| `npm run build` with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8003` | `frontend` | 0 | 14/14 pages | 0 | — | ~10s | Rebuilt to target the real-S14 backend |
| Browser verification via Chrome DevTools MCP | `/mission-overview`, `/live-monitoring` | — | — | — | — | — | Real S14 nominal/fault/rebuilding/recovered states and corrected synthetic-demo recovery all visually confirmed; see evidence index |
| `python scripts/verify_jury_release_evidence.py --root .` (after evidence reorganization) | (root) | 0 | 23 PRESENT | 0 | 1 MISSING (optional) | ~1s | 0 AMBIGUOUS, 0 EMPTY |
| `git diff --check` | (root) | 0 | clean | — | — | — | |

## Phase 2 — Stage 4/V1 fixes

| Command | Directory | Exit | Passed | Failed | Skipped | Duration | Notes |
|---|---|---:|---:|---:|---:|---:|---|
| `npm run lint` (after MetricTile/AppHeader/PresentationHeader/ExperimentalDispositionOrbit/mission-timeline/settings edits) | `frontend` | 0 | clean | 0 | — | ~3s | |
| `npx tsc --noEmit` | `frontend` | 0 | clean | 0 | — | ~15s | |
| `npm run verify:monitoring` (first run, before verifier path fix) | `frontend` | 2 | 1021 (state) | 1 (`timeline F-03` string checks) | — | ~2s | **Regression found**: `timelineSource`/`settingsSource` checks failed because the checked strings moved to the new `*Client.tsx` files |
| `npm run verify:monitoring` (after fixing `verify-monitoring-state.ts` + `verify-reduced-motion-unification.mjs` path literals) | `frontend` | 0 | 1021 + 5/5 | 0 | 0 | ~2s | Regression fixed |
| `NEXT_PUBLIC_API_BASE_URL=http://localhost:8003 npm run build` | `frontend` | 0 | 14/14 pages | 0 | — | ~5s | |
| Browser verification: `/ai-insights`, `/mission-timeline`, `/settings` headers; `/research/experimental` orbit sizing; replay-mode MetricTile overlap | Chrome DevTools MCP | — | — | — | — | — | All 4 findings visually confirmed fixed |
| `git diff --check` | (root) | 0 | clean | — | — | — | |

## Phase 3 — Stage 5/V2 verification (no source changes)

| Command | Directory | Exit | Passed | Failed | Skipped | Duration | Notes |
|---|---|---:|---:|---:|---:|---:|---|
| Live `evaluate_script` reduce-motion toggle regression test | `/settings` | — | pass | — | — | — | `aria-checked`, `reduce-motion` class, and `localStorage["biomin:reduce-motion"]` all correct in both directions after the Stage 4 `SettingsClient.tsx` extraction |
| Mobile "More" dialog open/Escape/focus-return regression test | `/mission-overview` @ 390x844 | — | pass | — | — | — | Accessibility-tree snapshots before/after confirm no regression from the `AppHeader` routing change |
| Viewport overflow checks: 1920x1080, 1440x900, 1024x768 | `/mission-overview` | — | pass (all 3) | — | — | — | `scrollWidth === clientWidth` at every size |
| `getBoundingClientRect()` on `ExperimentalDispositionOrbit`'s `<svg>` | `/research/experimental` (fresh tab, no emulation) | — | pass | — | — | — | 300×300, confirming the Stage 4 fix holds independent of any test-only viewport override |

## Final clean-tree verification (before final commit)

| Command | Directory | Exit | Passed | Failed | Skipped | Duration | Notes |
|---|---|---:|---:|---:|---:|---:|---|
| `npm run verify:monitoring` | `frontend` | 0 | 1021 + 5/5 | 0 | 0 | ~2s | |
| `npm run lint` | `frontend` | 0 | clean | 0 | — | ~3s | |
| `npx tsc --noEmit` | `frontend` | 0 | clean | 0 | — | ~15s | |
| `NEXT_PUBLIC_API_BASE_URL=http://localhost:8003 npm run build` | `frontend` | 0 | 14/14 pages | 0 | — | ~5s | |
| `python -m pytest -q backend` (after `verify_jury_release_evidence.py`'s `audit-main` glob was briefly narrowed) | `backend` | 1 | 345 | **2** | 4 | 8s | **Regression found**: `test_evidence_verifier_detects_present_empty_ambiguous` and `test_evidence_verifier_hash_is_optional_and_deterministic` both depend on `audit-main` staying a generic `**/AUDIT.md` wildcard |
| `git checkout -- scripts/verify_jury_release_evidence.py` | (root) | 0 | — | — | — | — | Reverted the narrowing; restored the original wildcard pattern |
| `python -m pytest -q backend` (after revert) | `backend` | 0 | 347 | 0 | 4 | 7.2s | Regression fixed; matches baseline exactly |
| `python scripts/verify_jury_environment.py --root .` | (root) | 0 | 19 PASS | 0 FAIL | 7 WARN | ~1s | Unchanged from baseline |
| `python scripts/verify_jury_release_evidence.py --root .` | (root) | 0 | 22 PRESENT | 0 EMPTY | 1 MISSING (optional), **1 AMBIGUOUS** (`audit-main`) | ~1s | The one intentionally-accepted, documented ambiguity — see `docs/JURY_RELEASE_EVIDENCE_MANIFEST.md`'s "Known ambiguity" note and AUDIT.md §4 |
| `git diff --check` | (root) | 0 | clean | — | — | — | |

## Summary of regressions found and fixed during this mission

Two genuine regressions were introduced and caught by this mission's own re-verification discipline, both fixed without weakening any test:

1. Moving `mission-timeline`/`settings` interactive bodies into `*Client.tsx` broke two hardcoded source-string checks in `verify-monitoring-state.ts` and one in `verify-reduced-motion-unification.mjs` — fixed by updating the checked file path to the new (correct) location of the same real content.
2. Narrowing the release-evidence verifier's `audit-main` glob to resolve an evidence-folder collision broke two backend unit tests that depend on it staying generic — fixed by reverting the verifier change and instead documenting the resulting (correct, honest) `AMBIGUOUS` result.

No test assertion was deleted, weakened, or replaced with a source-string check to make it pass. No regression was left silently unresolved.
