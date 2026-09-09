# Integration Readiness Contract — Stage 2-4 Science Handoff

**Purpose:** the exact, literal sequence to follow when Ismet's science-completion sprint produces
a real manifest. This is not guidance to interpret — it is a checklist to execute in order. Do not
skip, reorder, or improvise steps. Stop and get Emir's explicit sign-off wherever marked **STOP**.

**Preconditions before starting this sequence at all:** Emir has explicitly instructed integration
to begin (this contract, on its own, is not authorization — see governing prompt's closing
instruction: "Do not proceed into actual science integration without Emir's explicit instruction").

---

## Step 1 — Verify Ismet's final SHA

```bash
git fetch origin
git log --oneline -5 origin/<ismet-science-branch-name>
git rev-parse origin/<ismet-science-branch-name>
```
Record the exact SHA in chat before touching anything. Confirm with Emir which branch is the
final, frozen one (there may be several in-progress branches; do not guess).

## Step 2 — Verify the handoff manifest exists and is well-formed

Expected files (per governing prompt §8, not yet present as of this contract's writing):
- `results/stage2_4_science_completion_manifest.json` (machine-readable)
- `docs/ISMET_STAGE2_4_SCIENCE_COMPLETION_HANDOFF_TO_CLAUDE.md` (human-readable)

```bash
cd backend
.venv/bin/python -c "
from pathlib import Path
from app.research.future_science_ingestion import load_and_validate_manifest
manifest = load_and_validate_manifest(Path('../results/stage2_4_science_completion_manifest.json'))
print(f'OK: {len(manifest.entries)} entries, schema_version={manifest.schema_version}')
for e in manifest.entries:
    print(f'  {e.experiment_id}: {e.completion_state.value} / {e.replication_class.value}')
"
```
If this raises `ManifestValidationError`, **STOP**. Report the exact `error_code` and `message` to
Emir. Do not hand-patch the manifest to make it pass — send it back to Ismet, or get Emir's
explicit sign-off on a schema change (see Step 2a).

**Step 2a (only if the manifest doesn't fit the schema):** the schema
(`backend/app/schemas/experiment_manifest.py`) was designed against known needs as of Phase 2-4; a
real manifest may need a field the schema doesn't have. If so: extend the schema additively
(new optional fields with defaults, matching this repo's `StrictModel`/enum conventions), do NOT
loosen `extra="forbid"` or make an existing required field optional to force a fit. Re-run every
test in `backend/tests/test_future_science_ingestion.py`, `test_future_science_consumer_guards.py`,
and `test_phase4_integration_dry_run.py` after any schema change, before proceeding.

## Step 3 — Inspect scientific status per entry

For every entry printed in Step 2, before writing anything, answer explicitly (in chat, to Emir):
- Is `completion_state` what you expected for this experiment (not silently downgraded/upgraded)?
- Is `replication_class` correct — run `assert_replication_claim_is_plausible` against every
  declared `EXTERNAL_REPLICATION` entry paired with its primary counterpart; any
  `SUSPICIOUS_REPLICATION_CLAIM` raised here is a **STOP** condition requiring Ismet clarification.
- Does `metric.directionality` match this repo's `KNOWN_METRIC_DIRECTIONS` registry
  (`backend/app/research/future_science_ingestion.py`) for every metric name already known? A
  mismatch already raises `CONFLICTING_METRIC_DIRECTION` in Step 2 — if it did, resolve with Ismet
  before proceeding, don't override.
- Does `provenance.dataset_version`/`protocol_version` correctly distinguish any V1/V2-style
  legs? Run `forbid_mixed_protocol_derivation` pairwise across any entries sharing a `dataset` to
  confirm no two are silently compatible when they shouldn't be, and vice versa.

**STOP and report to Emir** before Step 4 with a plain-language summary of every entry's status.

## Step 4 — Controlled merge/cherry-pick strategy

- Create `stage2-4-controlled-integration` from the current tip of
  `stage2-4-claude-integration-prep` (this branch, `origin/stage2-4-claude-integration-prep`).
- Do **not** merge Ismet's science branch wholesale. The manifest (Step 2) is the interface — the
  training/eval code that produced it stays on Ismet's branch unless Emir explicitly asks for it
  to be pulled in too (e.g. for reproducibility archival).
- If Emir does want Ismet's producing scripts merged: use `git merge --no-ff <ismet-branch>` only
  after confirming zero file overlap via `git merge-tree` dry run (the pattern already used
  successfully for the Stage 1A H1/H2 merge, see `docs/STAGE1A_POST_REMEDIATION_INTEGRATION_REPORT.md`).

## Step 5 — Run the ingestion validator against the real manifest

Already done in Step 2 as a syntax/semantics check. Now run it as part of the actual test suite:
```bash
cd backend && .venv/bin/python -m pytest -q tests/test_future_science_ingestion.py tests/test_future_science_consumer_guards.py tests/test_phase4_integration_dry_run.py
```
All must still pass (they test the *pipeline*, not the specific manifest, so they should be
unaffected by a real manifest's arrival — if any fail, something in the manifest triggered an edge
case these tests didn't anticipate; **STOP** and add a new adversarial test capturing it before
proceeding).

## Step 6 — Regenerate canonical science artifacts (only if Emir explicitly authorizes promoting entries to canonical)

This step is **out of scope for the software/integration-prep track** — canonical science artifact
generation is Ismet's/Emir's call, not something this contract automates. If authorized:
- Confirm which entries have `completion_state == COMPLETE` and are cleared for promotion
  (`assert_promotable_to_headline` must not raise for any entry being promoted).
- Any new canonical `results/*.json` file must get its own builder script under `ml/` (matching
  the existing convention — every canonical JSON in this repo has a `ml/build_*.py` source) rather
  than being hand-written.
- Regenerate `results/pareto_decision_inputs.json` via `cd backend && .venv/bin/python -m app.research.decision_inputs` and confirm the diff is exactly the expected addition (review it — do not blindly commit).

## Step 7 — Update the API

- If new experiment types need dedicated routes beyond `/research/future-science-manifest`
  (e.g., a `/research/experiments/{id}` entry for a newly-canonical Stage 2-4 experiment), follow
  the existing `backend/app/api/routes/research.py` pattern exactly (Reader-class + `.artifact()`
  returning a typed Envelope).
- Do not modify the shape of `FutureScienceManifestEnvelope` or `ManifestEntryDisplayProjection`
  without re-running every test listed in Step 5 plus a full `tsc --noEmit` on the frontend (the
  TS types in `frontend/src/lib/types.ts` are hand-mirrored, not generated — a schema change here
  requires a matching manual TS edit).

## Step 8 — Update Research Mode

- The `FutureScienceHandoffCard.tsx` component already renders whatever is in
  `display_projections` — no code change should be needed for the pending→ingested transition
  itself. Verify this live (Step 12) rather than assuming.
- If a promoted entry should appear as a full first-class experiment card (like PPG-DaLiA/PTT/
  Sleep-EDF today), that requires new frontend work beyond this contract's scope — treat as a new,
  separate task, not an automatic consequence of ingestion.

## Step 9 — Update claims

- For every claim intended for the paper/jury referencing a Stage 2-4 entry, call
  `validate_claim_against_entry(entry, required_full_evidence=<True for headline claims>)` and
  confirm it does not raise, before writing the claim into any doc.
- Add corresponding entries to `results/claim_traceability.json` following the existing schema
  there, and re-run `ml/check_claim_consistency.py` — it must still print
  `STRUCTURED_TRACEABILITY_AND_FORBIDDEN_PATTERN_CHECK_PASS`.

## Step 10 — Update paper/jury

- Replace the relevant `PENDING_SCIENCE_HANDOFF` markers in
  `docs/CLAUDE_PHASE3_PAPER_SKELETON_STAGE2_4.md` with the real, validated results — cite the
  manifest's `provenance.source_artifact_path` for each, exactly as every other paper section
  already does.
- Update `docs/CLAUDE_PHASE3_JURY_FRAMEWORK_STAGE2_4.md` Q1 ("What actually replicated?") with the
  real answer, using the `replication_class_label` the software computed — do not write a new,
  hand-crafted characterization that could drift from what the guards actually verified.

## Step 11 — Run full tests

```bash
cd backend && .venv/bin/python -m pytest -q                          # expect 214+ passed, 0 failed
.venv-integration/bin/python -m pytest ml/tests -q                    # expect ~290 passed, only dataset/checkpoint-absence skips
.venv-integration/bin/python ml/check_claim_consistency.py            # expect PASS
cd backend && .venv/bin/python -m app.research.decision_inputs && cd .. && git diff --stat results/pareto_decision_inputs.json  # expect no diff unless Step 6 was authorized
cd frontend && npx tsc --noEmit && npx eslint . && npm run build      # expect clean, clean, successful build
```

## Step 12 — Run browser

Start `backend/.venv/bin/uvicorn app.main:app --port 8000` and `cd frontend && npm run dev`, then
inspect `/research`, `/digital-twin`, `/mission-overview` exactly as done in Phase 3 §11 of this
integration-prep sprint: zero console errors, all network requests 200, the Stage 2-4 card renders
the real (not pending) content correctly with correct badges per entry, Digital Twin still reads
synthetic/untrained, no other page regressed.

## Step 13 — Freeze candidate SHA

Commit everything from Steps 6-10 on `stage2-4-controlled-integration`, push it, and record the
exact SHA in a new `docs/STAGE2_4_INTEGRATION_FREEZE_<date>.md` (following the naming convention of
prior freeze docs, e.g. `docs/STAGE1A_POST_REMEDIATION_INTEGRATION_REPORT.md`). Do not merge to
`main` at this step — freezing means "this SHA is the audit candidate," not "this is final."

## Step 14 — Independent hostile audit

Before any merge to `main`, request an independent Codex or third-party re-audit of the frozen
candidate SHA, following the exact precedent of
`docs/CODEX_STAGE1A_POST_REMEDIATION_REAUDIT_HANDOFF.md` — a numbered "highest-risk re-checks"
attack list handed to a re-auditor who did not write the code being audited. At minimum, that
attack list must include every guard this integration-prep sprint built:
1. Can any entry with `completion_state != COMPLETE` render a numeric headline? (Try it — construct
   a malicious-looking manifest with a `BOUNDED_DIAGNOSTIC` entry carrying a plausible number.)
2. Can two entries with different `dataset_version`/`protocol_version` be combined into one delta?
3. Can a `SAME_DATASET_HOLDOUT` be relabeled `EXTERNAL_REPLICATION` without `assert_replication_claim_is_plausible` catching it, if it shares the primary's dataset+version?
4. Does ingesting the real manifest change `engineering_readiness`/`day6_research`/Pareto state at all? (It must not — re-run `test_case_ingesting_a_strong_positive_manifest_does_not_change_architecture_or_pareto_state`-style comparison against the real ingestion.)
5. Does any claim in the paper/jury docs cite an entry whose `completion_state` is `BLOCKED_BY_DATA_ACCESS`/`PENDING`/`SUPERSEDED`, or `BOUNDED_DIAGNOSTIC` where full evidence was claimed?

Only after this independent audit reports clean (or with disclosed, accepted limitations) should
Emir decide on merging toward `main`.

---

## What this contract deliberately does NOT automate

- Whether a given entry's science is *correct* (this is Ismet's/Emir's scientific judgment, not a
  software check). The software can only verify internal consistency (direction, provenance,
  state, version-matching) — never numerical truth.
- The decision to promote any entry to a paper headline, a final architecture input, or a Pareto
  computation. Every guard in this pipeline defaults to refusal; only an explicit human decision,
  applied through the steps above, changes that.
