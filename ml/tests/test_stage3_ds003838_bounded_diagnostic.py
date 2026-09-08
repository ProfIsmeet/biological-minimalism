"""Stage 3B contract tests for the ds003838 bounded diagnostic loader/trainer.
No performance-threshold assertions. Uses synthetic-shaped arrays for pure
contract checks (label parsing, leakage exclusion, capacity fairness) that
do not require the real ~1.5GB downloaded files to be present in CI."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.datasets.ds003838_eeg import SPARSE_CHANNELS, parse_trial_type  # noqa: E402
from ml.train_ds003838_eeg_minimalism import (  # noqa: E402
    channel_features,
    deranged_full_channel_epochs,
    pooled_features,
)


def test_parse_trial_type_extracts_length_from_text_not_raw_code():
    assert parse_trial_type("memory 01/05 correct: memorize digit 1 (first) in 5 digit sequence; correctly recalled") == ("memory", 5)
    assert parse_trial_type("control 03/13: listen to digit 3 in 13 digit sequence") == ("control", 13)
    assert parse_trial_type("STATUS") is None


def test_frozen_sparse_channels_are_muse_matched():
    assert SPARSE_CHANNELS == ["AF7", "AF8", "TP9", "TP10"]


def test_channel_features_fixed_width_five():
    epoch = np.random.default_rng(0).normal(size=1000)
    feats = channel_features(epoch)
    assert feats.shape == (5,)


def test_pooled_features_same_dimensionality_regardless_of_channel_count():
    rng = np.random.default_rng(0)
    channel_names = ["AF7", "AF8", "TP9", "TP10", "Cz", "Pz", "O1"]
    epochs = rng.normal(size=(10, len(channel_names), 200))
    a = pooled_features(epochs, channel_names, ["AF7", "AF8", "TP9", "TP10"])
    b = pooled_features(epochs, channel_names, None)
    assert a.shape == b.shape == (10, 5)


def test_control_c_never_deranges_the_frozen_sparse_channels():
    rng = np.random.default_rng(1)
    channel_names = ["AF7", "AF8", "TP9", "TP10", "Cz", "Pz"]
    epochs = rng.normal(size=(20, len(channel_names), 50))
    deranged = deranged_full_channel_epochs(epochs, channel_names, ["AF7", "AF8", "TP9", "TP10"], seed=42)
    for ch in ["AF7", "AF8", "TP9", "TP10"]:
        idx = channel_names.index(ch)
        assert np.array_equal(deranged[:, idx, :], epochs[:, idx, :])


def test_control_c_actually_deranges_non_sparse_channels():
    rng = np.random.default_rng(1)
    channel_names = ["AF7", "AF8", "TP9", "TP10", "Cz", "Pz"]
    epochs = rng.normal(size=(20, len(channel_names), 50))
    deranged = deranged_full_channel_epochs(epochs, channel_names, ["AF7", "AF8", "TP9", "TP10"], seed=42)
    cz_idx = channel_names.index("Cz")
    assert not np.array_equal(deranged[:, cz_idx, :], epochs[:, cz_idx, :])
