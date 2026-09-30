# Verification Ledger

| Gate | Baseline | Final |
|---|---|---|
| Monitoring | `1239/1239 passed, 0 failed` | `1247/1247 passed, 0 failed` |
| Bundled structural verifiers | All passed | All passed: consumers, live regions, reduced motion, modal primitives, WebGL fallback, Stage 7 |
| ESLint | Pass | Pass |
| TypeScript | Pass | Pass after serial rerun; an initial final attempt raced `next build` while `.next/types` regenerated and was discarded |
| Production build | Pass, 14/14 | Pass, 14/14 |
| Backend pytest | `351 passed, 4 skipped` | `351 passed, 4 skipped, 2 sandbox cache warnings in 13.39s` |
| Environment verifier | `PASS=19 WARN=7 FAIL=0` | `PASS=20 WARN=6 FAIL=0`; Docker/default-path warnings are environmental |
| Release evidence | Exit 2: `PRESENT=21 MISSING=1 AMBIGUOUS=2` | Exit 0: `PRESENT=23 MISSING=1 optional AMBIGUOUS=0` |
| Manifest hash/pixels | N/A | `32/32 passed` |
| `git diff --check` | Pass | Pass |

The final production build compiled, type-checked, generated all 14 static pages, and completed trace collection. The final standalone TypeScript command returned zero after the build. The two pytest warnings concern inability to write optional `.pytest_cache` in the managed worktree; no test failed.

The environment verifier intentionally does not prove the operator-local model location used by the running backend and warned that its default checkpoint/data locations were absent. Runtime S14 provenance and the backend’s validated checkpoint loader independently established the real replay subset. No local asset path is recorded here.
