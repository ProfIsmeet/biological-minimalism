# Hostile Scientific Self-Review (Day 14)

Written as a skeptical external reviewer would. Not defensive. Every
question below is answered honestly, including where the honest answer is
"this is a real weakness."

## PPG-DaLiA

**Is A_cap truly a sufficient capacity control?** Partially. A_cap matches
parameter *count* (28,865 vs. 29,089, 0.77% residual) but not necessarily
every architectural degree of freedom - a dual-branch encoder (PPG+IMU)
has a different *inductive bias* than a single wider PPG-only encoder even
at matched parameter count. The residual A_cap->B effect (+0.605 bpm)
could still be partly attributable to inductive-bias differences, not
purely "IMU information." This is disclosed as an open possibility, not
ruled out.

**Could dual-encoder inductive bias still confound?** Yes, plausibly. This
was not tested with an alternative capacity-matched architecture family.
**Strength downgrade**: the capacity-controlled claim should be read as
"a plausible, capacity-count-controlled residual effect," not "IMU
information isolated from all architectural confounds."

**Does C isolate synchronization cleanly?** C (shuffled IMU) breaks true
temporal correspondence but preserves per-subject motion-magnitude
statistics. It does not isolate synchronization from other properties the
shuffle destroys (e.g., any residual within-subject autocorrelation
structure C's shuffle preserves less well than a real signal). Reasonably
clean, not perfectly clean.

**Are 5 seeds meaningful evidence?** For *optimization-trajectory*
consistency, yes. For anything resembling statistical population
inference, no - 5 seeds is not statistical replication in any classical
sense (see `docs/STATISTICAL_REPORTING_STANDARD_DAY11.md`).

**Is the residual effect practically important?** Marginal. 0.605 bpm on
a task with double-digit MAE is a small relative improvement. A reviewer
could reasonably ask whether this magnitude justifies IMU hardware
inclusion - that is an engineering/Pareto decision this document does not
make.

## PTT

**n=4 subjects: is this publishable as evidence?** As *descriptive*
evidence, yes, if honestly labeled. As *inferential* evidence of a
population effect, no - n=4 is far too small, and this project never
claims otherwise.

**Does s2 dominate too much?** Yes - excluding s2 alone flips the
aggregate sign. This is the single most fragile result in the project.

**Is the result just noise?** At the subject level, plausibly yes in
large part. At the seed level (5/5 consistent direction on the *same*
4-subject data), the direction is consistent, but that consistency says
nothing about whether the underlying subject-level signal is real or
dominated by one atypical individual.

**What can actually be claimed?** Only: "on this specific 4-subject
held-out set, under this specific model, the two-site configuration
performed worse on average, seed-consistently, but the subject-level
picture is small and fragile." Nothing stronger.

## Sleep

**Same dataset only.** True throughout - primary, secondary, and
interaction all use the same Sleep-EDFx cassette source. No claim of
cross-dataset generalization is or should be made.

**Primary n=3, secondary n=8 - could selection bias remain?** The
secondary cohort was frozen by subject-index proximity (18-25, the next
contiguous block after the primary split's 00-17), not randomly sampled
from the full available population (up to ~80+ subjects exist in
Sleep-EDFx). This is a legitimate methodological choice (transparent,
predeclared, avoids outcome-based selection) but it is *not* a random
sample of the full dataset - a skeptical reviewer could ask whether
subjects 18-25 are representative of the broader population. Unverified.

**Does shuffled-EOG fully rule out capacity?** No - Model C has the
identical architecture/parameter count as Model B by construction, so
capacity is controlled by design here (unlike the original PPG-DaLiA
issue). This is one of the stronger controls in the project.

**Is the N3 regression a real tradeoff?** Yes, confirmed exactly (Day
9/11 diagnostics): N3 precision drops meaningfully (0.499->0.430) while
recall rises (0.853->0.884) in the secondary cohort. This is a genuine,
disclosed cost of the aligned-EOG configuration, not smoothed over.

**Does class imbalance distort macro-F1?** Macro-F1 already weights
classes equally regardless of support, which is the right choice for
imbalanced sleep-stage data, but this means a class with very few epochs
(N1) can swing macro-F1 disproportionately relative to its clinical
epoch-count importance. This is a known property of macro-F1, not a bug,
but worth flagging for a reviewer who expects epoch-weighted accuracy.

## Interaction

**Does EOG x Resp interaction mean anything at this sample size?**
Weakly. n=5 seeds, n=3 subjects (for the subject-level breakdown) is a
very small basis for any interaction claim.

**Is +0.0031 ± 0.0434 too noisy to interpret?** Essentially yes - the SD
is ~14x the mean. The correct, only defensible reading is "unresolved,"
which is exactly what this project reports. A less careful team would
have rounded this to "no interaction" (unsupported - absence of evidence
is not evidence of absence) or cherry-picked a positive-seed subset to
claim synergy (which this project explicitly did not do).

**Is model capacity truly controlled?** Yes, verified: constant
112-params-per-channel cost across all four configs, checked
programmatically before interpretation.

**Does one interaction experiment materially address global
interaction?** No. It addresses exactly one pair (EOG, Resp) for exactly
one target (sleep stage). The broader "one-at-a-time marginal value
doesn't prove global minimality" limitation remains open in general.

## Robustness

**S14 only.** A single subject. Any robustness claim is a case study, not
a population statement.

**First-batch IMU-noise calibration.** The additive-noise severities were
calibrated on this same subject's data - a circularity risk if the
calibration itself used information from the evaluation subject (this was
flagged in the original robustness audit addendum and is not re-litigated
here, only restated as a live caveat).

**Packet-loss availability.** The robustness protocol's fail-closed
availability metric measures whether the pipeline correctly *rejects*
degraded input, not whether it produces a *good* prediction under
degradation - a reviewer could argue this conflates "safe failure" with
"robustness" if not read carefully.

**Can "robust" be said at all?** Only in a narrow, explicitly-scoped
sense: "under these 114 specific conditions, for this one subject, this
one model degrades/fails-closed in this documented way." Not a general
robustness claim, and this project does not make one.

## Reproducibility

**Is clean-clone genuinely clean?** Mostly. Environment and checkpoint
reproducibility were tested from a genuine fresh clone/venv/checkpoint
extraction. Raw-dataset acquisition was tested via verified-hash file
copy rather than a second live network download in this session - see
`docs/CLEAN_CLONE_REPRODUCTION_DAY13.md` for the exact, disclosed
methodology. A maximally hostile reviewer would want a fully independent
network re-download; that was not done here, for time reasons, and this
document says so plainly rather than implying it was.

**Are datasets obtainable?** Yes for all three (PhysioNet x2, UCI x1),
all open/no-application-required, documented in `datasets/*/README.md`.

**Are all checkpoints archived?** As of this sprint, yes - 60/60 including
the 10 Day-10 interaction checkpoints that were found NOT externally
durable before this sprint (a real gap, now fixed - see Checkpoint
Archival Findings below).

**Are Day-10 interaction checkpoints archived?** Fixed this sprint (Day
14 archive, `day14-checkpoint-archive-v1`). Before this sprint: **no** -
this was a genuine gap that existed from Day 10 through the start of Day
14, now closed.

**Are environment pins enough?** Mostly - torch is pinned exactly; numpy
is not, and drifted by a patch version on a fresh install (no observed
impact, but disclosed as a real gap in `docs/SCIENTIFIC_REPRODUCTION_GUIDE.md`).

**Can another person reproduce without hidden local files?** Based on
this sprint's clean-clone test: yes, for code/environment/checkpoints. For
raw data, only with either PhysioNet/UCI network access or an
already-downloaded copy - documented, not hidden.

## Paper claims

**Which sentence would a reviewer reject immediately?** Any sentence
implying the PTT negative result is a population-level finding (n=4), or
any sentence describing the secondary Sleep holdout as "independent
replication" (same dataset).

**Which result has the weakest external validity?** PTT (n=4,
s2-dominated) and the robustness result (n=1 subject).

**Which figure could accidentally mislead?** Figure I (interaction) if
plotted with a truncated y-axis that hides how large the SD is relative
to the mean - the figure-source file explicitly flags this risk.

**Which limitation must be in the main text, not supplement?** The
same-dataset-only nature of every Sleep result (primary, secondary,
control, interaction) - this is easy to bury in a supplement and would
materially mislead a reader if it were.

## Checkpoint Archival Findings (Day 14, real gap found and fixed)

Before this sprint: the 10 Day-10 interaction checkpoints
(`sleep_edf_interaction_M_B_*`, `sleep_edf_interaction_M_AB_*`) existed
only in `ml/checkpoints/` on this Windows machine - not in
`checkpoint_manifest_consolidated.json`, not in
`checkpoint_archival_verification.json`, not in the Day-8 GitHub Release.
**This was a real, unflagged local-only-checkpoint dependency.**

Fixed this sprint: a new, separate, versioned archive
(`biological_minimalism_checkpoints_day14.tar.gz`, GitHub Release
`day14-checkpoint-archive-v1`, 10 checkpoints) was built, uploaded, and
verified byte-identical against the local copy. The Day-8 archive was
**not** mutated - a deliberate design choice, with explicit linkage
recorded in both archives' manifests. `results/final_checkpoint_inventory_day14.json`
now shows 60/60 checkpoints externally archived, 0 gaps.

## Scientific Claim Strength Matrix

| Claim | Strength | Evidence | Limitation |
|---|---|---|---|
| PPG-DaLiA IMU capacity-controlled benefit | MODERATE | 5/5 seeds, 3/3 subjects, capacity-matched, shuffle control | Small magnitude, possible residual inductive-bias confound, single dataset |
| PTT second-site negative effect | PRELIMINARY | 5/5 seeds, but n=4 subjects, s2-dominant | Direction flips on subject exclusion; not a population claim |
| Sleep primary EOG benefit | MODERATE | 4/5 seeds, matched shuffle control | n=3 subjects, concentrated in one (SC4011) |
| Sleep secondary holdout | MODERATE | 5/5 seeds x2 comparisons, n=8, more distributed | Same dataset/protocol as primary, not independent replication |
| Sleep N3 regression | STRONG (as a descriptive finding) | exact, reproduced, quantified | No mechanistic explanation offered or claimed |
| EOG x Resp interaction | DESCRIPTIVE / UNRESOLVED | capacity-verified, honestly reported | n=5 seeds, n=3 subjects, SD >> mean |
| Robustness (S14) | DESCRIPTIVE | 114/114 conditions reproduced exactly | n=1 subject, calibration circularity risk flagged |
| Reproducibility (code/env/checkpoint) | STRONG | clean-clone test, exact reproduction throughout | Raw-data acquisition tested via hash-verified copy, not live re-download |
| Any claim of independent-dataset replication | UNSUPPORTED | none exists | N/A |
| Any claim of global sensor minimality | UNSUPPORTED | one-at-a-time evidence only | `docs/SENSOR_INTERACTION_LIMITATION.md` |
| Any claim of astronaut/microgravity validation | UNSUPPORTED / FUTURE_ONLY | none attempted | N/A |
