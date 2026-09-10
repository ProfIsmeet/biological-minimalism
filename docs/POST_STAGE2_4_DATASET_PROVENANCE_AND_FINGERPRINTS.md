# Post-Stage2-4 Dataset Provenance and Fingerprints

## GalaxyPPG

- Source: Zenodo DOI 10.5281/zenodo.14635823.
- Archive: `GalaxyPPG.zip`, 481,594,233 bytes, MD5
  `d9a48bfcd07928fb22b96dc40cf2e7d4` (matches Zenodo's own record metadata
  exactly — verified prior sprint, re-used this sprint, not re-downloaded).
- License: CC BY 4.0.
- Real structure: `Dataset/P01..P24/{E4,GalaxyWatch,PolarH10}/*.csv` +
  `Event.csv` + `Meta.csv`.
- 24/24 real participants pass the real eligibility check
  (`results/galaxyppg_eligibility_stage2.json`): BVP + ACC + ECG present,
  >300s real overlap after the documented UTC+9 Polar correction.
- Native rates (measured, this and prior sprint): E4 BVP 64.0 Hz, E4 ACC
  32.0 Hz, Polar ECG ~130.3–130.5 Hz.

## LBNP

- Source: Zenodo DOI 10.5281/zenodo.10119427 (resolves to version record
  10119428).
- Archive: `Mayo_LBNP_raw_data.zip`, 712,958,490 bytes, MD5
  `376ddafa9ea162e223474a6a4aea39d9` (matches Zenodo's own record metadata
  exactly — verified prior sprint).
- License: CC BY 4.0.
- Real structure: 5 `.mat` files (`LBNP_level_times.mat`,
  `raw_av_ST_impedance_data.mat`, `raw_cheetah_bioimpedance.mat`,
  `raw_labchart_data.mat`, `raw_sciospec_dat.mat`).
- n=16 independently confirmed 3 ways this sprint (`LBNPinf`, `SSout`,
  `Labchart` struct-array shapes all `(1, 16)`).
- EIS: 100-point excitation-frequency axis (100.0008 Hz–1.00000005 MHz),
  3 sites (`Thoracic`, `Abdominal`, `Arm`), complex `Zmat` per site per
  subject, real per-spectrum timestamps (`tvec`) confirmed
  timebase-compatible with the real stage-transition timestamps
  (`LBNPinf.ts`).

## HMC

- Source: PhysioNet, `https://physionet.org/files/hmc-sleep-staging/1.1/`.
- Full-cohort access: blocked by a genuine external TLS certificate
  expiry (`notAfter=Sep 9 20:22:45 2026 GMT`, independently verified via
  `openssl s_client`), reconfirmed this sprint via one controlled recheck
  (still blocked, not retried further).
- 8/151 recordings (7 complete EDF+scoring pairs) downloaded and
  SHA256-verified against PhysioNet's own `SHA256SUMS.txt` before the
  expiry, in the prior sprint — unchanged, reused this sprint for the
  bounded n=7 diagnostic (also unchanged this sprint).

## Sleep-EDF

Unchanged — already local, already fingerprinted in prior sprints (856 MB,
36 files, 18-subject cohort, SHA256-verified against PhysioNet's own
`SHA256SUMS.txt`).

## Checksum terminology precision

- Zenodo-provided checksums for GalaxyPPG/LBNP: **MD5** (per Zenodo's own
  API `checksum` field format `md5:...`).
- PhysioNet-provided checksums for Sleep-EDF/HMC: **SHA256** (per
  PhysioNet's own `SHA256SUMS.txt` files).
- This project's own checkpoint-manifest hashes (all experiments): SHA256,
  independently computed with Python's `hashlib.sha256`, never conflated
  with the source datasets' own (differently-algorithmed) checksums.
