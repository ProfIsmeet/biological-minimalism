# Dataset Matrix — Target-First Research (Priority 1)

Per `docs/TECHNICAL_HANDOFF_V2.md` §9/§18 P1: search by target and ground truth, not
just sensor name, and re-verify real accessibility by actually attempting a
download/HEAD request before writing a dataset in as "available" — never assume from
a paper's stated distribution point. Every entry below was checked this way (commands
shown), not taken on faith from search-result text.

Template fields follow the handoff's own record format (§9).

---

## PPG-DaLiA — ✅ downloaded, preprocessed, used in a real experiment (Priority 2 complete)

```
Dataset name: PPG-DaLiA
Subjects: 15 (8 female, 7 male, aged 21-55)
Population: healthy adults, free-living/near-real-life activities
Signals: wrist (Empatica E4: 1-channel PPG @ 64 Hz, 3-axis accelerometer @ 32 Hz),
         chest device (ECG - ground-truth HR)
Which signals are simultaneous: PPG + IMU + ECG, same subject, same session, 8 daily
         activities (sitting, walking, cycling, driving, working, etc.) - genuinely
         synchronized multimodal data, satisfying handoff §8's "real fusion claim"
         requirement for the PPG+IMU sub-problem specifically
Sampling rates: PPG 64 Hz, ACC 32 Hz, ECG (chest) - see original paper for exact rate
Ground-truth labels: HR derived from the chest ECG
Target(s) we can honestly evaluate: heart-rate estimation from PPG, WITH and WITHOUT
         IMU-based motion-artifact correction - this is the exact experiment handoff
         §18 Priority 2 asks for ("how much does synchronized IMU improve
         PPG-derived heart-rate estimation under motion?")
Subject-level split possible: yes (15 subjects)
License/access: CC BY 4.0, fully open, no login
Space relevance: none (terrestrial, free-living activity) - general technique
         validation only, same caveat as BIDMC in the PDD
Known domain gap: general population, not astronaut/spaceflight-analog; motion
         context is terrestrial daily activity, not EVA/microgravity movement
Which ablation can this dataset support: PPG-with-IMU vs PPG-without-IMU heart-rate
         accuracy under real motion - directly supports Priority 2
```

**Access verification performed:** original UCI page
(`archive.ics.uci.edu/dataset/495/ppg+dalia`) does not itself serve files. Located a
real, open Zenodo mirror instead and verified two actual downloadable files via the
Zenodo API (`curl -s https://zenodo.org/api/records/3902728`):

| File | Size |
|---|---|
| `PPGDalia_TRAIN.ts` | 423,905,299 bytes (~424 MB) |
| `PPGDalia_TEST.ts` | 212,538,529 bytes (~213 MB) |

Note: this Zenodo copy is the Monash/UEA/UCR time-series-regression-repository
reformatting (`.ts` files, windowed PPG+ACC with HR as target already extracted).
**Inspected its header directly and found it has no subject/group field at all** —
impossible to verify its TRAIN/TEST split is subject-disjoint, which this
project's own standing rule (and the task's explicit requirement) does not allow
assuming. Not used for the actual experiment.

**Used the original raw per-subject distribution instead**
(`archive.ics.uci.edu/static/public/495/ppg+dalia.zip`, ~2.87 GB, downloaded
successfully — unlike WESAD's equivalent UCI static-zip check below, this one is
the real dataset, not a dead pointer). Verified real per-subject `.pkl` structure
by loading `S1.pkl` directly before writing the loader (`data['subject']`,
`data['signal']['wrist']['BVP']` @ 64 Hz, `data['signal']['wrist']['ACC']` @ 32 Hz,
`data['label']` = real ECG-derived HR per 8s/2s-step window). Full download,
preprocessing, and loader details: `datasets/ppg-dalia/README.md`.

**Priority 2 (first real ablation experiment) — complete.** Real result: adding
synchronized IMU reduced held-out heart-rate MAE from 9.090 to 7.032 bpm (≈23%),
subject-wise held out, stratified by motion severity, with a negative-control
(shuffled IMU) check. Full results: `ml/README.md` §"Priority 2" and
`ml/experiments/ppg_dalia_imu_ablation/results.json`.

---

## PulseDB — ❌ verified NOT anonymously accessible (all channels require login)

```
Dataset name: PulseDB
Subjects: 5,361 (from MIMIC-III matched-waveform subset + VitalDB)
Population: hospital/ICU (MIMIC-III) + surgical (VitalDB) patients
Signals: ECG, PPG, arterial blood pressure (ABP) waveform, per 10-second segment
Which signals are simultaneous: ECG + PPG + ABP, same subject/segment - would support
         a real ECG+PPG timing (PAT) + BP-reference experiment if accessible
Sampling rates: per Wang et al. (2023) - see PDD References
Ground-truth labels: real arterial-line blood pressure (not cuff-derived)
Target(s) we could honestly evaluate: cuffless BP trend from ECG-PPG timing, IF this
         dataset becomes accessible
Subject-level split possible: yes, in principle (5,361 subjects)
License/access: distribution requires an account on every channel checked
Space relevance: none - general/critical-care population
Known domain gap: same as any hospital-population dataset for this project's use
Which ablation can this dataset support: none currently - not accessible
```

**Access verification performed** (2026-08-30): checked all four distribution
channels listed in the PulseDB GitHub README
(`github.com/pulselabteam/PulseDB/blob/main/README.md`):

| Channel | Result |
|---|---|
| Box (`rutgers.box.com/s/...`) | `curl -sI -L` → **404 Not Found** |
| Google Drive | Requires Google account login (not attempted via curl - known to require auth) |
| OneDrive (Rutgers SharePoint) | Requires Microsoft account login |
| Kaggle (`doi.org/10.34740/KAGGLE/DS/2447469`) | Requires Kaggle account/API key |

**Status: blocked.** This is the PDD's originally-cited cuffless-BP dataset
(Section 7), never actually downloaded in this project — that citation remains valid
as a literature reference, but no training/ablation work can currently use this
dataset without someone on the team creating an account on one of the four platforms.
Flagged for the team rather than silently worked around.

---

## WESAD — ❌ re-verified dead (double-checked via a different official channel)

```
Dataset name: WESAD (Wearable Stress and Affect Detection)
Subjects: 15
Population: healthy adults, lab-based stress protocol (TSST)
Signals: wrist + chest device - BVP, ECG, EDA, EMG, RESP, TEMP, ACC
Which signals are simultaneous: all of the above, same subject/session
Sampling rates: per Schmidt et al. (2018) - see PDD References
Ground-truth labels: baseline/stress/amusement condition labels
Target(s): stress/autonomic-balance classification
Subject-level split possible: yes
License/access: CURRENTLY INACCESSIBLE - see below
Space relevance: none - terrestrial lab stressor
Known domain gap: general population, controlled lab stressor, no spaceflight context
Which ablation can this dataset support: none currently - not accessible
```

**Access verification performed** (2026-08-30, re-checked per the handoff's
instruction to try other mirrors before giving up again): this project's earlier
attempts (Sections 7/10.2 of the PDD) already found both
`https://uni-siegen.sciebo.de/s/pYjSgfOVs6Ntahr/download` and
`https://ubi29.informatik.uni-siegen.de/home/datasets/icmi18/` dead (404). This time,
checked UCI's own official static distribution endpoint directly:

```bash
curl -s "https://archive.ics.uci.edu/static/public/465/wesad+wearable+stress+and+affect+detection.zip" -o wesad.zip
# Real ZIP file (PK magic bytes confirmed), 261 bytes, contains one file: WESAD.txt
unzip -p wesad.zip WESAD.txt
```

Result: UCI's own official zip is a 261-byte pointer file, and its content is:

```
Link to the dataset: https://uni-siegen.sciebo.de/s/pYjSgfOVs6Ntahr/download
The zip-file also contains a dataset description file (readme.pdf).
```

**Same dead link**, now confirmed from UCI's own authoritative distribution point,
not just search-result text. **Status: dead, doubly-verified.** Not re-attempted a
third time; if the team can obtain WESAD through a personal contact at Uni-Siegen or
a different mirror, that would unblock the stress/autonomic-balance target this
project's abstract still names.

---

## HeartCycle — ⚠️ accessible, but audited and found PARTIALLY suitable only (Day 1, 2026-08-31)

```
Dataset name: HeartCycle
Subjects: 17 total, but only 4 (CH07-CH10) have any PPG data
Population: 17 healthy volunteers, age 19-40
Signals: ECG, ICG (thoracic, cardiac-timing-oriented - not the same as this
         project's fluid-shift bio-impedance concept), phonocardiography,
         echocardiography (reference standard), + PPG in 4 subjects only
Which signals are simultaneous: same file/session, but verified NOT full-duration
         aligned - Niccomo (ECG/ICG) channel was 2.44s shorter than the other
         three devices' channels in the one file directly inspected
Sampling rates: Niccomo ~198.5 Hz, stethoscope ~43,761 Hz, echo 136.0 Hz,
         PPG ~123.9 Hz (all measured directly from a real downloaded file)
Ground-truth labels: real, but inconsistently populated per-record - the one
         file inspected had several ground-truth fields (Niccomo PEP/LVET,
         all three Niccomo BP fields, PPG-derived PEP/LVET) as placeholder/
         missing-value sentinels, not real measurements
Target(s) we can honestly evaluate: none at Priority-2 rigor (see below);
         possibly a small-N PAT/PEP-vs-echocardiography correlation study
Subject-level split possible: only with 4 subjects (PPG) or up to 17 (non-PPG,
         no PPG-related question) - far thinner than Priority 2's 15
Which ablation can this dataset support: none cleanly - see full audit
```

**Full audit:** `datasets/HEARTCYCLE_AUDIT.md` (real file downloaded and
opened with `h5py`, not assumed from the dataset description).

**Verdict: PARTIALLY suitable.** Real, open access (verified: real directory
listing + real 14.2 MB file downloaded and parsed). Fails the gates for a
Priority-2-style trained ablation: only 4/17 subjects have PPG, records are
short (~5-8s snippets, not continuous recordings), and ground-truth fields
are inconsistently populated per-record. Not pursued further today — see the
audit's §10 for the recommended next step (re-flag PulseDB access to the
team, or scope a much smaller correlation study if HeartCycle is chosen
deliberately).

---

## Already downloaded and used (background — see PDD Section 10.2 / `ml/README.md`)

| Dataset | Role | Status |
|---|---|---|
| PhysioNet Sleep-EDF | EEG pathway | Downloaded, real training run complete (72.6% held-out accuracy) |
| PhysioNet BIDMC PPG and Respiration | PPG pathway (HR, RESP) | Downloaded, real training run complete (HR beats baseline, RESP does not) |
| PhysioNet QDE (dehydration) | BioZ + temperature pathway | Downloaded, real training run complete (small-N null result) |

None of these three provide real synchronized *cross-modal* data (each covers one
modality's own subjects only) — consistent with handoff §8's rule, this project's
per-modality checkpoints were trained independently and never presented as a fused
multimodal result.

## Not yet investigated

- **NASA OSDR** — re-confirmed in the PDD (Section 8) and `ml/README.md`: its public
  search API returns only 'omics (molecular biology) studies for every
  bio-impedance-related query attempted; it does not appear to host raw physiological
  sensor time series in a form this project could use. Not re-checked again in this
  pass since nothing has changed since that verification.
- **Synchronized multimodal cognitive/stress dataset** beyond WESAD (handoff §18 P1
  item 3) — not yet searched; next candidate to look for once WESAD is confirmed
  unavailable (done, above).
- **Circadian/light/actigraphy dataset** (handoff §18 P1 item 5) — not yet searched;
  only relevant if the circadian target and a light context channel stay in scope
  (Priority 0/`docs/TAXONOMY.md` keeps light as a context channel, not yet resolved
  whether the paper keeps a dedicated circadian target requiring dataset validation).

## What this unblocked

**Priority 2** (first real ablation result — "how much does synchronized IMU improve
PPG-derived heart-rate estimation under motion?") is complete, using PPG-DaLiA — real,
accessible, exactly fit for that question. Result: synchronized IMU reduced held-out
HR MAE by ≈23% (9.090 → 7.032 bpm), consistent across all 3 held-out test subjects and
all motion-severity quartiles (see `ml/README.md`). PulseDB and WESAD stay blocked
pending team action (an account holder downloading them) — not silently substituted
again the way Sleep-EDF/BIDMC/QDE substituted for WESAD earlier, per the handoff's
own caution against over-substituting away from the datasets a target actually needs.
