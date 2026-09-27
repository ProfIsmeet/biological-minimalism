# INDEPENDENT_REVIEW_ENTRYPOINT — claude/stage4-5-visual-command-deck

**Do not trust this report without reproducing it.** Every claim below has a
command or action you can run yourself. Where a claim depends on an
environment-specific asset (the PPG-DaLiA dataset/checkpoint), that is
called out explicitly so you know which claims are portable and which are
conditional.

## Target

- Repository: `https://github.com/ProfIsmeet/biological-minimalism.git`
- Branch: `claude/stage4-5-visual-command-deck`
- Base SHA: `98b73c168f95c91e7f5f5e8e4beef9ca79136d53` (`claude/stage2-3-final-acceptance`)
- Final SHA: see `STATUS.md` (updated at push time) and `git log --oneline -5` on the branch

## Fetch and checkout

```bash
git clone https://github.com/ProfIsmeet/biological-minimalism.git
cd biological-minimalism
git fetch origin
git checkout claude/stage4-5-visual-command-deck
git log --oneline -5   # expect: final docs commit, ec655e9, 6ea2d05, 98b73c1, ...
```

## Report reading order

1. This file.
2. `docs/claude-stage4-5-visual-command-deck/STATUS.md` — current state, one page.
3. `docs/claude-stage4-5-visual-command-deck/MASTER_HANDOFF_REPORT.md` — full narrative, all 28 required sections.
4. `docs/claude-stage4-5-visual-command-deck/CHANGE_LEDGER.md` — every file touched.
5. `docs/claude-stage4-5-visual-command-deck/VERIFICATION_LEDGER.md` — every command run, including two self-caught regressions.
6. `frontend/qa-screenshots/claude-stage4-5-visual-command-deck/AUDIT.md` — the Stage 4 and Stage 5 hostile-audit findings, most load-bearing for design review.
7. `frontend/qa-screenshots/claude-stage2-3-final-acceptance/AUDIT.md` section 12 — the Stage 2-3 re-audit corrections.
8. `docs/claude-stage4-5-visual-command-deck/RUN_STATE.md` — the durable execution log, useful for chronology.

## Highest-risk files to review directly

- `frontend/src/components/layout/AppHeader.tsx` / `PresentationHeader.tsx` — the route-cohesion fix; verify no route was accidentally left on the legacy `TopBar`.
- `frontend/src/components/ui/MetricTile.tsx` — verify the 6-character heuristic doesn't clip a legitimate short-but-important value elsewhere in the app (grep all `MetricTile` usages — there is currently exactly one, in `PrimaryVitalsPanel.tsx`).
- `frontend/scripts/verify-monitoring-state.ts` and `verify-reduced-motion-unification.mjs` — the two path-literal fixes; confirm they now point at real, existing files with the expected content.
- `scripts/verify_jury_release_evidence.py` — confirm this file is byte-identical to the base commit (it was edited and then explicitly reverted; verify with `git diff 98b73c168f95c91e7f5f5e8e4beef9ca79136d53 -- scripts/verify_jury_release_evidence.py`, expect empty output).
- `frontend/qa-screenshots/claude-stage2-3-final-acceptance/evidence-index.json` — cross-check every `sha256` field against the actual file with `shasum -a 256`.

## Highest-risk behaviors to reproduce

1. **Real S14 acceptance.** This is the mission's largest claim and is conditional on assets not present in the git history:
   - Locate (or obtain, per `docs/DATASET_REPLAY.md`) a PPG-DaLiA archive and the `model_b_ppg_plus_imu_ppg_dalia.pt` checkpoint (expected SHA-256 `c53a34586d2d6baf68aae4441b6c15a0f5f623f0ea70c023c7371c2dbded0e77`, 138086 bytes).
   - `export BIOMIN_PPG_DALIA_PATH=<PPG_DALIA_ARCHIVE_PATH>`
   - `export BIOMIN_PPG_DALIA_HR_CHECKPOINT_PATH=<PPG_DALIA_CHECKPOINT_PATH>`
   - `cd backend && python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
   - `export BIOMIN_ALLOWED_ORIGINS='["http://localhost:3003"]' && uvicorn app.main:app --port 8003`
   - `curl -X POST http://127.0.0.1:8003/data-source/replay/load -d '{"subject_id":"S14"}' -H "Content-Type: application/json"` — expect `dataset_name: "PPG-DaLiA"`, `duration_seconds: 8958.0`.
   - `curl -X POST http://127.0.0.1:8003/data-source/replay/play`, wait 9+ seconds, `curl http://127.0.0.1:8003/metrics/live` — expect a `heart_rate_prediction` object with `evidence_level: "AI_ESTIMATED"` and `provenance.checkpoint_sha256` matching the hash above.
   - `curl -X POST http://127.0.0.1:8003/data-source/replay/fault -d '{"fault_type":"packet_loss","target":"ppg","severity":0.9,"seed":2026}' -H "Content-Type: application/json"`, re-check `/metrics/live` — expect `heart_rate_prediction: null`, `heart_rate_inference.status: "error"`.
   - `curl -X DELETE http://127.0.0.1:8003/data-source/replay/fault`, re-check immediately — expect `heart_rate_inference.status: "warming_up"`; wait 9s and re-check — expect a fresh `AI_ESTIMATED` prediction.
2. **The 4 Stage 4 defects, before/after.** Check out `98b73c168f95c91e7f5f5e8e4beef9ca79136d53` in a scratch worktree, build, and visit `/ai-insights` — expect to see "Mission Control / Earth Orbit" in the header (not present on this branch). Then check out this branch and repeat — expect "Biological Minimalism / AI INSIGHTS".
3. **The two self-caught regressions.** `git show ec655e9 -- frontend/scripts/verify-monitoring-state.ts` and `verify-reduced-motion-unification.mjs` show the path-literal fixes; `git diff 98b73c168f95c91e7f5f5e8e4beef9ca79136d53 -- scripts/verify_jury_release_evidence.py` should be empty (confirming the second regression's fix — a revert — left no trace in that file).

## Portable environment placeholders

Never write a real absolute path from this host into a committed file. Use:

- `<REPO_ROOT>` for the repository checkout root.
- `<PPG_DALIA_ARCHIVE_PATH>` / `<PPG_DALIA_CHECKPOINT_PATH>` for the two dataset/checkpoint env vars.

## Verification commands and expected counts

| Command | Directory | Expected |
|---|---|---|
| `npm ci && npm run verify:monitoring` | `frontend` | `1021/1021 passed`, `5/5` structural verifiers PASSED |
| `npm run lint` | `frontend` | clean |
| `npx tsc --noEmit` | `frontend` | clean |
| `npm run build` | `frontend` | `14/14` pages |
| `python -m pytest -q` (Python 3.12, `pip install -r backend/requirements.txt`) | `backend` | `347 passed, 4 skipped` |
| `python -m pytest -q -k "cors or deploy or jury"` | `backend` | `30 passed` |
| `python scripts/verify_jury_environment.py --root .` | repo root | `19 PASS / 7 WARN / 0 FAIL` (WARNs: Docker absent, dataset/checkpoint env vars unset) |
| `python scripts/verify_jury_release_evidence.py --root .` | repo root | `22 PRESENT / 1 MISSING (optional) / 0 EMPTY / 1 AMBIGUOUS` (`audit-main` — see `docs/JURY_RELEASE_EVIDENCE_MANIFEST.md`) |
| `git diff --check` | repo root | clean |

## Runtime ports used by this task (isolated; reuse any free ports)

- Frontend: `3003`
- Backend: `8003`

## Evidence directories

- `frontend/qa-screenshots/claude-stage2-3-final-acceptance/` — Stage 2-3 evidence, corrected this session.
- `frontend/qa-screenshots/claude-stage4-5-visual-command-deck/` — Stage 4/5 evidence.
- `docs/claude-stage4-5-visual-command-deck/superseded-stage2-3-evidence/` — two preserved-incorrect screenshots, kept for the audit trail only, never part of the release bundle.

## External blockers

- Docker Engine is not installed on the host this mission ran on. All Docker gates are `BLOCKED_EXTERNAL`. If Docker is available in your review environment, run the full Stage 3A container-runtime matrix yourself — it was not possible to do so here.
- Real S14 acceptance depends on assets (dataset archive + checkpoint) that are git-ignored and were found only on this specific host's filesystem, outside the repository. They are not committed anywhere in this branch. If you don't have them, every real-S14 claim above is unreproducible on your machine — that is expected, not a defect.
- Actual OS screen-reader (VoiceOver/NVDA/Narrator) verification is explicitly deferred by the repository owner until after Stages 6-7. Do not treat its absence as an outstanding Stage 4/5 defect.

## Prioritized adversarial review checklist

1. Reproduce the real-S14 trace above if you have the assets; if you don't, verify the code paths (`backend/app/data/ppg_dalia.py`, `backend/app/ml/ppg_dalia_hr.py`) are internally consistent with the claimed provenance/hash-check behavior by reading them.
2. Grep the entire diff (`git diff 98b73c168f95c91e7f5f5e8e4beef9ca79136d53..HEAD`) for any scientific constant, calculation, or availability-semantic change — there should be none outside the two verifier path-literal fixes and the one reverted verifier edit.
3. Visually re-inspect every screenshot in both evidence directories at full resolution — do not trust a filename or an SHA-256 alone as proof of content.
4. Re-run the 200% zoom evidence's claim independently: open `/mission-overview` at 1280x800, then apply a genuine browser zoom (not CSS `zoom`) to 200%, and confirm the layout matches `mission-overview-200-zoom-real-devicemetrics.png`.
5. Check that `main` and `claude/stage2-3-final-acceptance` are unchanged: `git log --oneline -1 origin/main` and `git log --oneline -1 origin/claude/stage2-3-final-acceptance` should show the same SHAs recorded in `MASTER_HANDOFF_REPORT.md` section 2.
6. Decide independently whether the V2-01 finding (Inference Integrity Orbit + Hex Flow reviewed, not consolidated) was the right call, or whether you'd consolidate them — this is a judgment call this mission documented rather than resolved unilaterally.
7. Confirm `READY_TO_MERGE: NO` in the final YAML is honored — do not merge this branch as part of your review.
