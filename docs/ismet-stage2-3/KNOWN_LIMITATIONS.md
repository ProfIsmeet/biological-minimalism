# Known Limitations — Stage 2-3 (ismet/frontend-stage2-3-hardening)

Honest, as-of-this-branch limitations. Nothing here is fixed by wording it
differently elsewhere — this list exists so a reviewer or a jury operator
knows exactly what has and has not been verified, and never mistakes an
absence of a problem report for a positive verification that didn't happen.

## 1. No browser automation was available in this environment

Every accessibility and interaction claim in Stage 2 (A1-A4) — live-region
announcement boundaries, reduced-motion propagation, mobile dialog focus
containment, WebGL fallback rendering — was verified with deterministic
**source-level structural checks** (regex/text assertions against the actual
shipped source, following this repo's own `verify-monitoring-consumers.mjs`
convention) plus `tsc`, `lint`, and `next build`. These checks prove the
required code patterns exist and are wired correctly; they do not prove a
real browser, screen reader, or keyboard-only session behaves as intended.
See `docs/ismet-stage2-3/STATUS.md`'s "Behavioral-review debt" section for
the exact enumerated list of what still needs a real runtime pass before
Stage 2 can be marked final `COMPLETE` rather than
`IMPLEMENTATION_COMPLETE_PENDING_FINAL_BEHAVIORAL_REVIEW`.

## 2. Docker/Compose was not runnable in this environment

`docker --version` fails (`command not found`). All Docker/Compose-related
work in Milestone B (deterministic `npm ci` install, build-arg wiring,
`docker-compose.yml` CORS/WS configuration) was verified by static file
inspection and the `verify_jury_environment.py`/`test_deployment_contract.py`
test suites, never by an actual `docker compose up --build` run. Report this
as `NOT_RUN_DOCKER_UNAVAILABLE`, never as passed.

## 3. No physical projector or jury hardware was available

The projector/browser acceptance checklist in
`docs/JURY_DEPLOYMENT_RUNBOOK.md` §19 documents what to check; it has not
been executed against real projector hardware from this environment.

## 4. HR-checkpoint readiness is not exposed by the backend API contract

Neither Presenter Preflight nor the canonical jury demo bootstrap's
prerequisite gate can independently confirm the PPG+IMU HR checkpoint is
present and valid before attempting to use it — this is an existing,
pre-Stage-2 backend contract gap (see `derivePresenterPreflight`'s
`hr-model` fact, honestly `"unknown"`). A missing/invalid checkpoint would
surface as a failed `load-subject` step in the canonical bootstrap, not as a
pre-flight block.

## 5. No release-evidence (QA screenshot) tree exists in this checkout

`scripts/verify_jury_release_evidence.py --root .` run against this actual
repository honestly reports `F-07 status: INCOMPLETE` — 23 of 24 required
evidence artifacts (state screenshots, human-figure views, hostile-audit
dossier, presenter script, etc.) are MISSING because this is a source-only
checkout with no accompanying QA evidence bundle. This is expected and
correctly reported by the verifier itself; it is not a regression introduced
by this branch, and this branch does not fabricate or claim that evidence
exists.

## 6. This branch does not attempt Stage 4 or any scientific/architecture change

Out of scope by explicit instruction: no model retraining, no scientific
metric changes, no sensor-set decision changes, no visual/art-direction
redesign, no new 3D human model, no activation of any rejected/experimental
asset. `CORE_PLUS_CONTEXT` and all other Stage 4 architecture decisions are
unchanged.
