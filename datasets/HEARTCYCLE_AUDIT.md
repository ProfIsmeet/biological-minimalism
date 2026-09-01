# HeartCycle Dataset Audit (Priority 1 / Day 1 targeted research)

**Question this audit answers:** *Can HeartCycle support a scientifically valid,
synchronized, subject-wise sensor-ablation experiment (in the style of Priority 2)
that meaningfully advances Biological Minimalism?*

**Verdict: PARTIALLY suitable.** Real, verified access and real synchronized
multimodal data exist, but the data's actual shape (very short per-record
duration, only 4 of 17 subjects have PPG, and inconsistent per-record
ground-truth population — all found by direct inspection, not assumed) does
**not** support a Priority-2-style trained-model ablation with a strict
held-out subject split. It may support a smaller-scope, formula/signal-
processing validation study instead. See §8 for the full reasoning and the
recommended next step.

All findings below come from directly downloading and inspecting a real file
with `h5py`, not from the dataset's own description alone.

---

## 1. Source

Illueca Fernandez, E., Couceiro, R., Abtahi, F., Henriques, J., Paiva, R. P.,
Goncalves, L., Millet, J., Seoane, F., Muehlsteff, J., & Carvalho, P. (2025).
HeartCycle: A comprehensive dataset of synchronized impedance cardiography
and echocardiography for accurate hemodynamic predictions (version 1.0.0).
PhysioNet. https://physionet.org/content/heartcycle/1.0.0/

**License:** Open Data Commons Attribution License v1.0 (open access).
**Ethics approval:** University of Coimbra Hospital (CES-238).

---

## 2. Access (§9 gate 1)

**✅ Real, working, anonymous access — verified directly**, not assumed:

```bash
curl -s "https://physionet.org/files/heartcycle/1.0.0/59146237/measure/" # real directory listing, no login
curl -sS -o CH10_s0000001.h5 "https://physionet.org/files/heartcycle/1.0.0/59146237/measure/CH10_59146237_s0000001.h5"
# -> 14,217,606 bytes, a real, valid HDF5 file (opened successfully with h5py 3.16.0)
```

Total dataset: 2.3 GB uncompressed (per PhysioNet page), 208 records across
3 sub-experiments. Not downloaded in full for this audit — one representative
record per finding was downloaded and inspected instead
(`datasets/heartcycle-audit/raw/`, gitignored).

---

## 3. Subject structure (§10 gate 2/3)

| Experiment ID | Records | Subjects | Signals |
|---|---|---|---|
| `59146237` | 37 (directly counted, not the 32 the summary page states — real listing wins) | **4** (`CH07`, `CH08`, `CH09`, `CH10`) | ECG, ICG, PCG, ECHO, **+ PPG** |
| `59146238` | 84 | 10 (`CH01`–`CH06` confirmed present; remainder per PhysioNet page) | ECG, ICG, PCG, ECHO (no PPG) |
| `59146239` | 92 | 7 | ECG, ICG, PCG, ECHO (no PPG) |
| **Total** | 208 | **17** | — |

**Critical finding: only 4 of the 17 subjects have any PPG data at all.**
Any experiment involving PPG (e.g. a PPG+ECG timing/PAT ablation, the most
direct analog to Priority 2's PPG+IMU work) is limited to `CH07`–`CH10` —
4 subjects. A strict subject-wise train/val/test split (this project's hard
rule — §22 Rule 1) with only 4 subjects leaves at most 2 for training, which
is far thinner than Priority 2's 10/2/3 split and would produce a much
weaker generalization estimate, similar to (or worse than) the QDE
bio-impedance experiment's already-flagged small-N limitation.

Real filenames follow `[SubjectID]_[ExperimentID]_[RecordID].h5`, subject IDs
are unambiguous and directly usable for a subject-wise split.

---

## 4. Signals (§11) — verified by direct HDF5 inspection, not the ObjectMapping.csv alone

`ObjectMapping.csv` (downloaded, real) documents 127 signal/parameter IDs
across 5 devices (Niccomo `_000`–`_036`, Stethoscope `_060`–`_066`,
Echocardiogram `_090`–`_096`, PPG monitor `_120`–`_126`). **Directly opening a
real file found 150 keys present** (`_000`–`_149`) — 23 extra
(`_127`–`_149`) not documented in `ObjectMapping.csv`. Inspected all 23 in
the one file checked: each is a 2-element `[0, 0]` "matrix" — either unused
placeholder fields in this dataset release, or populated only in specific
records not checked here. Flagged as an open question, not resolved.

| Signal | Device | Documented rate | Measured rate (real file) |
|---|---|---|---|
| ECG + raw impedance | Niccomo | 200 Hz | **198.5 Hz** |
| Phonocardiography (heart sounds) | Stethoscope | 44,100 Hz | **43,760.9 Hz** |
| Echocardiography (3D: channel × time × distance/velocity) | Echo probe | 136 Hz | **136.0 Hz** (exact) |
| Plethysmography (PPG) | PPG monitor | 125 Hz | **123.9 Hz** |

**Impedance clarification (per §11's explicit instruction not to treat all
"impedance" as equivalent):** `_031`/`IMP` is the **raw thoracic impedance
cardiography (ICG) signal** from the Niccomo bioimpedance monitor — this
measures beat-to-beat thoracic impedance change, used (via its time
derivative dZ/dt, per the dataset's own README) to derive cardiac timing
events (AVO/AVC/PEP/LVET). This is **not** the same measurement as this
project's peripheral/segmental bio-impedance sensor concept (fluid-shift-
oriented, PDD Section 8) or the QDE dataset's limb-segment impedance — ICG is
specifically a **thoracic, cardiac-timing-oriented** impedance measurement.
This distinction is added to `docs/TAXONOMY.md`'s scope (see §9 below).

---

## 5. Synchronization (§12) — the most important, and most concerning, finding

Directly inspected one file (`CH10_59146237_s0000001.h5`) and found that
**signals from different devices within the same file/session do not cover
the same time span**:

| Device | Signal duration in this file |
|---|---|
| Niccomo (ECG, ICG) | **5.62 s** |
| Stethoscope (PCG) | 8.06 s |
| Echocardiogram | 8.06 s |
| PPG monitor | 8.06 s |

All four devices start recording as part of the "same session" (same
filename, same nominal recording event), but Niccomo's channel is 2.44
seconds shorter than the other three. This means "recorded during the same
session" does **not** automatically mean "covers the exact same time window"
— exactly the distinction §12 of the handoff warns about. Any experiment
using Niccomo (ECG/ICG) alongside another device must explicitly handle this
partial-overlap, not assume full alignment.

The dataset's own documentation mentions a "synchronization percentage"
data-quality metric between signal pairs; this audit did not locate where
that metric is actually stored in the HDF5 structure (the 23 undocumented
`_127`–`_149` fields were all empty in the one file checked) — **unresolved,
flagged for follow-up if this dataset is pursued further**, not assumed to
exist and not assumed to be favorable.

---

## 6. Sampling / timing (§13)

- Record duration is short: the file inspected covers ~5.6–8.1 s per signal
  (a handful of heartbeats), not a continuous multi-minute recording.
- File sizes are consistent within a subject's Niccomo-covered set (e.g. all
  8 of `CH10`'s files in `59146237` are within 14.2–14.4 MB of each other)
  but vary substantially across subjects/experiments (e.g. `CH01`'s files in
  `59146238` range 2.1–7.9 MB) — indicating **variable record duration
  across the dataset**, most likely corresponding to different protocol
  phases (e.g. rest vs. stress-test stages) rather than a uniform window
  length. This was not exhaustively characterized for all 208 records within
  this audit's time budget.
- No missing-sample/dropout behavior was characterized beyond the duration
  mismatch in §5.

---

## 7. Ground truth (§14) — real, but inconsistently populated per-record

Each of the 4 devices independently computes its own AVO (aortic valve
opening), AVC (closing), PEP (pre-ejection period), and LVET (left
ventricular ejection time) — **Echocardiography is the physiological
reference standard** (this is the dataset's own stated purpose: quantifying
ICG's timing bias against real ultrasound-derived valve events).

**Directly inspected PEP/LVET values in one file, per device:**

| Device | PEP (ms) | LVET (ms) | Assessment |
|---|---|---|---|
| Niccomo | `[110, 110]` | `[275, 275]` | Suspicious — identical repeated pair, looks like a static/placeholder value, not a real per-beat measurement |
| Stethoscope | `[46.5, 41.3]` | *(index pair, not ms values)* | PEP values look physiologically plausible; LVET field did not contain ms values in this record |
| **Echo (reference)** | `[47.9, 904.3]` | *(index pair)* | First value plausible; second value (904 ms) is **not** a physiologically plausible PEP — likely bad data or a units/field mixup in this specific record |
| PPG | `[0, 0]` | `[0, 0]` | Empty — not populated in this record |
| Niccomo BP fields (`_012` DBP, `_013` PAM, `_014` SBP) | — | — | All `-1` — a clear missing-value sentinel, not real blood pressure |
| Niccomo SpO2 (`_020`) | `97` | — | Real, plausible value |

**Honest conclusion:** ground truth is real where populated, but **not
uniformly populated across records** — the one file checked has several key
fields as placeholders or clearly-invalid values. A real experiment would
need a systematic per-record data-quality pass (checking for `-1` sentinels,
repeated-static pairs, and implausible ranges) across some or all of the 208
records before selecting a usable subset — this was not done for all records
within this audit's time budget; it is the concrete next step if this
dataset is pursued.

---

## 8. Suitability decision (§15)

### A. Is HeartCycle suitable?
**PARTIALLY.**

### B. What Biological Minimalism decision could it answer, if pursued?

Not the Priority-2-style trained ablation this audit was checking for
(insufficient N and per-subject data volume — see below). What it *could*
support, if a team member pursues it further: a **small-N, per-cycle
signal-processing validation** — e.g. "does a PAT/PEP-style timing feature
computed from real synchronized ECG+PPG (the 4 `CH07`–`CH10` subjects)
correlate with the real echocardiography-derived PEP reference?" This is a
correlation/formula-validation study (closer to classical signal-processing
validation than to a trained deep-learning ablation), and is only proposed
here as a possibility — not started, per §18's stop-point instruction.

### C. Can a clean ablation (Model A minimal input, Model B + one modality, same subjects/split/target/preprocessing) be constructed?

**No, not at Priority-2's rigor level.** Two hard blockers, both directly
verified:
1. Only 4 subjects have PPG at all — a subject-wise train/val/test split
   this thin would produce a much weaker, less trustworthy generalization
   estimate than Priority 2's 10/2/3 split.
2. Records are short (~5–8 s) and per-record ground truth is inconsistently
   populated (§7) — the effective usable data volume per subject is far
   below what PPG-DaLiA provided (8+ minutes/subject, thousands of windows).

### D. Feasibility within the remaining sprint

Not estimated in detail, because the suitability gates above already fail
for the originally-implied ablation use case. If the smaller-scope
correlation study from §8.B were pursued instead: loader/preprocessing
effort would be **higher** than Priority 2's (HDF5 nested-group parsing,
per-record data-quality filtering, and reconciling the Niccomo/other-device
duration mismatch), while the deliverable (a correlation coefficient on 4
subjects) is scientifically thinner than Priority 2's held-out MAE result.

---

## 9. Taxonomy note (feeds back into `docs/TAXONOMY.md`)

This audit surfaced a real distinction worth freezing alongside the existing
taxonomy: **"bio-impedance" is not one measurement.** HeartCycle's Niccomo
ICG is thoracic, cardiac-timing-oriented; this project's own bio-impedance
sensor concept (PDD Section 8) and the QDE dataset's segmental limb
impedance are fluid-status-oriented. Both are legitimately "bio-impedance"
in a loose sense, but they measure different physiological phenomena via
different electrode placements and are not interchangeable evidence for one
another. Not yet added as a formal taxonomy edit — flagged here for the next
`docs/TAXONOMY.md` revision.

---

## 10. Recommendation

**HeartCycle = PARTIAL.** Do not use it today for a Priority-2-style
ablation. Two options going forward, neither started today:

1. **Backup direction (recommended over immediately re-scoping HeartCycle):**
   a focused replacement search for a dataset with (a) real synchronized
   ECG+PPG, (b) a defensible cardiovascular ground truth, (c) enough
   subjects (≥10, matching Priority 2's scale) for a real subject-wise
   split, and (d) longer per-subject recordings than HeartCycle's ~5–8 s
   snippets. `PulseDB` (already flagged as access-blocked in
   `datasets/DATASET_MATRIX.md`) would satisfy (a)–(c) if access is ever
   obtained — worth re-flagging to the team rather than searching for a new
   candidate from scratch.
2. **If HeartCycle is deliberately chosen anyway:** scope it explicitly as
   the smaller correlation/validation study in §8.B, on the 4-subject PPG
   subset, with the per-record data-quality pass from §7 done first — a
   different kind of deliverable than Priority 2's ablation MAE, and should
   be presented as such (not inflated to sound like the same kind of
   result).

No training was started against HeartCycle today, per the audit-first stop
point.
