# Furkan Paper Handoff — Day 10 Addendum (Reproducibility + First Interaction)

Extends `docs/FURKAN_PAPER_HANDOFF_CANONICAL_DAY9.md`. Day 10 adds reproducibility
evidence and one interaction experiment. **No canonical metric changed.** Nothing
below upgrades a prior claim.

> **Stage 1A update (Day 12, H1/H2 remediation):** the Sleep-EDF Primary A/B
> macro-F1 values below (0.7473 / 0.7693, from this doc's shared M0/M_A
> baseline) are the **historical (pre-seedfix)** numbers. A corrected,
> seed-controlled rerun exists for Primary A/B only — **cite the corrected
> V2 numbers (0.7365 / 0.7647, +0.0282) for the headline going forward**; see
> `docs/SLEEP_V1_V2_CITATION_MAPPING_STAGE1A.md` for the full mapping. The
> interaction experiment (M0/M_A/M_B/M_AB) below has **not** been rerun under
> the corrected protocol and remains historical-protocol evidence only —
> do not combine its M_A/M_B/M_AB legs with the corrected V2 Primary A/B
> values in any derived comparison.

## New writable sections (Day 10)

### Methods — Reproducibility (new, writable)
- **Frozen environment.** The scientific training/evaluation stack was verified
  field-by-field against the frozen manifest (Python 3.13.0, PyTorch 2.6.0+cpu, no
  CUDA, NumPy 2.5.2, SciPy 1.18.1, scikit-learn 1.9.0, MNE 1.12.1, WFDB 4.3.1,
  pandas 3.0.5, torch threads=4) → `RECORDED_ENVIRONMENT_MATCH_FOR_CHECKED_FIELDS` (scoped per audit §48: interpreter/backend versions + thread setting are checked; CPU model and full env vars are not, so this is not a bit-for-bit "EXACT" claim). No package was changed to force a match.
- **Dataset fingerprinting.** All 266 raw input records used by the canonical
  experiments (PPG-DaLiA 16, PTT 198, Sleep primary 36, Sleep secondary 16) are
  fingerprinted; 266/266 present; **0 raw files committed to git**.
- **Checkpoint archival.** 50 checkpoints externally durable (GitHub Release).
- **Frozen-checkpoint reproduction.** Every checkpoint-based canonical result was
  re-evaluated from frozen weights with **zero** numerical difference.
- **114-condition robustness reproduction.** Full sweep re-run from the local frozen
  checkpoint; all 114 conditions match within 1e-4 bpm (max observed 7.6e-6 bpm).
- **Honest framing.** This is *independent re-evaluation from frozen artifacts* on
  the same stack — **not** independent-dataset or independent-lab replication.

### Results/Methods — Interaction (new, writable, NOT a headline)
- One predeclared, capacity-fair (constant 112 params/channel) factorial experiment
  on Sleep-EDF: M0 = EEG, M_A = EEG+EOG, M_B = EEG+Resp, M_AB = EEG+EOG+Resp, 5 seeds.
- Means: M0 0.7473, M_A 0.7693, M_B 0.7332, M_AB 0.7583 (macro-F1).
- Interaction term = Benefit(AB) − Benefit(A) − Benefit(B) = **+0.0031 ± 0.0434**
  (2/5 seeds positive): **approximately additive / unresolved**.
- Plain-language claim: *"Adding both EOG and respiration did not show a stable extra
  benefit beyond their individual effects under this model and dataset."*
- Immediately bound it: *"This does not prove that sensor interactions are absent in
  general."* **No synergy claim. No redundancy claim. Not 'interaction absent'.**
- Value is methodological honesty (we tested it and reported the null), not a result.
- Capacity-fairness caveat to keep visible: architecture growth was controlled by a
  consistent per-channel convention, but this remains a **model-specific,
  within-dataset** interaction estimate.

## Claims that DO NOT change (Day 10)
- **PPG-DaLiA:** still a modest, target-specific IMU HR benefit (capacity-controlled).
- **PTT:** still a heterogeneous negative for HR.
- **Sleep:** still same-dataset (Sleep-EDF); primary + secondary holdout, not
  independent replication.
- **Digital Twin:** still architecture-only, untrained, unvalidated.
- **Spaceflight/microgravity:** still motivation, not validation.
- **Final architecture:** still UNRESOLVED; Pareto still `FORMAL_PARETO_NOT_READY`.

## Future-only claims (do not state as achieved)
- Independent-dataset sleep replication; global interaction coverage; final BOM /
  system power / system mass; trained Digital Twin; astronaut validation.

## Developer / reproducibility note — CRLF portable hashing (Day 10, §34)
This repo has `core.autocrlf=true`. On a Windows checkout, text JSON artifacts have
CRLF line endings on disk, while git stores (and the machine that froze the
`FROZEN_FAULT_ROBUSTNESS_SHA256` guard hashed) the **LF-normalized** blob. Hashing
raw bytes made the guard falsely fire on every Windows clone even when the JSON
content was byte-for-byte identical after parsing (`json.loads(committed) ==
json.loads(working)` was True).

**Fix** (`ml/build_sensor_marginal_value_contract.py::_sha256`): normalize `\r\n → \n`
before hashing small text JSON source artifacts (whole-file read, so a CRLF is never
split across a chunk boundary).

**Safety:** this only normalizes **text line endings** on JSON *source artifacts*. It
is **not** applied to binary checkpoints (`.pt`) — those are never passed to this
helper. A genuine content edit still changes the LF-normalized bytes and still trips
the guard, so the scientific meaning of the SHA is preserved. Do **not** globally
normalize binary artifacts. Mac (LF-native) tests are unaffected and pass.
