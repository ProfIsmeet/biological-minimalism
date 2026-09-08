# Stage 4 Findings Register

## BLOCKER

None. No finding in this sprint invalidates a reported result or requires
halting the branch.

## HIGH

1. **Unexplained pre-existing untracked result file at session start**
   (`results/qde_v2_leg_bioz_stage2.json` existed on disk before this
   session did any work, with no corresponding trainer script anywhere in
   git history).
   - Evidence: `git status` showed it as untracked on the very first
     command of this session; `git log -- ml/train_qde_v2_leg_bioz.py`
     (before this sprint's commit) returns nothing.
   - Reproduction/inspection path: re-run `git log --all --
     '*qde_v2_leg_bioz*'` on the pre-sprint HEAD.
   - Affected result: none of this sprint's REPORTED numbers (the file was
     moved aside and never used) — but it indicates *something* produced
     real-looking training output outside of any committed, reviewable
     code path at some point.
   - Affected claim: none directly, but it is a genuine integrity/
     provenance gap worth Emir's awareness.
   - Fix: none needed for this branch's own numbers (independently
     regenerated from committed code, reproducibility-verified). Recommend
     asking whoever/whatever produced the original file for its source.
   - Disposition: **documented, not used, root cause unresolved.**

## MEDIUM

2. **ds003838 bounded-diagnostic per-subject control seed used `hash(sid)`**
   (non-deterministic across processes) — found and **fixed** this sprint
   (subject-numeric-ID-based seed now used). See
   `docs/STAGE4_HOSTILE_SELF_REVIEW.md` Dimension A.7.
   - Disposition: **FIXED.**

3. **QDE V2 nested-LOSO alpha selection uses only 9 training subjects per
   fold** — a real, disclosed small-sample source of noise in the
   regularization choice itself, on top of the already-small n=10 overall.
   - Affected result: `results/qde_v2_leg_bioz_stage2.json` (all three
     conditions).
   - Disposition: **disclosed in the hostile review (Dimension C), not
     fixable within this dataset's size — inherent to n=10.**

## LOW

4. **ds003838 loader assumes uniform montage/preprocessing across subjects**
   based on one representative subject's (sub-032) BIDS sidecar (Stage 1B)
   — this sprint's `main()` DOES assert montage equality across whichever
   subjects were actually downloaded (`assert channel_names ==
   channel_names_ref`), which is a real, if partial (bounded to the
   downloaded subset), safeguard.
   - Disposition: **partially mitigated by an existing assertion; full
     65-subject uniformity still unverified (Stage 1B's own disclosed
     limitation, unchanged).**

5. **QDE V2 alpha grid is a fixed, hand-picked list** (`[0.001 ... 1000.0]`)
   rather than a continuous search — a reasonable, common practice, but
   worth naming as a design choice rather than an exhaustively justified
   optimum.
   - Disposition: **acceptable design choice, not a defect.**

## INFO

6. GalaxyPPG and LBNP access blocks are both specific to `zenodo.org` (not
   a general network failure) — reproduced independently via curl (direct
   + API) and WebFetch, with successful same-sprint control access to
   PhysioNet, GitHub, and OpenNeuro's S3 bucket. Worth investigating from a
   different network environment in a future session.

7. Real per-file access to ds003838 was proven end-to-end this sprint
   (byte-exact MD5 match against the dataset's own git-annex hash for two
   real files) — this is a genuinely positive, verified feasibility signal
   for that dataset specifically, distinct from GalaxyPPG/LBNP's situation.
