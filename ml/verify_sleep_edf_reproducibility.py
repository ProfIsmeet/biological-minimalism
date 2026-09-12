#!/usr/bin/env python
"""Reproducibility check for the 10 Sleep-EDF EEG/EEG+EOG checkpoints:
independently reload each from disk and confirm it reproduces its stored
held-out macro-F1/accuracy."""

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

from ml.datasets.sleep_edf import EEG_CHANNEL, EOG_CHANNEL  # noqa: E402
from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier, evaluate_full, load_split_data  # noqa: E402

TOLERANCE = 1e-6


def main() -> None:
    results_path = REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation.json"
    results = json.loads(results_path.read_text())
    split = results["frozen_protocol"]["subject_split"]

    configs = {"baseline_eeg_only": (EEG_CHANNEL,), "candidate_eeg_plus_eog": (EEG_CHANNEL, EOG_CHANNEL)}
    test_data = {name: load_split_data(split["test"], ch) for name, ch in configs.items()}

    all_ok = True
    report = []
    for entry in results["checkpoint_manifest"]:
        name = entry["config"]
        test_x, test_y = test_data[name]
        model = SleepStageClassifier(in_channels=entry["in_channels"])
        model.load_state_dict(torch.load(REPO_ROOT / entry["path"], map_location="cpu"))
        model.eval()

        reproduced = evaluate_full(model, test_x, test_y)
        stored = results["runs"][name][f"seed{entry['seed']}"]
        f1_diff = abs(reproduced["macro_f1"] - stored["macro_f1"])
        ok = f1_diff < TOLERANCE
        all_ok = all_ok and ok
        report.append({"run_id": entry["run_id"], "ok": ok, "f1_diff": f1_diff})
        print(f"{entry['run_id']}: {'OK' if ok else 'MISMATCH'} (dF1={f1_diff:.2e})")

    out_path = REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation_reproducibility.json"
    out_path.write_text(json.dumps({"tolerance": TOLERANCE, "all_ok": all_ok, "runs": report}, indent=2))
    print(f"\n{'ALL OK' if all_ok else 'MISMATCH FOUND'}")
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
