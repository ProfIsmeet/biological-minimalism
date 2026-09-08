#!/usr/bin/env python
"""H1 reproduction probe (Day 12): demonstrates, with real model weights
(not a metadata assertion), that the CURRENT trainer order does not let
the recorded seed control model initialization, and that the CORRECTED
order (ml/sleep_seed_utils.py) does.

Real mechanism, not a simulation of an unrelated RNG: this probe
constructs the actual SleepStageClassifier used by every Sleep-EDF
trainer and reads its actual initial Conv1d/Linear weights.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT))

from app.ml._torch_bootstrap import ensure_torch_dll_path  # noqa: E402

ensure_torch_dll_path()

from ml.sleep_seed_utils import derive_sleep_run_seeds, seed_for_model_init  # noqa: E402
from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier  # noqa: E402

RUN_SEED = 42


def first_conv_weight_fingerprint(model: torch.nn.Module) -> list[float]:
    """A compact, exact fingerprint of the model's actual initial weights -
    the first 8 values of the first Conv1d layer's weight tensor."""
    first_conv = next(m for m in model.modules() if isinstance(m, torch.nn.Conv1d))
    return first_conv.weight.detach().flatten()[:8].tolist()


def ambient_perturbation(n_ops: int) -> None:
    """Simulates realistic 'unrelated prior torch RNG consumption before
    this seed's model gets constructed' - exactly what happens in the real
    multi-seed training loop (data loading, a previous seed's DataLoader
    shuffling, etc. all consume the global torch RNG before the NEXT
    seed's `model = SleepStageClassifier(...)` line runs)."""
    for _ in range(n_ops):
        torch.rand(37)  # arbitrary global-RNG-consuming op, discarded


def buggy_order_init(run_seed: int, ambient_ops_before: int) -> list[float]:
    """Reproduces the CURRENT (buggy) trainer order EXACTLY:
    model construction happens first; torch.manual_seed(seed) (what
    train_one() does) happens only AFTER, so it cannot affect the
    already-drawn initial weights. `ambient_ops_before` stands in for
    however much unrelated global-RNG consumption happened earlier in the
    real training loop/process before this seed's iteration reached the
    `model = SleepStageClassifier(...)` line."""
    ambient_perturbation(ambient_ops_before)
    model = SleepStageClassifier(in_channels=2)  # <-- constructed BEFORE seeding, exactly like the real bug
    torch.manual_seed(run_seed)  # <-- what train_one() does; too late to affect the line above
    return first_conv_weight_fingerprint(model)


def corrected_order_init(run_seed: int, ambient_ops_before: int) -> list[float]:
    """The CORRECTED order: seed_for_model_init() runs BEFORE construction,
    using ml/sleep_seed_utils.py's derived model_init_seed."""
    ambient_perturbation(ambient_ops_before)
    seeds = derive_sleep_run_seeds(run_seed)
    seed_for_model_init(seeds)  # <-- fix: seeds BEFORE construction
    model = SleepStageClassifier(in_channels=2)
    return first_conv_weight_fingerprint(model)


def main() -> None:
    # --- Probe 1: same recorded seed, different ambient RNG state, BUGGY order ---
    buggy_a = buggy_order_init(RUN_SEED, ambient_ops_before=0)
    buggy_b = buggy_order_init(RUN_SEED, ambient_ops_before=17)
    buggy_differ = buggy_a != buggy_b

    # --- Probe 2: same recorded seed, different ambient RNG state, CORRECTED order ---
    corrected_a = corrected_order_init(RUN_SEED, ambient_ops_before=0)
    corrected_b = corrected_order_init(RUN_SEED, ambient_ops_before=17)
    corrected_identical = corrected_a == corrected_b

    # --- Probe 3: corrected order, DIFFERENT seeds -> DIFFERENT weights (sanity: not a constant) ---
    corrected_seed42 = corrected_order_init(42, ambient_ops_before=5)
    corrected_seed43 = corrected_order_init(43, ambient_ops_before=5)
    different_seeds_differ = corrected_seed42 != corrected_seed43

    result = {
        "purpose": "H1 real reproduction probe - actual SleepStageClassifier weights, not a metadata assertion.",
        "run_seed_used": RUN_SEED,
        "probe_1_buggy_order_same_seed_different_ambient_state": {
            "ambient_ops_before_a": 0,
            "ambient_ops_before_b": 17,
            "fingerprint_a": buggy_a,
            "fingerprint_b": buggy_b,
            "weights_differ": buggy_differ,
            "conclusion": "CONFIRMS H1: same recorded seed produces DIFFERENT initial weights under the current (buggy) construction order." if buggy_differ else "FAILED TO REPRODUCE BUG",
        },
        "probe_2_corrected_order_same_seed_different_ambient_state": {
            "ambient_ops_before_a": 0,
            "ambient_ops_before_b": 17,
            "fingerprint_a": corrected_a,
            "fingerprint_b": corrected_b,
            "weights_identical": corrected_identical,
            "conclusion": "CONFIRMS FIX: same recorded seed produces IDENTICAL initial weights under the corrected order, regardless of ambient RNG state." if corrected_identical else "FIX DID NOT WORK",
        },
        "probe_3_corrected_order_different_seeds_sanity_check": {
            "seed_a": 42,
            "seed_b": 43,
            "fingerprint_a": corrected_seed42,
            "fingerprint_b": corrected_seed43,
            "weights_differ": different_seeds_differ,
            "conclusion": "Sanity check: the corrected protocol is not a constant - different seeds still produce different weights." if different_seeds_differ else "SANITY CHECK FAILED - corrected protocol may be broken",
        },
        "overall_h1_confirmed": buggy_differ and corrected_identical and different_seeds_differ,
    }

    out_path = REPO_ROOT / "results" / "sleep_seed_initialization_audit_day12.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print("\nWrote", out_path)


if __name__ == "__main__":
    main()
