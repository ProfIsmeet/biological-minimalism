# Stage 3 — Gate 3 Final Resolver Closure Report

Branch `stage3-gate3-final-resolver-closure`, base
`stage3-acceptance-gate-closure @ a06e61a84beb31838fc529cf64d805109a56fef0`.
No science retrained, reevaluated, or numerically changed.

## The exact defect

`resolve_current()` resolved governance (registry + semantic check) but
never verified hash integrity, while `resolve_and_verify()` did. The
independent auditor demonstrated:

```
resolve_current: ACCEPTED_CORRUPTED 999.0
resolve_and_verify: REJECTED IntegrityVerificationError HASH_MISMATCH
```

A corrupted governing artifact could therefore be consumed through a
documented, public current-resolution API.

## The fix

- Extracted hash-verification into a single shared `_verify_integrity(path)`
  helper — no duplicated integrity logic.
- `resolve_and_verify()` now calls it (behavior unchanged).
- `resolve_current()` is now a literal one-line alias:
  `return resolve_and_verify(family_id)`. There is exactly one verified
  resolution implementation.
- `resolve_by_path_or_status()` — the third public route that returns
  governing content — was audited per Section 9 and found to have the
  identical gap for its `GOVERNING`-status success path. Fixed
  identically (calls `_verify_integrity()` before returning content).
- Added `_resolve_current_unverified()`: a private, underscore-prefixed
  helper performing registry + semantic checks only, no hash check.
  Documented in its own docstring as never safe for science consumption,
  never exported, never to be used by Stage-4 code — for internal
  debugging only.

## Public API inventory

| Function | Returns governing content? | Integrity-verified? |
|---|---|---|
| `resolve_current(family_id)` | Yes | **Yes** (alias of `resolve_and_verify`) |
| `resolve_and_verify(family_id)` | Yes | **Yes** (authoritative implementation) |
| `resolve_by_path_or_status(path)` | Yes, for `GOVERNING` paths | **Yes** (fixed this sprint) |
| `resolve_governing_path(family_id)` | No (returns a path string only) | N/A — caller must not read the file directly; use the above instead |
| `_resolve_current_unverified(family_id)` | Yes | **No** — private, documented as unsafe, not a public route |

## Hostile corruption probe

Corrupted `results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json`'s
`A_mean` field, called both public routes, restored the file
byte-for-byte afterward:

```
resolve_current:      REJECTED IntegrityVerificationError HASH_MISMATCH
resolve_and_verify:   REJECTED IntegrityVerificationError HASH_MISMATCH
```

Made permanent as
`ml/tests/test_stage3_gate3_final_resolver_closure.py::test_reproduces_auditors_exact_attack_both_apis_reject`.

## Handoff

`docs/STAGE3_HANDOFF_TO_EMIR_AND_INTEGRATION_OWNER.md`'s opening
resolver-usage paragraph rewritten: states `resolve_current` is the
authoritative call, explicitly notes it is a direct alias of
`resolve_and_verify` (not a separate lower-safety route), and explicitly
prohibits using `_resolve_current_unverified()` for science consumption
or Stage-4 code. No remaining wording recommends an unsafe alternative.

## Freeze

Regenerated after the handoff doc's legitimate content change: **21
registry families, 21 governing artifacts, 31 tracked frozen files** —
unchanged counts from the prior sprint (only the handoff's own hash
updated). No stale freeze hash left behind.

## Tests

Static inventory before this sprint: **539**. Tests added: **13**
(`test_stage3_gate3_final_resolver_closure.py`, covering Tests A-H plus
the exact attack reproduction, the alias-not-duplicate check, and the
private-helper-is-unsafe check). Static inventory after: **552**.
Executed: **552 collected, 552 passed, 0 failed, 0 skipped, 0 collection errors.**

## Science non-regression

Confirmed byte/value-identical: Galaxy A_cap-B=+0.834268 bpm,
C-B=+0.916231 bpm, `EXTERNAL_REPLICATION_SUPPORTIVE`; LBNP A=20.972675,
B=21.425060, C=20.131778 mmHg, `COMPLETE_MIXED`.

## Final self-test

"No documented/public CURRENT science resolution route can return
modified governing content whose bytes/text no longer match the frozen
integrity record." — **TRUE**, verified for `resolve_current`,
`resolve_and_verify`, and `resolve_by_path_or_status`.

## Remaining carried limitations

Unchanged from the prior sprint: PPG/PTT cache provenance, HMC/ds003838
full-cohort work (`FULL_COHORT_PENDING`), 6 unverified HMC recording
pairs, unavailable historical Mac-reproduction checkpoint bytes.

## Architecture

`FINAL_ARCHITECTURE = UNRESOLVED`. `FORMAL_PARETO = NOT_READY`. Unchanged.

## Verdict

`STAGE3_GATE3_RESOLVER_FAIL_CLOSURE_REPORTED_CLOSED_PENDING_FINAL_INDEPENDENT_ACCEPTANCE`
