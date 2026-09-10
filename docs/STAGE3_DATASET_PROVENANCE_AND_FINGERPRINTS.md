# Stage 3 Dataset Provenance and Fingerprints

## GalaxyPPG

Unchanged provenance from the prior sprint (Zenodo DOI 10.5281/zenodo.14635823,
MD5 `d9a48bfcd07928fb22b96dc40cf2e7d4`, CC BY 4.0). This sprint reuses the
already-downloaded, already-verified local archive — no re-download.
Real measured rates: E4 BVP 64.0 Hz, E4 ACC 32.0 Hz, Polar ECG ~130.3–130.5 Hz.
24/24 real participants eligible.

## LBNP

Unchanged archive provenance from the prior sprint (Zenodo DOI
10.5281/zenodo.10119427 / version record 10119428, MD5
`376ddafa9ea162e223474a6a4aea39d9`, CC BY 4.0). **New this sprint**: real
native rate for ECG/pleth/MAP confirmed as 1000 Hz (derived directly from
`Labchart.ts`'s real inter-sample delta). **New real eligibility finding**:
only 12/16 subjects have valid (non-NaN) pleth — reducing the usable
cohort from the previously-reported n=16 to a real, actual-file-verified
n=12.

## HMC

Source: PhysioNet, `https://physionet.org/files/hmc-sleep-staging/1.1/`.
**New this sprint**: TLS certificate confirmed renewed
(`notAfter=Dec 9 2026`, independently verified via `openssl s_client`).
Full 151-recording download resumed (skipping the 8 recordings already
SHA256-verified before the prior expiry). Exact final downloaded/verified
count recorded in the final Stage 3 completion report (download was
in-progress at documentation time).

## ds003838

Unchanged from prior sprints. n=3 bounded diagnostic remains the best
available real evidence; full 65-subject cohort requires ~93 GB / ~9.4h
additional download (quantified this sprint,
`docs/DS003838_STAGE3_FULL_EXPERIMENT_STATUS.md`) — not attempted.

## Sleep-EDF / QDE

Unchanged, already local, already fingerprinted in prior sprints.

## Checksum terminology (unchanged discipline)

Zenodo sources: MD5. PhysioNet sources: SHA256. This project's own
checkpoint manifests: SHA256 (`hashlib.sha256`), never conflated with
source-dataset checksums.
