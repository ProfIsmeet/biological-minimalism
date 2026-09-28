# Evidence Adjudication

The former directory ranking was rejected. The authoritative mechanism is now
`docs/JURY_RELEASE_EVIDENCE_POLICY.json`; each slot independently declares an
exact canonical path, pinned digest, visual-review approval, superseded paths,
and audit-only paths.

Fail-closed rules:

1. Any matching path absent from all three classifications is `AMBIGUOUS`.
2. A missing or empty canonical fails.
3. Digest drift or missing visual approval is `AMBIGUOUS`.
4. Canonical paths must match their slot pattern.
5. Optional absence remains visible but does not fail required completeness.
6. Codex's `AUDIT.md` is explicitly audit-only and cannot become canonical by naming or sorting.

Every selected canonical PNG was opened and inspected, including nominal,
disconnected, fault, rebuilding, recovered, mobile, live monitoring, system
brief, experimental, digital twin, preflight, 200% zoom, and three human-view
images. Text dossiers were also read. The verifier reports 23 PRESENT and one
optional MISSING with no ambiguity. Superseded paths remain in text and JSON.

The independent browser session additionally inspected fresh corrected
viewports and runtime states through CUA. Canonical release artifacts remain
the explicitly adjudicated files in policy; no independent audit directory is
promoted automatically.
