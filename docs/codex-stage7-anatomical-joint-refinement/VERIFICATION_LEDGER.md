# Verification ledger

## Baseline at `f80280a41034b3b5e535b9dca0874029fa2d9e45`

| Gate | Result |
|---|---|
| Git source identity | PASS — exact required SHA |
| `npm run verify:monitoring` | PASS — `1091/1091`, all structural verifiers pass |
| `npm run lint` | PASS |
| `npx tsc --noEmit` | PASS after allowing incremental metadata write |
| `npm run build` | PASS — 14/14 routes |
| `git diff --check` | PASS |
| Fresh browser baseline | PASS — seven legacy diagnostic PNGs captured |

## Final at implementation checkpoint `972cedd591320bf8a283cbf964160fd61b6f0d17`

| Gate | Result |
|---|---|
| `npm run verify:monitoring` | PASS — `1116/1116`, all structural verifiers pass |
| Pure geometry topology | PASS — one component, all edges incidence 2, no boundaries/non-manifold edges |
| `npm run lint` | PASS |
| `npx tsc --noEmit` | PASS. One parallel run briefly referenced the deleted temporary capture route in stale `.next/types`; the successful production build refreshed generated types and the immediate rerun passed cleanly. |
| `npm run build` | PASS — compiled, typechecked, generated 14/14 routes |
| Backend `.venv/bin/python -m pytest -q` | PASS — `351 passed, 4 skipped in 11.23s` |
| `python scripts/verify_jury_release_evidence.py --root .` | PASS/exit 0 — `PRESENT=23 MISSING=1(optional) EMPTY=0 AMBIGUOUS=0` |
| `git diff --check` | PASS |
| Real-browser view matrix | PASS — 13 final PNGs plus live inspection |
| Console | PASS — zero errors; two pre-existing Three.js `Clock` deprecation warnings |
| Canvas/lifecycle | PASS — canvas count `1 → 0 → 1` across route unmount/remount |
| View controls | PASS — keys 1–4 and Home exercised on clean server |
| Screenshot hashes | PASS — SHA-256 recorded for all files |

The release verifier result is reported exactly. This surgical task did not independently re-prove the separate genuine browser 200% zoom gate and does not claim ownership of broader release-evidence policy closure.
