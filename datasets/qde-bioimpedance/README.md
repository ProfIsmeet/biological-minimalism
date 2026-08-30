# PhysioNet Quantitative Dehydration Estimation (QDE) — real bio-impedance + temperature data

Substituted for NASA OSDR in this project's first bio-impedance training pass:
OSDR's public search API (`https://osdr.nasa.gov/osdr/data/search?term=...`)
was queried directly (not assumed) for `impedance`, `bioimpedance`,
`fluid shift`, `dry immersion`, and `head-down tilt` while building this
loader. Every hit was a molecular-biology study (transcriptomics, proteomics,
gene expression, microarray) — OSDR is GeneLab-derived and hosts 'omics data,
not raw physiological sensor time series. No downloadable real bio-impedance
sensor dataset was found there.

## Source

PhysioNet, *Quantitative Dehydration Estimation*, v1.0.0 (published
2017-08-10). Open Data Commons Attribution License v1.0 (open access, no
credentialing required, verified by direct download):
https://physionet.org/content/qde/1.0.0/

## What it is

10 subjects ran on a treadmill for 120 minutes without fluid intake, split
into 8 × 15-minute intervals (9 measurement points per subject including the
pre-exercise baseline). At each point, real data was recorded:

- **Segmental bio-impedance** at 1000 kHz — right arm, left arm, trunk,
  right leg, left leg (Ohms) — the same measurement *technique* this
  project's bio-impedance sensor concept is built around (PDD Section 8).
- **Skin temperature** at 11 sites (°C) — this project's peripheral
  temperature sensor's real-world analog.
- **Total body water** (TBW, liters, via InBody 720 bioelectrical impedance
  analysis) — the real target used for training (see `../../ml/train_bioimpedance.py`).

This is exercise-induced dehydration, not microgravity-induced cephalad fluid
shift — a real, physiologically-grounded body-fluid-loss protocol using the
same measurement technique, not a spaceflight-analog study. That distinction
is stated plainly in the PDD (Section 8) and in `ml/train_bioimpedance.py`.

## Download

```bash
mkdir -p raw && cd raw
curl -sS -o dehydration_estimation.csv \
  "https://physionet.org/files/qde/1.0.0/dehydration_estimation.csv"
```

~14 KB, 90 rows (10 subjects × 9 measurement points), tabular — not a
high-sample-rate waveform, so it is loaded directly as a small table rather
than windowed (`ml/datasets/qde_bioimpedance.py`).

## Real result

See `../../ml/README.md` for the full, honest result — a small MLP trained
with leave-one-subject-out cross-validation, reframed to predict each
subject's fluid change *from their own baseline* (matching this project's
actual "fluid shift" framing, not absolute body water, which is dominated by
body size). Reported with equal weight to what it does and does not show.
