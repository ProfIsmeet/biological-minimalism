# Evidence Adjudication

The audit package contains 33 fresh Codex PNGs and one JSON manifest. No Ismet screenshot was reused as independent proof.

- Every PNG was opened and visually inspected.
- SHA-256 and PNG width/height were recomputed from bytes: 33/33 matched.
- Nominal, fault, rebuilding, recovered, startup, awaiting-source, source-error, keyboard, reduced-motion, desktop, tablet, and mobile states are represented.
- The real fault/recovery timeline was produced in one continuing browser session and records a 9.4-second PPG-fault interval followed by a new confirmed HR.
- Canonical release evidence was not replaced. Source-branch and Codex state images are registered as `audit_only` in the fail-closed policy.
- `32-radar-source-error.png` is the real fail-closed result of an authoritative REST failure; it is not relabeled as an awaiting state.
- Genuine 200% zoom has no screenshot because page zoom could not be verified. This is an explicit `BLOCKED_EXTERNAL`, not a synthetic image.

The authoritative file list, state, route, source, viewport, expected facts, pixel dimensions, review flag, and digest are in `frontend/qa-screenshots/codex-mission-overview-independent-visual-audit/EVIDENCE_MANIFEST.json`.
