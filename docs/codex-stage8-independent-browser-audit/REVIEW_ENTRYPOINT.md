# Review entrypoint

Start with [MASTER_INDEPENDENT_REVIEW.md](MASTER_INDEPENDENT_REVIEW.md), then inspect [FINDING_LEDGER.md](FINDING_LEDGER.md), [AUTOMATED_VERIFICATION_LEDGER.md](AUTOMATED_VERIFICATION_LEDGER.md), [BROWSER_ACCEPTANCE_MATRIX.md](BROWSER_ACCEPTANCE_MATRIX.md), and [EVIDENCE_ADJUDICATION.md](EVIDENCE_ADJUDICATION.md).

Reproduction commands:

```text
cd frontend
npm run verify:monitoring
npm run lint
./node_modules/.bin/tsc --noEmit
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8138 npm run build
npm run verify:rendered -- http://127.0.0.1:3148

cd ../backend
python -m pytest -q -p no:cacheprovider

cd ..
python scripts/verify_jury_release_evidence.py --root . --hash
git diff --check
```

The backend/frontend ports above are examples from this audit; do not leave services running after reproduction.
