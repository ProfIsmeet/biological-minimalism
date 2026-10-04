# Automated verification ledger

| Gate | Baseline | Final |
|---|---|---|
| Lockfile install | `npm ci` PASS; no version update; npm reported 1 moderate/9 high advisory items | unchanged dependencies |
| TypeScript | PASS | PASS |
| ESLint | PASS | PASS |
| Production build | PASS, 14 static-generation pages | PASS, 14 static-generation pages |
| Monitoring | `1327/1327` | `1341/1341` |
| Monitoring sub-verifiers | 7/7 PASS | 7/7 PASS |
| Rendered routes | `146/146` | `146/146` |
| Backend | `351 passed, 4 skipped` | `353 passed, 4 skipped` |
| Release evidence | exit 0; PRESENT 23, optional MISSING 1, EMPTY 0, AMBIGUOUS 0 | same |
| `git diff --check` | PASS | PASS |

Final frontend command: `tsc --noEmit && npm run lint && npm run verify:monitoring && NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8138 npm run build`.

Final rendered command: `npm run verify:rendered -- http://127.0.0.1:3148`.

Final backend command: `python -m pytest -q -p no:cacheprovider`.
