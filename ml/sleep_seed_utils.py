"""Corrected deterministic seeding protocol for Sleep-EDF training (H1
remediation, Day 12). See docs/SLEEP_SEEDING_PROTOCOL_V2.md for the full
rationale and RNG-source inventory.

Root cause being fixed: every existing Sleep-EDF trainer
(ml/train_sleep_edf_eeg_eog_ablation.py, ml/train_sleep_edf_shuffled_eog_control.py,
ml/train_sleep_edf_interaction_resp.py) constructs `SleepStageClassifier(...)`
BEFORE calling `torch.manual_seed(seed)` (which only happens later, inside
`train_one()`). Model weight initialization consumes the GLOBAL torch RNG
at construction time, so the recorded "seed" does NOT control the model's
initial weights - only the DataLoader shuffle order and (for the control)
the already-independently-seeded EOG permutation are actually controlled
by the recorded seed.

This module provides ONE corrected protocol: derive three independent
sub-seeds from the run seed, and seed torch's global RNG for model
initialization BEFORE the model is constructed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np
import torch

# Fixed, documented offsets - large enough that model_init/data_order/
# control_shuffle sub-seeds for any of this project's run seeds (42-46)
# never collide with each other or with a different run seed's sub-seeds.
_MODEL_INIT_OFFSET = 0
_DATA_ORDER_OFFSET = 100_000
_CONTROL_SHUFFLE_OFFSET = 200_000


@dataclass(frozen=True)
class SleepRunSeeds:
    run_seed: int
    model_init_seed: int
    data_order_seed: int
    control_shuffle_seed: int


def derive_sleep_run_seeds(run_seed: int) -> SleepRunSeeds:
    """Deterministically derives the three independent sub-seeds used by
    the corrected Sleep-EDF training protocol from one recorded run seed."""
    return SleepRunSeeds(
        run_seed=run_seed,
        model_init_seed=run_seed + _MODEL_INIT_OFFSET,
        data_order_seed=run_seed + _DATA_ORDER_OFFSET,
        control_shuffle_seed=run_seed + _CONTROL_SHUFFLE_OFFSET,
    )


def seed_for_model_init(seeds: SleepRunSeeds) -> None:
    """Seeds Python, NumPy, and torch's global RNG using model_init_seed.
    MUST be called BEFORE constructing the model - this is the exact fix
    for H1. Also seeds Python/NumPy defensively even though the current
    SleepStageClassifier architecture (Conv1d/BatchNorm1d/Linear only, no
    dropout, no numpy-based init) only actually consumes the torch RNG at
    construction time - future architecture changes should not silently
    regress this guarantee."""
    random.seed(seeds.model_init_seed)
    np.random.seed(seeds.model_init_seed)
    torch.manual_seed(seeds.model_init_seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seeds.model_init_seed)


def seed_for_data_order(seeds: SleepRunSeeds) -> None:
    """Seeds torch's global RNG using data_order_seed. MUST be called
    AFTER the model is constructed and BEFORE the training DataLoader is
    built, so DataLoader shuffle order is controlled by a sub-seed
    independent of model initialization (changing one must not silently
    change the other)."""
    torch.manual_seed(seeds.data_order_seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seeds.data_order_seed)
