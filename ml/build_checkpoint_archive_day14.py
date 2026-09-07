#!/usr/bin/env python
"""Day 14: durable archival for the 10 Day-10 interaction checkpoints
(sleep_edf_interaction_M_B_*/M_AB_* x seeds 42-46), which were found NOT
to be in the Day-8 archive (they didn't exist yet when that archive was
built) and NOT externally durable.

Design choice: a SEPARATE, small, versioned archive
(biological_minimalism_checkpoints_day14.tar.gz) containing only the new
10 checkpoints, with explicit linkage back to the Day-8 archive for the
other 50 - chosen over silently repackaging all 60 into one archive, so
the existing Day-8 archive/release/hash chain is never mutated.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"
ARCHIVAL_DIR = REPO_ROOT / "archival" / "checkpoints_day14"
ARCHIVE_PATH = REPO_ROOT / "archival" / "biological_minimalism_checkpoints_day14.tar.gz"
OUT_PATH = REPO_ROOT / "results" / "checkpoint_archival_verification_day14.json"

INTERACTION_CHECKPOINTS = sorted(CKPT_DIR.glob("sleep_edf_interaction_*.pt"))


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert len(INTERACTION_CHECKPOINTS) == 10, f"expected 10 interaction checkpoints, found {len(INTERACTION_CHECKPOINTS)}"

    ARCHIVAL_DIR.mkdir(parents=True, exist_ok=True)
    ckpt_out_dir = ARCHIVAL_DIR / "checkpoints"
    ckpt_out_dir.mkdir(exist_ok=True)

    manifest_entries = []
    for ckpt in INTERACTION_CHECKPOINTS:
        dest = ckpt_out_dir / ckpt.name
        dest.write_bytes(ckpt.read_bytes())
        sha = sha256_of(dest)
        manifest_entries.append({
            "checkpoint_id": ckpt.stem,
            "path": f"checkpoints/{ckpt.name}",
            "size_bytes": dest.stat().st_size,
            "sha256": sha,
        })

    manifest = {
        "archive_id": "biological_minimalism_checkpoints_day14",
        "purpose": "Durable archival for the 10 Day-10 interaction checkpoints not covered by the Day-8 archive.",
        "linked_archive": {
            "name": "biological_minimalism_checkpoints_day8.tar.gz",
            "github_release_tag": "day8-checkpoint-archive-v1",
            "covers": "the other 50 canonical checkpoints (PPG-DaLiA, PTT, Sleep primary/control/legacy)",
            "sha256": "5e0661a6d5adcf345dfc86fe4c80138b20df405038a13817c7d97a1189572de4",
        },
        "checkpoints": manifest_entries,
        "n_checkpoints": len(manifest_entries),
    }
    (ARCHIVAL_DIR / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))

    sha_lines = "\n".join(f"{e['sha256']}  {e['path']}" for e in manifest_entries) + "\n"
    (ARCHIVAL_DIR / "SHA256SUMS.txt").write_text(sha_lines, encoding="utf-8", newline="\n")

    readme = f"""# Biological Minimalism - Day 14 Checkpoint Archive

10 checkpoints from the Day-10 Sleep-EDF EOG x Resp interaction experiment
(M_B = EEG+Resp, M_AB = EEG+EOG+Resp, seeds 42-46 each). These did not
exist when the Day-8 archive (`biological_minimalism_checkpoints_day8.tar.gz`,
GitHub Release `day8-checkpoint-archive-v1`) was built, and were found NOT
externally durable during the Day 14 hostile scientific review.

For the other 50 canonical checkpoints, see the Day-8 archive - this
archive intentionally does NOT duplicate them.

See `MANIFEST.json` / `SHA256SUMS.txt` for exact identities.
"""
    (ARCHIVAL_DIR / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    with tarfile.open(ARCHIVE_PATH, "w:gz") as tar:
        tar.add(ARCHIVAL_DIR, arcname="checkpoints_day14")

    archive_sha = sha256_of(ARCHIVE_PATH)

    # Re-verify by re-opening and re-hashing every member.
    verified = []
    all_ok = True
    with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
        names = [m.name for m in tar.getmembers()]
        raw_dataset_ext = (".edf", ".pkl", ".npz", ".csv", ".dat", ".hea")
        raw_hits = [n for n in names if n.lower().endswith(raw_dataset_ext)]
        for member in tar.getmembers():
            if not member.name.endswith(".pt"):
                continue
            f = tar.extractfile(member)
            data = f.read()
            sha = hashlib.sha256(data).hexdigest()
            expected = next(e["sha256"] for e in manifest_entries if member.name.endswith(e["path"]))
            ok = sha == expected
            all_ok = all_ok and ok
            verified.append({"name": member.name, "sha256_in_archive": sha, "matches_manifest": ok})

    out = {
        "archive_path": str(ARCHIVE_PATH.relative_to(REPO_ROOT)),
        "archive_sha256": archive_sha,
        "archive_size_bytes": ARCHIVE_PATH.stat().st_size,
        "n_checkpoints_packaged": len(manifest_entries),
        "n_checkpoints_verified_ok": sum(1 for v in verified if v["matches_manifest"]),
        "all_checkpoints_verified_ok": all_ok,
        "raw_dataset_files_found_in_archive": raw_hits,
        "no_raw_datasets_included": raw_hits == [],
        "linked_archive": manifest["linked_archive"],
        "checkpoint_details": verified,
        "archival_status": "LOCAL_VERIFIED_PENDING_EXTERNAL_UPLOAD",
    }
    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("Wrote", ARCHIVE_PATH, "sha256:", archive_sha)
    print("Wrote", OUT_PATH)
    print(f"{out['n_checkpoints_verified_ok']}/{out['n_checkpoints_packaged']} verified OK")


if __name__ == "__main__":
    main()
