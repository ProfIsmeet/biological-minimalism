# Claude → Ismet: Stage 2–4 Science Transfer Handoff

**Verdict:** `CLAUDE_SCIENCE_WORK_PRESERVED_WITH_LIMITATIONS_READY_FOR_ISMET_VERIFICATION`

This document is self-contained. It lets Ismet (and Ismet's AI) understand and
reuse Claude's accidental Stage-2 science sprint **without access to the chat
session**. Machine-readable companion: `results/claude_to_ismet_science_transfer_manifest.json`.

---

## 1. Why this transfer exists

Claude was briefly run on a Stage 2→4 ML-science sprint (corrected Sleep V2
closure + HMC external replication). Emir stopped it at a stage boundary and
issued a coordination correction: **the ML-science line belongs to Ismet /
Ismet's AI** (dataset audits, loaders, preprocessing, splits, training,
evaluation, controls, statistics, checkpoints, reproducibility, scientific
interpretation). **Claude owns the implementation/integration line** (backend,
frontend/Research Mode, claim migration, traceability, paper/jury integration,
cross-layer consistency, software hostile review).

Nothing Claude produced is thrown away. This handoff preserves it so Ismet can
**verify-and-adopt / reproduce-eval-only / rerun-selected / rerun-all / reject**
each item on its own merits — ownership alone neither validates nor invalidates
a computation.

**No new training was run to produce this handoff.**

---

## 2. Repository state at handoff

- Repo: `/Users/emirharunsunbul/Documents/ChatGPT/IAC`
- Remote: `https://github.com/ProfIsmeet/biological-minimalism.git`
- Claude branch: `stage2-4-sleep-canonical`
- Base: `52bd2eca1ef89b0460a4a3dd3648118176ad6610` (== `origin/day12-post-remediation-integration`, verified exactly)
- Commits made during the science sprint: **NONE** (branch sat at base; all work was uncommitted working-tree state until the preservation/handoff commit that adds only this doc + the manifest + the Claude science files).
- `main` = `d257f19…`, `origin/main` = `b02c6db…` (untouched).

---

## 3. What "Stage 1" (the stopped stage) actually was

Emir asked Claude to split the sprint into ~2–3h stages and report after each.
**Stage 1 = corrected V2 A/B reproduction.** It completed. Claude had just
launched **Stage 2 = corrected shuffled-EOG control (C)** when Emir stopped it;
C was killed at the first seed's training start.

---

## 4. Active processes

**NONE.** All training and download processes are stopped. No servers running.

---

## 5. Datasets (both real, byte-verified, gitignored, reusable)

### Sleep-EDF (sleep-cassette), PhysioNet 1.0.0
- `datasets/sleep-edfx/raw/` — 856 MB, 36 files, 18 subjects.
- Frozen primary split `ml/experiments/sleep_edf_eeg_eog_ablation/subject_split.json`
  (train 12 / val 3 / test 3). Test subjects: SC4011, SC4081, SC4131.
- **All 36 files SHA256-verified against PhysioNet `SHA256SUMS.txt` (byte-exact).**
- Same lineage as existing corrected A/B. **Ismet can reuse this copy directly.**

### HMC Sleep Staging, PhysioNet 1.1
- `datasets/hmc-sleep-staging/raw/` — 1.3 GB, 36 files, **12 recordings (SN001–SN012)**.
- This is a **reduced 12-of-151 bandwidth-limited pilot** (see §9). Split
  `results/hmc_split_stage2.json` (train SN001–008 / val SN009–010 / test SN011–012).
- **All 36 pilot files SHA256-verified against PhysioNet `SHA256SUMS.txt`.**
- Channel labels confirmed from a real EDF header: `EEG C4-M1`, `EEG F4-M1`,
  `EEG O2-M1`, `EEG C3-M2`, `EMG chin`, `EOG E1-M2`, `EOG E2-M2`, `ECG` — all
  native 256 Hz. Annotation format `SNxxx_sleepscoring.txt` confirmed
  (`Date, Time, Recording onset, Duration, Annotation, Linked channel`).
- **NO HMC TRAINING WAS RUN.**

No preprocessing cache was written for either dataset (loaders parse EDF on the fly).

---

## 6. Corrected A/B reproduction (Stage 1 — the one completed result)

Claude re-ran the **existing** `ml/train_sleep_edf_primary_seedfix_v2.py`
(unmodified) against the freshly downloaded raw data, producing 10 fresh
checkpoints and a fresh result. This was a **reproduction**, not a protocol change.

| | Canonical (Ismet, committed) | Claude fresh reproduction | 
|---|---|---|
| baseline (EEG) mean | 0.73649 | 0.73391 |
| candidate (EEG+EOG) mean | 0.76469 | 0.76453 |
| B−A mean | +0.02820 | +0.03062 |
| favorable seeds | 4/5 | 4/5 |

Per-seed max abs diff ≈ 0.0084 macro-F1. **Direction and favorable-count
preserved; not bit-exact** (cross-platform: Windows/Ismet → Mac/Claude torch
2.14.0). This is expected floating-point/platform drift, not a protocol
divergence.

**Preservation action taken:** Claude's reproduction accidentally overwrote the
committed `results/sleep_edf_primary_seedfix_v2.json` during the run. This has
been **reverted**: the canonical committed file is restored (verified clean vs
HEAD), and the reproduction is preserved separately at
`results/claude_noncanonical_sleep_edf_primary_seedfix_v2_reproduction.json`.
**Canonical Ismet provenance is NOT regressed.**

The 10 reproduction checkpoints (gitignored) with full SHA256 are in the
manifest. They are `NONCANONICAL_PENDING_ISMET_VERIFICATION`.

---

## 7. Corrected C (shuffled-EOG control) — IMPLEMENTED, NOT COMPLETED

- Script: `ml/train_sleep_edf_shuffled_eog_control_seedfix_v2.py` (new, complete).
- Ran once: loaded data (train 32656 / val 7989 / test 8412 epochs), verified
  capacity match (**Model C 8309 params == Model B 8309**), reached seed-42
  training start, then **killed by Emir. No checkpoint, no result JSON written.**
- Control design (per the frozen predeclaration
  `docs/SLEEP_EDF_SHUFFLED_EOG_PREDECLARATION.md`): EOG permuted **within-subject,
  within-partition**; labels untouched; EEG untouched; deterministic; driven by
  an **isolated `control_shuffle_seed` (run_seed + 200000)** — an improvement
  over the V1 control which reused the bare run seed.
- Status: `PARTIAL_INCOMPLETE`. Ismet must run it (or its own equivalent) to get C / B−C.

---

## 8. Corrected interaction (M_B, M_AB) — IMPLEMENTED, NEVER RUN

- Script: `ml/train_sleep_edf_interaction_resp_seedfix_v2.py` (new, complete, never executed).
- Frozen formula (unchanged from Day 10): `interaction = M_AB − M_A − M_B + M0`.
- **M0/M_A equivalence decision (Claude's assertion, `UNRESOLVED` pending Ismet):**
  reuse corrected V2 A/B as M0/M_A because architecture, frozen split, and
  hyperparameters (epochs 20, batch 64, lr 1e-3, embed 32, AdamW, class-weighted
  CE) are identical; only the H1 seeding order ever differed, and V2 already fixes
  it. Ismet must independently accept or reject this equivalence before trusting
  any V2 interaction number.
- Resp rate provenance carried correctly: **native 1 Hz, 100 Hz common/model grid
  (FFT upsample)** — do not let this regress to "native 100 Hz".
- Status: `PARTIAL_INCOMPLETE`. Corrected V2 interaction is **NOT_VALIDLY_COMPUTABLE** yet.

---

## 9. HMC pipeline — CODE + DATA ONLY, NO TRAINING

- New loader `ml/datasets/hmc_sleep.py`; new trainer `ml/train_hmc_sleep_a_b_c.py`;
  frozen split `results/hmc_split_stage2.json`; deviation doc
  `docs/HMC_STAGE2_BANDWIDTH_REDUCED_COHORT_DEVIATION.md`.
- Implements Ismet's own Stage-1B frozen protocol `results/hmc_protocol_stage1b.json`
  (C4-M1 EEG; E1-M2 minus E2-M2 EOG; W/N1/N2/N3/REM; recording==subject).
- **Outcome-inspection boundary:** every scientific choice (channels, stage
  mapping, split, reduced-cohort selection by sequential RECORDS order) was frozen
  **before any HMC file was opened and before any performance was viewed.** No
  channel/hyperparameter/exclusion decision was outcome-informed — because **no
  HMC result exists.** No post-hoc contamination possible.
- Status: `HMC_TRAINING_NOT_STARTED` / `PARTIAL_INCOMPLETE`.

---

## 10. Overlap vs Ismet `stage2-4-expansion-science` (verified `0f1ba3be…`, read-only)

Ismet's completed expansion sprint did **QDE V2** (real n=10), **ds003838**
(n=3 bounded diagnostic), **GalaxyPPG**/**LBNP** (both data-access blocked), plus
all Stage-1B protocols and Stage-4 integration docs. Ismet's branch has **no**
corrected Sleep V2 C, **no** M_B/M_AB, **no** HMC loader/trainer.

| Workstream | Ismet state | Claude work | Useful transfer? |
|---|---|---|---|
| Corrected Sleep C | not done | script + capacity-verified partial run | **Yes — code reusable** |
| Corrected interaction M_B/M_AB | not done | script (never run) | **Yes — code reusable** |
| HMC loader/trainer | not done | loader + trainer + 12-rec pilot data | **Yes — code + data reusable** |
| A/B reproduction | canonical exists | fresh cross-platform reproduction | Optional confirmation |
| QDE V2 / ds003838 / GalaxyPPG / LBNP | Ismet-owned | none | No overlap |

**Potentially avoidable duplicate compute for Ismet:** re-downloading Sleep-EDF
(856 MB) and the 12-recording HMC pilot (1.3 GB) — both are present and
byte-verified locally.

---

## 11. Reuse classification (summary; full detail in manifest)

- `READY_FOR_ISMET_VERIFICATION`: `results/hmc_split_stage2.json`, both verified raw datasets.
- `NONCANONICAL_RESULT_PENDING_ISMET_REVIEW`: A/B reproduction JSON + 10 checkpoints.
- `POTENTIALLY_REUSABLE_IMPLEMENTATION`: C trainer, interaction trainer, HMC loader, HMC trainer, deviation doc.
- `PARTIAL_INCOMPLETE`: C run, interaction run, HMC run.
- `DO_NOT_REUSE_WITHOUT_CORRECTION`: none identified.
- `CLAUDE_INTEGRATION_ONLY`: (future) backend/frontend/paper/jury integration of accepted numbers.

---

## 12. Suggested Ismet verification order (recommendation only — do not assume Claude will run it)

1. Confirm canonical `results/sleep_edf_primary_seedfix_v2.json` is unchanged vs your provenance (it was restored).
2. Optionally fixed-checkpoint-eval or ignore the 10 A/B reproduction checkpoints.
3. Review + adopt/rewrite `ml/datasets/hmc_sleep.py` and add recording-disjoint-fold + channel/stage-mapping tests.
4. Review the C trainer's control design and the interaction trainer's M0/M_A equivalence claim; run under your ownership if accepted.
5. Decide full-151 HMC cohort run vs reduced pilot.
6. Only then does Claude integrate **accepted** numbers into backend/frontend/paper/jury.

---

## 13. Known concerns / limitations

- M0/M_A equivalence is asserted, not independently verified.
- C control is implemented but produced no results to inspect.
- HMC pilot is 12/151 with no training; not a full replication.
- Trainers re-parse EDF each run (no shared cache) — efficiency, not correctness.
- No new tests were written for the Claude Stage-2 code; Ismet must add them.

**No Claude-generated training result was promoted into any canonical surface
(sensor-value contract, preferred Sleep V2, Research Mode headline, paper, jury,
architecture, Pareto). Stage-1A canonical science is preserved unchanged.**
