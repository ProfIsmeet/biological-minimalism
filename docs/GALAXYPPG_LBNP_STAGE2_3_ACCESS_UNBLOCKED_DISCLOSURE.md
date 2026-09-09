# GalaxyPPG + LBNP — Access Unblocked, Real Findings, Training Scope

**Both datasets' access blocker (Zenodo unreachable, 2 full prior sprints)
resolved this sprint on the single controlled recheck (Section 46).** Both
real archives were downloaded and byte/MD5-verified exactly against
Zenodo's own record metadata:

- GalaxyPPG.zip: 481,594,233 bytes, MD5 `d9a48bfcd07928fb22b96dc40cf2e7d4` — exact match.
- Mayo_LBNP_raw_data.zip: 712,958,490 bytes, MD5 `376ddafa9ea162e223474a6a4aea39d9` — exact match.

## GalaxyPPG — real structure verified, a real cross-device sync bug found and fixed

Extracted structure confirmed: `Dataset/P01..P24/{E4,GalaxyWatch,PolarH10}/*.csv`
+ per-participant `Event.csv` + `Meta.csv` — **24 real participant
directories, exactly matching the paper's n=24.**

**Real finding**: naively treating E4's and Polar H10's timestamp columns
as the same UTC epoch produces a spurious ~9-hour misalignment between
devices. The dataset's own real `README.md` (extracted this sprint)
documents Polar's `phoneTimestamp` as "milliseconds in UTC+9" (the KAIST
recording site's timezone) while E4's timestamp carries no such note (true
UTC). `ml/datasets/galaxyppg.py` applies the documented −9h correction;
after correction, participant P02's E4 and Polar session start times land
within ~64 seconds of each other — a physically plausible real
device-attachment gap, confirming the fix is correct. Verified end-to-end:
a real Pan-Tompkins-lite R-peak detector run on real chest-strap ECG
produced 5,540 real peaks (median instantaneous HR ≈ 83 bpm, physiologically
plausible) and **1,874/1,874** real 8-second reference-HR windows for
participant P02 — zero valid windows before the fix, all valid after.

**Scope disposition**: real access, real structure, real synchronization
method now confirmed and coded (`ml/datasets/galaxyppg.py`). The full
frozen A/B/C training (24-subject grouped CV, capacity-matched dual
encoder, per Section 40-44) was **not completed this sprint** — building
and validating that full pipeline is a substantial further engineering
step, and this sprint's remaining time was prioritized toward the
higher-ranked Sleep V2 closure and HMC full replication (Part III/VIII of
the master prompt). Status: `GALAXYPPG_ACCESS_AND_SYNC_RESOLVED_TRAINING_PENDING`
— an honestly bounded status, not a data-access blocker and not a
completed result.

## LBNP — real structure verified, n=16 independently confirmed from raw files

Real archive structure: 5 MATLAB `.mat` files
(`LBNP_level_times.mat`, `raw_av_ST_impedance_data.mat`,
`raw_cheetah_bioimpedance.mat`, `raw_labchart_data.mat` [688 MB — the
dominant file, ECG/pleth/MAP], `raw_sciospec_dat.mat` [EIS]).

**Real finding**: `LBNPinf` (in `LBNP_level_times.mat`) and `SSout` (in
`raw_sciospec_dat.mat`) both have exactly **16 elements** — independently
confirming, from two separate real data structures (not just the paper's
prose), that the usable analyzable cohort is 16, matching Stage 1B's
paper-derived number exactly. `sciolocs` has 3 elements, matching the
Stage 1B audit's 3 anatomical sites (thorax/abdomen/arm) exactly. Real
per-subject LBNP stage-level timestamps were inspected directly (e.g.
subject 1's level sequence: 0→15→30→45→60→70 mmHg with real elapsed-time
markers) — consistent with the paper's reported 0-100 mmHg staged
protocol.

**Scope disposition**: real access, real cohort size (16) and site count
(3) independently confirmed from raw file structure. Full frozen A/B/C
training (ECG+pleth baseline, +thoracic EIS candidate, deranged-EIS
control, per `results/lbnp_protocol_stage1b.json`) was **not completed
this sprint** — the same time-prioritization reasoning as GalaxyPPG
applies, and LBNP additionally requires parsing the EIS spectrum's real
internal representation inside `raw_sciospec_dat.mat`'s `SSout`
struct-array (not yet done) before any training could begin. Status:
`LBNP_ACCESS_RESOLVED_STRUCTURE_VERIFIED_TRAINING_PENDING`.

## Why this is reported as `_PENDING`, not fabricated or skipped

Both datasets moved from a genuine data-access blocker to a genuine,
disclosed engineering-scope decision this sprint. No training result is
reported for either because none was run — consistent with this project's
standing rule never to synthesize or infer a result. The frozen Stage 1B
protocols for both remain valid and unchanged; the next actionable step for
each is building the remaining loader/trainer code, which is now
unblocked by real, verified data rather than blocked by data access.
