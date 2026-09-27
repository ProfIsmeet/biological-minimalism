# Jury Release-Evidence Manifest

This manifest enumerates the release-evidence artifacts a complete, reproducible
jury bundle is expected to contain, and how each one is verified. It is the
human-readable companion to the read-only verifier
[`scripts/verify_jury_release_evidence.py`](../scripts/verify_jury_release_evidence.py);
the verifier's `EVIDENCE` table is kept in sync with the table below.

## How verification works

Run, from a checkout root:

```bash
python scripts/verify_jury_release_evidence.py --root .
# add --hash for SHA-256 provenance, --json for machine-readable output
```

The verifier globs for each expected artifact and reports one of four statuses:

- **PRESENT** — exactly one non-empty file matches.
- **MISSING** — no file matches.
- **EMPTY** — a single match exists but is zero bytes.
- **AMBIGUOUS** — more than one file matches a single expected artifact.

Exit code is `0` only when **every required** artifact is PRESENT; otherwise it
is `2` and the verifier prints `F-07 status: INCOMPLETE`.

## Honesty limitation (F-07 status)

**The source-only base commit does not carry the QA screenshot / dossier tree.**
On such a checkout the verifier correctly reports most artifacts as MISSING and
`F-07 status: INCOMPLETE`. The existence of this manifest and the verifier does
**not** by itself close F-07. F-07 is only closable once the project owner has
explicitly approved the evidence bundle (licensing/privacy included) and it is
actually present in the release checkout. The verifier can compute a file hash
for provenance, but a hash is **not** evidence that an image was visually
reviewed — visual review remains a separate human step.

## Evidence table

Columns: **ID** (verifier key) · **Expected path/pattern** (glob, relative to
root) · **Req.** (required/optional) · **Class** (runtime-critical = needed for
the live demo; audit-only = provenance/review) · **Distributable** (allowed in a
publicly distributed release) · **License/privacy review**.

| ID | Expected path / pattern | Req. | Class | Distributable | License/privacy review |
|---|---|---|---|---|---|
| `audit-main` | `frontend/qa-screenshots/**/AUDIT.md` | required | audit-only | yes | no |
| `audit-matrix` | `frontend/qa-screenshots/**/FIVE_STAGE_COMPLETENESS_MATRIX.md` | required | audit-only | yes | no |
| `audit-recommendation` | `frontend/qa-screenshots/**/JURY_DEMO_RECOMMENDATION.md` | required | audit-only | yes | no |
| `prompt-3bc-human-visual` | `frontend/qa-screenshots/**/prompt-3*/**/*` | required | audit-only | yes | **yes** (human figure) |
| `prompt-4-a11y-hardening` | `frontend/qa-screenshots/**/prompt-4*/**/*` | required | audit-only | yes | no |
| `prompt-5-hostile-dossier` | `frontend/qa-screenshots/**/prompt-5*/**/*` | required | audit-only | yes | no |
| `presenter-script` | `**/presenter*script*.*` | required | audit-only | yes | no |
| `recovery-card` | `**/recovery*card*.*` | required | audit-only | yes | no |
| `state-nominal` | `frontend/qa-screenshots/**/*nominal*.png` | required | runtime-critical | yes | no |
| `state-fault` | `frontend/qa-screenshots/**/*fault*.png` | required | runtime-critical | yes | no |
| `state-rebuilding` | `frontend/qa-screenshots/**/*rebuild*.png` | required | runtime-critical | yes | no |
| `state-recovered` | `frontend/qa-screenshots/**/*recover*.png` | required | runtime-critical | yes | no |
| `state-disconnected` | `frontend/qa-screenshots/**/*disconnect*.png` | required | runtime-critical | yes | no |
| `mobile-mission-overview` | `frontend/qa-screenshots/**/*mobile*mission*overview*.png` | required | runtime-critical | yes | no |
| `live-monitoring` | `frontend/qa-screenshots/**/*live*monitoring*.png` | required | runtime-critical | yes | no |
| `system-brief` | `frontend/qa-screenshots/**/*system*brief*.png` | required | runtime-critical | yes | no |
| `experimental` | `frontend/qa-screenshots/**/*experimental*.png` | required | runtime-critical | yes | no |
| `digital-twin` | `frontend/qa-screenshots/**/*digital*twin*.png` | required | runtime-critical | yes | no |
| `presenter-preflight` | `frontend/qa-screenshots/**/*preflight*.png` | required | runtime-critical | yes | no |
| `zoom-200` | `frontend/qa-screenshots/**/*200*zoom*.png` | required | runtime-critical | yes | no |
| `human-front` | `frontend/qa-screenshots/**/*human*front*.png` | required | audit-only | yes | **yes** (human figure) |
| `human-side` | `frontend/qa-screenshots/**/*human*side*.png` | required | audit-only | yes | **yes** (human figure) |
| `human-three-quarter` | `frontend/qa-screenshots/**/*human*three*quarter*.png` | required | audit-only | yes | **yes** (human figure) |
| `rejected-cesiumman` | `frontend/qa-screenshots/**/*cesium*` | optional | audit-only | **no** (rejected asset) | **yes** (asset license/provenance) |

### Notes per class

- **Runtime-critical** screenshots document the demonstrable Mission Overview
  states (nominal → fault → rebuilding → recovered → disconnected) plus the
  route surfaces (Live Monitoring, System Brief, Experimental, Digital Twin,
  Presenter Preflight), the mobile Mission Overview first-view, and the 200%
  zoom accessibility evidence. They substantiate what a jury will actually see.
- **Audit-only** artifacts are the independent audit, the Prompt 3B/3C/4/4A/5
  dossiers, the presenter script, the recovery card, the human front/side/
  three-quarter figure evidence, and the rejected-CesiumMan provenance record.
- **License/privacy review** is flagged for any artifact depicting the human
  figure and for the rejected CesiumMan asset (its licensing/attribution and
  the reason for rejection must ship with the provenance record, and the
  rejected asset itself must not be redistributed as an accepted asset).

## Resolved: cross-run duplicate evidence (formerly "known ambiguity")

- 2026-09-27 (`claude/stage4-5-visual-command-deck`): a second stage-specific
  evidence directory, `frontend/qa-screenshots/claude-stage4-5-visual-command-deck/`,
  was added alongside the existing `claude-stage2-3-final-acceptance/` one,
  giving `audit-main`'s `**/AUDIT.md` glob two matches and making it report
  `AMBIGUOUS`. At the time, narrowing the glob to a single hardcoded path was
  tried and reverted because it broke `backend/tests/test_jury_verifiers.py`
  (which depends on the pattern staying a generic wildcard), so the ambiguity
  was left in place and documented as accepted.
- 2026-09-27 (`claude/stage4-5-real-visual-implementation`): a third evidence
  directory (this run's own `claude-stage4-5-real-visual-implementation/`) made
  the same glob collect three matches, plus new cross-run duplicates for
  `state-fault`, `state-rebuilding`, and `state-recovered` — four `AMBIGUOUS`
  entries in total. Leaving this "accepted" was explicitly rejected: an
  evidence verifier that never reaches exit 0 is not a passing gate.
  **Fix**: `scripts/verify_jury_release_evidence.py` now resolves matches by
  their `frontend/qa-screenshots/<run>/` directory and, when a manifest slot's
  matches span more than one run, treats the highest-precedence run
  (`CANONICAL_RUN_ORDER`, newest/most-authoritative first) as canonical for
  PRESENT/EMPTY/AMBIGUOUS purposes. Matches from every other run are not
  discarded — they are still globbed, still hashed on request, and now
  reported explicitly as `superseded` (visible in both the text and `--json`
  output) so the audit trail stays intact. A genuine duplicate **within** one
  run directory (the scenario the original unit tests fixture) is still,
  correctly, `AMBIGUOUS` — cross-run precedence only disambiguates *across*
  runs, never papering over a real same-directory clash. Both the glob pattern
  and the test suite were updated together
  (`test_evidence_verifier_resolves_cross_run_duplicates_via_precedence` in
  `backend/tests/test_jury_verifiers.py`), and no existing test's assertions
  were weakened or removed — all 9 pre-existing evidence-verifier assertions
  still pass unmodified, plus the new one. `python scripts/verify_jury_release_evidence.py --root .`
  now exits `0` from this branch.

## Scope boundaries

- The verifier **does not** copy evidence from any other checkout, and it never
  creates placeholder files to make a check pass.
- Patterns are deterministic globs; if a project reorganizes the evidence tree,
  update both this table and the verifier's `EVIDENCE` list together.
- Presence is necessary but not sufficient for release: approval, licensing,
  privacy/de-identification review, and human visual review are separate gates
  the verifier cannot perform.
