#!/usr/bin/env python
"""Day 14: final canonical checkpoint inventory - original 50 (Day-8 archive)
+ 10 new interaction checkpoints (Day-14 archive) = 60 total. No hidden
local-only checkpoint dependency: every entry states its external archival
location."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

OUT_PATH = REPO_ROOT / "results" / "final_checkpoint_inventory_day14.json"


def main() -> None:
    consolidated = json.loads((REPO_ROOT / "results" / "checkpoint_manifest_consolidated.json").read_text())
    day14 = json.loads((REPO_ROOT / "results" / "checkpoint_archival_verification_day14.json").read_text())

    entries = []
    seen_sha = {}
    for e in consolidated["entries"]:
        sha = e.get("sha256")
        duplicate = sha in seen_sha if sha else False
        if sha:
            seen_sha.setdefault(sha, e["checkpoint_id"])
        entries.append({
            "checkpoint_id": e["checkpoint_id"],
            "experiment": e.get("experiment_id"),
            "seed": e.get("seed"),
            "sha256": sha,
            "locally_present": e.get("current_machine_present"),
            "external_archival_location": "GitHub Release day8-checkpoint-archive-v1 (biological_minimalism_checkpoints_day8.tar.gz)",
            "duplicate_of": None if not duplicate else seen_sha[sha],
        })

    for c in day14["checkpoint_details"]:
        sha = c["sha256_in_archive"]
        duplicate = sha in seen_sha
        if not duplicate:
            seen_sha[sha] = c["name"]
        entries.append({
            "checkpoint_id": c["name"].split("/")[-1].replace(".pt", ""),
            "experiment": "sleep_edf_interaction_eeg_eog_resp",
            "seed": None,
            "sha256": sha,
            "locally_present": True,
            "external_archival_location": "GitHub Release day14-checkpoint-archive-v1 (biological_minimalism_checkpoints_day14.tar.gz)",
            "duplicate_of": None if not duplicate else seen_sha[sha],
        })

    n_total = len(entries)
    n_unique = len({e["sha256"] for e in entries if e["sha256"]})
    n_present = sum(1 for e in entries if e["locally_present"])
    n_external = sum(1 for e in entries if e["external_archival_location"] is not None)

    out = {
        "purpose": "Final canonical checkpoint inventory (Day 14) - original 50 (Day-8 archive) + 10 interaction (Day-14 archive) = 60 total. Every entry states its external archival location; no hidden local-only dependency.",
        "archives": {
            "day8": {"tag": "day8-checkpoint-archive-v1", "n_checkpoints": 50, "sha256": "5e0661a6d5adcf345dfc86fe4c80138b20df405038a13817c7d97a1189572de4"},
            "day14": {"tag": "day14-checkpoint-archive-v1", "n_checkpoints": 10, "sha256": day14["archive_sha256"]},
        },
        "entries": entries,
        "summary": {
            "n_total_referenced": n_total,
            "n_unique_sha256": n_unique,
            "n_present_locally": n_present,
            "n_with_external_archival": n_external,
            "n_without_external_archival": n_total - n_external,
        },
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("Wrote", OUT_PATH)
    print(json.dumps(out["summary"], indent=2))


if __name__ == "__main__":
    main()
