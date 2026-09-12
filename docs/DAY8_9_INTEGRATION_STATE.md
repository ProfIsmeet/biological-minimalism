# Day 8/9 Integration State — What Is Frozen, What Is Pending

**Branch:** `day8-9-systems-readiness` (cut from `day7-accelerated-integration` @ `230bd65`)
**Author role:** integration / systems / paper-support / jury-readiness lead
**Scientific continuation owner:** Ismet (do not merge his active ML branches in this sprint)

This document is the single honest source of truth for **which scientific evidence is
integrated into this branch** versus **which evidence exists on Ismet's ML branches and is
still pending integration**. It exists so that no downstream surface (dashboard, paper, jury
answer) silently presents un-integrated or future evidence as if it were frozen here.

---

## 1. Frozen and integrated on THIS branch (`230bd65`)

| Target / dataset | Candidate | Result on this branch | Key limitation |
|---|---|---|---|
| HR / PPG-DaLiA | synchronized wrist IMU | Positive; A→B ~20.6% raw, but capacity-matched A_cap→B ~0.605 bpm and C→B ~0.776 bpm (5/5 seeds) | effect much smaller after capacity control; 3 held-out subjects |
| HR / PTT-PPG | second physical PPG site | Aggregate negative, heterogeneous (2/4 subjects better), s2-dominated, 5/5 optimization seeds | n=4 held-out subjects; s2-sensitive |
| Sleep stage / Sleep-EDF | horizontal EOG added to EEG | Positive, modest: macro-F1 0.7473→0.7693 (Δ≈0.022), **candidate better in 4/5 training seeds** | **3 held-out subjects; NO shuffled-EOG control on this branch; NO per-subject breakdown on this branch** |

Twin: `ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED`. Pareto: `NOT_READY`.

---

## 2. PENDING scientific integration (exists on Ismet's branches — NOT here)

> These are **real committed artifacts on Ismet's ML branches**, but they are **not merged into
> this integration base**. Until Ismet's branch is integrated and re-verified, every surface must
> show these as `PENDING_SCIENTIFIC_INTEGRATION` and must NOT display their numbers as frozen.

| Pending item | Where it currently lives | Status marker to use |
|---|---|---|
| Sleep-EDF **shuffled-EOG negative control** (Model C) and **B>C** replication | `origin/day8-sleep-strengthening-ml` (`docs/SLEEP_EDF_SHUFFLED_EOG_RESULTS.md`, `results/sleep_edf_eeg_eog_control_analysis.json`) | `PENDING_SCIENTIFIC_INTEGRATION` |
| Sleep-EDF **per-subject decomposition** (SC4011 dominance) | `origin/day8-sleep-strengthening-ml` (`results/sleep_edf_per_subject_analysis.json`) | `PENDING_SCIENTIFIC_INTEGRATION` |
| Sleep-EDF **prospective secondary holdout** | `origin/day9-sleep-secondary-holdout-ml` (in progress) | `PENDING_EXTERNAL_SCIENTIFIC_INTEGRATION` |
| Durable **external checkpoint archival** | tag `day8-checkpoint-archive-v1`, Ismet's archival work | `archival: pending external evidence` |

**Why this matters (finding #1):** the Day-8/9 sprint brief describes the shuffled-EOG control
and SC4011 dominance as already-canonical. On this branch they are not. The safe, prohibition-
compliant behavior is to treat them as pending (same bucket as the secondary holdout), build the
schema/UI to receive them cleanly, and never fabricate or hardcode their values here.

---

## 3. Integration-compatibility checklist for when Ismet's branch lands

When `day8-sleep-strengthening-ml` (and later `day9-sleep-secondary-holdout-ml`) are integrated:

1. Replace the Day-7 `results/sleep_edf_eeg_eog_ablation.json` seed/subject fields only from the
   verified merged artifact.
2. Update `backend/app/research/catalog.py::adapt_sleep_edf_ablation` — it currently
   **hard-asserts `better == 4`** and lists limitations "No shuffled-EOG / negative-control
   experiment was run" and "No per-subject decomposition computed yet." Both must be revised to
   the merged reality (expected B>C 5/5, per-subject present).
3. Re-run `PYTHONPATH=backend python ml/build_target_evidence_matrix.py` so the matrix's Sleep
   entry reflects the shuffled control and per-subject heterogeneity.
4. Flip `results/sleep_secondary_holdout_pending.json` fields from `pending` to the verified
   outcome (support / weaken / contradict) and per-subject secondary results.
5. Re-run the consistency checker (`python ml/check_claim_consistency.py`) and the backend suite.
6. Re-check the provenance SHA chain (regenerating the contract/operational catalog cascades a
   decision-inputs SHA break — regenerate the join too).

Nothing in this sprint changes the frozen ML numbers; it only prepares the receiving surfaces.
