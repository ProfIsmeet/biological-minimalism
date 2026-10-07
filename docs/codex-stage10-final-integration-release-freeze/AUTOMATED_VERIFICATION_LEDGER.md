# Automated Verification Ledger

| Gate | Final result |
|---|---|
| Monitoring + seven sub-verifiers | 1345/1345, PASS |
| Rendered routes | 146/146 |
| Backend full suite | 365 passed, 4 skipped |
| SHAP concurrency | 2 passed |
| Public contract/deployment | 23 passed |
| TypeScript / ESLint | PASS / PASS |
| Production build | 14/14 pages |
| Scientific verifier | PASS |
| Stage 10 evidence | 42 artefacts, 160 checks, hashes/review PASS |
| Legacy release evidence | PRESENT 23, optional missing 1, ambiguous 0 |
| Stage 8 closure | 565 PASS, 0 FAIL, 40/40 slots |
| Stage 9 evidence | PASS, 23 reports, 10 transcripts |
| Clean clone | PASS |
| Local endurance | 600 s, 3 clients, PASS |
| Public WSS | 60 s, 2 clients, PASS |
| Diff/conflict/secret/path/asset scans | PASS |
| Docker runtime | BLOCKED_EXTERNAL |

Core commands: `npm run verify:monitoring`, `node scripts/verify-rendered-routes.mjs <origin>`, `pytest -q`, `pytest -q tests/test_explainability_concurrency.py`, `pytest -q tests/test_public_presentation.py tests/test_deployment_contract.py`, `npm run lint`, `npx tsc --noEmit`, `npm run build`, `npm run verify:stage10-scientific`, `npm run verify:stage10-evidence`, `python3 scripts/verify_jury_release_evidence.py --root . --hash`, and `npm run verify:stage10-manifest`.
