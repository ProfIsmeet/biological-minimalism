# Cardiovascular Dataset Decision — Day 2 (2026-09-01)

**Search question:** Find the strongest currently accessible dataset that
provides subject-identifiable, synchronized ECG + PPG and an independent
cardiovascular ground truth suitable for subject-wise held-out sensor-
ablation research within the remaining sprint days.

**Shortlist (3 candidates):** HeartCycle (Day 1, re-summarized here for the
comparison table), PulseDB (re-checked today — access status changed), and a
new candidate found today, PhysioNet's **Pulse Transit Time PPG Dataset**.

---

## 1. PulseDB — re-check result: access status CORRECTED from Day 1

Day 1 concluded PulseDB was blocked based on `curl -I` (HEAD) requests
returning 404 on the Box share link. **That conclusion was a methodological
error, corrected today:** Box's servers reject `HEAD` requests but serve
real data on `GET` with a redirect chain. Verified directly:

```bash
curl -s -L -r 0-0 "https://rutgers.box.com/shared/static/7l8n3tn9tr0602tdss1x7e3uliahlibp.001" -D -
# -> 301 -> 301 -> 302 -> 206 Partial Content
# content-range: bytes 0-0/15728640000   (a REAL, ~15.7 GB file part)
```

**Corrected status: technically ACCESSIBLE, but impractical within the
sprint.** `PulseDB_MIMIC.zip` alone is split into at least 12 parts of
~15.7 GB each (~188 GB+ for one of the two source datasets; VitalDB's part
not fully enumerated). The much smaller, ready-to-use **Kaggle
"Supplementary Subset"** (VitalDB-derived) remains blocked — its DOI
(`doi.org/10.34740/KAGGLE/DS/2447469`) resolves to a 404, and Kaggle
datasets generally require an account/API token for programmatic download
regardless. **Not pursued further** — correct per instructions ("do NOT
attempt bypasses... if access remains blocked after the timebox, move to
targeted replacement research"); the *practical* blocker here is data
volume/credentials, not raw reachability, but the effect is the same.

---

## 2. HeartCycle — frozen from Day 1 (see `datasets/HEARTCYCLE_AUDIT.md`)

PARTIAL. Not re-audited today per instructions ("HeartCycle decision is now
frozen"). Included in the comparison table below for completeness only.

---

## 3. Pulse Transit Time PPG Dataset — NEW candidate, found and verified today

Kirk, J. T. (2022). Pulse Transit Time PPG Dataset (version 1.1.0).
PhysioNet. https://doi.org/10.13026/jpan-6n92

**Access:** ✅ Real, open (Open Data Commons Open Database License v1.0),
verified directly — real file listing, real `.hea`/`.csv` files downloaded
and inspected (not assumed from the description page).

```bash
curl -s "https://physionet.org/files/pulse-transit-time-ppg/1.1.0/s10_sit.hea"
curl -s "https://physionet.org/files/pulse-transit-time-ppg/1.1.0/csv/s10_sit.csv"
```

**Subjects:** 22 healthy subjects (real filenames `s1`..`s22` confirmed in
the real `RECORDS` listing), 6 female / 16 male, age 20–53. 66 total records
(22 subjects × 3 activities: sit / stationary walk / run). Substantially
more subjects than HeartCycle's 4-PPG-subject limit, comparable in scale to
Priority 2's PPG-DaLiA (15 subjects).

**Signals (verified directly from a real `.hea` file, 18 channels + `peaks`
annotation):** 1 ECG (500 Hz), 6 PPG channels — 2 sites (distal + proximal
phalanx of the left index finger) × 3 wavelengths each (red/infrared/green),
2 attachment-pressure load cells, 3 temperature sensors, 3-axis
accelerometer + 3-axis gyroscope (i.e. a real IMU). All read from one
microcontroller within a 2ms window — genuinely hardware-synchronized, not
just "same session."

**Ground truth — the important nuance:** blood pressure (OMRON HEM-7322,
cuff-based), HR (OMRON + iHealth pulse oximeter), and SpO₂ (iHealth) are
**only measured at the start and end of each activity** — confirmed directly
in a real header's embedded metadata: `bp_sys_start: 106, bp_sys_end: 98,
bp_dia_start: 69, bp_dia_end: 65, hr_1_start: 73, ..., spo2_start: 95,
spo2_end: 98`. This means BP/SpO2 give only **2 labeled points per
66-record dataset per subject-activity**, not a continuous per-window
label — **not enough for a Priority-2-style windowed regression ablation on
BP itself** without a very different (correlation-style, small-N) framing.

**What IS continuous and independent, however:** the dataset ships real,
separately-annotated **ECG R-peaks** (`.atr` files / `peaks` CSV column) —
usable to derive a continuous, independent heart-rate ground truth
throughout each full recording, exactly analogous to how PPG-DaLiA's chest
ECG produced Priority 2's HR label, but from an entirely different
population and — critically — including a real **running** activity (more
extreme motion than any PPG-DaLiA activity) and **two distinct PPG sensor
sites**, neither of which Priority 2 could test.

**Subject-wise split:** yes, real subject IDs, straightforward.

**License:** ODbL v1.0, open.

**Feasibility:** Similar effort to Priority 2 (WFDB/CSV parsing instead of
pickle, otherwise the same shape of problem); 2.9 GB total, fully downloadable
within the sprint.

---

## 4. Comparison table

| Dataset | Usable subjects (for the relevant question) | Signals | Ground truth | Synchronization | Access | License | Feasibility | Decision |
|---|---|---|---|---|---|---|---|---|
| HeartCycle | 4 (PPG) / 17 (no PPG) | ECG, ICG, PCG, ECHO, PPG (4 subj.) | Real but inconsistently populated per-record; short (~5-8s) records | Verified partial-duration mismatch across devices in one file | ✅ open | ODC-BY | Poor (thin data per subject) | **REJECTED** (frozen Day 1) |
| PulseDB | 5,361 (in principle) | ECG, PPG, ABP | Real, continuous, independent (arterial line) | Real (per source datasets) | ⚠️ technically reachable, ~100GB+ practical volume; curated subset blocked (Kaggle) | ODC-BY (Frontiers paper) | Poor within sprint (volume/credentials) | **BACKUP** (re-flag to team for credentialed/targeted partial access) |
| **Pulse Transit Time PPG Dataset** | **22** | ECG, 6-channel multi-site PPG, IMU (accel+gyro), pressure, temp | BP/SpO2 real but sparse (2 pts/activity); **ECG R-peaks real and continuous** | ✅ hardware-synchronized (2ms window, verified) | ✅ open, verified directly | ODbL | Good — similar scope to Priority 2 | **PRIMARY** (reframed target — see §5) |

---

## 5. Decision and reframed Day 3 research question

**PRIMARY: Pulse Transit Time PPG Dataset — with the target honestly
reframed to fit what the data actually supports**, per this project's own
rule against inflating a sparse label into a continuous one it isn't.

Rather than force a windowed BP regression onto 2-points-per-activity labels
(scientifically weak — same trap this project avoided with HeartCycle), the
recommended Day 3 experiment reuses this dataset's genuine strength — dense,
truly synchronized, multi-site PPG + real continuous ECG-derived HR ground
truth, across sit/walk/**run** — to ask a question Priority 2 could not:

> **Does a second PPG sensor site add measurable value for heart-rate
> estimation over a single PPG site, particularly during running (the most
> extreme motion condition available)?**

- Model A: single-site PPG only (`pleth_1/2/3` — distal phalanx, 3 wavelengths)
- Model B: two-site PPG (`pleth_1..6` — distal + proximal phalanx)
- Ground truth: real ECG R-peak-derived HR (continuous, independent — ECG is
  never a model input, avoiding the exact circularity this project's own
  rules warn against)
- Subject-wise split, same rigor as Priority 2 (train/val/held-out test,
  seeded, no window leakage)
- Stratified by activity (sit/walk/run) — a real, clean motion-severity
  axis, cleaner than Priority 2's derived motion-energy quartiles

The sparse BP/SpO2 labels remain available as a **secondary, small-N,
honestly-scoped correlation check** (not the primary ablation metric) if
time permits later — e.g. does a PAT-style feature computed from ECG-to-PPG
timing correlate with the real (if sparse) BP change from sit to run.

**BACKUP:** PulseDB, contingent on a team member obtaining real credentialed
access (Kaggle account) to its much smaller curated subset — re-flagged to
the team, not pursued further today per the access/volume finding above.

**REJECTED:** HeartCycle (frozen Day 1 decision, unchanged).

No download, loader, or training for the Pulse Transit Time PPG Dataset was
started today — this document is the frozen decision; data preparation is
scoped as Day 3's first task, per today's "decide, don't rush into training"
instruction.
