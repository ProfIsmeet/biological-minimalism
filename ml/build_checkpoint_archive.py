#!/usr/bin/env python
"""Durable checkpoint archival package (Day 8, Reviewer B).

Packages every unique, currently-present checkpoint from
ml/checkpoints/ (per results/checkpoint_manifest_consolidated.json) into
one compressed archive under archival/checkpoints_day8/ (gitignored - not
committed, contains large binaries), together with the manifest,
SHA256SUMS, and a README.

Does NOT include any raw dataset file. Does NOT regenerate a missing
checkpoint. This is packaging only - upload to an external durable
location (GitHub Release/LFS/Zenodo) is a separate, later step for
Emir/Claude, not performed here.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

MANIFEST_PATH = REPO_ROOT / "results" / "checkpoint_manifest_consolidated.json"
CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"
ARCHIVAL_DIR = REPO_ROOT / "archival" / "checkpoints_day8"
VERIFICATION_OUT = REPO_ROOT / "results" / "checkpoint_archival_verification.json"


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    present_unique = [e for e in manifest["entries"] if e["current_machine_present"] and e["unique_file"]]

    ARCHIVAL_DIR.mkdir(parents=True, exist_ok=True)
    staging_ckpt_dir = ARCHIVAL_DIR / "checkpoints"
    staging_ckpt_dir.mkdir(exist_ok=True)

    sha256sums_lines = []
    copied = []
    for entry in present_unique:
        src = REPO_ROOT / entry["file_path"]
        dst = staging_ckpt_dir / src.name
        shutil.copy2(src, dst)
        copied.append(entry["path"])
        sha256sums_lines.append(f"{entry['sha256']}  checkpoints/{src.name}")

    (ARCHIVAL_DIR / "SHA256SUMS.txt").write_text("\n".join(sorted(sha256sums_lines)) + "\n")
    (ARCHIVAL_DIR / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))

    readme = f"""# Biological Minimalism — Checkpoint Archival Package (Day 8)

Contains {len(copied)} unique model checkpoints (.pt files) referenced by
this project's frozen scientific results, packaged for durable off-machine
storage (GitHub Release / LFS / Zenodo / institutional storage - upload
target chosen by Emir/Claude, not performed by this package).

## Contents

- `checkpoints/` - the actual .pt files (PyTorch state_dicts only, no raw data)
- `MANIFEST.json` - full canonical manifest (dataset, target, experiment,
  model role, seed, architecture, SHA256, size) for every checkpoint
- `SHA256SUMS.txt` - flat checksum list for a quick `sha256sum -c` verification

## What is explicitly NOT included

- No raw dataset files (PPG-DaLiA, PTT, Sleep-EDF, BIDMC, etc.)
- No regenerated/fabricated checkpoints for entries that were missing on
  the source machine - see MANIFEST.json's `current_machine_present` field
- No credentials, no unrelated project files

## Verification

Run from inside this directory (or see
results/checkpoint_archival_verification.json for the equivalent already
performed): `sha256sum -c SHA256SUMS.txt`
"""
    (ARCHIVAL_DIR / "README.md").write_text(readme)

    # Build the compressed archive
    archive_path = ARCHIVAL_DIR.parent / "biological_minimalism_checkpoints_day8.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(ARCHIVAL_DIR, arcname="checkpoints_day8")

    # --- Verification pass: re-hash everything inside the archive ----------
    verification_entries = []
    all_ok = True
    with tarfile.open(archive_path, "r:gz") as tar:
        members = [m for m in tar.getmembers() if m.isfile()]
        raw_dataset_hits = [m.name for m in members if "datasets/" in m.name or m.name.lower().endswith((".edf", ".pkl", ".npz", ".csv"))]
        for m in members:
            if m.name.endswith(".pt"):
                f = tar.extractfile(m)
                data = f.read()
                actual_sha = hashlib.sha256(data).hexdigest()
                expected = next((e for e in present_unique if e["path"] == Path(m.name).name), None)
                ok = expected is not None and actual_sha == expected["sha256"]
                all_ok = all_ok and ok
                verification_entries.append({"name": m.name, "size_in_archive": m.size, "sha256_in_archive": actual_sha, "matches_manifest": ok})

    verification = {
        "archive_path": str(archive_path.relative_to(REPO_ROOT)),
        "archive_size_bytes": archive_path.stat().st_size,
        "n_checkpoints_packaged": len(copied),
        "n_checkpoints_verified_ok": sum(1 for e in verification_entries if e["matches_manifest"]),
        "all_checkpoints_verified_ok": all_ok,
        "raw_dataset_files_found_in_archive": raw_dataset_hits,
        "no_raw_datasets_included": len(raw_dataset_hits) == 0,
        "checkpoint_details": verification_entries,
    }

    VERIFICATION_OUT.write_text(json.dumps(verification, indent=2))

    print(f"Packaged {len(copied)} checkpoints into {archive_path}")
    print(f"Archive size: {archive_path.stat().st_size / 1e6:.1f} MB")
    print(f"All verified OK: {all_ok}")
    print(f"Raw dataset files found: {raw_dataset_hits}")
    print(f"Wrote {VERIFICATION_OUT}")


if __name__ == "__main__":
    main()
