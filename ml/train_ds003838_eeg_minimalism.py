#!/usr/bin/env python
"""Real training run: ds003838 EEG channel-minimalism bounded diagnostic
(Stage 3B). Frozen protocol: results/ds003838_protocol_stage1b.json.

IMPORTANT SCOPE DISCLOSURE: this is NOT the full n=65 Stage-2/3 cohort
result. Downloading all 65 subjects' memory-task EEG (~96 GB total,
directly measured in Stage 1B) was not feasible within this session's
network throughput (~2.75 MB/s observed) and time budget. This script
operates on whichever real, actually-downloaded subject .set files exist
under --data-dir - a small, neutral-rule-selected subject subset (first N
eligible subject IDs in sorted order, per Section 15's explicit allowance
for a preregistered neutral subset when full download is impractical).
See docs/DS003838_STAGE3_BOUNDED_DIAGNOSTIC.md for the full disclosure.

Feature design (capacity-fair by construction, per the frozen protocol's
"channel-wise shared encoder + fixed-width aggregation"): each channel is
reduced to the SAME fixed 5-dim feature vector (mean abs amplitude, std,
and 3 FFT band powers: <8Hz, 8-13Hz, 13-30Hz), then mean-pooled ACROSS
channels to one 5-dim vector regardless of how many channels contributed.
A (4 channels) and B (all channels) therefore feed the identical-dimension
5-vector into the identical logistic-regression classifier - the ONLY
difference between A and B is which/how-many real channels contributed to
the pooled average, never raw parameter count.

C uses B's full channel set, but every channel EXCEPT the frozen sparse 4
has its trial-to-epoch correspondence deranged (permuted across trials,
within subject, A's own 4 channels stay real/aligned).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.datasets.ds003838_eeg import SPARSE_CHANNELS, load_subject_epochs  # noqa: E402

CONTROL_SHUFFLE_SEED_BASE = 200042


def channel_features(epoch_channel: np.ndarray, sfreq: float = 1000.0) -> np.ndarray:
    """5-dim fixed feature vector for one (n_samples,) real channel segment."""
    mean_abs = np.mean(np.abs(epoch_channel))
    std = np.std(epoch_channel)
    fft = np.abs(np.fft.rfft(epoch_channel))
    freqs = np.fft.rfftfreq(len(epoch_channel), d=1.0 / sfreq)
    low = fft[(freqs >= 0.5) & (freqs < 8)].mean() if np.any((freqs >= 0.5) & (freqs < 8)) else 0.0
    mid = fft[(freqs >= 8) & (freqs < 13)].mean() if np.any((freqs >= 8) & (freqs < 13)) else 0.0
    high = fft[(freqs >= 13) & (freqs < 30)].mean() if np.any((freqs >= 13) & (freqs < 30)) else 0.0
    return np.array([mean_abs, std, low, mid, high], dtype=np.float64)


def pooled_features(epochs: np.ndarray, channel_names: list[str], channel_subset: list[str] | None) -> np.ndarray:
    """(n_epochs, 5) - per-epoch mean-pooled fixed-width features over the
    given channel subset (or all channels if None)."""
    idx = range(len(channel_names)) if channel_subset is None else [channel_names.index(c) for c in channel_subset]
    n_epochs = epochs.shape[0]
    out = np.zeros((n_epochs, 5), dtype=np.float64)
    for e in range(n_epochs):
        feats = np.stack([channel_features(epochs[e, c, :]) for c in idx], axis=0)
        out[e] = feats.mean(axis=0)
    return out


def deranged_full_channel_epochs(epochs: np.ndarray, channel_names: list[str], sparse: list[str], seed: int) -> np.ndarray:
    """Copy of epochs where every channel EXCEPT `sparse` has its trial index
    permuted (a derangement, no fixed points), independently drawn but
    applied identically across those channels' trial axis (same donor
    trial per shuffled channel-set) - subject-seeded, label-independent."""
    n_epochs = epochs.shape[0]
    rng = np.random.default_rng(seed)
    deranged_idx = np.arange(n_epochs)
    for _ in range(1000):
        rng.shuffle(deranged_idx)
        if not np.any(deranged_idx == np.arange(n_epochs)):
            break
    out = epochs.copy()
    sparse_idx = {channel_names.index(c) for c in sparse}
    for c in range(epochs.shape[1]):
        if c in sparse_idx:
            continue  # A's channels stay real/aligned in C
        out[:, c, :] = epochs[deranged_idx, c, :]
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=str(REPO_ROOT.parent / "scratchpad_ds003838"))
    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    subject_dirs = sorted(data_dir.glob("sub-*_task-memory_eeg.set"))
    subject_ids = sorted({p.name.split("_")[0] for p in subject_dirs})
    print("Found real subject files for:", subject_ids)

    per_subject_data = {}
    channel_names_ref = None
    for sid in subject_ids:
        set_path = data_dir / f"{sid}_task-memory_eeg.set"
        events_path = data_dir / f"{sid}_task-memory_events.tsv"
        if not set_path.exists() or not events_path.exists():
            print(f"skipping {sid}: missing real file(s)")
            continue
        epochs, labels, channel_names = load_subject_epochs(set_path, events_path)
        if channel_names_ref is None:
            channel_names_ref = channel_names
        assert channel_names == channel_names_ref, f"{sid} montage differs from reference subject"
        for ch in SPARSE_CHANNELS:
            assert ch in channel_names, f"{sid} missing frozen sparse channel {ch}"
        per_subject_data[sid] = {"epochs": epochs, "labels": labels}
        print(f"{sid}: {epochs.shape[0]} real memory-condition epochs, labels {np.unique(labels, return_counts=True)}")

    eligible = sorted(per_subject_data.keys())
    if len(eligible) < 2:
        print("BLOCKED: fewer than 2 real subjects with complete files - cannot run subject-wise LOSO.")
        out = {"status": "DS003838_STAGE3_BOUNDED_DIAGNOSTIC_INSUFFICIENT_SUBJECTS", "n_subjects_available": len(eligible)}
        (REPO_ROOT / "results" / "ds003838_eeg_minimalism_stage3_bounded_diagnostic.json").write_text(json.dumps(out, indent=2))
        return

    results = {"A": {}, "B": {}, "C": {}}
    for sid in eligible:
        d = per_subject_data[sid]
        results["A"][sid] = pooled_features(d["epochs"], channel_names_ref, SPARSE_CHANNELS)
        results["B"][sid] = pooled_features(d["epochs"], channel_names_ref, None)
        subject_numeric_id = int(sid.split("-")[1])  # "sub-032" -> 32, stable across processes/machines (unlike hash())
        deranged = deranged_full_channel_epochs(d["epochs"], channel_names_ref, SPARSE_CHANNELS, CONTROL_SHUFFLE_SEED_BASE + subject_numeric_id)
        results["C"][sid] = pooled_features(deranged, channel_names_ref, None)

    def run_loso(key: str) -> dict:
        per_subject = {}
        for test_sid in eligible:
            train_sids = [s for s in eligible if s != test_sid]
            X_tr = np.concatenate([results[key][s] for s in train_sids], axis=0)
            y_tr = np.concatenate([per_subject_data[s]["labels"] for s in train_sids], axis=0)
            X_te = results[key][test_sid]
            y_te = per_subject_data[test_sid]["labels"]
            mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
            sd[sd == 0] = 1.0
            clf = LogisticRegression(max_iter=2000)
            clf.fit((X_tr - mu) / sd, y_tr)
            pred = clf.predict((X_te - mu) / sd)
            from sklearn.metrics import f1_score
            macro_f1 = float(f1_score(y_te, pred, average="macro"))
            per_subject[test_sid] = {"n_test_epochs": int(len(y_te)), "macro_f1": macro_f1}
        f1s = np.array([v["macro_f1"] for v in per_subject.values()])
        return {"per_subject": per_subject, "macro_f1_mean": float(f1s.mean()), "macro_f1_sd_ddof1": float(f1s.std(ddof=1)) if len(f1s) > 1 else None}

    out = {
        "status": "DS003838_STAGE3_BOUNDED_DIAGNOSTIC_COMPLETE",
        "scope_disclosure": "NOT the full n=65 Stage-2/3 cohort - bounded diagnostic on real, actually-downloaded subjects only, per docs/DS003838_STAGE3_BOUNDED_DIAGNOSTIC.md.",
        "n_subjects": len(eligible),
        "subject_ids": eligible,
        "frozen_sparse_channels": SPARSE_CHANNELS,
        "A_sparse4": run_loso("A"),
        "B_full_montage": run_loso("B"),
        "C_deranged_extra_channels": run_loso("C"),
    }
    (REPO_ROOT / "results" / "ds003838_eeg_minimalism_stage3_bounded_diagnostic.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k in ("A_sparse4", "B_full_montage", "C_deranged_extra_channels")}, indent=2))


if __name__ == "__main__":
    main()
