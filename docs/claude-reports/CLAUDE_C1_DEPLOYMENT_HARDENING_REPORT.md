# CLAUDE C1 — Deployment Hardening Report

Package: jury-environment reproducibility hardening (F-08, F-18, F-07-reproducibility).
Assume an independent reviewer who will re-verify every claim against the repository.

## 1. Executive outcome

PARTIAL (by design). F-08 (deterministic install + explicit API/WS/CORS contract
+ clean-machine runbook) and F-18 (public backend-env leak) are addressed and
verified. The reproducibility portion of F-07 is **implemented as manifest +
verifier only**; the actual QA/evidence bundle is not present on this branch, so
F-07 remains PARTIAL and is honestly reported as INCOMPLETE by the verifier.
The Docker/Compose runtime path could not be executed here (Docker unavailable)
and is reported as NOT RUN, not passed.

## 2. Original-checkout safety statement

The shared original checkout `/Users/emirharunsunbul/Documents/ChatGPT/IAC` was
never edited. Post-work verification: its branch is still
`stage5-dashboard-canonical-sync` at `c99ed8f…`, none of this package's new
files exist there, and the CORS validator string `_reject_unsafe_cors_origins`
is absent from its `backend/app/core/config.py`. The other agent's uncommitted
work was never read, staged, merged, or modified. The two pre-existing prunable
worktrees were left untouched (not pruned).

## 3. Worktree path

`/Users/emirharunsunbul/Documents/ChatGPT/IAC-claude-deployment-hardening`

## 4. Branch

`claude/deployment-hardening`

## 5. Starting HEAD

`c99ed8f14a2d9605c0059fd3a1444cf0b31fbe19` (equal to the required base commit).

## 6. Ending HEAD

The single commit created by this package (message
`chore(deployment): harden jury environment reproducibility`). Its hash is
reported in the session's final response and is retrievable via `git -C
<worktree> log -1`. (A report cannot embed its own commit hash without an
amend, which policy forbids.)

## 7. Starting status

Clean working tree on a freshly created worktree (0 status lines).

## 8. Ending status (before commit)

Modified (9): `README.md`, `backend/.env.example`, `backend/app/core/config.py`,
`docker-compose.yml`, `docs/DATASET_REPLAY.md`, `frontend/.env.local.example`,
`frontend/Dockerfile`, `frontend/src/components/demos/DataSourceControl.tsx`,
`frontend/src/lib/config.ts`.
New (8, incl. this report): `backend/tests/test_cors_config.py`,
`backend/tests/test_deployment_contract.py`, `backend/tests/test_jury_verifiers.py`,
`docs/JURY_DEPLOYMENT_RUNBOOK.md`, `docs/JURY_RELEASE_EVIDENCE_MANIFEST.md`,
`scripts/verify_jury_environment.py`, `scripts/verify_jury_release_evidence.py`,
`docs/claude-reports/CLAUDE_C1_DEPLOYMENT_HARDENING_REPORT.md`.
`frontend/node_modules/` was created by `npm ci` but is git-ignored and not staged.
`frontend/package-lock.json` is byte-for-byte unchanged.

## 9. Worktree-list evidence

`git worktree list` shows the original checkout (`stage5-dashboard-canonical-sync`),
two unrelated prunable worktrees under scratchpad, and this package's worktree
at the required path on `claude/deployment-hardening`.

## 10. Full changed-file list

See §8. Total: 9 modified + 8 new = 17 paths, every one within the package
allowlist (§5 of the brief). No protected path changed.

## 11. File-by-file change explanation

- `frontend/Dockerfile` — deps stage now `COPY package.json package-lock.json ./`
  + `RUN npm ci` (deterministic). Build stage documents `NEXT_PUBLIC_*` as public
  and adds an explicit `ARG/ENV NEXT_PUBLIC_WS_URL` (empty default).
- `docker-compose.yml` — backend gains explicit `BIOMIN_ALLOWED_ORIGINS`
  (exact origins matching defaults, JSON array); frontend gains explicit
  `NEXT_PUBLIC_WS_URL` build arg. Ports 3000/8000 unchanged.
- `backend/app/core/config.py` — imports `field_validator`; documents the
  `BIOMIN_ALLOWED_ORIGINS` JSON override; adds `_reject_unsafe_cors_origins`
  (rejects empty/blank/`*`, trims whitespace).
- `backend/.env.example` — documents `BIOMIN_ALLOWED_ORIGINS` (commented example).
- `frontend/.env.local.example` — documents API+WS together, public/non-secret,
  derivation, and a non-local example.
- `frontend/src/lib/config.ts` — empty-string coercion (treat empty as unset),
  trailing-slash-safe WS derivation, exported pure `deriveWebSocketUrl`.
- `frontend/src/components/demos/DataSourceControl.tsx` — one fallback `<p>`
  copy line changed; no env var / path / shell / URL; styling preserved.
- `README.md` — §15 points to the runbook + preflight; manual frontend step uses
  `npm ci`.
- `docs/DATASET_REPLAY.md` — operator-only note clarifying the public UI does not
  instruct end users to set backend env vars.
- `docs/JURY_DEPLOYMENT_RUNBOOK.md` — new 25-section clean-machine runbook.
- `docs/JURY_RELEASE_EVIDENCE_MANIFEST.md` — new evidence manifest.
- `scripts/verify_jury_environment.py` — read-only environment verifier.
- `scripts/verify_jury_release_evidence.py` — read-only evidence verifier.
- `backend/tests/test_*.py` — CORS config tests, static deployment-contract
  tests, verifier fixture tests.

## 12. F-08 before/after analysis

Before: `frontend/Dockerfile` copied only `package.json` and ran `npm install`
(non-deterministic; lockfile ignored). Frontend WS/API contract implicit; no
clean-machine runbook. After: `npm ci` from the copied lockfile (fails on
mismatch — proven by a successful `npm ci` here); explicit API+WS build args in
Dockerfile/compose; documented `.env.local.example`; a full clean-machine
runbook; and a read-only preflight verifier. Result: deterministic install YES.

## 13. F-18 before/after analysis

Before: `DataSourceControl.tsx:262` rendered "Set `BIOMIN_PPG_DALIA_PATH` in the
backend environment to enable replay." After: "Recorded PPG-DaLiA replay is not
available on this deployment. Contact the demo administrator or run the presenter
preflight to enable it." No env var, path, shell, URL, or port. The backend
setup instructions live in the runbook and `DATASET_REPLAY.md`. A static test
and the environment verifier assert no backend env var appears in rendered
frontend copy (developer comment lines in protected modules are out of scope and
are not policed — one such comment remains in `src/lib/monitoring/runtimeState.ts`,
a protected file, and is not user-facing).

## 14. F-07 reproducibility status

PARTIAL. A manifest (`docs/JURY_RELEASE_EVIDENCE_MANIFEST.md`) and a read-only
verifier (`scripts/verify_jury_release_evidence.py`) were implemented. The base
commit and this branch do **not** carry the QA screenshot/dossier tree, so the
verifier honestly reports `F-07 status: INCOMPLETE` (24 artifacts MISSING,
exit 2). No evidence was copied from the original checkout and no placeholder was
fabricated. F-07 is not marked fixed.

## 15. CORS threat analysis

Defaults remain exactly `http://localhost:3000` + `http://127.0.0.1:3000` (not
wildcard). Origins are overridable via `BIOMIN_ALLOWED_ORIGINS` (JSON list) with
no source edit. The new validator fails closed on `*`, empty list, and blank
entries; a non-JSON value already raised `SettingsError` (pre-existing
pydantic-settings behavior, confirmed) — so access can never be silently widened.
`allow_credentials=True` requires exact origins, which the validator enforces.
**WebSocket honesty:** Starlette `CORSMiddleware` does not enforce origin on the
WS handshake; this is documented in the runbook and not claimed otherwise. The
package does not conflate frontend URL, backend bind address, and allowed browser
origin (each is described distinctly).

## 16. API/WebSocket configuration analysis

`NEXT_PUBLIC_*` are build-time, public, non-secret (documented). `WS_URL` uses an
explicit `NEXT_PUBLIC_WS_URL` when set, else `deriveWebSocketUrl(API_BASE_URL)`:
`http→ws`, `https→wss`, `/ws/live-feed` appended, trailing slash trimmed. Empty
strings coerce to "unset" so the explicit-but-empty Dockerfile WS arg falls back
safely instead of emitting a malformed URL. Verified by executed Node assertions
(5 derivation cases + empty-coercion) and `tsc --noEmit`.

## 17. Docker dependency reproducibility analysis

`npm ci` requires and installs strictly from `frontend/package-lock.json`, and
fails if it disagrees with `package.json`. A real `npm ci` in the isolated
worktree succeeded (452 packages, 39s) without modifying the lockfile,
demonstrating manifest/lock agreement. No dependency version changed; the
lockfile is byte-for-byte identical.

## 18. Public-copy analysis

Only the single fallback paragraph changed. Visual structure/styling preserved
(`<p class="text-xs text-slate-500">`). Unavailable-replay semantics remain
truthful. No new controls; no backend mutation.

## 19. Environment-verifier behavior

`scripts/verify_jury_environment.py`: read-only, stdlib-only, `--root`/`--quiet`/
`--help`, deterministic, repeatable. PASS/WARN/FAIL; exit 0 only when no FAIL.
Reports whether env vars are set without printing values (tested). Against this
worktree: PASS=19, WARN=7, FAIL=0, exit 0. Tool/dataset/checkpoint absence is a
WARN, never a silent pass.

## 20. Evidence-verifier behavior

`scripts/verify_jury_release_evidence.py`: read-only, stdlib-only,
`--root`/`--hash`/`--json`/`--help`. Distinguishes PRESENT/MISSING/EMPTY/
AMBIGUOUS; marks required vs optional and runtime-critical vs audit-only. Exit 0
only when every required artifact is PRESENT; otherwise exit 2 with an explicit
INCOMPLETE message. It never copies, renames, deletes, or fabricates evidence; a
hash is provenance only, never a claim of visual review.

## 21. Commands executed (working dir / command / exit / observed)

All in the isolated worktree unless noted. Venv = scratchpad `.venv-c1`
(Python 3.14.5; pydantic 2.13.5, pydantic-settings 2.15.0, pytest 9.1.1).

- `git worktree add -b claude/deployment-hardening <worktree> c99ed8f…` → 0 (observed).
- Node WS-derivation + empty-coercion assertions (frontend) → 0 (observed, all PASS).
- CORS Settings baseline + validator probes (venv) → 0 (observed).
- `python scripts/verify_jury_environment.py --root <worktree>` → 0 (observed).
- `python scripts/verify_jury_release_evidence.py --root <worktree>` → 2 (observed, INCOMPLETE).
- `pytest tests/test_cors_config.py tests/test_deployment_contract.py tests/test_jury_verifiers.py` → 0, 30 passed (observed).
- `npm ci` (frontend) → 0, 452 packages (observed).
- `npx tsc --noEmit` (frontend) → 0 (observed).
- `npm run lint` (frontend) → 0 (observed).
- `python -m py_compile` on new scripts/tests → 0 (observed).
- `git diff --check` → clean (observed).

## 22. Tests executed

- `backend/tests/test_cors_config.py` (9): defaults, 2-origin override,
  production https example, invalid-format raises, wildcard/empty/blank rejected,
  whitespace trimmed.
- `backend/tests/test_deployment_contract.py` (12): npm ci / lockfile / no
  npm-install directive / lockfile exists; no-wildcard backend + compose CORS;
  compose pins API+WS args + standard ports; config.ts WS contract; no public
  env leak / no backend setup instructions / no rendered leak tree-wide.
- `backend/tests/test_jury_verifiers.py` (9): env verifier good-root pass,
  npm-install/missing-lock fail, wildcard-CORS fail, rendered-leak fail,
  comment-leak allowed, no-secret-value printing; evidence verifier
  empty-root incomplete, PRESENT/EMPTY/AMBIGUOUS detection, deterministic hash.

## 23. Exact pass/fail/skip counts

- New backend tests: 30 passed, 0 failed, 0 skipped.
- Frontend: `tsc --noEmit` 0 errors; `eslint .` 0 problems.
- Environment verifier: PASS=19 WARN=7 FAIL=0 (exit 0).
- Evidence verifier: 24 entries, 0 PRESENT, exit 2 (INCOMPLETE) — expected.
- Full backend pytest suite: NOT RUN (requires torch/numpy/sklearn/shap, not
  installable on the available Python 3.14; unrelated to this change). NOT a pass.

## 24. Docker/Compose verification

`docker` is NOT available in this environment. `docker compose config`,
`docker compose up`, and any container build were **NOT RUN**. They are reported
as NOT RUN, not passed. The compose contract is instead covered by static
assertions (explicit API/WS args, non-wildcard CORS, standard ports) and by the
runbook, which flags the Docker path as specified-but-unexecuted.

## 25. Build verification

Frontend production build (`next build`) was NOT run (heavier than needed;
`tsc --noEmit` + `eslint` cover the changed TS). `npm ci` succeeded, proving
deterministic dependency resolution. The container image build was NOT run
(Docker unavailable).

## 26. Anything not verified

Container builds, `docker compose config/up`, live REST/WS/CORS connectivity,
`next build`, and the full backend pytest suite. The end-to-end clean-machine
procedure was not executed.

## 27. Known limitations

- Config/CORS unit tests ran on pydantic 2.13.5 / pydantic-settings 2.15.0
  (cp314 wheels), not the pinned 2.10.4 / 2.7.1 (pinned pydantic-core has no
  cp314 wheel and its source build fails on Python 3.14). The behaviors tested
  (JSON-list env parse, wildcard/empty rejection, trim) are stable across these
  versions; still, this is a version delta from production.
- Docker path unverified (see §24).
- WS handshake is not CORS-restricted (documented, not "fixed" — out of scope).

## 28. Protected-file confirmation

No file under `frontend/src/components/{monitoring,operations,jury,experimental,
systembrief,visualization}`, `frontend/src/app/{mission-overview,live-monitoring,
ai-insights,mission-timeline,system-brief,research,digital-twin}`,
`frontend/src/store`, `frontend/src/lib/{monitoring,runtime}`, navigation,
`globals.css`, `tailwind.config.ts`, scientific constants, API schemas, replay/
fault/model code, dataset readers, screenshots, or GLB/human assets was changed.
`frontend/src/lib/config.ts` is not a protected path (only `lib/monitoring` and
`lib/runtime` are). `DataSourceControl.tsx` is the single allowed product
component, changed for public copy only.

## 29. Scientific-lock confirmation

No scientific value, label, inference, availability state, replay behavior, or
fault behavior changed. CORE_PLUS_CONTEXT, module topology, five modalities,
EOG-only delta, BioZ/EIS exclusion, PPG-DaLiA/S14 framing, missing-data honesty,
Digital-Twin-only boundary, and simulated-fault framing are untouched.

## 30. Commit hash, if created

Reported in the final response (single commit; not amended; not pushed).

## 31. Integration instructions for the user

From the original checkout, review then merge the branch:
`git -C /Users/emirharunsunbul/Documents/ChatGPT/IAC merge --no-ff claude/deployment-hardening`
(or open a PR). The branch is based on `c99ed8f…`; the other agent's work is
independent and unmodified here.

## 32. Expected merge-conflict surface

Low. The other agent's uncommitted changes are in monitoring/store/panels/
mission-timeline and `frontend/scripts/verify-monitoring-state.ts` — disjoint
from this package's files. Overlap risk is limited to `frontend/src/lib/config.ts`
if the other agent later edits it (it did not appear in their changed set) and to
README/compose if both touch them. All new files are conflict-free.

## 33. Rollback instructions

`git -C /Users/emirharunsunbul/Documents/ChatGPT/IAC branch -D claude/deployment-hardening`
after removing the worktree with `git worktree remove
/Users/emirharunsunbul/Documents/ChatGPT/IAC-claude-deployment-hardening`
(operator action; not performed by this package). If already merged, revert the
single merge/commit.

## 34. Claims that remain partial

F-07 (evidence still absent from the branch; manifest/verifier only). Docker/
Compose runtime path (NOT RUN). Full backend suite (NOT RUN). These are disclosed,
not represented as complete.

## 35. Final verdict

PARTIAL. F-08 and F-18 are implemented and verified within the constraints of
this environment; F-07 reproducibility tooling is implemented but the evidence
bundle is not present, so F-07 remains PARTIAL and is reported honestly. No
protected file, scientific behavior, or visual design changed. Ready for
independent review.
