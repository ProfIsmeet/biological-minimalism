# Stage 1B Dataset Expansion Feasibility Report

## 1. Repository State

Branch `stage1b-dataset-expansion-prep`, created from
`origin/day12-sleep-scientific-remediation` @ `0e03c63` (independently
re-verified via `git fetch` + `git rev-parse` before any edit — matched
exactly; working tree was clean; `main` untouched at `b02c6db`).

## 2. Source Scientific State

`docs/CLAUDE_H1_H2_SCIENTIFIC_REMEDIATION_HANDOFF.md`,
`docs/SCIENTIFIC_FREEZE_REASSESSMENT_H1_H2.md`,
`results/sleep_scientific_remediation_day12.json`, and
`results/scientific_freeze_candidate_post_audit_day12.json` were read
directly this sprint (fresh reads, not reused from any prior turn's
unverified claims). H1 is closed for Primary A/B with updated numbers; H2 is
closed metadata-only; freeze status is
`SCIENTIFIC_FREEZE_CANDIDATE_READY_WITH_LIMITATIONS`. None of these were
modified by Stage 1B.

## 3. Audit Method

Actual-file verification prioritized in the order: authoritative dataset
page → data-descriptor paper → real file listing/metadata → representative
raw files → existing repo loader. Network access to `zenodo.org` was blocked
this sandbox's egress (repeated timeouts); PhysioNet, OpenNeuro's GitHub
mirror, and NCBI/PMC were all directly reachable and used for real fetches.

## 4. Dataset Access Summary

See `results/dataset_access_stage1b.json`. Four of five are fully open
(GalaxyPPG, HMC, QDE, ds003838); LBNP's precise license/access could not be
directly confirmed (Zenodo blocked) though the paper states the data are
open.

## 5. GalaxyPPG

**GO.** 24 participants; all three signals this project needs (E4 BVP, E4
ACC, Polar H10 raw ECG) reported complete for all 24, per the paper's own
measured (not nominal) sample-rate table. Frozen A/B/C use raw-ECG
R-peaks as reference, grouped subject-wise CV, architecture-matched capacity
control. See `results/galaxyppg_actual_file_audit_stage1b.json`,
`results/galaxyppg_protocol_stage1b.json`,
`docs/GALAXYPPG_EXTERNAL_REPLICATION_PROTOCOL_STAGE1B.md`.

## 6. HMC

**GO_WITH_DEPENDENCY.** 151 recordings, confirmed one recording per unique
subject (explicitly checked against the "151 ≠ 151 unique subjects" risk),
confirmed uniform 256 Hz across all channels. Frozen EEG derivation C4/M1,
EOG = E1/M2−E2/M2. The only blocker is a workflow dependency (must wait for
Claude/Emir's Stage 1A Sleep V2 freeze), not a data flaw. See
`results/hmc_actual_file_audit_stage1b.json`,
`results/hmc_protocol_stage1b.json`,
`docs/HMC_SLEEP_EXTERNAL_REPLICATION_PROTOCOL_STAGE1B.md`.

## 7. QDE V2

**GO_WITH_LIMITATIONS.** Not a new dataset — QDE was already in this repo
(`ml/datasets/qde_bioimpedance.py`). New experiment: bilateral leg impedance
vs. baseline-relative Kern-scale body-mass change (reduced circularity vs.
the old InBody-TBW target). 10/10 subjects complete, verified directly from
the CSV. Frozen ridge-regression model class, LOSO, jointly-deranged
bilateral control. See `results/qde_v2_actual_file_audit_stage1b.json`,
`results/qde_v2_protocol_stage1b.json`,
`docs/QDE_V2_LEG_BIOZ_PROTOCOL_STAGE1B.md`.

## 8. LBNP

**GO_WITH_LIMITATIONS.** 18 enrolled / 16 usable (this project uses 16, not
18). LBNP levels corrected from the prompt's placeholder (0/15/30/45/60) to
the actual full 0–100 mmHg protocol. EIS is a per-stage snapshot (~1
spectrum/minute), never a continuous signal — documented explicitly. Major
leakage threat (monotonic protocol time) is real but mitigable by feature
exclusion; several native rates (ECG/pleth/MAP/EIT) and the exact
16-vs-18-file public release structure remain unverified pending direct
Zenodo access (blocked this sprint). See
`results/lbnp_actual_file_audit_stage1b.json`,
`results/lbnp_protocol_stage1b.json`,
`docs/LBNP_IMPEDANCE_PROTOCOL_STAGE1B.md`.

## 9. ds003838

**GO_WITH_LIMITATIONS.** 86 recruited, **65 with usable EEG — confirmed two
independent ways that agree exactly** (README's enumerated exclusion list vs.
an independently computed `participants.tsv` count). Real BIDS sidecars
fetched directly: 63 channels, 1000 Hz, 50 Hz power line (checked, not
assumed 60 Hz). Frozen sparse set AF7/AF8/TP9/TP10 — the exact Muse headband
montage, confirmed present in the real channel list before freezing.
Resource cost, directly measured via git-annex object sizes: ~96–99 GB for
EEG-only (both tasks, 65 subjects) — smaller than the prior audit's rough
~250 GB estimate. See `results/ds003838_metadata_audit_stage1b.json`,
`results/ds003838_protocol_stage1b.json`,
`docs/DS003838_EEG_CHANNEL_MINIMALISM_PROTOCOL_STAGE1B.md`.

## 10. Dataset Lineage

`results/dataset_lineage_stage1b.json` — GalaxyPPG, HMC, LBNP, and ds003838
are all new independent families; QDE V2 is confirmed an existing family
with a new experiment, matching the prompt's expected conceptual
interpretation exactly.

## 11. Access/Licensing

`results/dataset_access_stage1b.json`. No credentials stored anywhere.

## 12. Rate/Timing Provenance

`results/dataset_expansion_rate_provenance_stage1b.json` — every spectroscopy
excitation-frequency axis (QDE's 1000 kHz single-frequency BIA, LBNP's
100 Hz–1 MHz 100-point EIS sweep) is kept in a separate field from temporal
acquisition cadence, per the H2-driven discipline.

## 13. Leakage Matrix

`results/dataset_expansion_leakage_matrix_stage1b.json` — every candidate
feature/metadata family classified per dataset.

## 14. Control Design Review

Every C control across all five protocols: within-subject only, never
cross-subject, RNG isolated via the `ml/sleep_seed_utils.py` sub-seed
pattern, never label-informed. Details embedded in each dataset's protocol
JSON (`control_C` / `feature_sets.C` block).

## 15. Eligibility/Exclusion Rules

Data-integrity rules only (missing signal, instrumentation exclusion,
invalid label) — never outcome-based — recorded per dataset in each
protocol JSON's `eligibility_rules`.

## 16. Frozen Metrics

GalaxyPPG: MAE/RMSE (bpm). HMC: Macro-F1/balanced accuracy. QDE V2: MAE/RMSE
(kg). LBNP: MAE (mmHg), ordinal chosen over categorical F1 given the
genuinely ordered stages. ds003838: Macro-F1 (3-class)/balanced
accuracy/ordinal error. All frozen before any training.

## 17. Subject-Level Reporting Plan

Every protocol requires per-subject candidate-vs-baseline delta, favorable-
direction count, and dominance/concentration reporting, matching this
project's existing Sleep-EDF/PTT/QDE convention.

## 18. Statistics Policy

Continues project convention: sample SD (ddof=1) for seed-level reporting;
seeds are optimization repetitions, subjects are biological units; no
p-values without a justified inferential design; small-N bootstrap only if
explicitly descriptive.

## 19. Resource/Compute Assessment

GalaxyPPG: LOW-MEDIUM. HMC: MEDIUM-HIGH (15.7 GB). QDE V2: LOW (already
local). LBNP: MEDIUM-HIGH (unverified exact size). ds003838: MEDIUM-HIGH
(~96–99 GB, directly measured — smaller than previously feared).

## 20. Stage-2 Execution Order

Independently recomputed from this sprint's actual-file evidence:

1. **QDE V2** — zero new access cost, already local, LOW implementation
   cost, immediately trainable.
2. **GalaxyPPG** — GO with no open blockers beyond two pre-training
   verification steps (sync method, session durations), LOW-MEDIUM cost.
3. **ds003838** — GO_WITH_LIMITATIONS but no workflow blocker; the main
   cost is download time/storage, now well-characterized (~96-99 GB).
4. **LBNP** — GO_WITH_LIMITATIONS with a genuine open blocker (Zenodo file
   access not yet directly confirmed); should follow direct-access
   resolution.
5. **HMC** — dataset itself is excellent (GO_WITH_DEPENDENCY) but should
   run last among the five because it explicitly should not start full
   training before Claude/Emir's Stage 1A Sleep V2 freeze — a workflow, not
   scientific, constraint.

This differs from the prior research audit's order (GalaxyPPG, QDE V2, HMC,
LBNP, ds003838) by moving QDE V2 to first (zero access cost, already local)
and HMC to last (the only program with an external workflow dependency) —
based on this sprint's actual-file evidence, not preserved by default.

## 21. Workflow Dependencies

Only HMC carries one: full training must wait for Claude/Emir's Stage 1A
Sleep V2 protocol freeze.

## 22. Backup Activation Status

Not activated. No primary candidate failed a hard feasibility gate; no
broad backup dataset search (ScientISST MOVE, TROIKA, CAP Sleep, STEW,
ds004902) was performed this sprint, per Sections 30–31 and 51–52.

## 23. Fingerprints

`results/dataset_expansion_fingerprints_stage1b.json` — `PARTIAL_FILE_AUDIT`
coverage overall; QDE V2 is the only dataset with its full (single) raw file
SHA256-fingerprinted this sprint
(`186f24f567eee623e475f6556217344a9cc3a522d969d76df02ffe5820628074`). HMC and
ds003838 have real metadata/pointer-level facts for a representative
subject/index. GalaxyPPG and LBNP have zero direct file access this sprint
(Zenodo blocked) — disclosed explicitly, not glossed over.

## 24. Tests

35 new Stage-1B contract tests added across
`ml/tests/test_stage1b_{galaxyppg,hmc,qde_v2,lbnp,ds003838,master}.py` — all
passing (see Section 53 test run below). No performance-threshold assertions
anywhere, per Section 38.

## 25. Artifacts Created

7 shared manifests (`results/dataset_{lineage,access,expansion_rate_provenance,expansion_leakage_matrix,expansion_fingerprints,expansion_stage1b_master,expansion_role_map}_stage1b.json`
plus `results/science_expansion_readiness_stage1b.json`), 1 forbidden-claims
doc, 1 cache-provenance schema module, 5×(actual-file-audit JSON + protocol
JSON + protocol doc + Stage-2 handoff doc) = 20 per-dataset files, 6 new test
files, this report. 36 new files total.

## 26. Commit History

7 commits on `stage1b-dataset-expansion-prep`: shared infra; GalaxyPPG; HMC;
QDE V2; LBNP; ds003838; master/readiness/role-map/fingerprints/report/tests
(this commit).

## 27. Push / Clean Tree / Main State

Pushed to `origin/stage1b-dataset-expansion-prep`. Remote HEAD verified to
match local HEAD. Working tree clean. `main` untouched at `b02c6db`
throughout (independently re-verified, not just carried forward from the
start-of-sprint check).

## 28. Remaining Risks

- Zenodo access was blocked this entire sprint (sandbox network egress) —
  GalaxyPPG and LBNP facts rest on paper text, not this session's own file
  listing/hashing; both are flagged for mandatory direct-file re-verification
  at Stage-2 implementation time.
- LBNP's public 16-vs-18-subject file structure, and its ECG/pleth/MAP/EIT
  native rates, remain genuinely unverified.
- HMC and ds003838's per-file channel/montage uniformity was checked on an
  index/single-representative-subject basis, not all 151/65 files
  individually.
- ds003838's ~96-99 GB download is a real resource commitment even though
  smaller than previously feared.
- The 10 new QDE-V2-adjacent artifacts introduce a second QDE experiment
  (body-mass-change target) alongside the historical TBW target on the same
  10 subjects — future documentation must keep the two experiments and their
  targets clearly distinguished (done via file naming and explicit
  cross-references in this sprint's artifacts).

## 29. Final Verdict

`STAGE1B_COMPLETE_WITH_CONDITIONAL_DATASETS`

(Not `STAGE1B_COMPLETE_ALL_SELECTED_DATASETS_READY_FOR_STAGE2`, since HMC
carries a real workflow dependency and LBNP carries a real open
data-access gap — both disclosed, neither blocking, but both real
conditions on an unconditional "all ready" verdict.)
