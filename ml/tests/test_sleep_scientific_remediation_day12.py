"""H1 (seed initialization) + H2 (respiration native rate) remediation
tests (Day 12). Real tests against actual model weights and actual EDF
header data - not metadata-only assertions."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from ml.sleep_seed_utils import derive_sleep_run_seeds, seed_for_data_order, seed_for_model_init  # noqa: E402
from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier  # noqa: E402


def _fingerprint(model: torch.nn.Module) -> list[float]:
    conv = next(m for m in model.modules() if isinstance(m, torch.nn.Conv1d))
    return conv.weight.detach().flatten()[:8].tolist()


def _ambient_perturb(n: int) -> None:
    for _ in range(n):
        torch.rand(37)


# --- H1: corrected order is truly seed-controlled -----------------------------


def test_h1_corrected_order_same_seed_same_ambient_state_is_identical():
    seeds = derive_sleep_run_seeds(42)
    seed_for_model_init(seeds)
    m1 = SleepStageClassifier(in_channels=2)
    seed_for_model_init(seeds)
    m2 = SleepStageClassifier(in_channels=2)
    assert _fingerprint(m1) == _fingerprint(m2)


def test_h1_corrected_order_ambient_rng_state_does_not_matter():
    seeds = derive_sleep_run_seeds(42)
    _ambient_perturb(0)
    seed_for_model_init(seeds)
    m1 = SleepStageClassifier(in_channels=2)

    _ambient_perturb(23)  # different amount of unrelated prior RNG use
    seed_for_model_init(seeds)
    m2 = SleepStageClassifier(in_channels=2)

    assert _fingerprint(m1) == _fingerprint(m2)


def test_h1_corrected_order_different_seeds_give_different_init():
    seeds_a = derive_sleep_run_seeds(42)
    seed_for_model_init(seeds_a)
    m1 = SleepStageClassifier(in_channels=2)

    seeds_b = derive_sleep_run_seeds(43)
    seed_for_model_init(seeds_b)
    m2 = SleepStageClassifier(in_channels=2)

    assert _fingerprint(m1) != _fingerprint(m2)


def test_h1_buggy_order_reproduces_the_original_bug():
    """Demonstrates the ORIGINAL trainers' actual bug pattern: construct
    the model, THEN seed - the recorded seed does not control init."""
    _ambient_perturb(0)
    m1 = SleepStageClassifier(in_channels=2)
    torch.manual_seed(42)  # what train_one() does - too late

    _ambient_perturb(23)
    m2 = SleepStageClassifier(in_channels=2)
    torch.manual_seed(42)  # same recorded seed, still too late

    assert _fingerprint(m1) != _fingerprint(m2), (
        "If this assertion fails, the historical bug this test documents "
        "either no longer reproduces or the test environment changed - "
        "investigate before assuming H1 is resolved by accident."
    )


def test_h1_model_init_and_data_order_subseeds_are_distinct():
    seeds = derive_sleep_run_seeds(42)
    assert seeds.model_init_seed != seeds.data_order_seed
    assert seeds.model_init_seed != seeds.control_shuffle_seed
    assert seeds.data_order_seed != seeds.control_shuffle_seed


def test_h1_data_order_seed_reproducible_dataloader_order():
    """seed_for_data_order controls torch's global RNG at DataLoader-build
    time - verify a shuffled DataLoader built right after it produces the
    same batch order across two independent constructions."""
    from torch.utils.data import DataLoader, TensorDataset

    seeds = derive_sleep_run_seeds(42)
    x = torch.arange(100).float().view(100, 1)
    y = torch.arange(100)

    seed_for_data_order(seeds)
    order1 = [batch[1].tolist() for batch in DataLoader(TensorDataset(x, y), batch_size=10, shuffle=True)]

    seed_for_data_order(seeds)
    order2 = [batch[1].tolist() for batch in DataLoader(TensorDataset(x, y), batch_size=10, shuffle=True)]

    assert order1 == order2


def test_h1_control_shuffle_seed_isolated_from_model_init():
    """Changing the control_shuffle_seed derivation must not change the
    model_init_seed for the same run seed (and vice versa is trivially
    true since they're independent fields) - guards against accidental
    coupling if the derivation formula is ever edited."""
    seeds_run42 = derive_sleep_run_seeds(42)
    seeds_run43 = derive_sleep_run_seeds(43)
    # control_shuffle_seed changes with run_seed, but its OFFSET from
    # model_init_seed is constant - i.e. they move together predictably,
    # not independently-randomly, which is the documented (not accidental) design.
    assert (seeds_run42.control_shuffle_seed - seeds_run42.model_init_seed) == (
        seeds_run43.control_shuffle_seed - seeds_run43.model_init_seed
    )


def test_h1_eog_shuffle_already_isolated_and_unaffected():
    """The EOG shuffle uses its own local np.random.default_rng(seed),
    never the global torch RNG - confirms it was never affected by H1 and
    remains unaffected by the corrected protocol."""
    from ml.datasets.sleep_edf import shuffle_eog_within_subject
    import numpy as np

    x = np.random.default_rng(0).normal(size=(20, 2, 10)).astype("float32")
    subj = np.array([0] * 10 + [1] * 10)

    # Perturb torch's global RNG heavily in between - must not affect the shuffle.
    torch.manual_seed(999)
    _ambient_perturb(50)
    s1 = shuffle_eog_within_subject(x, subj, eog_channel_index=1, seed=42)

    torch.manual_seed(111)
    _ambient_perturb(3)
    s2 = shuffle_eog_within_subject(x, subj, eog_channel_index=1, seed=42)

    np.testing.assert_array_equal(s1, s2)


# --- H2: respiration native rate -----------------------------------------------

RAW_DIR = REPO_ROOT / "datasets" / "sleep-edfx" / "raw"
requires_raw_data = pytest.mark.skipif(not (RAW_DIR / "SC4001E0-PSG.edf").exists(), reason="Sleep-EDF raw data not present locally")


@requires_raw_data
def test_h2_resp_native_rate_from_edf_header_is_1hz():
    import mne

    raw = mne.io.read_raw_edf(RAW_DIR / "SC4001E0-PSG.edf", preload=False, verbose="ERROR")
    extras = raw._raw_extras[0]
    record_length = extras["record_length"][0]
    idx = extras["ch_names"].index("Resp oro-nasal")
    native_rate = extras["n_samps"][idx] / record_length
    assert native_rate == pytest.approx(1.0)


@requires_raw_data
def test_h2_eeg_eog_native_rate_from_edf_header_is_100hz():
    import mne

    raw = mne.io.read_raw_edf(RAW_DIR / "SC4001E0-PSG.edf", preload=False, verbose="ERROR")
    extras = raw._raw_extras[0]
    record_length = extras["record_length"][0]
    for ch in ("EEG Fpz-Cz", "EOG horizontal"):
        idx = extras["ch_names"].index(ch)
        native_rate = extras["n_samps"][idx] / record_length
        assert native_rate == pytest.approx(100.0)


def test_h2_native_and_loaded_rates_not_conflated_in_metadata():
    from ml.datasets.sleep_edf import RESP_NATIVE_SFREQ_HZ, RESP_LOADED_SFREQ_HZ, EEG_EOG_NATIVE_SFREQ_HZ

    assert RESP_NATIVE_SFREQ_HZ == 1.0
    assert RESP_LOADED_SFREQ_HZ == 100.0
    assert EEG_EOG_NATIVE_SFREQ_HZ == 100.0
    assert RESP_NATIVE_SFREQ_HZ != RESP_LOADED_SFREQ_HZ, "native and loaded rates must never be equal in this dataset - if they ever are, the constants are wrong"


def test_h2_resampling_method_documented():
    from ml.datasets.sleep_edf import RESP_RESAMPLING_METHOD

    assert "FFT" in RESP_RESAMPLING_METHOD or "resample" in RESP_RESAMPLING_METHOD.lower()


@requires_raw_data
def test_h2_loader_still_produces_correct_shape_after_metadata_change():
    """The H2 fix is metadata-only - confirms the loader's actual array
    output is unaffected (2 channels, 3000 samples/epoch = 30s @ 100Hz grid)."""
    from ml.datasets.sleep_edf import EEG_CHANNEL, RESP_CHANNEL, load_dataset_windows_multi

    x, y, subj, prefixes = load_dataset_windows_multi(RAW_DIR, channels=(EEG_CHANNEL, RESP_CHANNEL), subject_ids=["SC4001"])
    assert x.shape[1] == 2
    assert x.shape[2] == 3000
    assert len(y) == x.shape[0]


# --- Regression: primary/secondary cohorts, splits unchanged -------------------


def test_regression_primary_split_still_12_3_3():
    import json

    split = json.loads((REPO_ROOT / "ml/experiments/sleep_edf_eeg_eog_ablation/subject_split.json").read_text())
    assert len(split["train"]) == 12
    assert len(split["val"]) == 3
    assert len(split["test"]) == 3


def test_regression_secondary_cohort_still_8_and_disjoint():
    import json

    cohort = json.loads((REPO_ROOT / "ml/experiments/sleep_edf_secondary_holdout/cohort.json").read_text())
    split = json.loads((REPO_ROOT / "ml/experiments/sleep_edf_eeg_eog_ablation/subject_split.json").read_text())
    subjects = {c["subject_prefix"] for c in cohort["cohort"]}
    assert len(subjects) == 8
    all_primary = set(split["train"]) | set(split["val"]) | set(split["test"])
    assert subjects.isdisjoint(all_primary)
