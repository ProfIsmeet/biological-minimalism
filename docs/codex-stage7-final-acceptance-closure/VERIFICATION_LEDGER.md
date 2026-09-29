# Verification Ledger

## Environment

- Node.js 22.23.1; npm 10.9.8
- System Python 3.14.5; repository backend environment Python 3.12.14
- macOS 26.5.2 build 25F84
- Safari 26.5.2

## Baseline and final gates

| Command / activity | Baseline | Final |
| --- | --- | --- |
| `npm run verify:monitoring` (`frontend`) | PASS, 1116/1116; seven chained verifiers pass | PASS, 1116/1116; seven chained verifiers pass |
| `npm run lint` (`frontend`) | PASS | PASS |
| `npx tsc --noEmit --incremental false` (`frontend`) | PASS | PASS |
| `npm run build` (`frontend`) | PASS, 14/14 routes | PASS, 14/14 routes |
| `.venv/bin/python -m pytest -q` (`backend`) | PASS, 351 passed, 4 skipped | PASS, 351 passed, 4 skipped |
| Release verifier plain/hash/JSON/JSON+hash | PASS, exit 0, 23/1 optional/0/0 | PASS, exit 0, 23/1 optional/0/0 |
| `git diff --check` | PASS | PASS |
| Screenshot dimensions/hashes/uniqueness | not applicable | PASS, twelve unique 2880×1800 PNGs |

`npm ci` installed 452 packages and reported advisory output (one moderate and one high npm audit item). No audit fix was authorized or applied; this did not alter the lockfile. Build route output contained 14 routes. Existing non-blocking runtime diagnostics were a Three.js `Clock` deprecation warning, a Safari-extension hydration mismatch involving `coupert-item`, expected service-unavailable messages on an unrelated backend-dependent route while port 8000 was intentionally absent, and normal WebGL context loss during route teardown.

The first final-state build attempt completed monitoring, lint, and TypeScript but the build process could not open ignored `.next/trace` under the managed sandbox (`EPERM`). Re-running the identical build with worktree write permission passed 14/14; this was an execution-permission issue, not a product failure. The final backend run passed with two `PytestCacheWarning` messages because the managed sandbox denied updates inside the existing ignored `.pytest_cache`; test collection and assertions were unaffected.

## Structural verifiers

The monitoring chain passed the monitoring-state suite and the consumer ownership, live-region boundary, reduced-motion unification, modal dialog primitive, WebGL fallback, and Stage 7 Digital Twin verifiers. No test or expected count was removed or weakened.

## Browser gates

The 100% anatomy spot-check and full genuine 200% matrix passed. Reduced motion was exercised only through the application path; OS settings were not changed. Prior unchanged WebGL unsupported, context-loss, retry, responsive, and anatomy evidence was hash-reviewed and retained.
