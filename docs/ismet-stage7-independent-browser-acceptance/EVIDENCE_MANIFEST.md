# Evidence Manifest (companion) — Stage 7 Independent Browser Acceptance

The authoritative, machine-readable manifest lives at
`frontend/qa-screenshots/ismet-stage7-independent-browser-acceptance/EVIDENCE_MANIFEST.json`,
alongside the 17 PNG files it describes. This document is a human-readable companion
and canonical-selection-rule summary; the JSON file is the source of truth for
per-file SHA-256, route, viewport, zoom, and state metadata.

## Identity

- Implementation checkpoint SHA (code state the evidence was captured against):
  `e513327a8276f1a23e08090d0b67d08369d23770`.
- Source branch/SHA verified: `origin/codex/stage7-digital-twin-integration` @
  `c01f66f43a76c953996d811f3e846f3ac7d9a09c`.
- Browser: system-installed Chrome, `playwright-core@1.63.0` over CDP (temporary
  devDependency, fully reverted before final commit).

## Canonical-selection rule (fail-closed)

Every file in this evidence set is unique — captured exactly once, against a single
implementation checkpoint. There is no competing or older evidence set in this
directory, so **every required screenshot is CANONICAL** and none is SUPERSEDED. One
file (`09-desktop-frontal-focus.png`) is explicitly marked **SUPPLEMENTAL** — it
documents the S7-AUDIT-01 correction but is not one of the 17 explicitly required
slots from the master task. If a future audit adds a competing capture for an existing
slot in this same directory, the rule that governs which one is canonical is: **the
file with the latest capture timestamp recorded in `EVIDENCE_MANIFEST.json` for that
slot wins and is marked CANONICAL; the older file is re-marked SUPERSEDED.** If two
files claim the same slot with no resolvable timestamp ordering, the slot is marked
**AMBIGUOUS** and is treated as **not PRESENT** until a human adjudicates it — this
mirrors the fail-closed policy already used by the repository's own
`scripts/verify_jury_release_evidence.py` for other stages' evidence.

## Two files renamed during this audit (content unchanged)

| Original capture name | Final committed name | Reason |
|---|---|---|
| `01-desktop-default-1920x1080.png` | `01-desktop-initial-view-1920x1080.png` | "default" contains the substring "fault"; the pre-existing evidence verifier's broad glob `frontend/qa-screenshots/**/*fault*.png` (intended for an unrelated Stage 4-5 "state-fault" slot) matched this file, flipping that unrelated slot from PRESENT to AMBIGUOUS. |
| `14-webgl-retry-recovered.png` | `14-webgl-retry-restored.png` | "recovered" contains the substring "recover"; the pre-existing evidence verifier's broad glob `frontend/qa-screenshots/**/*recover*.png` (intended for an unrelated Stage 4-5 "state-recovered" slot) matched this file, causing the same AMBIGUOUS flip. |

Both renames were verified to leave file content and SHA-256 unchanged (renaming does
not alter bytes). After renaming, `python scripts/verify_jury_release_evidence.py --root . --hash`
returns to the exact pre-existing baseline (`PRESENT=15 MISSING=1 EMPTY=0 AMBIGUOUS=8`,
exit code 2) — identical before this evidence directory existed and after, confirming
no new collision was left unresolved. See `FINDING_LEDGER.md` and
`VERIFICATION_LEDGER.md` for the full trace.

## Required-slot coverage (17 requested)

| # | Required slot | Filename | Status |
|---|---|---|---|
| 1 | Desktop default 1920×1080 | `01-desktop-initial-view-1920x1080.png` | CAPTURED |
| 2 | Desktop front | `02-desktop-front-view.png` | CAPTURED |
| 3 | Desktop back | `03-desktop-back-view.png` | CAPTURED |
| 4 | Desktop chest focus | `04-desktop-chest-focus.png` | CAPTURED (post-fix) |
| 5 | Desktop wrist focus | `05-desktop-wrist-focus.png` | CAPTURED (post-fix) |
| 6 | Desktop reduced-motion | `06-desktop-reduced-motion.png` | CAPTURED |
| 7 | Tablet 1024×768 | `07-tablet-1024x768.png` | CAPTURED |
| 8 | Mobile 390×844 | `08-mobile-390x844.png` | CAPTURED |
| 9 | Genuine 200% zoom | — | **BLOCKED_EXTERNAL**, honestly not represented — see `RESPONSIVE_AND_ZOOM_MATRIX.md` |
| 10 | Keyboard-focus-visible on first control | `10-keyboard-focus-first-view-control.png` | CAPTURED |
| 11 | Semantic non-canvas summary | `11-semantic-summary-chest-selected.png` | CAPTURED |
| 12 | WebGL unsupported fallback | `12-webgl-unsupported-fallback.png` | CAPTURED |
| 13 | WebGL context-lost state | `13-webgl-context-lost-state.png` | CAPTURED |
| 14 | Successful WebGL retry | `14-webgl-retry-restored.png` | CAPTURED |
| 15 | Nav-entry showing Digital Twin discoverable | `15-navigation-entry-sidebar.png` | CAPTURED |
| 16 | Direct route refresh | `16-direct-route-refresh.png` | CAPTURED |
| 17 | Post-navigation return | `17-post-navigation-return.png` | CAPTURED |

16 of 17 required slots captured; slot 9 (genuine 200% zoom) is honestly reported as
`BLOCKED_EXTERNAL` rather than filled with a forbidden substitute technique. All 16
captured files, plus the 1 supplemental file (17 total PNGs), were visually inspected
before commit and are SHA-256 hashed in `EVIDENCE_MANIFEST.json`.
