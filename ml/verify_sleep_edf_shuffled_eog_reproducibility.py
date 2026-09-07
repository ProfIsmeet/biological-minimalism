#!/usr/bin/env python
"""Reproducibility check for the 5 shuffled-EOG control checkpoints:
reload each from disk and confirm it reproduces its stored held-out
macro-F1 on the SAME shuffled test data (regenerated deterministically
from the same seed, per the frozen shuffle policy)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.ml._torch_bootstrap import ensure_torch_dll_path  # noqa: E402

ensure_torch_dll_path()

import torch  # noqa: E402

torch.set_num_threads(4)

from ml.datasets.sleep_edf import shuffle_eog_within_subject  # noqa: E402
from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier, evaluate_full  # noqa: E402
from ml.train_sleep_edf_shuffled_eog_control import load_partition

TOLERANCE = 1e-6


def main() -> None:
    control = json.loads((REPO_ROOT / "results" / "sleep_edf_eeg_eog_control_analysis.json").read_text())
    split = control["frozen_protocol"]["subject_split"]

    test_x, test_y, test_subj = load_partition(split["test"])

    all_ok = True
    report = []
    for entry in control["checkpoint_manifest"]:
        seed = entry["seed"]
        shuffled_test_x = shuffle_eog_within_subject(test_x, test_subj, eog_channel_index=1, seed=seed)

        model = SleepStageClassifier(in_channels=2)
        model.load_state_dict(torch.load(REPO_ROOT / entry["path"], map_location="cpu"))
        model.eval()

        reproduced = evaluate_full(model, shuffled_test_x, test_y)
        stored = control["runs"][f"seed{seed}"]
        f1_diff = abs(reproduced["macro_f1"] - stored["macro_f1"])
        ok = f1_diff < TOLERANCE
        all_ok = all_ok and ok
        report.append({"run_id": entry["run_id"], "ok": ok, "f1_diff": f1_diff})
        print(f"{entry['run_id']}: {'OK' if ok else 'MISMATCH'} (dF1={f1_diff:.2e})")

    out_path = REPO_ROOT / "results" / "sleep_edf_shuffled_eog_control_reproducibility.json"
    out_path.write_text(json.dumps({"tolerance": TOLERANCE, "all_ok": all_ok, "runs": report}, indent=2))
    print(f"\n{'ALL OK' if all_ok else 'MISMATCH FOUND'}")
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
