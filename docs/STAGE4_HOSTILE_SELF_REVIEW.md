# Stage 4 Hostile Self-Review — Expansion Science Branch

> **Scope limit (Section 89 — stated explicitly, not a formality):** This is
> an internal hostile audit of the expansion-science branch
> (`stage2-4-expansion-science`) and the inherited state available on it. It
> is NOT the final independent full-project audit, because Claude's current
> Stage-1A/integration lineage (`day12-post-remediation-integration @
> 52bd2ec`) is not present on this branch and was never merged, cherry-
> picked, or inspected here. A later independent Codex/GPT/Astra-class
> reviewer must audit the combined frozen SHA after controlled integration.

## Dimension A — Software / Data Correctness

1. **QDE V2 sign convention**: `delta_weight_kg = weight_i - weight_0`,
   verified by direct inspection of `ml/train_qde_v2_leg_bioz.py`'s
   `build_subject_arrays` — becomes negative as mass is lost. Correctly
   documented, not silently implicit. Severity if wrong: HIGH (would flip
   every interpretation). **Disposition: verified correct.**
2. **QDE V2 baseline point in condition C**: could a bug accidentally
   derange the baseline (interval 0, delta=0 by construction) along with
   the other intervals, silently making "B vs C" partly a "real baseline
   vs missing baseline" comparison rather than a legs-only test? **Checked
   via `test_control_c_baseline_point_never_deranged`** — confirmed the
   derangement permutation only touches indices 1..8, baseline (index 0)
   is provably identical between B and C. **Disposition: verified correct,
   test added.**
3. **ds003838 label leakage via the raw trigger `value` column**: the loader
   (`ml/datasets/ds003838_eeg.py`) parses `trial_type` text, never `value` —
   verified by direct code read and `test_parse_trial_type_extracts_length_
   from_text_not_raw_code`. **Disposition: verified correct.**
4. **ds003838 epoch-duration-encodes-length risk**: every epoch is a fixed
   1.0s window regardless of the trial's actual sequence length (5/9/13),
   so tensor shape cannot leak the label. **Disposition: verified correct
   by construction (EPOCH_TMAX is a constant, not derived from `length`).**
5. **Ridge/logistic-regression normalization leakage**: both QDE V2 and the
   ds003838 diagnostic compute `mu, sd` from the TRAINING fold only inside
   each LOSO iteration, never from the held-out subject. Verified by direct
   code read (`nested_loso_select_alpha`, `run_condition`, `run_loso`).
   **Disposition: verified correct.**
6. **Pre-existing untracked `qde_v2_leg_bioz_stage2.json` found at session
   start**: numbers closely matched (but were not byte-identical to) this
   session's own from-scratch, fully-scripted, deterministically-reproduced
   result, with NO corresponding trainer script committed anywhere in the
   repository history to explain its provenance. **Disposition: treated as
   untrusted, moved aside, and NOT used for any reported number** — every
   number in this report traces to `ml/train_qde_v2_leg_bioz.py`, a
   committed, deterministic, clean-rerun-verified script. Flagged as a
   BLOCKER-severity integrity concern for the session generally (see
   Section 55/56 below), not for the final QDE V2 numbers themselves (which
   are independently regenerated and verified).
7. **ds003838 bounded-diagnostic derangement seed (originally found using
   `hash(sid) % 10000`)**: `hash()` on a string is NOT guaranteed stable
   across Python processes/versions (`PYTHONHASHSEED` randomization),
   which would have made the control's exact derangement non-reproducible
   byte-for-byte across reruns/machines, unlike QDE V2's integer-subject-
   ID-based seeding. **Severity as found: MEDIUM** (did not affect
   correctness of the control's *properties* - still within-subject, still
   excludes A's channels, still label-independent - but broke exact numeric
   reproducibility, which this project otherwise holds as a hard standard).
   **Disposition: FIXED this sprint** - `ml/train_ds003838_eeg_minimalism.py`
   now derives the per-subject seed from the subject's own numeric ID
   (`"sub-032"` -> `32`), stable across processes/machines, matching QDE
   V2's convention.

## Dimension B — Scientific Validity

1. **Does QDE V2's A/B genuinely isolate leg-BioZ information value, not
   model capacity?** A and B use the identical ridge model class with
   independently-tuned regularization per condition (nested LOSO) — B's
   extra 2 features are a small, disclosed dimensionality increase, not a
   capacity confound on the scale of, e.g., a bigger neural network.
   **Assessment: reasonably well-isolated, disclosed.**
2. **Does one subject drive everything (QDE V2)?** Yes, explicitly
   identified: subject 2. This is reported, not hidden — see the results
   doc's dedicated single-subject-dominance discussion.
3. **Is the ds003838 target circular?** No — sequence length (5/9/13) is
   externally imposed by the experimenter, not derived from any recorded
   signal.
4. **Did any protocol change after seeing outcomes?** No — the QDE V2 and
   ds003838 A/B/C/target/metric/split definitions were all fixed in Stage 1B
   before this sprint's training ran, and were not altered afterward. The
   `hash()`-seeding issue above (finding A.7) is a NEW-CODE bug, not a
   post-hoc protocol change.

## Dimension C — Experimental Logic (hostile falsification attempt)

- **QDE V2**: could the observed (mild, non-dominant-subject) B-vs-A
  difference come from something other than leg-BioZ information? The
  ridge regularization is independently tuned per condition and per fold,
  which could in principle let B "explain away" noise via regularization
  choice rather than signal — partially mitigated by the nested-LOSO
  procedure using held-out-subject MAE as the selection criterion (not
  in-sample fit), but with n=9 training subjects per fold, alpha selection
  itself is a further small-sample-noise source. **This is disclosed as a
  contributing uncertainty, not resolved.**
- **ds003838 bounded diagnostic**: with 2-3 subjects, ANY result (in either
  direction) is far more likely to reflect between-subject baseline
  differences in overall EEG amplitude/impedance than genuine spatial-
  coverage information content. This is exactly why the diagnostic's
  results are NOT reported as a scientific finding in the master matrix —
  only "real access works" is claimed from it.

## Dimension D — Jury/Reviewer Attack

- The single strongest overclaim risk in this sprint's own outputs would be
  citing the ds003838 bounded diagnostic's F1 numbers as if they answered
  the sparse-vs-full-EEG question — explicitly guarded against in three
  places (the scope-disclosure doc, the trainer's own status string, and
  the master matrix's `exact_result` field).
- The second-strongest risk would be citing QDE V2's negative aggregate mean
  without the subject-2-dominance context, which would misrepresent a
  heterogeneous result as a clean "legs don't help" finding — guarded
  against by leading with the per-subject breakdown in every place this
  result is reported.

## Dimension E — Biological Minimalism Thesis Coherence

The central thesis — that a small, carefully justified sensor set can match
or approach a larger one's information value for specific mission-relevant
targets — is **partially supported and partially complicated** by this
sprint's evidence: Sleep EEG+EOG (inherited) and PPG+IMU (inherited, not yet
independently replicated) support the "a small addition beyond a minimal
baseline earns its keep" half of the thesis; QDE V2's negative-leaning leg-
BioZ result is a genuine counter-example (an added sensor did NOT clearly
earn its burden cost here); ds003838's actual minimalism question (sparse
vs. full EEG) remains entirely unresolved. **This branch does not yet
possess enough completed, independent evidence to say whether Biological
Minimalism generalizes as a design principle or is specific to the sensors
tested so far — and does not claim otherwise.**
