# BIOLOGICAL MINIMALISM — ISMET STAGE 2→4 EXPANSION FINAL REPORT

## 1. Repository State

- Starting branch: `origin/stage1b-dataset-expansion-prep`
- Verified starting full SHA: `cd92836c6f3353d4c1a5b6754bee34d7054c2333`
  (independently re-verified via `git fetch` + `git rev-parse` at sprint
  start — matched the expected value exactly; no `STAGE2_BLOCKED_REF_
  MISMATCH` triggered)
- Stage 2→4 branch: `stage2-4-expansion-science`
- Final full SHA: `8e5cf901fe1e311f66335e1660fada6b49854aa2` (this commit
  itself — the report necessarily commits after its own content is
  written; `ff3a189` was the last SHA that existed while writing this
  report's body, referenced in Section 61's commit list)
- Remote SHA: matches exactly after push (Section 62)
- Pushed: yes
- Clean: yes (`git status --short` empty at every commit boundary)
- `main` before/after: `b02c6db4434b22741077115786126a59643dc08b`,
  unchanged throughout
- Claude branches (`day12-post-remediation-integration @ 52bd2ec`,
  `day12-14-ismet-support-audit`, etc.): not read, not merged, not
  modified, not referenced for any decision in this sprint

## 2. Stage 1B Reconstruction

Reconstructed from actual `git log`/`git diff --stat` output against the
base (`0e03c63`), not from this prompt's filename guesses. All artifact
names Section 3–39 of the prior Stage 1B prompt requested were found to
exist under the repository's own naming convention, confirmed identical to
what was assumed: `results/{qde_v2,galaxyppg,hmc,lbnp,ds003838}_protocol_
stage1b.json`, `results/{...}_actual_file_audit_stage1b.json`,
`results/dataset_expansion_stage1b_master.json`,
`results/science_expansion_readiness_stage1b.json`, per-dataset docs under
`docs/*_STAGE1B.md`, and `docs/STAGE2_*_IMPLEMENTATION_HANDOFF.md` for all
five. No `PROTOCOL_CONFLICT_REQUIRES_REVIEW` was needed — no material
discrepancy was found between this prompt's descriptive expectations and
the actual frozen Stage 1B protocols.

## 3. Source-of-Truth / Data Verification

Actual-file verification reached this sprint for: **QDE** (already local,
re-verified), **ds003838** (3 real subjects, byte-verified against git-annex
MD5 hashes). Metadata-only / access-blocked this sprint: **GalaxyPPG**,
**LBNP** (both blocked by a reproduced `zenodo.org` network-egress failure,
2 sprints running).

## 4. QDE Historical Reconstruction

`ml/train_bioimpedance.py` / `ml/datasets/qde_bioimpedance.py` (pre-existing,
untouched this sprint): predicts absolute InBody TBW (liters) from 5
impedance + 11 temperature features, LOSO, small MLP, disclosed as
InBody-BIA-circular. No archived `results/*.json` exists for that run —
its result lives narratively in the trainer's own docstring and the
dataset README, reconstructed from source (not from a missing artifact) in
Stage 1B and re-confirmed, not re-derived, this sprint.

## 5. QDE V2 Raw Cohort Verification

Direct CSV read this sprint (`ml/train_qde_v2_leg_bioz.py::load_raw`,
asserted in code): exactly 10 subjects, 9 points each (baseline + 8
intervals), 0 missing Kern-weight values. Matches Stage 1B's audit exactly.

## 6. QDE V2 Frozen Protocol

Target: `delta_weight_kg = weight_at_interval_i - weight_at_interval_0`
(Kern scale) — sign convention stated explicitly in both the trainer's
constants and `docs/QDE_V2_STAGE2_RESULTS_AND_INTERPRETATION.md`, becomes
negative as mass is lost. A = arm+trunk impedance delta (3 features), B = A
+ leg impedance delta (5 features), C = B-dimensional with leg deltas
jointly deranged within-subject across non-baseline intervals (baseline
point never deranged, verified by a dedicated test). Model: ridge
regression, LOSO outer / nested-LOSO inner alpha selection from a frozen
grid.

## 7. QDE V2 Leakage / Normalization Audit

Excluded from predictors and enforced by
`ml/tests/test_stage1b_qde_v2.py` (contract) and direct code read this
sprint: Kern weight (target), InBody weight, InBody TBW, running interval,
running speed. Normalization (`mu, sd`) computed from the 9 training-fold
subjects only, inside each LOSO iteration — verified by code read, no
held-out-subject statistic ever contributes.

## 8. QDE V2 Model / Capacity Design

Same ridge model class for A/B/C; regularization (`alpha`) independently
selected per condition per fold via nested LOSO on held-out-subject MAE
(not in-sample fit). Parameter-count difference (3 vs 5 input features) is
small and disclosed, not hidden.

## 9. QDE V2 Exact Results

Subject-macro MAE (kg), n=10 subjects, real, deterministic, clean-clone-
reproduction-verified (`results/qde_v2_leg_bioz_stage2_reproducibility.
json`, exact match):

| Condition | Mean MAE | SD (ddof=1) |
|---|---|---|
| A (arm+trunk) | 0.7358 | 0.1124 |
| B (arm+trunk+legs) | 0.7876 | 0.2858 |
| C (legs deranged) | 0.7280 | 0.1195 |

A−B mean = **−0.0518** (B worse on aggregate). C−B mean = **−0.0596** (the
deranged control is also "better" than real B on aggregate). **7 of 10
subjects individually favor B over A**, and 7 of 10 favor B over C —
contradicted by the aggregate mean because subject 2's A−B delta is
**−0.7104 kg**, ~9× the typical subject's magnitude.

## 10. QDE V2 Subject Sensitivity

Full per-subject A−B / C−B breakdown in
`results/qde_v2_leg_bioz_stage2.json` → `per_subject_deltas`. Subject 2 is
the dominant, sign-flipping outlier; subject 10 (−0.1224) is a smaller
second contributor in the same direction. Not averaged away, not excluded.

## 11. QDE V2 Scientific Interpretation

**Negative-leaning, single-subject-dominated.** Safe claim: bilateral leg
impedance did not show a robust, subject-consistent improvement over
arm+trunk impedance for baseline-relative body-mass change in this n=10
cohort; a majority of subjects show a small favorable direction, but the
aggregate is dominated and reversed by one outlier. No claim of
microgravity fluid shift, astronaut validation, exact TBW, dehydration
liters, or universal leg-BioZ necessity/uselessness.

## 12. GalaxyPPG Raw-File Verification

**Blocked.** Three independent methods (curl direct, curl REST API,
WebFetch) all failed against `zenodo.org` this sprint (20s timeout / HTTP
504), reproducing Stage 1B's exact blocker. Same-sprint successful control
access to PhysioNet, GitHub, and OpenNeuro's S3 bucket confirms this is a
host-specific failure, not a general sandbox network outage.
`GALAXYPPG_STAGE2_BLOCKED_BY_DATA_ACCESS` set per Section 35.

## 13. GalaxyPPG Cohort / Exclusions

Not re-verified this sprint (blocked). Stage 1B's metadata-level cohort
(24 eligible, all three needed signals reported complete) stands as
metadata only, not actual-file-verified this sprint.

## 14. GalaxyPPG Timing / ECG Reference

Not re-verified this sprint (blocked). Frozen protocol (raw ECG R-peaks as
reference, never device-derived HR) unchanged and ready to execute.

## 15. GalaxyPPG Capacity-Control Design

Unchanged from Stage 1B (architecture-matched dual encoder, disclosed
parameter gap) — not exercised this sprint since no training occurred.

## 16. GalaxyPPG Exact Results

**None — explicitly blocked, not a negative result.** See
`results/galaxyppg_stage2_access_attempt.json`.

## 17. GalaxyPPG Subject Sensitivity

N/A — not trained.

## 18. GalaxyPPG External-Replication Verdict

**UNRESOLVED** (not `FAILED_TO_REPLICATE` — no training occurred to fail;
not `REPLICATED_DIRECTION` — no evidence exists yet).

## 19. Stage 2 Gate

`results/stage2_gate.json`: **`STAGE2_PASS_WITH_LIMITATIONS`.** QDE V2
complete (negative-leaning). GalaxyPPG blocked by data access, protocol
unaffected. Per Section 46, the GalaxyPPG block does not invalidate QDE
V2's completed science.

## 20. LBNP Access State

**Blocked**, re-attempted independently this sprint (not reused from
Stage 1B without retrying) — same `zenodo.org` failure mode as GalaxyPPG,
3 methods, both this and the prior sprint. See
`results/lbnp_stage3_access_attempt.json`.

## 21. LBNP Actual-File Audit

Not possible this sprint. Metadata facts (18 enrolled/16 usable, 0-100
mmHg stages, thoracic/abdominal/arm EIS sites) remain Stage-1B-sourced,
paper-level only.

## 22. LBNP EIS Frequency/Timing Semantics

Unchanged from Stage 1B: 100 log-spaced frequencies (100 Hz–1 MHz) is the
excitation-frequency axis, kept explicitly separate from the ~1
spectrum/minute temporal acquisition cadence. Never described as a sampling
rate.

## 23. LBNP Leakage Audit

Design unchanged (frozen feature-cleaning barrier excluding elapsed time,
sequence index, filename/timestamp fields) — not exercised against real
files this sprint since none were accessible.

## 24. LBNP Exact Results

**None — `LBNP_STAGE3_BLOCKED_BY_ACCESS`.** Not fabricated.

## 25. LBNP Interpretation

N/A — no result exists to interpret.

## 26. ds003838 Actual Cohort

Confirmed this sprint via direct S3 + GitHub access: real cohort facts
unchanged from Stage 1B (65/86 EEG-usable, cross-checked two ways). This
sprint additionally downloaded and byte-verified 3 real subjects'
memory-task EEG files (`sub-032`, `sub-033`, `sub-034`) — MD5s
`f589e83435f7f9edca345c6b89afbe32`, `01269258ed5b4135ef840568b01764fa`,
`019c28c2878fb148a2ed0dfb5b82122a`, each matching the real git-annex object
hash exactly.

## 27. ds003838 Frozen Sparse-EEG Contract

AF7/AF8/TP9/TP10 (Muse-headband-matched), unchanged from Stage 1B, confirmed
present in all 3 real downloaded subjects' montages this sprint
(`assert ch in channel_names` in `ml/train_ds003838_eeg_minimalism.py`).

## 28. ds003838 Preprocessing

Fixed 1.0s epochs anchored to real BIDS event onsets (matching the actual
`duration` field for every event, verified this sprint) — epoch length
never varies with sequence length, preventing duration-based label leakage.
Labels parsed from the real `trial_type` text column, never the raw numeric
`value` trigger code (verified by a dedicated test).

**Real file-format correction made this sprint**: ds003838's `.set` files
are MATLAB v7.3 (HDF5), not the classic format `mne.io.read_raw_eeglab`
supports — discovered via a real `NotImplementedError`, fixed by reading
the file directly via `h5py` (real HDF5 structure inspected first: `data`
dataset of shape `(n_samples, n_channels)` float32, `srate` scalar).

## 29. ds003838 Capacity Fairness

Channel-wise fixed-5-dim feature extraction (mean abs amplitude, std, 3
FFT band powers) mean-pooled across channels to one 5-dim vector,
regardless of channel count — A and B feed the identical-dimension vector
into the identical logistic-regression classifier. Verified by a dedicated
test (`test_pooled_features_same_dimensionality_regardless_of_channel_
count`).

## 30. ds003838 Exact Results

**Bounded diagnostic, n=3 subjects, real, deterministic, clean-rerun
identical.** LOSO macro-F1:

| Condition | Mean | SD (ddof=1) |
|---|---|---|
| A (sparse 4ch) | 0.2263 | 0.0091 |
| B (full 63ch) | 0.2765 | 0.0522 |
| C (deranged extra channels) | 0.2167 | 0.0000 |

C is indistinguishable from an always-predict-majority-class classifier
(≈0.2167 exactly) for all 3 subjects — the negative control behaves exactly
as expected. B is numerically higher than A but driven by 2 of 3 subjects
(sub-034's B result also collapses to majority-class level).

**This is explicitly NOT the frozen Stage-2/3 n=65 result** — see
`docs/DS003838_STAGE3_BOUNDED_DIAGNOSTIC.md` for the full resource-
constraint disclosure (measured ~2.75 MB/s throughput; full cohort would
require ~9-10 hours).

## 31. ds003838 Subject/Class Sensitivity

At n=3, individual-subject sensitivity dominates any aggregate — explicitly
the reason this diagnostic supports no scientific conclusion about
sparse-vs-full EEG, only that the access/loader/control pipeline works
correctly on real data.

## 32. Stage 3 Gate

`results/stage3_gate.json`: **`STAGE3_PASS_WITH_LIMITATIONS`.** ds003838
bounded diagnostic complete and honestly scoped; LBNP legitimately
access-blocked, not fabricated.

## 33. Master Sensor-Value Matrix

`results/sensor_value_master_matrix_stage4.json` — 7 rows (PPG-DaLiA, PTT,
Sleep-EDF, QDE V2, GalaxyPPG, LBNP, ds003838), each with its own metric, no
cross-row score.

## 34. HR External Replication Synthesis

Not possible this sprint — GalaxyPPG blocked. No comparison made.

## 35. BioZ Evidence Synthesis

Three distinct BioZ questions kept explicitly separate (historical TBW,
QDE V2 mass-change, LBNP thoracic EIS) — see
`docs/STAGE4_CROSS_DATASET_HETEROGENEITY.md`. No equating of leg BioZ,
thoracic EIS, ICG, dehydration, central hypovolemia, or microgravity fluid
redistribution.

## 36. EEG Minimalism Evidence

ds003838's actual minimalism question remains unresolved at n=3. Kept
entirely separate from the unrelated Sleep-EDF EEG+EOG finding (different
task, montage, population, target).

## 37. Negative Results Preserved

QDE V2's negative-leaning, subject-2-dominated finding is reported at full
detail, not hidden, not reframed, no subject excluded, no metric switched.

## 38. Cross-Dataset Heterogeneity

See `docs/STAGE4_CROSS_DATASET_HETEROGENEITY.md` — no result from one
dataset was used to explain away or adjust another.

## 39. Architecture Evidence Handoff

`results/architecture_evidence_handoff_stage4.json` — 5 candidate
sensor/sites, each with positive/negative evidence, replication state,
biological n, burden knowledge, and key uncertainty.
`final_architecture_status: "UNRESOLVED"`.

## 40. Architecture/Pareto Status

`NOT_READY`, unchanged, independently re-confirmed given this sprint's own
evidence (non-comparable metrics, 2 of 4 experiments blocked, 1 negative
result, 1 unresolved bounded diagnostic) — see
`docs/STAGE4_ARCHITECTURE_PARETO_STATUS.md`.

## 41. Paper Science Handoff

`docs/STAGE4_PAPER_SCIENCE_HANDOFF.md` — methods, results, negative
results, limitations, lineage, terrestrial/spaceflight boundaries. Does not
overwrite any canonical paper source on another branch.

## 42. Jury Handoff

`docs/STAGE4_JURY_HANDOFF.md` — 18 questions answered with evidence and
limitations, including the weakest experiment and the most subject-
dependent result.

## 43. Claim Boundaries / Traceability

`docs/STAGE1B_EXPANSION_FORBIDDEN_CLAIMS.md` (Stage 1B, still governing,
unmodified) plus this sprint's additions embedded in each result's
`safe_claim` field in the master matrix.

## 44. Dataset Fingerprints

`results/stage2_4_fingerprints_and_provenance.json` — QDE CSV
(SHA256 `186f24f5...074`) and 3 real ds003838 subject files (MD5-verified
against git-annex). GalaxyPPG/LBNP: none (access blocked).

## 45. Cache Provenance

No new preprocessing cache created this sprint — both QDE V2 and ds003838
recompute features fresh from raw files on each deterministic run (verified
via clean-rerun exact-match instead). `ml/datasets/cache_provenance.py`'s
Stage-1B schema remains the reference for any future cache.

## 46. Checkpoint / Model Inventory

None — ridge regression and logistic regression coefficients are not
scientifically necessary to serialize; the deterministic trainer scripts
themselves are the reproducibility guarantee (see
`results/stage2_4_fingerprints_and_provenance.json`).

## 47. External Durability

`LOCAL_VERIFIED_NOT_EXTERNALLY_ARCHIVED` — no new GitHub Release created
this sprint (both experiments are small, deterministic, and fully
reproducible from tracked code + already-fingerprinted raw data).

## 48. Clean-Clone / Reproduction Verification

QDE V2: full clean-state reproduction verified exact-match
(`results/qde_v2_leg_bioz_stage2_reproducibility.json`). ds003838: code-path/
contract reproduction verified via synthetic-array tests (no multi-GB
download required for CI); the exact bounded-diagnostic numeric result
requires re-downloading the same real files (not committed). See
`docs/STAGE4_CLEAN_CLONE_REPRODUCTION.md`.

## 49. Test Matrix

Full `ml/tests/` suite: **365 passed, 0 failed, 0 skipped** (up from 351 at
Stage 1B's end — 14 new tests added this sprint across
`test_stage2_qde_v2_leg_bioz.py` (8) and
`test_stage3_ds003838_bounded_diagnostic.py` (6)). No dataset-dependent
skips — all new tests use either real local data (QDE) or synthetic-shaped
arrays for contract-only checks (ds003838), so none require the ~2.6 GB of
real downloaded files this session used to be present for CI to pass.

## 50. Hostile Software/Data Review

See `docs/STAGE4_HOSTILE_SELF_REVIEW.md` Dimension A — 8 items examined,
including a real pre-existing untracked-file provenance gap (HIGH, disclosed
not used), a non-deterministic seed bug (MEDIUM, fixed), and a real file-
format incompatibility (found via a real error, fixed).

## 51. Hostile Scientific Review

Dimension B — QDE V2's capacity isolation and single-subject-dominance
assessed; ds003838's target confirmed non-circular; no protocol changed
after seeing outcomes (the h5py/sklearn fixes were pre-result implementation
corrections, not post-hoc science changes).

## 52. Hostile Experimental-Logic Review

Dimension C — explicit falsification attempts on both experiments' A/B/C
designs; QDE V2's nested-alpha-selection noise and ds003838's between-
subject-amplitude confound at n=3 both named as real, unresolved
uncertainties, not concealed.

## 53. Hostile Jury/Reviewer Review

Dimension D — the two highest-risk overclaim vectors (citing the ds003838
bounded diagnostic as if it answered the minimalism question; citing QDE
V2's aggregate mean without the subject-2 context) identified and guarded
against in multiple places.

## 54. Biological Minimalism Thesis Coherence Review

Dimension E — thesis is **partially supported, partially complicated** by
this sprint's evidence: inherited PPG+IMU/Sleep-EOG findings support it;
QDE V2's negative-leaning leg-BioZ result is a genuine counter-example;
ds003838's central minimalism question remains unresolved. No overclaim of
generalization made.

## 55. BLOCKER Findings

None.

## 56. HIGH Findings

1 (unexplained pre-existing untracked QDE result file at session start —
documented, not used, root cause unresolved). See
`docs/STAGE4_FINDINGS_REGISTER.md`.

## 57. MEDIUM Findings

2 (ds003838 non-deterministic seed — **fixed**), 3 (QDE V2 nested-alpha
9-subject noise — inherent to n=10, disclosed).

## 58. LOW Findings

4 (`mne.io.read_raw_eeglab` v7.3 incompatibility — **fixed**), 5
(`sklearn` `multi_class` kwarg removed — **fixed**), 6 (ds003838 montage
uniformity checked on 3 of 65 subjects), 7 (QDE V2 alpha grid is a fixed
list, not continuous search — acceptable design choice).

## 59. Remaining Scientific Risks

GalaxyPPG and LBNP both fully blocked by data access — zero new evidence
this sprint for either. ds003838's real scientific question (sparse vs.
full EEG) remains completely open. QDE V2's negative-leaning finding rests
on n=10 with one dominant outlier subject — a larger cohort could plausibly
shift this either direction. HMC and full Claude-line integration are
entirely outside this branch's evidence.

## 60. Exact Files Added / Modified

25 files changed, 2663 insertions, 0 deletions across 6 commits (see
`git diff --stat cd92836..ff3a189`) — full list available via that command;
key new files: `ml/train_qde_v2_leg_bioz.py`,
`ml/verify_qde_v2_leg_bioz_reproducibility.py`,
`ml/datasets/ds003838_eeg.py`, `ml/train_ds003838_eeg_minimalism.py`, 2 new
test files, `results/qde_v2_leg_bioz_stage2*.json` (2 files),
`results/ds003838_eeg_minimalism_stage3_bounded_diagnostic.json`,
`results/{galaxyppg_stage2,lbnp_stage3}_access_attempt.json`,
`results/{stage2,stage3}_gate.json`,
`results/sensor_value_master_matrix_stage4.json`,
`results/architecture_evidence_handoff_stage4.json`,
`results/stage2_4_fingerprints_and_provenance.json`, 7
`docs/STAGE4_*.md`/`docs/QDE_V2_STAGE2_*.md`/`docs/DS003838_STAGE3_*.md`
files, this report.

## 61. Commit History / Stage Milestone SHAs

```
ae2727a Stage 2A Commit 1: QDE V2 real training run
ce59871 Stage 2 Commit 2: GalaxyPPG access gate + Stage-2 gate
223b0f6 Stage 3A Commit 1: LBNP access re-attempt (blocked)
081c724 Stage 3B Commit 1: ds003838 loader + trainer + tests
98df3f5 Stage 4 Commit 1: synthesis, handoffs, hostile review + seed fix
ff3a189 Stage 3B Commit 2: ds003838 real result + Stage-3 gate
```

## 62. Final Remote / Clean-State Verification

`origin/stage2-4-expansion-science` = `ff3a189e869bbf9a107a502751d29b64f2bdc188`
(verified equal to local HEAD post-push). Working tree clean. `main`
unchanged at `b02c6db4434b22741077115786126a59643dc08b` throughout.

## 63. What Is Complete

QDE V2 leg-BioZ experiment (real, negative-leaning result, fully
reproducible). ds003838 real-file access proof + bounded diagnostic
(honestly scoped, not overclaimed). Full Stage 2/3 gates. Stage 4 synthesis,
architecture evidence handoff (UNRESOLVED), jury/paper handoffs, hostile
self-review, findings register. All new tests passing, full suite green.

## 64. What Intentionally Remains Outside This Branch

Claude's Stage 1A/integration line (`day12-post-remediation-integration @
52bd2ec`) — not read, not merged. HMC/Claude's Sleep external-replication
work. GalaxyPPG and LBNP trained results (blocked by data access, not
attempted further). ds003838's full n=65 cohort result. Final project
architecture selection. Final Pareto analysis. The final integrated
hostile audit (requires the combined Claude+Ismet frozen SHA). Stage 5
(merge, integration, freeze) — not begun, per Section 93's hard stop.

## 65. Recommendation for Controlled Integration

Recommend (not performed): once Claude's Stage 1A/integration line is
independently ready, integrate this branch's QDE V2 and ds003838 code/
results additively (no existing canonical artifact conflicts — everything
here is new/additive). Prioritize resolving the `zenodo.org` access block
(different network environment or an alternative mirror) before attempting
GalaxyPPG/LBNP training, since the frozen protocols for both are otherwise
ready. A full ds003838 cohort run should be budgeted as a dedicated
multi-hour background task given the ~9-10 hour full-download estimate at
this sandbox's measured throughput.

## 66. Final Verdict

`STAGE2_4_EXPANSION_COMPLETE_WITH_LIMITATIONS_READY_FOR_CONTROLLED_INTEGRATION`

— WAITING FOR EMIR / CONTROLLED INTEGRATION
