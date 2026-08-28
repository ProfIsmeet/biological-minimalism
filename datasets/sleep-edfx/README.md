# PhysioNet Sleep-EDF (sleep-cassette) — real data used for this project's first training run

Substituted for WESAD in this project's first real-data training pass: WESAD's
two official distribution points were both dead when checked directly
(`https://uni-siegen.sciebo.de/s/pYjSgfOVs6Ntahr/download` → 404;
`https://ubi29.informatik.uni-siegen.de/home/datasets/icmi18/` → 404) at the
time this was written. Sleep-EDF is fully open (no login, no application), and
is already cited in this project's PDD (Dataset Research, Section 7) for
respiration/circadian structure — and several of its recordings include real
`Resp oro-nasal` and `Temp rectal` channels alongside EEG.

## Source

Kemp, B., Zwinderman, A. H., Tuk, B., Kamphuisen, H. A. C., & Oberye, J. J. L.
(2000). Analysis of a sleep-dependent neuronal feedback loop: the slow-wave
microcontinuity of the EEG. *IEEE Transactions on Biomedical Engineering*,
47(9), 1185-1194. Distributed via PhysioNet (Goldberger et al., 2000):
https://physionet.org/content/sleep-edfx/1.0.0/

## What is downloaded here

Three subjects' overnight polysomnography recordings (`raw/`, gitignored, not
committed — ~150MB total):

```bash
mkdir -p raw && cd raw
for f in SC4001E0-PSG.edf SC4001EC-Hypnogram.edf \
         SC4002E0-PSG.edf SC4002EC-Hypnogram.edf \
         SC4011E0-PSG.edf SC4011EH-Hypnogram.edf; do
  curl -sS -o "$f" "https://physionet.org/files/sleep-edfx/1.0.0/sleep-cassette/$f"
done
```

Each `*-PSG.edf` is verified against its real `Content-Length` header after
download (byte-exact match required — a partial/corrupted download is not
used for training). Channels present: `EEG Fpz-Cz`, `EEG Pz-Oz`,
`EOG horizontal`, `Resp oro-nasal`, `EMG submental`, `Temp rectal`,
`Event marker`, sampled at 100 Hz.

## What this data was used for

See `../../ml/train_sleep_edf.py` and `../../ml/README.md` — real 30-second
`EEG Fpz-Cz` windows, labeled with the real hypnogram-scored sleep stage, used
to train the project's actual `Conv1DEncoder` (from
`backend/app/ml/models.py`, imported unmodified) as a 5-class sleep-stage
classifier, with a **subject-level** (not epoch-level) held-out split: trained
on 2 subjects, tested on the 1 fully held-out third subject.

This is EEG-only. The `Resp oro-nasal` and `Temp rectal` channels present in
these files were not used in this first pass — they are a documented
opportunity for a follow-up pass (see `ml/README.md`'s "Next steps").
