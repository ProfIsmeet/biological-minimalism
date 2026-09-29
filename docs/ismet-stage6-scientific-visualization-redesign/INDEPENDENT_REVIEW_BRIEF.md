# Independent Review Brief — Stage 6 Scientific Visualization Redesign

What a genuinely independent reviewer (a fresh Codex/Claude session with no
memory of this implementation) must challenge before recommending merge.

## Priority items to re-verify independently

1. **Re-derive the exact source SHA and branch identity** — do not trust
   this report; run `git rev-parse origin/codex/stage7-final-acceptance-closure`
   yourself and compare to `011a31683ce3444cd1b8f258c0308fb4c6997490`.
2. **Obtain the PPG-DaLiA dataset archive and re-capture all replay-dependent
   evidence** this implementation pass could not: real HR trend, a
   populated fault/recovery timeline (apply a real simulated fault, confirm
   the onset/clear markers land at the correct real replay-time positions,
   confirm an ongoing fault correctly extends to the current edge, confirm
   3+ fault/recovery cycles don't duplicate/corrupt the event log), real
   waveform lanes.
3. **Genuine 200% browser zoom** — not attempted in this pass at all;
   independently determine whether it passes, fails, or is
   `BLOCKED_EXTERNAL` in your environment, following the same "no CSS/
   transform/emulation substitute" discipline the project's prior Stage 7
   audit established.
4. **Stress-test `FaultRecoveryTimeline` at 390px with real populated
   data** — the one specific, disclosed gap in `VISUAL_ACCEPTANCE_MATRIX.md`.
5. **Independently re-verify every number in `SensitivitySmallMultiples.tsx`
   and `evidenceBurdenMatrix.ts`** against the cited `results/*.json` files
   — this implementation copied them by hand (with care, cross-checked
   against `results/final_figure_manifest.json`'s own provenance list), but
   a fresh, independent re-read of the raw JSON is the correct verification
   standard, not trusting this report's transcription.
6. **Confirm the missing spec directory claim** — verify independently
   that `frontend/qa-screenshots/codex-independent-final-frontend-audit/`
   genuinely does not exist at the source tip (this report claims it
   doesn't; don't take that on trust either).
7. **Re-run the full self-adversarial review checklist** from the master
   task's own §30 independently — this implementation's own pass
   (`FINDING_LEDGER.md`) found and fixed 2 real defects (S6-FIND-01 HIGH,
   S6-FIND-02 MEDIUM) but is explicitly NOT a substitute for an
   independent audit, per the master task's own instruction.
8. **Re-verify cross-component consistency claims in `CROSS_COMPONENT_CONSISTENCY.md`
   live in a browser**, not just by reading source code as this report did
   — e.g., confirm the coverage matrix and pipeline strip genuinely agree
   on PPG/IMU state during a live fault-injection cycle.
9. **Confirm no `main`/Stage 7/Stage 4-5 source branch was modified** —
   independently check `git log`/`git diff` against those refs.
10. **Re-run the evidence verifier and confirm the exit-code-2 baseline is
    genuinely unchanged** by this task, not merely re-stated.

## What this implementation does NOT claim

- Not claimed: `COMPLETE_ACCEPTED` — see `MERGE_RECOMMENDATION.md` for the
  exact verdict and why.
- Not claimed: full screen-reader verification (explicitly
  `DEFERRED_BY_OWNER_UNTIL_STAGE9`).
- Not claimed: exhaustive 25-item screenshot coverage — 16 of 25 suggested
  items captured, with an honest accounting of what's missing and why in
  `EVIDENCE_MANIFEST.md`.
- Not claimed: this implementation's own adversarial self-review
  (`FINDING_LEDGER.md`) is a substitute for independent review.
