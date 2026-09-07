"""Build a machine-readable inventory of every model checkpoint referenced by the
committed research artifacts (§14 reproducibility).

For each referenced checkpoint this records: experiment, role, seed, the expected
repository-relative POSIX path, expected SHA256 and size (as declared in the
artifact), whether the file is currently present on disk, whether it is git-tracked,
its archival status, and its reconstructability. For files that ARE present the
declared SHA256 is verified against the file on disk.

This script performs NO training and does not modify any frozen artifact. Run:

    python ml/build_checkpoint_inventory.py

Missing historical checkpoints are reported as missing. A missing checkpoint is
never regenerated and relabelled "original".
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
OUT_PATH = RESULTS / "checkpoint_inventory.json"

SEED_RE = re.compile(r"seed(\d+)")


def posix_rel(raw_path: str) -> str:
    """Normalise a possibly Windows-style, possibly absolute path to a POSIX
    repository-relative path."""
    p = raw_path.replace("\\", "/")
    idx = p.find("ml/checkpoints/")
    if idx >= 0:
        return p[idx:]
    return p.lstrip("/")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_tracked(rel_path: str) -> bool:
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO), "ls-files", "--error-unmatch", rel_path],
            capture_output=True,
            text=True,
        )
        return out.returncode == 0
    except OSError:
        return False


def _role_from(name: str) -> str | None:
    n = name.lower()
    if "shuffled" in n or "model_c" in n:
        return "ppg_plus_shuffled_imu (capacity-matched control C)"
    if "plus_imu" in n or "model_b" in n:
        return "ppg_plus_imu (candidate B)"
    if "ppg_only" in n or "model_a" in n:
        return "ppg_only (baseline A)"
    return None


def _collect_records(obj, experiment: str, out: list[dict]) -> None:
    if isinstance(obj, dict):
        keys = obj.keys()
        if "sha256" in keys and ("path" in keys or "run_id" in keys or "model_id" in keys):
            raw_path = obj.get("path") or obj.get("checkpoint_path") or ""
            run_id = obj.get("run_id") or obj.get("model_id") or ""
            # Only real model checkpoints: a checkpoint file path, or a seed run id.
            is_checkpoint = raw_path.replace("\\", "/").lower().endswith((".pt", ".pth", ".ckpt")) or (
                bool(run_id) and "seed" in run_id.lower()
            )
            if is_checkpoint and (raw_path or run_id):
                out.append(
                    {
                        "experiment": experiment,
                        "run_id": run_id,
                        "raw_path": raw_path,
                        "declared_sha256": obj.get("sha256"),
                        "declared_size_bytes": obj.get("size_bytes"),
                    }
                )
        for v in obj.values():
            _collect_records(v, experiment, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect_records(v, experiment, out)


# The operational replay checkpoint used by the running backend. Its expected
# SHA256 is pinned in backend/app/ml/ppg_dalia_hr.py (EXPECTED_CHECKPOINT_SHA256)
# and enforced at load time. It is the single reproducibility anchor the live
# system actually depends on, so it is inventoried explicitly.
REPLAY_ANCHOR = {
    "experiment": "ppg-dalia-imu-ablation (single-seed Model B; backend replay)",
    "run_id": "model_b_ppg_plus_imu_ppg_dalia",
    "raw_path": "ml/checkpoints/model_b_ppg_plus_imu_ppg_dalia.pt",
    "declared_sha256": "c53a34586d2d6baf68aae4441b6c15a0f5f623f0ea70c023c7371c2dbded0e77",
    "declared_size_bytes": None,
}


def build() -> dict:
    raw_records: list[dict] = [dict(REPLAY_ANCHOR)]
    for artifact in sorted(RESULTS.glob("*.json")):
        if artifact.name == OUT_PATH.name:
            continue
        # The consolidated manifest is Ismet's cross-machine roll-up recorded on
        # his Windows clone (bare filenames, present_locally reflects THAT machine).
        # It is kept as a separate, un-collapsed view (see cross_machine_manifest
        # below), not merged into this Mac-reality inventory.
        if artifact.name == "checkpoint_manifest_consolidated.json":
            continue
        try:
            data = json.loads(artifact.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        _collect_records(data, artifact.name, raw_records)

    seen: dict[tuple, dict] = {}
    for rec in raw_records:
        rel = posix_rel(rec["raw_path"]) if rec["raw_path"] else ""
        key = (rec["declared_sha256"], rel or rec["run_id"])
        entry = seen.get(key)
        if entry is None:
            seed_match = SEED_RE.search(rec["run_id"] or rel)
            entry = {
                "expected_path_posix": rel or None,
                "run_id": rec["run_id"] or None,
                "seed": int(seed_match.group(1)) if seed_match else None,
                "role": _role_from(rec["run_id"] or rel),
                "declared_sha256": rec["declared_sha256"],
                "declared_size_bytes": rec["declared_size_bytes"],
                "referenced_by": [],
            }
            seen[key] = entry
        if rec["experiment"] not in entry["referenced_by"]:
            entry["referenced_by"].append(rec["experiment"])

    inventory = []
    present = missing = verified = mismatched = 0
    for entry in seen.values():
        rel = entry["expected_path_posix"]
        on_disk = (REPO / rel) if rel else None
        is_present = bool(on_disk and on_disk.is_file())
        record = dict(entry)
        record["present"] = is_present
        record["git_tracked"] = git_tracked(rel) if rel else False
        record["sha256_verification"] = "not_present"
        if is_present:
            present += 1
            actual = sha256_of(on_disk)
            record["actual_sha256"] = actual
            record["actual_size_bytes"] = on_disk.stat().st_size
            if entry["declared_sha256"] is None:
                record["sha256_verification"] = "no_declared_sha"
            elif actual == entry["declared_sha256"]:
                record["sha256_verification"] = "verified"
                verified += 1
            else:
                record["sha256_verification"] = "MISMATCH"
                mismatched += 1
        else:
            missing += 1
        record["archival_status"] = "present_local_untracked" if is_present else "absent"
        record["reconstructability"] = (
            "deterministic_training_script_exists_but_rerun_not_guaranteed_bit_identical"
        )
        inventory.append(record)

    inventory.sort(key=lambda r: (r["expected_path_posix"] or r["run_id"] or ""))

    # Cross-machine reconciliation (§10/§23): Ismet's consolidated manifest records
    # 43 checkpoint hashes as present on HIS Windows machine. Model weights are
    # machine-local and gitignored, so that count must NOT be conflated with what
    # physically exists on this Mac. Report both, un-collapsed.
    cross_machine = None
    consolidated_path = RESULTS / "checkpoint_manifest_consolidated.json"
    if consolidated_path.is_file():
        try:
            consolidated = json.loads(consolidated_path.read_text(encoding="utf-8"))
            cm_summary = consolidated.get("summary", {})
            cross_machine = {
                "source_artifact": "results/checkpoint_manifest_consolidated.json",
                "hashes_recorded_on_ismet_windows_machine": cm_summary.get("total_expected"),
                "present_locally_on_ismet_windows_machine": cm_summary.get("present_locally"),
                "checkpoint_files_physically_present_on_this_mac": present,
                "durably_archived": False,
                "archival_note": (
                    "No checkpoint weight files are committed to git (ml/checkpoints/* is "
                    "gitignored) and none were pushed to the remote. A recorded hash is NOT a "
                    "durable archive. Regenerating weights would not reproduce the originals "
                    "bit-identically and must never be relabelled 'original'."
                ),
            }
        except (OSError, json.JSONDecodeError):
            cross_machine = None

    return {
        "inventory_id": "biological-minimalism-checkpoint-inventory-v1",
        "note": (
            "Model checkpoints are gitignored (ml/checkpoints/*). This inventory records "
            "every checkpoint referenced by committed EXPERIMENT artifacts on THIS machine, "
            "whether it is present, and whether present files match their declared SHA256. "
            "Ismet's cross-machine roll-up (checkpoint_manifest_consolidated.json) is kept "
            "separate under 'cross_machine_manifest' and is NOT merged in. Missing historical "
            "checkpoints are NOT regenerated. Paths are normalised to POSIX repository-relative "
            "form; source artifacts contain non-portable Windows-style paths (documented, not "
            "rewritten, to preserve their frozen SHA chains)."
        ),
        "summary": {
            "total_referenced_checkpoints": len(inventory),
            "present": present,
            "missing": missing,
            "sha256_verified": verified,
            "sha256_mismatched": mismatched,
        },
        "cross_machine_manifest": cross_machine,
        "checkpoints": inventory,
    }


if __name__ == "__main__":
    payload = build()
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("Wrote", OUT_PATH.relative_to(REPO))
    print(json.dumps(payload["summary"], indent=2))
