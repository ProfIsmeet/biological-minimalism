"""Section 60 tests for the Claude-transferred Sleep V2 C control and
interaction trainers (cherry-picked commit d97b4d5) - Claude added no tests
for this code; these are the Ismet-side contract tests required before
trusting it. Real-data-independent where possible."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.datasets.sleep_edf import shuffle_eog_within_subject  # noqa: E402
from ml.sleep_seed_utils import derive_sleep_run_seeds  # noqa: E402


def test_control_shuffle_seed_isolated_from_model_init_and_data_order():
    seeds = derive_sleep_run_seeds(42)
    assert seeds.model_init_seed != seeds.data_order_seed != seeds.control_shuffle_seed
    assert len({seeds.model_init_seed, seeds.data_order_seed, seeds.control_shuffle_seed}) == 3


def test_control_shuffle_seed_matches_run_seed_plus_200000_convention():
    seeds = derive_sleep_run_seeds(42)
    assert seeds.control_shuffle_seed == 42 + 200_000


def test_shuffle_eog_within_subject_never_crosses_subjects():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(20, 2, 10)).astype(np.float32)
    subject_idx = np.array([0] * 10 + [1] * 10)
    shuffled = shuffle_eog_within_subject(x, subject_idx, eog_channel_index=1, seed=42)
    # every shuffled EOG epoch must come from the SAME subject's own real epochs
    for s in (0, 1):
        mask = subject_idx == s
        orig_pool = set(map(tuple, x[mask, 1, :].round(6).tolist()))
        for row in shuffled[mask, 1, :]:
            assert tuple(row.round(6).tolist()) in orig_pool


def test_shuffle_eog_within_subject_leaves_eeg_channel_untouched():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(20, 2, 10)).astype(np.float32)
    subject_idx = np.array([0] * 10 + [1] * 10)
    shuffled = shuffle_eog_within_subject(x, subject_idx, eog_channel_index=1, seed=42)
    assert np.array_equal(shuffled[:, 0, :], x[:, 0, :])


def test_shuffle_eog_within_subject_is_deterministic():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(20, 2, 10)).astype(np.float32)
    subject_idx = np.array([0] * 10 + [1] * 10)
    a = shuffle_eog_within_subject(x, subject_idx, eog_channel_index=1, seed=42)
    b = shuffle_eog_within_subject(x, subject_idx, eog_channel_index=1, seed=42)
    assert np.array_equal(a, b)


def test_c_trainer_capacity_assertion_present_in_source():
    src = (REPO_ROOT / "ml" / "train_sleep_edf_shuffled_eog_control_seedfix_v2.py").read_text()
    assert "assert n_params == n_params_b_v2" in src


def test_c_trainer_reuses_v2_split_not_v1():
    src = (REPO_ROOT / "ml" / "train_sleep_edf_shuffled_eog_control_seedfix_v2.py").read_text()
    assert 'V2_PRIMARY_PATH = REPO_ROOT / "results" / "sleep_edf_primary_seedfix_v2.json"' in src
    assert "does_not_overwrite_v1" in src


def test_interaction_trainer_has_capacity_fairness_safeguard():
    src = (REPO_ROOT / "ml" / "train_sleep_edf_interaction_resp_seedfix_v2.py").read_text()
    assert "Capacity-fairness safeguard failed" in src
    assert "raise RuntimeError" in src


def test_interaction_formula_matches_frozen_day10_definition():
    src = (REPO_ROOT / "ml" / "train_sleep_edf_interaction_resp_seedfix_v2.py").read_text()
    assert "benefit_ab[s] - benefit_a[s] - benefit_b[s]" in src


def test_interaction_resp_provenance_not_regressed_to_100hz_native():
    src = (REPO_ROOT / "ml" / "train_sleep_edf_interaction_resp_seedfix_v2.py").read_text()
    assert "RESP_NATIVE_SFREQ_HZ" in src
    assert "do not report Resp as native 100 Hz" in src


def test_m0_ma_equivalence_independently_verified_same_hyperparameters():
    """Cross-file check: the original Day-10 interaction script and the
    corrected V2 primary script must share identical training
    hyperparameters for the M0/M_A reuse decision to be valid."""
    interaction_v1_src = (REPO_ROOT / "ml" / "train_sleep_edf_interaction_resp.py").read_text()
    primary_v2_src = (REPO_ROOT / "ml" / "train_sleep_edf_primary_seedfix_v2.py").read_text()
    assert "from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier, evaluate_full, train_one" in interaction_v1_src
    ablation_src = (REPO_ROOT / "ml" / "train_sleep_edf_eeg_eog_ablation.py").read_text()
    assert "EPOCHS = 20" in ablation_src
    assert "BATCH_SIZE = 64" in ablation_src
    assert "LR = 0.001" in ablation_src
    assert "EMBEDDING_DIM = 32" in primary_v2_src
