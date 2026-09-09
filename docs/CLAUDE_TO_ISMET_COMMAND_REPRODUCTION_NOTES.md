# Claude → Ismet: Command Reproduction Notes

These are the commands from Claude's Stage-2 science sprint. Commands marked
**EXACT** were run verbatim this session. Commands marked **DERIVED** are
reconstructed from the scripts/config and are correct in intent but the exact
invocation string is not separately logged. Nothing here is fabricated; where a
detail is unknown it is marked `UNKNOWN`.

## Environment (EXACT)
- ML venv: `.venv-integration/bin/python` (Python 3.14, torch 2.14.0, mne 1.12.1, numpy 2.5.3, scikit-learn present)
- Backend venv: `backend/.venv/bin/pytest` (Python 3.12)
- Working dir: `/Users/emirharunsunbul/Documents/ChatGPT/IAC`

## Dataset downloads (EXACT intent; resumable, checksum-verified)
Sleep-EDF 18-subject cohort and HMC 12-recording pilot were fetched with
resumable `curl -C -` loops against:
- `https://physionet.org/files/sleep-edfx/1.0.0/sleep-cassette/<file>`
- `https://physionet.org/files/hmc-sleep-staging/1.1/recordings/<file>`
Each file verified byte-exact against the server `Content-Length` and then
against the official `SHA256SUMS.txt`. Files landed in
`datasets/sleep-edfx/raw/` and `datasets/hmc-sleep-staging/raw/`.
The exact loop scripts were session scratch files (not in-repo); the file lists
are the frozen split subject/recording IDs (see
`ml/experiments/sleep_edf_eeg_eog_ablation/subject_split.json` and
`results/hmc_split_stage2.json`).

## A/B reproduction (EXACT)
```
.venv-integration/bin/python -u ml/train_sleep_edf_primary_seedfix_v2.py
```
Produced the 10 reproduction checkpoints + (accidentally) overwrote
`results/sleep_edf_primary_seedfix_v2.json`, since preserved as
`results/claude_noncanonical_sleep_edf_primary_seedfix_v2_reproduction.json`
and canonical restored from HEAD.

## C (shuffled-EOG control) — partial (EXACT, killed early)
```
.venv-integration/bin/python -u ml/train_sleep_edf_shuffled_eog_control_seedfix_v2.py
```
Killed at seed-42 training start. No artifacts written.

## Interaction (M_B, M_AB) — NEVER RUN
Intended (DERIVED, not executed):
```
.venv-integration/bin/python -u ml/train_sleep_edf_interaction_resp_seedfix_v2.py
```

## HMC A/B/C — NEVER RUN
Intended (DERIVED, not executed):
```
.venv-integration/bin/python -u ml/train_hmc_sleep_a_b_c.py
```

## Tests (EXACT)
```
.venv-integration/bin/python -m pytest ml/tests -q            # 290 passed, 19 skipped
(cd backend && .venv/bin/pytest -q)                           # 158 passed
.venv-integration/bin/python -m pytest ml/tests/test_sleep_scientific_remediation_day12.py \
  ml/tests/test_sleep_edf_eeg_eog_ablation.py \
  ml/tests/test_sleep_edf_shuffled_eog_control.py \
  ml/tests/test_sleep_edf_secondary_holdout.py -q             # 61 passed, 5 skipped
```

## Checkpoint hashing / loadability (EXACT intent)
SHA256 + `torch.load(..., weights_only=True)` over
`ml/checkpoints/sleep_edf_*seedfix_v2_seed*.pt` — full hashes in the manifest.
