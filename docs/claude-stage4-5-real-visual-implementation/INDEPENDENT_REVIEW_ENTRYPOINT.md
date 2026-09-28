# INDEPENDENT_REVIEW_ENTRYPOINT — claude/stage4-5-real-visual-implementation

IMPLEMENTATION_CHECKPOINT_SHA: 6d169c4abe6d68a7758f515bad5df39b8d851727
REPORT_COMMIT: this commit — resolve with `git rev-parse HEAD`

This document is written for an independent reviewer (Codex or otherwise) who
has not read this run's chat transcript. Read this file first.

## 1. What this branch claims, in one paragraph

Starting from `origin/claude/stage4-5-visual-command-deck` @
`7afe57114ad6f7537b73f17683f7ecd733606730`, this branch makes real code and
evidence changes — not just new reports — to fix 10 previously-confirmed
defects (C-01 through C-10, see `STATUS.md`) in the Stage 4 visual system and
Stage 5 Mission Overview command deck, re-captures three pieces of real-S14
evidence whose metadata did not match their own pixels, fixes the
release-evidence verifier so it exits 0, and adds regression tests tied to
each fixed defect.

## 2. Fastest way to check this isn't just report theater

```bash
git log --oneline 7afe571..6d169c4      # 4 non-doc commits, real diffs
git diff --stat 7afe571..6d169c4        # 20 files changed outside docs/
```

If that diff is small or docs-only, treat every claim below as suspect. It is
not: 616 insertions / 145 deletions across 20 non-doc files.

## 3. Re-run the automated verification yourself

```bash
cd frontend && npm ci && npm run lint && npx tsc --noEmit && npm run verify:monitoring && npm run build
cd ../backend && python3.12 -m venv .venv312 && .venv312/bin/pip install -r requirements.txt && .venv312/bin/python -m pytest -q
cd .. && python3 scripts/verify_jury_release_evidence.py --root .   # must exit 0
```

Expected: lint/tsc clean, `verify:monitoring` 1042/1042, build succeeds,
pytest 348 passed / 4 skipped, evidence verifier exit 0. See
`VERIFICATION_LEDGER.md` for the exact output shape.

## 4. Re-verify the three re-captured evidence images yourself

Open these three files directly (do not trust the JSON description alone —
that is exactly how C-06 happened the first time):

- `frontend/qa-screenshots/claude-stage4-5-real-visual-implementation/state-fault-real-s14-packet-loss.png` — must show the full text "PPG · packet loss · severity 0.9" with no ellipsis.
- `.../state-rebuilding-real-s14-hr-warmup-v2.png` — must show "Unavailable" / "Model is warming up" and **no numeric bpm figure anywhere**.
- `.../state-recovered-real-s14-v2.png` — must show a numeric bpm figure and "Model available"; the exact number (96.3) is documented in `EVIDENCE_INDEX.json` and should match what you see.

## 5. Reproduce the C-06 fix yourself (optional, ~30s)

```bash
curl -s -X POST http://127.0.0.1:8004/data-source/replay/fault \
  -H "Content-Type: application/json" \
  -d '{"fault_type":"packet_loss","target":"ppg","severity":0.9,"seed":1}'
sleep 3
curl -s -X DELETE http://127.0.0.1:8004/data-source/replay/fault
# Screenshot /mission-overview within the next ~2-9 seconds: HR panel should
# read "Unavailable" / "Model is warming up" with no numeric value, then
# transition to a numeric bpm + "Model available" roughly 8-10s after clear.
```
(Requires the isolated backend running with the real S14 dataset/checkpoint
configured — see `RUN_STATE.md` for the exact env vars used.)

## 6. Where to look for each defect's fix

See `STATUS.md`'s table for the one-line status + evidence pointer per C-01
through C-10, and `CHANGE_LEDGER.md` for the exact file/commit that fixed each
one. `MASTER_HANDOFF_REPORT.md` has the full narrative if you want the
reasoning, not just the outcome.

## 7. What NOT to expect

- No change to `backend/app/ml/` model code, thresholds, or the S14 dataset —
  this run was scoped to presentation only, per the mission's explicit
  constraint. Confirm with `git diff --stat 7afe571..6d169c4 -- backend/app`
  (should be empty except the test file listed in `CHANGE_LEDGER.md`).
- A handful of sub-12px labels remain in components exclusive to routes this
  mission did not target (see `STATUS.md`'s "What is explicitly NOT claimed").
  Do not treat this as a hidden C-01 regression — it is disclosed.

## 8. If you disagree with something here

Say so specifically, citing the file/line and the concrete pixel or behavior
you observed — the same standard this run held the prior stage4-5-visual-
command-deck submission to.
