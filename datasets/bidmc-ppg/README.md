# BIDMC PPG and Respiration Dataset — real data used for this project's PPG training run

Substituted for WESAD in this project's PPG modality training pass: WESAD's
two official distribution links were both confirmed dead (see
`../sleep-edfx/README.md`). BIDMC is arguably a better fit for the PPG
modality specifically than WESAD would have been: it pairs a real 125 Hz PPG
(PLETH) waveform with real per-second clinical-monitor ground truth for HR
and respiration rate — direct real labels for two of this project's actual
`OUTPUT_TARGETS` (`heart_rate_bpm`, `respiration_rate_bpm`), not a proxy task.

## Source

Pimentel, M. A. F., Johnson, A. E. W., Charlton, P. H., Birrenkott, D.,
Watkinson, P. J., Tarassenko, L., & Clifton, D. A. (2017). Toward a Robust
Estimation of Respiratory Rate From Pulse Oximeters. *IEEE Transactions on
Biomedical Engineering*, 64(8), 1914–1923. A subset of the MIMIC II matched
waveform database (critically-ill adult ICU patients, Beth Israel Deaconess
Medical Center). Distributed via PhysioNet, Open Data Commons Attribution
License v1.0 (open access, no credentialing required, verified by direct
download): https://physionet.org/content/bidmc/1.0.0/

## Download

53 subjects, ~147 MB total (`raw/`, gitignored, not committed):

```bash
mkdir -p raw && cd raw
for i in $(seq -w 1 53); do
  for suffix in Signals Numerics; do
    curl -sS -o "bidmc_${i}_${suffix}.csv" \
      "https://physionet.org/files/bidmc/1.0.0/bidmc_csv/bidmc_${i}_${suffix}.csv"
  done
done
```

`*_Signals.csv`: 125 Hz `Time, RESP, PLETH, V, AVR, II` (this project uses
only `PLETH`). `*_Numerics.csv`: real per-second `Time, HR, PULSE, RESP,
SpO2` from the bedside clinical monitor.

## Real result

Trained the project's real `Conv1DEncoder` (`backend/app/ml/models.py`,
imported unmodified) on non-overlapping 8-second real PPG windows, subject-
level held-out split (37 train subjects / 16 fully unseen test subjects, 3,172
real windows total after dropping windows with a real missing clinical-monitor
reading — see `../../ml/README.md` for the full, honest numbers including
where this did **not** beat a naive baseline).
