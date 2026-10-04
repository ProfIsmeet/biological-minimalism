# Test-change audit

- Existing source tests removed: 0.
- Existing assertions weakened: 0.
- Expected values loosened: 0.
- Dependency versions changed: 0.
- Product files changed: 0.
- New permanent dependency: 0.
- New closure scripts: capture, genuine zoom capture, Chrome accessibility-tree verification, manifest generation, and fail-closed manifest verification.

The scripts use the available workspace/browser runtime and installed Chrome; they do not alter package manifests. The new verifier adds checks without modifying the existing release verifier. It fails on missing/empty/undecodable files, dimension or hash disagreement, absent required coverage, ambiguous canonical slots, superseded-as-canonical state, private absolute paths, or missing visual decisions.

The targeted SHAP concurrency suite remained 2/2 and the complete backend suite remained 353 passed with 4 skipped. Monitoring stayed 1341/1341 with all seven sub-verifiers.
