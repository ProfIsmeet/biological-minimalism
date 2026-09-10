# Post-Stage2-4 Parallel Science Expansion — Hostile Science Review

Scope: this sprint's new work only (checkpoint durability, GalaxyPPG full
training, LBNP structural verification, HMC recheck). Builds on, does not
replace, the prior sprint's `docs/STAGE2_4_HOSTILE_REVIEW_ADDENDUM.md`.

## BLOCKER

None.

## HIGH

None found this sprint.

## MEDIUM

1. **GalaxyPPG P01 is a severe outlier** (MAE ≈32 bpm vs. 4–11 bpm for the
   other 3 test subjects) across all three conditions. Investigated: P01
   is the same subject the dataset's own README flags for a Galaxy Watch
   configuration error — plausibly linked, though that specific flag is
   about GalaxyWatch data, not E4/Polar (which P01 has). **Not excluded**
   — no predeclared data-quality rule flags P01's E4/Polar files as
   invalid, and excluding it now (after seeing the poor MAE) would be
   exactly the post-hoc exclusion this project forbids. Disposition:
   **disclosed, retained, not fixed** — a real, reportable finding.
2. **GalaxyPPG's single-fold bound (not full 6-fold CV)** means the 4 test
   subjects are the only ones with held-out evaluation — the other 20
   subjects' subject-level behavior under this protocol remains unknown.
   This is disclosed explicitly in every result artifact and doc, not
   hidden.
3. **A_cap vs B/C uses a slightly different effective regularization
   exposure**: A_cap's two encoder branches see IDENTICAL input (BVP twice)
   while B/C's two branches see genuinely different modalities — this is
   the same design already accepted for PPG-DaLiA's capacity control (not
   a new confound introduced this sprint), but worth restating as an
   inherited, not resolved, methodological choice.

## LOW

4. `gh release create`/`gh release upload` failed with a "no matches
   found" error when passed multiple file arguments via shell
   command-substitution in one call (worked fine for single-file calls,
   and in a subsequent standalone single-variable invocation) — resolved
   by uploading files individually. Root cause not fully diagnosed
   (suspected CRLF contamination in an intermediate file-list text file);
   does not affect the correctness of the final uploaded/verified
   checkpoints (all 30 total across the two new archives were
   independently re-hashed after re-download and matched exactly).
5. LBNP's real structural verification (this sprint) stopped short of a
   full training pipeline — a disclosed scope decision (Section 121/71:
   LBNP is priority 2, GalaxyPPG priority 1; remaining LBNP work —
   ECG/pleth/MAP native rate extraction, time-alignment implementation —
   was not started this sprint).

## INFO

6. Three independent real data structures in the LBNP archive
   (`LBNPinf`, `SSout`, `Labchart`) all agree on n=16 — stronger
   provenance confirmation than the prior sprint's two-way check.
7. PhysioNet's TLS certificate remains expired as of this sprint's single
   recheck (Section 101 compliance — not retried further).
8. GalaxyPPG's per-subject MAE range (4–33 bpm) is substantially higher
   than PPG-DaLiA's typically-reported values — plausibly reflecting
   GalaxyPPG's genuinely harder semi-naturalistic protocol (TSST stress
   speech, treadmill running, etc.), not a pipeline defect; the R-peak
   detector was independently validated on P02 in the prior sprint
   (physiologically plausible instantaneous HR distribution) and the
   real reference-HR pipeline behaves consistently across all 24
   participants in the eligibility check.

## Capacity-fairness re-confirmation

`A_cap` (28,865 params) vs `B`/`C` (29,089 params) — 0.77% residual,
identical magnitude and rationale to the already-accepted PPG-DaLiA
capacity-control precedent. No new capacity confound introduced.

## Statistical unit compliance re-confirmed

GalaxyPPG: 24 real subjects (eligibility), 4 real held-out test subjects,
5 optimization seeds — never conflated. Real subject-level heterogeneity
(sign reversal) preserved and reported, not averaged away.
