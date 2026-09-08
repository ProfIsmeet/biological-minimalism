"""Audit M7/§35-§36: PPG-DaLiA cache provenance verification.

A cache whose embedded subject id does not match the requested subject must be
REJECTED (never silently trusted); a legacy cache with no provenance must be
tolerated but WARNED as LEGACY_CACHE_UNVERIFIED; a valid cache loads cleanly."""

from __future__ import annotations

import json

import numpy as np
import pytest

from ml.datasets.ppg_dalia import (
    ACC_FS,
    CACHE_SCHEMA_VERSION,
    PPG_FS,
    STEP_SECONDS,
    WINDOW_SECONDS,
    load_cached_subject,
)


def _write_cache(path, subject_id, *, provenance: bool, meta_subject=None):
    arrays = dict(
        ppg=np.zeros((2, 4), np.float32),
        acc=np.zeros((2, 3, 4), np.float32),
        hr=np.zeros((2,), np.float32),
        activity=np.zeros((2,), np.int64),
        motion_energy=np.zeros((2,), np.float32),
    )
    if provenance:
        meta = {
            "cache_schema_version": CACHE_SCHEMA_VERSION,
            "subject_id": meta_subject or subject_id,
            "modality_config": {"ppg_fs": PPG_FS, "acc_fs": ACC_FS,
                                "window_seconds": WINDOW_SECONDS, "step_seconds": STEP_SECONDS},
        }
        arrays["_provenance"] = np.array(json.dumps(meta))
    np.savez_compressed(path / f"{subject_id}.npz", **arrays)


def test_valid_cache_loads(tmp_path):
    _write_cache(tmp_path, "S1", provenance=True)
    win = load_cached_subject(tmp_path, "S1")
    assert win.subject_id == "S1"


def test_mismatched_subject_is_rejected(tmp_path):
    # File named S2.npz but its provenance records subject S9 -> reject.
    _write_cache(tmp_path, "S2", provenance=True, meta_subject="S9")
    with pytest.raises(ValueError, match="provenance mismatch"):
        load_cached_subject(tmp_path, "S2")


def test_legacy_cache_warns_but_loads(tmp_path):
    _write_cache(tmp_path, "S3", provenance=False)
    with pytest.warns(UserWarning, match="LEGACY_CACHE_UNVERIFIED"):
        win = load_cached_subject(tmp_path, "S3")
    assert win.subject_id == "S3"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
