# Verification Ledger

Implementation checkpoint: `c688d54c37dbd71d8dee1619bd388cf3b3b05b51`.

| Command / check | Result |
|---|---|
| `npm ci` | 452 packages installed from lock; two npm audit notices (1 moderate, 1 high), no automatic mutation performed. |
| `npm run verify:monitoring` (baseline) | 1059/1059. |
| `npm run verify:monitoring` (final) | 1085/1085 plus all structural scripts pass. |
| `npm run lint` | PASS. |
| `npx tsc --noEmit --incremental false` | PASS. |
| `npm run build` | PASS; 14/14 pages. |
| `.venv-integration/bin/python -m pytest -q` | 351 passed, 4 skipped. |
| `python3 scripts/verify_jury_release_evidence.py --root . --hash` | exit 0; 23 required PRESENT; 1 optional MISSING; 0 EMPTY/AMBIGUOUS. |
| `git diff --check` | PASS. |
| Real keyboard | PASS for focus, 3/chest, 4/wrist, Escape/reset. |
| Accessibility tree | PASS; complete non-canvas state/topology exposed. |
| Reduced motion | PASS for Settings enable/disable and cross-tab propagation. |
| Navigation | PASS for discoverability, direct route, refresh, back, forward. |
| Runtime console | No errors; one upstream deprecation warning. |
| WebGL supported | PASS; canvas rendered in real browser. |
| WebGL unsupported/loss/retry | BLOCKED_EXTERNAL runtime; structural guard PASS. |
| 200% zoom | BLOCKED_EXTERNAL. |
| VoiceOver | OWNER_DEFERRED. |

The backend rerun using `-p no:cacheprovider` was started in parallel and initially exceeded one tool-yield window; the already-complete baseline run produced the exact accepted `351 passed, 4 skipped` result.
