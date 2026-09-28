# Change Ledger

SOURCE_SHA: `979836ff704c2d6df43152e4d733d48703d12848`
IMPLEMENTATION_CHECKPOINT_SHA: `6d169c4abe6d68a7758f515bad5df39b8d851727`
REPORT_COMMIT: this commit; resolve with `git rev-parse HEAD`
Target: `codex/stage4-5-independent-visual-audit`

- Mission Overview: corrected tablet ordering, mobile next-state placement, affected-region language, HR-ring explanation, unavailable-current trend behavior, essential label sizing, and stale comments.
- Shared presentation: made Panel headers resilient to long titles/actions and installed a 12px floor for legacy 9–11px utility classes.
- Settings: added an accessible switch name, visible keyboard focus, and live cross-tab preference synchronization.
- Monitoring protection: added `hrOperationalPresentation.ts` as a pure fail-closed presentation boundary and replaced critical source-string-only assertions with behavioral cases.
- Evidence selection: removed hidden global run precedence; added `docs/JURY_RELEASE_EVIDENCE_POLICY.json` with per-slot canonical path, pinned SHA-256, visual-review flag, superseded set, and audit-only set.
- Evidence tests: cover missing policy, same-slot unknown collision, future run, independent audit classification, per-entry mixed canonical runs, empty canonical, hash drift, and unreviewed canonical.
- Scientific boundary: no model, replay, identity, store ownership, availability contract, dataset, or checkpoint was modified.
