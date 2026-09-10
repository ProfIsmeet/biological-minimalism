# Stage 4 Clean-Port Adjudication

`INTEGRATION_OWNER` sprint: `STAGE4_PARALLEL_ENGINEERING_AND_CLEAN_INTEGRATION_PREPARATION`.

This document records the individual adjudication of each of the five known
implementation-only commits on the contaminated `stage2-4-claude-integration-prep`
lineage (HEAD `98275b702bc98bfc209b1bd186239eefc0e72428`), per governing-prompt §12-15.

## Method

For each commit: inspected `git diff-tree --name-status`, the full patch content
(not just the commit message), and grepped the complete diff for any reference to
the ten files introduced by the quarantine commit `d97b4d5ea82ab039c6d79e095b0c2833ca82bb71`
("Preserve Claude Stage-2 science candidate + Ismet transfer handoff"). Confirmed
independently — not by trusting the prior session's own self-review — that:

- `git merge-base --is-ancestor d97b4d5... 52bd2eca...` → **not an ancestor** (clean base is genuinely clean).
- `git merge-base --is-ancestor d97b4d5... 98275b7...` → **is an ancestor** (confirms the contamination).
- None of the five commits' own diffs (`git diff-tree --name-status -r <sha>`) touch any of the
  ten quarantine files.

## Adjudication table

| Commit | Title | Files changed | Quarantine dependency | Classification |
|---|---|---|---|---|
| `8271d4f` | Phase 1: software/engineering hardening audit | `backend/app/research/catalog.py`, `backend/tests/test_research_api.py`, `frontend/src/components/panels/DigitalTwinPreview.tsx`, +1 doc | None | **SAFE_TO_PORT_AS_IS** |
| `558a30b` | Phase 2: generic future-science ingestion contract | `backend/app/schemas/experiment_manifest.py` (new), `backend/app/research/future_science_ingestion.py` (new), `backend/app/api/routes/research.py`, `backend/tests/test_future_science_ingestion.py` (new), +1 doc | None in code. Module docstring pointed at `docs/CLAUDE_TO_ISMET_STAGE2_4_SCIENCE_TRANSFER_HANDOFF.md` for "design rationale." | **SAFE_TO_PORT_WITH_REPAIR** |
| `7e8e567` | Phase 3: Research Mode/frontend + paper/jury/claim infrastructure | `backend/app/research/future_science_ingestion.py`, `backend/app/schemas/experiment_manifest.py`, `backend/tests/test_future_science_consumer_guards.py` (new), `frontend/src/components/research/FutureScienceHandoffCard.tsx` (new), `frontend/src/components/research/ResearchMode.tsx`, `frontend/src/lib/api.ts`, `frontend/src/lib/types.ts`, `frontend/src/store/researchStore.ts`, +3 docs | Two prose citations in newly-added docs: Jury Framework Q4 cited `docs/CLAUDE_TO_ISMET_STAGE2_4_SCIENCE_TRANSFER_HANDOFF.md`; Paper Skeleton Methods cited `docs/HMC_STAGE2_BANDWIDTH_REDUCED_COHORT_DEVIATION.md`. Both files exist only in the quarantine commit. | **SAFE_TO_PORT_WITH_REPAIR** |
| `c9c87e3` | Phase 4: integration dry-run + hostile review + readiness contract | `backend/app/research/future_science_ingestion.py`, `backend/app/schemas/experiment_manifest.py`, `backend/tests/test_phase4_integration_dry_run.py` (new), +2 docs | None | **SAFE_TO_PORT_AS_IS** |
| `98275b7` | Phase 4 close-out: surface subject/seed n through display projection | `backend/app/research/future_science_ingestion.py`, `backend/app/schemas/experiment_manifest.py`, `backend/tests/test_future_science_ingestion.py`, `backend/tests/test_sample_size_labeling.py` (new), `frontend/src/components/research/FutureScienceHandoffCard.tsx`, `frontend/src/lib/types.ts` | None | **SAFE_TO_PORT_AS_IS** |

No commit was classified `PARTIALLY_REUSABLE`, `REJECT_DUE_TO_QUARANTINE_DEPENDENCY`, or `SUPERSEDED` —
all five were implementation-only work with no science content, and the only
dependencies found were two dangling documentation citations, both repaired
post-port rather than requiring a rejected/partial port.

## Repairs made

Two follow-up commits repaired the dangling citations found in the ported content
(governing-prompt §15: replace with clean-base source-of-truth artifacts or an
honest pending statement — never fabricate the missing file):

1. **`docs/CLAUDE_PHASE3_JURY_FRAMEWORK_STAGE2_4.md` §4** — replaced the citation
   to the quarantine handoff doc with the two clean-base canonical artifacts that
   already carry the same n=3/n=8 counts: `results/sleep_scientific_remediation_day12.json`
   (primary, n=3) and `results/sleep_edf_secondary_holdout_evaluation.json`
   (secondary holdout, n=8) — both verified present on `52bd2eca` before citing them.
2. **`docs/CLAUDE_PHASE3_PAPER_SKELETON_STAGE2_4.md` §Methods** — replaced the
   citation to the non-existent `docs/HMC_STAGE2_BANDWIDTH_REDUCED_COHORT_DEVIATION.md`
   with an honest statement that the HMC/ds003838 protocol documents are
   candidate work-in-progress on the Science Owner's branch and do not exist
   on this branch yet.
3. **`backend/app/schemas/experiment_manifest.py`** module docstring — removed
   the dangling "see `docs/CLAUDE_TO_ISMET_STAGE2_4_SCIENCE_TRANSFER_HANDOFF.md`"
   pointer (design-rationale text only; no functional symbol changed).

No science value, number, or claim was altered by any repair — only path
references to a file this branch deliberately does not contain.

## Port mechanics

Cherry-picked all five commits in original order directly onto a fresh branch
from the clean base (`git cherry-pick 8271d4f 558a30b 7e8e567 c9c87e3 98275b7`).
All five applied with **zero merge conflicts** (git's own confirmation that no
commit's diff overlapped file state introduced by the quarantine commit).
Repairs were applied as two additional commits on top, not squashed into the
cherry-picks, so the port history remains auditable against the original
five source commits.

## Resulting clean-branch commits

| Original SHA | New SHA on `stage4-engineering-integration-prep` |
|---|---|
| `8271d4f54c00ef64ab3644f4218cfdeff53a9de0` | `5e2e415` |
| `558a30be04de27066c7f545be38c365973d1bc26` | `abfca32` |
| `7e8e567643e2d05ce6bae7dcf994cdfbce717f9e` | `37b3b9e` |
| `c9c87e34368ae021b8c71ad5f5bd20ae7a56c5b9` | `fd89360` |
| `98275b702bc98bfc209b1bd186239eefc0e72428` | `246d547` |
| (repair 1/2) | `10df46c` |
| (repair 2/2) | `c3b4b31` |

## Verification after port

- `git merge-base --is-ancestor d97b4d5... HEAD` on the new branch → **not an
  ancestor** (quarantine commit is genuinely absent from this branch's history,
  not merely unreferenced).
- Repo-wide grep for all ten quarantine filenames/paths across `backend/`,
  `frontend/`, and `docs/` on the new branch → zero remaining matches, except
  two purely-descriptive historical mentions in `docs/CLAUDE_PHASE1_PARALLEL_HARDENING_REPORT.md`
  (prose describing the Phase-1 audit that confirmed isolation on the *old*
  branch — accurate historical record, not a file-existence dependency; nothing
  fails if a reader cannot open the referenced file, since it is cited as history,
  not as a live source).
- Full backend suite: **224/224 passed** after the port (before any Stage-4
  engineering work was added on top).
- The 76 tests newly introduced by the five ported commits: **76/76 passed**
  in isolation.
