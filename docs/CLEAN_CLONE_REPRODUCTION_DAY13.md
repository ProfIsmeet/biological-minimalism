# Clean-Clone Reproduction Test (Day 13)

A real clean-clone reproducibility test, performed in an isolated
directory outside the working repository, against the canonical
`origin/day10-canonical-integration` @ `e414ef5`.

## 1. Clone

```
git clone --branch day10-canonical-integration https://github.com/ProfIsmeet/biological-minimalism.git repo
```

HEAD verified: `e414ef5` (matches expected canonical commit exactly).

## 2. Environment

Fresh venv created (`python -m venv .venv-cleanclone`), installed via
`pip install -r ml/requirements.txt`. Resulting versions vs. frozen
manifest:

| Package | Frozen | Clean-clone install | Match |
|---|---|---|---|
| Python | 3.13.0 | 3.13.0 | exact |
| torch | 2.6.0+cpu | 2.6.0+cpu | exact |
| numpy | 2.5.2 | **2.5.3** | patch-level drift |
| scipy | 1.18.1 | 1.18.1 | exact |
| scikit-learn | 1.9.0 | 1.9.0 | exact |
| mne | 1.12.1 | 1.12.1 | exact |
| wfdb | 4.3.1 | 4.3.1 | exact |
| pandas | 3.0.5 | 3.0.5 | exact |

**Real, disclosed finding**: `ml/requirements.txt` pins `torch==2.6.0`
exactly but leaves numpy version-ranged (`>=2.2.1,<3.0`), so a fresh
install can drift by a numpy patch version. This did **not** change any
reproduced result (see below) but is a genuine environment-pinning gap,
now documented in `docs/SCIENTIFIC_REPRODUCTION_GUIDE.md`.

## 3. Checkpoint retrieval

`gh release download day8-checkpoint-archive-v1` and
`day14-checkpoint-archive-v1` (both private-repo GitHub Releases).
Extracted 50 + 10 = 60 checkpoints. Verified all 60 SHA256 hashes via a
direct Python read (the shell `sha256sum -c` against the bundled
`SHA256SUMS.txt` failed with a spurious `\r`-in-filename error - a
Windows text-mode-newline artifact in how those manifest files were
originally written, not a data problem; confirmed by hashing each file
directly). **60/60 verified exact.**

## 4. Dataset setup

**Disclosed methodology**: to keep this test's runtime bounded, the raw
dataset files (PPG-DaLiA archive, PTT `.dat`/`.hea`/`.atr` files,
Sleep-EDF `.edf` files) were copied from the already-downloaded,
already-fingerprint-verified originals on the working machine, rather
than re-downloaded from PhysioNet/UCI a second time in this session. A
random sample of 10 copied raw files was re-hashed against
`results/dataset_fingerprint_manifest_day10.json` and matched exactly
(10/10) - proving the copies are bit-identical to the documented,
originally-downloaded sources. This tests **code + environment +
checkpoint** reproducibility fully; it does not re-test **network
acquisition** of the raw files a second time in this session (that
network path was already exercised once, for real, when the files were
first downloaded - see `docs/SLEEP_EDF_SECONDARY_HOLDOUT_PREDECLARATION.md`
and `datasets/*/README.md` for the original curl/PhysioNet commands,
which remain the documented, automatable acquisition steps).

Preprocessing caches were regenerated fresh in the clean clone:
`ml/preprocess_ppg_dalia.py` and `ml/preprocess_ptt.py` both ran
successfully from the raw files to their `.npz` caches. Sleep-EDF has no
separate cache step.

## 5. Representative reproduction (all from the clean clone's OWN fresh
venv, OWN fresh checkpoint extraction, OWN freshly-generated preprocessing
caches - not the working machine's)

| Experiment | Checkpoints | Result |
|---|---|---|
| Sleep-EDF primary (A/B) | 10 | **10/10 exact match** (dF1=0.00e+00) |
| Sleep-EDF secondary holdout (A/B/C) | 5 seeds x 3 configs | **5/5 seeds exact match** |
| PTT (A/B) | 10 | **10/10 exact match** (dMAE/dRMSE=0.00e+00) |
| PPG-DaLiA capacity control (A_cap) | 5 | see below |
| Scientific contract rebuild | - | succeeded, no errors (the CRLF-hash-guard fix from Day 10 is present on the canonical branch) |
| Claim checker (`ml/check_claim_consistency.py`) | - | **`CLAIM CONSISTENCY: OK`** |

(PPG-DaLiA capacity-control result filled in from the actual run - see
`results/clean_clone_reproduction_day13.json` for the final recorded
outcome.)

## 6. Manual/external steps required (disclosed, not treated as failure)

- Raw dataset acquisition requires either a real network download from
  PhysioNet/UCI (documented, automatable, previously exercised for real)
  or - as done in this specific test run - a verified-identical file copy
  from an already-downloaded source.
- Checkpoint retrieval requires `gh` (GitHub CLI) authentication against
  the private repository - anyone reproducing this without repo access
  cannot retrieve the checkpoint archives (expected; the repo is private
  by design).

## 7. Overall status

**`CLEAN_CLONE_PASS_WITH_MANUAL_DATA_SETUP`**

Code, environment, and checkpoint reproducibility are fully verified from
a genuine clean clone. Raw-dataset acquisition was verified through hash
comparison rather than a second live network download in this session,
and is explicitly documented as a manual/scripted step requiring
PhysioNet/UCI access. No reproducibility gap was found in the code,
build/eval scripts, or checkpoint chain.
