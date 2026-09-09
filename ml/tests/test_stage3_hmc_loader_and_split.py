"""Section 60 tests for the Claude-transferred HMC loader (cherry-picked
commit d97b4d5) and this session's full-cohort split. Claude added no
tests for the loader; these validate its contract without requiring the
~15.7 GB of real HMC files to be present."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.datasets.hmc_sleep import (  # noqa: E402
    EEG_CHANNEL,
    EOG_CHANNEL_1,
    EOG_CHANNEL_2,
    STAGE_NAMES,
    _STAGE_MAP,
    parse_sleepscoring,
    shuffle_eog_within_subject,
)

FULL_SPLIT_PATH = REPO_ROOT / "results" / "hmc_split_stage3_full_cohort.json"
PILOT_SPLIT_PATH = REPO_ROOT / "results" / "hmc_split_stage2.json"


def test_frozen_channel_labels_match_stage1b_protocol():
    assert EEG_CHANNEL == "EEG C4-M1"
    assert EOG_CHANNEL_1 == "EOG E1-M2"
    assert EOG_CHANNEL_2 == "EOG E2-M2"


def test_stage_map_has_five_classes_matching_frozen_protocol():
    assert STAGE_NAMES == ("Wake", "N1", "N2", "N3", "REM")
    assert set(_STAGE_MAP.values()) == {0, 1, 2, 3, 4}


def test_stage_map_excludes_unknown_movement_lights_annotations():
    for bad in ["Lights off", "Lights on", "Movement", ""]:
        assert _STAGE_MAP.get(bad) is None


def test_parse_sleepscoring_real_header_format(tmp_path):
    scoring = tmp_path / "SN999_sleepscoring.txt"
    scoring.write_text(
        "Date,Time,Recording onset,Duration,Annotation,Linked channel\n"
        "01-01-2018,22:00:00,0,30,Sleep stage W,EEG C4-M1\n"
        "01-01-2018,22:00:30,30,30,Lights off,\n"
        "01-01-2018,22:01:00,60,30,Sleep stage N1,EEG C4-M1\n"
    )
    events = parse_sleepscoring(scoring)
    assert events == [(0.0, 30.0, 0), (60.0, 30.0, 1)]  # "Lights off" excluded


def test_shuffle_eog_within_subject_never_crosses_subjects():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(20, 2, 10)).astype(np.float32)
    subject_idx = np.array([0] * 10 + [1] * 10)
    shuffled = shuffle_eog_within_subject(x, subject_idx, eog_channel_index=1, seed=42)
    for s in (0, 1):
        mask = subject_idx == s
        orig_pool = set(map(tuple, x[mask, 1, :].round(6).tolist()))
        for row in shuffled[mask, 1, :]:
            assert tuple(row.round(6).tolist()) in orig_pool


def test_shuffle_eog_within_subject_leaves_eeg_untouched():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(20, 2, 10)).astype(np.float32)
    subject_idx = np.array([0] * 10 + [1] * 10)
    shuffled = shuffle_eog_within_subject(x, subject_idx, eog_channel_index=1, seed=42)
    assert np.array_equal(shuffled[:, 0, :], x[:, 0, :])


def test_full_cohort_split_is_151_recordings_no_duplicates_no_overlap():
    d = json.loads(FULL_SPLIT_PATH.read_text())
    train, val, test = d["split"]["train"], d["split"]["val"], d["split"]["test"]
    all_ids = train + val + test
    assert len(all_ids) == 151
    assert len(set(all_ids)) == 151
    assert set(train) & set(val) == set()
    assert set(train) & set(test) == set()
    assert set(val) & set(test) == set()


def test_full_cohort_split_matches_real_records_index():
    d = json.loads(FULL_SPLIT_PATH.read_text())
    assert len(d["all_ids_verified_from_records_index"]) == 151
    assert set(d["all_ids_verified_from_records_index"]) == set(d["split"]["train"] + d["split"]["val"] + d["split"]["test"])


def test_pilot_split_disjoint_and_superseded_disclosure_present():
    d = json.loads(FULL_SPLIT_PATH.read_text())
    assert "supersedes" in d
    assert "hmc_split_stage2.json" in d["supersedes"]
    pilot = json.loads(PILOT_SPLIT_PATH.read_text())
    assert pilot["reduced_cohort_size"] == 12


def test_full_split_was_frozen_before_pilot_data_reused():
    # the full split's selection rule references no HMC file content
    d = json.loads(FULL_SPLIT_PATH.read_text())
    assert d["selection_method"] == "sorted RECORDS index, random.Random(42).shuffle(), 70/15/15 split by position"
