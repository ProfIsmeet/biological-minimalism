# Codex Spot-Audit Brief — Stage 6 Fresh-Session Audit & Closure

What a later, genuinely independent Codex spot audit should re-verify
first, in priority order.

1. **Re-derive the exact identity chain independently**: `git rev-parse
   origin/ismet/stage6-scientific-visualization-redesign` should equal
   `82d136ab104211bd3d854e096faca123e95be225`; the branch under review
   (`ismet/stage6-final-audit-closure`) should trace to it exactly.
2. **Re-run the evidence verifier from a completely fresh clone** (not
   this worktree) to confirm the `.gitattributes` fix genuinely works on a
   from-scratch checkout, not just on the worktree this audit happened to
   fix in place. This is the single highest-value re-check, since it
   validates the root-cause claim rather than the specific-machine patch.
3. **Independently obtain a PPG-DaLiA dataset archive and a trained HR
   checkpoint**, and re-run the populated fault/recovery timeline exercise
   from scratch. This audit's own artifacts came from a session-local
   scratchpad that will not exist in a fresh environment — a spot audit
   must independently source or be given equivalent assets to re-verify
   `POPULATED_TIMELINE_ACCEPTANCE.md`'s claims are reproducible, not a
   one-off.
4. **Re-attempt genuine native 200% zoom** with a different automation
   stack (e.g., real OS-level input injection outside CDP's scope, or a
   manual human tester) — this remains the one gate neither this audit nor
   its predecessor could close.
5. **Re-check S6A-FIND-05's disclosed upstream limitation**
   (`prediction_recovered` essentially never firing in
   `operationalEvents.ts`'s `deriveEventsFromTransition`) — this audit
   deliberately worked around it within its own module rather than fixing
   the shared infrastructure. A spot audit should judge whether that
   upstream bug itself now warrants a dedicated fix outside Stage 6's
   scope, and whether this audit's workaround is the right long-term
   answer or a stopgap.
6. **Verify no Stage 4-5/Stage 7 regression** by diffing this branch
   against `main` and against `origin/codex/stage7-final-acceptance-closure`,
   confirming only the files listed in this report set's commit summaries
   changed.
7. **Spot-check 2-3 of this audit's own SHA-256 hashes** against the
   actual committed PNG bytes to confirm the manifest wasn't
   miscomputed or edited after the fact.
8. **Re-read `FINDING_LEDGER.md`'s S6A-FIND-04 finding** and confirm, via
   its own code, that `prediction_available` genuinely cannot trigger a
   spurious "Recovery" marker any more — this is a subtle classification
   bug class (two semantically different transitions sharing one output
   kind) worth an independent re-derivation, not just trusting this
   report's narrative.

## What this audit does NOT claim

- Not claimed: this is a fully independent external audit — see the
  `AUDIT_DESIGNATION` field and the explicit limitation statement in
  `MASTER_FRESH_SESSION_AUDIT_AND_CLOSURE.md`.
- Not claimed: genuine native 200% zoom passes — honestly `BLOCKED_EXTERNAL`.
- Not claimed: the populated-timeline evidence is reproducible on a machine
  without access to a PPG-DaLiA archive and a trained checkpoint — it is
  real, genuine evidence from THIS session, not a claim that any future
  session can trivially reproduce it without equivalent assets.
- Not claimed: `S6A-FIND-05`'s upstream root cause in `operationalEvents.ts`
  is fixed — only worked around within this task's own ownership boundary.
