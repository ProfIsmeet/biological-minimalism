# Evidence adjudication

Fresh final-branch screenshots were rendered and visually inspected through the in-app Chromium surface. The control surface returned screenshot bytes and, for a subset, SHA-256 values, but its security boundary prevented exporting those bytes into the managed worktree. A `data:` export attempt was blocked; no workaround or fabricated file was used.

Accordingly:

- repository-backed final screenshot count: `0`;
- transient screenshots visually reviewed: more than 30, spanning every route and required breakpoint class;
- representative hash records retained in `EVIDENCE_MANIFEST.json`: `12`;
- canonical/ambiguous final screenshots: `0 / 0`;
- Stage 8 durable evidence requirement: **BLOCKED_EXTERNAL**;
- existing release-evidence verifier: exit `0`, PRESENT `23`, optional MISSING `1`, EMPTY `0`, AMBIGUOUS `0`.

Earlier-branch images were never used as proof of this branch. Full-page images affected by the browser's stitching duplication artifact were rejected for canonical use.
