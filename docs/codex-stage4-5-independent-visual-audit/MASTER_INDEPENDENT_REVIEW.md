# Stage 4–5 Independent Review

SOURCE_SHA: `979836ff704c2d6df43152e4d733d48703d12848`
IMPLEMENTATION_CHECKPOINT_SHA: `6d169c4abe6d68a7758f515bad5df39b8d851727`
REPORT_COMMIT: this commit; resolve with `git rev-parse HEAD`
Target branch: `codex/stage4-5-independent-visual-audit`

## Executive verdict

Stage 4 and Stage 5 are independently accepted **after** nine confirmed defects
were corrected. The inherited product was materially strong but its tablet
first viewport, stale trend summary, affected-region wording, operational
typography floor, reduced-motion switch, and evidence-selection architecture
did not support the inherited unconditional COMPLETE claim.

The corrected branch has no open high- or medium-severity findings. It preserves
scientific behavior and fail-closed telemetry semantics. Merge is recommended
after owner approval. Docker reproduction remains externally blocked and actual
screen-reader testing remains owner-deferred.

## Identity, isolation, and preservation

- Repository: `https://github.com/ProfIsmeet/biological-minimalism.git`.
- Source remote/local branch resolved exactly to SOURCE_SHA after a normal fetch.
- Base `7afe57114ad6f7537b73f17683f7ecd733606730` is an ancestor.
- Fresh managed worktree and target branch were used; starting tree was clean.
- Starting and final checked preservation refs: `main` and `origin/main`
  `3efb49a02e4c824a82410793d245d3141a5942f1`; Claude source local/remote SOURCE_SHA.
- Node `v22.23.1`, npm `10.9.8`, Python `3.14.5`; supported backend suite
  used an existing Python 3.12 environment.
- Browser mechanisms: Codex in-app Chromium via CUA plus native Safari Page Menu
  for an explicitly reported 200% zoom.
- Docker: unavailable (`docker: command not found`), reported `BLOCKED_EXTERNAL`.
- Task services used isolated ports 3014 and 8014. No pre-existing process was stopped.

## Baseline reproduction

The inherited baseline reproduced 1042/1042 monitoring assertions, all five
structural guards, lint, TypeScript, a 14-page build, and 348 passed / 4 skipped
backend tests. Evidence text/hash/JSON exited zero with 23 PRESENT and one
optional MISSING. That exit was not accepted at face value: the hidden
`CANONICAL_RUN_ORDER` could silently subordinate future evidence.

The complete base-to-source diff, all 30 changed files, required components,
model/replay contracts, store identity and availability logic, reports,
manifest, verifier, and verifier tests were reviewed. No model behavior,
dataset semantics, or store subscription ownership change was found.

## Findings, root causes, and corrections

The authoritative detail is in `FINDING_LEDGER.md`. Root causes were:

- a desktop breakpoint/layout assertion standing in for rendered tablet proof;
- presentation logic reading a last historical HR value without first gating
  on current prediction availability;
- copy conflating “no active simulated fault” with affected/healthy regions;
- typography guards limited to selected source tokens and missing SVG/chart text;
- local Settings state not subscribing to the shared preference event stream;
- directory naming/order used as evidence authorization.

Corrections are narrow: presentation-only derivation, layout breakpoint/order,
copy, label sizes, Panel wrapping, Settings synchronization/accessibility, and
explicit evidence policy. Critical unavailable behavior is now protected by
behavioral helper cases rather than source strings alone.

Disproved suspicions are also recorded: fault text did not truncate; shared
Panel consumers did not exhibit a material regression; missing channels did
not render as zero.

## Route and shared-system review

Material routes inspected were Mission Overview, Live Signals, System Brief,
Experimental Research, Digital Twin Reference, Settings, and presenter
preflight. Approximately 22 Panel imports were inventoried. Long headings and
actions receive `min-w-0`, wrapping, and nonshrinking action treatment.

Typography now enforces a 12px operational floor for inherited 9–11px utility
classes, and essential Recharts/hex labels are 12px. Muted text remained
legible on the dark surfaces in inspected screenshots. The result preserves
editorial hero hierarchy while keeping operations dense; no material card-wall
or projector-readability finding remains.

## Viewport matrix

| Viewport | First-viewport result |
|---|---|
| 1920×1080 | PASS; complete command deck and trend hierarchy. |
| 1440×900 | PASS after compact sizing; trend is readable, not merely at the edge. |
| 1280×800 | PASS after HR/trend row correction. |
| 1024×768 | PASS after correction: identity, connection/fault, affected region, HR state/reason, and compact trend visible. |
| 390×844 | PASS after moving next-safe-state guidance before the compact ring. |
| Safari 200% | PASS; Safari's Page Menu displayed `%200`, compact navigation activated, text remained readable, no observed horizontal clipping. |

## Runtime state matrix and S14 trace

| State | Trigger | Expected / actual | Verdict |
|---|---|---|---|
| Loading | initial navigation | connecting, unavailable, no stale identity | PASS |
| Synthetic nominal | default source | explicit synthetic/non-live, missing channels remain missing | PASS |
| Disconnected/source error | stop task backend | unavailable/disconnected, identity and numeric HR hidden, source_error priority | PASS |
| Identity convergence | replay selection | pending identity blocks confirmation | PASS |
| Real S14 | select/load/play S14 | PPG-DaLiA · S14 and AI_ESTIMATED output | PASS |
| Packet-loss fault | PPG, severity .9, seed 7272 | full text, Wrist/PPG affected, HR withheld | PASS |
| Rebuilding | clear fault | REST `warming_up`; no numeric current HR | PASS |
| Recovery | wait for fresh synchronized window | new numeric HR, fault cleared, S14 metadata retained | PASS |
| Missing channels | S14/synthetic source | absent EEG/EOG/secondary channels remain “No channel” | PASS |
| More dialog / demo drawer | keyboard | entry, trap, Escape, restoration, inert background | PASS |
| Reduced motion | app toggle and two tabs | persistence, live class, and visible switch synchronized | PASS |
| WebGL fallback | supported guard/components | unsupported/error/context-loss paths remain present | PASS |

The critical stale-trend defect was reproduced during fault/rebuilding: the core
correctly withheld HR while the trend header looked current. The corrected
trend never exposes a numeric “current” summary unless
`predictionAvailability === "available"`; retained history is labeled as
historical and gaps remain gaps. No reference HR line or smoothing was added.

## HR and affected-region adjudication

The ring is accepted as a four-item categorical availability checklist because
the visible proximate label explicitly says “not confidence or model
certainty,” the readable checklist is the textual source of truth, unavailable
states retain meaning, and mobile sizing remains legible.

Affected-region wording now says “No active simulated-fault region” and
separately lists confirmed replay inputs. It makes no whole-body, diagnosis,
health, or channel-completeness claim. EEG/EOG absence remains visible.

## Accessibility and reduced motion

Landmarks, heading order, names, expanded/selected states, status boundaries,
and color-independent text were inspected. Skip navigation, mobile More,
drawer focus entry/trap/Escape/restoration, and inert background passed with
real keyboard input. The Settings switch now has an accessible name and visible
focus style. A fresh two-tab test changed `false,false` to `true,true` for
both switch state and effective `reduce-motion` class, then restored it.

No VoiceOver claim is made:
`ACTUAL_SCREEN_READER_STATUS: DEFERRED_BY_OWNER_UNTIL_AFTER_STAGE7`.

## Evidence architecture and adjudication

`docs/JURY_RELEASE_EVIDENCE_POLICY.json` is the explicit source of canonical
selection. Every required slot has its own exact path, SHA-256, approval,
superseded list, and audit-only list. Unknown future matches, same-slot
duplicates, digest drift, missing approval, missing canonical, or empty
canonical fail closed. Different slots can deliberately select different runs.
Codex's audit is explicitly audit-only.

All selected canonical PNGs were opened, not merely hashed. Text and JSON show
canonical, superseded, audit-only, unregistered, expected digest, actual digest
when requested, and issues. Final result: exit 0 for 23 required PRESENT,
one optional MISSING, zero EMPTY, zero AMBIGUOUS.

## Scientific-integrity ledger

- HR model/checkpoint: unchanged.
- Replay/dataset contract and source identity: unchanged.
- Store access/ownership: unchanged; 20 protected consumers pass.
- Fail-closed source error, confirmation, and prediction availability: preserved.
- Missing data: never converted to zero.
- Synthetic data: never presented as model output.
- No diagnostic, health, confidence, validation, or population claim added.
- S14 remains described as a single-participant robustness demonstration.

## Final verification and reproduction

Run:

```sh
cd frontend
npm run verify:monitoring
npm run lint
npx tsc --noEmit
npm run build
cd ../backend
python -m pytest -q
cd ..
python3 scripts/verify_jury_release_evidence.py --root .
python3 scripts/verify_jury_release_evidence.py --root . --hash
python3 scripts/verify_jury_release_evidence.py --root . --hash --json
git diff --check
```

Final counts: monitoring 1059/1059; backend 351 passed, 4 skipped; production
build 14/14; evidence 23 PRESENT, one optional MISSING, zero ambiguity.

## Remaining risks and recommendation

Docker startup was not reproducible on this host. OS-level reduced-motion was
inspected through the shared OR logic but the available in-app browser exposed
no media-query emulation; app load/live/cross-tab behavior passed. Actual
screen-reader acceptance remains deferred. These are external/deferred gates,
not unresolved Stage 4–5 product defects.

Recommend merge after owner approval. No merge was performed.

```yaml
CODEX_STAGE4_5_INDEPENDENT_AUDIT_STATUS: COMPLETE
SOURCE_SHA_VERIFIED: YES
ISOLATED_WORKTREE_CONFIRMED: YES

CLAUDE_STAGE4_VERDICT_INDEPENDENTLY_ACCEPTED: YES
CLAUDE_STAGE5_VERDICT_INDEPENDENTLY_ACCEPTED: YES
CLAUDE_EVIDENCE_VERDICT_INDEPENDENTLY_ACCEPTED: YES

MONITORING_BASELINE_REPRODUCED: YES
MONITORING_FINAL_COUNT: "1059/1059"
LINT_PASSED: YES
TYPESCRIPT_PASSED: YES
PRODUCTION_BUILD_PASSED: YES
BACKEND_TEST_RESULT: "351 passed, 4 skipped"

DESKTOP_FIRST_VIEWPORT_CONTRACT: PASS
TABLET_1024_FIRST_VIEWPORT_CONTRACT: PASS
MOBILE_390_FIRST_VIEWPORT_CONTRACT: PASS
REAL_200_PERCENT_ZOOM_CONTRACT: PASS

CRITICAL_FAULT_TEXT_TRUNCATED: NO
AFFECTED_REGION_SEMANTICS_ACCURATE: YES
HR_RING_SEMANTICS_ACCEPTABLE: YES
TREND_LEGIBILITY_ACCEPTABLE: YES
ESSENTIAL_TEXT_BELOW_12PX_REMAINING: NO
SHARED_PANEL_CONSUMER_REGRESSIONS: NO
CARD_WALL_MATERIAL_FINDING_REMAINING: NO

REAL_S14_CYCLE_REPRODUCED: YES
FAULT_STATE_VERIFIED: YES
GENUINE_REBUILDING_VERIFIED: YES
REBUILDING_SHOWS_NUMERIC_CURRENT_HR: NO
RECOVERY_VERIFIED: YES
RECOVERY_METADATA_MATCHES_PIXELS: YES

EVIDENCE_VERIFIER_EXIT_ZERO: YES
SAME_RUN_DUPLICATE_FAILS_CLOSED: YES
UNKNOWN_FUTURE_RUN_HANDLED_SAFELY: YES
CANONICAL_EVIDENCE_SELECTION_EXPLICIT: YES
SUPERSEDED_EVIDENCE_TRACEABLE: YES
CODEX_AUDIT_EVIDENCE_AUTOMATICALLY_CANONICAL: NO

SCIENTIFIC_BEHAVIOR_CHANGED: NO
FAIL_CLOSED_BEHAVIOR_PRESERVED: YES
SOURCE_IDENTITY_PRESERVED: YES
DATASET_HISTORY_ISOLATION_PRESERVED: YES
MISSING_DATA_RENDERED_AS_ZERO: NO
SYNTHETIC_PRESENTED_AS_MODEL_OUTPUT: NO
DUPLICATE_MONITORING_OWNERSHIP_INTRODUCED: NO

KEYBOARD_AND_DIALOG_ACCEPTANCE_PASSED: YES
REDUCED_MOTION_MATRIX_PASSED: YES
ACCESSIBILITY_TREE_REVIEW_COMPLETE: YES
ACTUAL_SCREEN_READER_STATUS: DEFERRED_BY_OWNER_UNTIL_AFTER_STAGE7

STAGE6_STARTED: NO
STAGE7_INTEGRATED: NO
ISMET_STAGE7_BRANCH_MODIFIED: NO
MAIN_MODIFIED: NO
CLAUDE_SOURCE_BRANCH_MODIFIED: NO
DATASET_OR_CHECKPOINT_COMMITTED: NO
PRIVATE_ABSOLUTE_PATH_COMMITTED: NO
FORCE_PUSH_USED: NO
TASK_SERVICES_STOPPED: YES
WORKING_TREE_CLEAN: YES
LOCAL_REMOTE_SHA_MATCH: YES

HIGH_SEVERITY_FINDINGS_REMAINING: 0
MEDIUM_SEVERITY_FINDINGS_REMAINING: 0
READY_FOR_MERGE_AFTER_OWNER_APPROVAL: YES
MERGE_PERFORMED: NO
```
