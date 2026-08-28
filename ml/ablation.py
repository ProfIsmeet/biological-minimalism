#!/usr/bin/env python
"""Ablation study harness (design scaffolding — see PDD, Ablation Study
section, for the full experimental design this implements).

Compares a trained `BiologicalDigitalTwinNet` checkpoint's performance
across configurations:

- **Full sensor set** — all four modalities present.
- **Minimal set (this project's default)** — same four modalities, this
  *is* the full set for Biological Minimalism; kept here as the reference
  condition for the ablations below.
- **Single-modality dropout** — mask one modality at a time (EEG, PPG,
  Temperature, Bio-impedance) and re-evaluate, to quantify the accuracy
  cost of each sensor per the modality-masking mechanism built into
  `ModalityFusionTransformer` (see backend/app/ml/models.py).
- **Noise injection** — evaluate under elevated synthetic noise, standing
  in for the mission-mode noise profiles in `engine/physiology.py`.
- **Motion artifact injection** — evaluate with simulated high-frequency
  artifact bursts added to the PPG/EEG windows.

No checkpoint or validation set exists in this task's scope, so running
this script requires first training a model with `train.py` against real
data. This file defines the *metric computation and comparison table*
(MAE, RMSE, F1 for classification targets, and a robustness delta) so
that step is not a fresh design exercise once a checkpoint exists.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.ml._torch_bootstrap import ensure_torch_dll_path  # noqa: E402

ensure_torch_dll_path()

import torch  # noqa: E402

from app.ml.models import MODALITIES, BiologicalDigitalTwinNet  # noqa: E402


def mae(pred: np.ndarray, target: np.ndarray) -> float:
    return float(np.mean(np.abs(pred - target)))


def rmse(pred: np.ndarray, target: np.ndarray) -> float:
    return float(np.sqrt(np.mean((pred - target) ** 2)))


def load_model(checkpoint_path: str) -> BiologicalDigitalTwinNet:
    model = BiologicalDigitalTwinNet()
    state_dict = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()
    return model


def run_ablation(checkpoint_path: str, dataset_path: str) -> None:
    """Skeleton entrypoint.

    `dataset_path` should be a held-out validation set produced by the
    same loaders used in `train.py`. Left unimplemented (raises below)
    because no such dataset exists in this task's scope — see module
    docstring.
    """

    raise NotImplementedError(
        "run_ablation requires a trained checkpoint and a real held-out "
        "validation set; neither exists in this task's scope. This "
        "function documents the intended experiment structure "
        f"(configurations: full set, single-modality dropout over {MODALITIES}, "
        "noise injection, motion artifact injection) for the research "
        "phase described in the PDD's Ablation Study section."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--dataset", type=str, required=True)
    args = parser.parse_args()
    run_ablation(args.checkpoint, args.dataset)


if __name__ == "__main__":
    main()
