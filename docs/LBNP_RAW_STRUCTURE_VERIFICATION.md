# LBNP Raw MATLAB Structure — Verified This Sprint

Real archive extracted (`datasets/lbnp-impedance/raw/Mayo_LBNP_raw_data.zip`,
MD5-verified against Zenodo, see prior sprint's disclosure doc). Five real
`.mat` files inspected directly via `scipy.io.loadmat`.

## Biological n — independently confirmed a THIRD way

- `LBNP_level_times.mat` → `LBNPinf`: shape `(1, 16)` struct array.
- `raw_sciospec_dat.mat` → `SSout`: shape `(1, 16)` struct array.
- `raw_labchart_data.mat` → `Labchart`: shape `(1, 16)` struct array.

**All three independent real data structures agree exactly: n=16** — the
same number reported in the paper (18 enrolled, 16 usable) and now
confirmed three separate ways from raw file content, not just prose.

## Real EIS structure (`SSout`)

`SSout[0, subject_idx]['sciodat']` is a 3-element struct array — one per
anatomical site, in the exact order given by `sciolocs`: `['Thoracic',
'Abdominal', 'Arm']` — matching Stage 1B's audit exactly. Each site struct
has real fields:

- `tvec`: (43, 1) — real per-spectrum timestamps (subject 1's thoracic
  site: 692.28 to 729.87, consistent units across all 3 sites for a given
  subject — appears to be minutes elapsed in the session, consistent with
  ~1 spectrum/minute over ~38 real minutes, matching the paper's stated
  acquisition cadence).
- `fs`: (100, 1) — the real excitation-frequency axis, 100.0008 Hz to
  1.00000005 MHz, **exactly 100 points**, confirming Stage 1B's audit.
- `Zmat`: (43, 100) **complex** impedance matrix (real spectra × real
  frequencies) — genuine real+imaginary impedance values, not a
  placeholder.
- `erflg`: (43, 1) — per-spectrum error flags (0 = good; subject 1's
  thoracic site: all-zero, i.e. no flagged errors in this sample).

## Real ECG/pleth/MAP structure (`Labchart`)

`Labchart[0, subject_idx]` has fields `ts` (timestamps), `ecgs`, `MAP`,
`pleth` — exactly the three A-arm signals the frozen protocol needs.
Internal shapes/sample rates not yet extracted (deferred — see below).

## What remains for a full LBNP A/B/C training run (not done this sprint)

1. Extract real native sample rates for `ecgs`/`MAP`/`pleth` from `ts`
   (currently unverified — Stage 1B flagged this as unverified, and it
   remains unverified this sprint too).
2. Time-align `Labchart`'s `ts` axis with `SSout`'s `tvec` axis (per
   subject) and with `LBNP_level_times.mat`'s real stage-transition times
   to build the real target label per EIS spectrum / ECG-pleth window.
3. Build the frozen A (ECG+pleth) / B (+thoracic EIS) / C (+deranged EIS)
   windowing and training pipeline.

**This sprint's real contribution**: full raw-file structural verification
(3-way independent n=16 confirmation, real complex EIS matrix confirmed,
real 100-point frequency axis confirmed, real site order confirmed, real
ECG/pleth/MAP field presence confirmed) — genuinely de-risks the remaining
implementation work, but the remaining work itself (time alignment +
training) was not completed this sprint, time-prioritized behind
GalaxyPPG per the master prompt's explicit ordering (LBNP is priority 2,
GalaxyPPG is priority 1).

**Status: `LBNP_STRUCTURE_VERIFIED_TRAINING_STILL_PENDING`** (progress
beyond the prior sprint's "training pending" status: 3-way n confirmation,
full EIS field-level structure, real complex Zmat confirmed).
