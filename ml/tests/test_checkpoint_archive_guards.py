"""Adversarial tests for the checkpoint-archive builder guards (audit M9 §37/§38).

Prove that empty selection, a filename collision, a missing checkpoint, and a
hash mismatch each make the builder EXIT NONZERO (a printed failure with exit 0
is not acceptable), and that a valid selection exits zero and verifies."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

_MOD = Path(__file__).resolve().parents[1] / "build_checkpoint_archive.py"
_spec = importlib.util.spec_from_file_location("build_checkpoint_archive", _MOD)
bca = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(bca)


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Redirect the module's hardcoded paths into a temp tree."""
    (tmp_path / "ml" / "checkpoints").mkdir(parents=True)
    (tmp_path / "results").mkdir()
    (tmp_path / "archival" / "checkpoints_day8").mkdir(parents=True)
    monkeypatch.setattr(bca, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(bca, "MANIFEST_PATH", tmp_path / "results" / "manifest.json")
    monkeypatch.setattr(bca, "CKPT_DIR", tmp_path / "ml" / "checkpoints")
    monkeypatch.setattr(bca, "ARCHIVAL_DIR", tmp_path / "archival" / "checkpoints_day8")
    monkeypatch.setattr(bca, "VERIFICATION_OUT", tmp_path / "results" / "verification.json")
    monkeypatch.delenv("BIOMIN_ARCHIVE_OVERWRITE", raising=False)
    return tmp_path


def _ckpt(root: Path, rel: str, content: bytes) -> dict:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return {
        "path": Path(rel).name,
        "file_path": rel,
        "sha256": hashlib.sha256(content).hexdigest(),
        "current_machine_present": True,
        "unique_file": True,
    }


def _write_manifest(root: Path, entries: list[dict]) -> None:
    (root / "results" / "manifest.json").write_text(json.dumps({"entries": entries}))


def test_empty_selection_exits_nonzero(sandbox):
    _write_manifest(sandbox, [])
    assert bca.main() == 1


def test_missing_checkpoint_exits_nonzero(sandbox):
    entry = _ckpt(sandbox, "ml/checkpoints/a.pt", b"weights-a")
    (sandbox / "ml/checkpoints/a.pt").unlink()  # manifest says present, file gone
    _write_manifest(sandbox, [entry])
    assert bca.main() == 1


def test_filename_collision_exits_nonzero(sandbox):
    e1 = _ckpt(sandbox, "ml/checkpoints/x/a.pt", b"one")
    e2 = _ckpt(sandbox, "ml/checkpoints/y/a.pt", b"two")  # same basename a.pt
    _write_manifest(sandbox, [e1, e2])
    assert bca.main() == 1


def test_hash_mismatch_exits_nonzero(sandbox):
    entry = _ckpt(sandbox, "ml/checkpoints/a.pt", b"real-weights")
    entry["sha256"] = "0" * 64  # manifest claims a wrong hash
    _write_manifest(sandbox, [entry])
    assert bca.main() == 1


def test_valid_selection_exits_zero_and_verifies(sandbox):
    entries = [
        _ckpt(sandbox, "ml/checkpoints/a.pt", b"weights-a"),
        _ckpt(sandbox, "ml/checkpoints/b.pt", b"weights-b"),
    ]
    _write_manifest(sandbox, entries)
    assert bca.main() == 0
    verification = json.loads((sandbox / "results" / "verification.json").read_text())
    assert verification["all_checkpoints_verified_ok"] is True
    assert verification["membership_complete"] is True
    assert verification["no_raw_datasets_included"] is True


def test_overwrite_guard_blocks_existing_archive(sandbox, monkeypatch):
    entries = [_ckpt(sandbox, "ml/checkpoints/a.pt", b"weights-a")]
    _write_manifest(sandbox, entries)
    assert bca.main() == 0  # first run creates the archive
    assert bca.main() == 1  # second run refuses to clobber without the env flag
    monkeypatch.setenv("BIOMIN_ARCHIVE_OVERWRITE", "1")
    assert bca.main() == 0  # explicit opt-in allows regeneration


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
