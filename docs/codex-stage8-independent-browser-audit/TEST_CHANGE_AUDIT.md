# Test-change audit

- Source Stage 8 tests removed: `0`.
- Review-branch tests removed: `0`.
- Assertions weakened or expected values loosened: `0`.
- Browser finding replaced by source-only reassurance: `NO`.
- Monitoring assertions added: `14` (`1327` to `1341`).
- Backend tests added: `2`; full suite moved from `351 passed, 4 skipped` to `353 passed, 4 skipped`.

The SHAP tests use a deliberately non-reentrant stand-in and real thread-pool concurrency, so they fail if calls overlap. UI checks preserve exact source-aware wording, content-safe breakpoints, and minimum target classes; they supplement, rather than replace, Chromium measurements.
