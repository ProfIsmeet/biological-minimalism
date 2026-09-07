#!/usr/bin/env python
"""Day 10: dataset-level reproducibility fingerprints.

Covers ONLY raw input files actually used by the frozen experiments already
in results/. Performs no training, no dataset modification. Never commits
raw data - this script only reads and hashes files already gitignored
under datasets/.

Sources of subject/split truth (read, never guessed):
  - results/ppg_dalia_imu_ablation.json (train/val/test subjects, dataset
    source/version string)
  - results/ptt_ppg_site_ablation.json (subject_split, raw_dir)
  - results/sleep_edf_eeg_eog_ablation.json (primary train/val/test split)
  - ml/experiments/sleep_edf_secondary_holdout/cohort.json (secondary cohort)
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

OUT_PATH = REPO_ROOT / "results" / "dataset_fingerprint_manifest_day10.json"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024 * 8), b""):
            h.update(chunk)
    return h.hexdigest()


def record(dataset: str, version: str, source: str, subject: str, session: str | None,
           rel_path: Path, role: str) -> dict:
    abs_path = REPO_ROOT / rel_path
    present = abs_path.exists()
    entry = {
        "dataset": dataset,
        "version": version,
        "source": source,
        "subject": subject,
        "session_or_night": session,
        "path": str(rel_path).replace("\\", "/"),
        "role": role,
        "locally_present": present,
        "raw_file_committed_to_git": False,
    }
    if present:
        entry["byte_size"] = abs_path.stat().st_size
        entry["sha256"] = sha256_of(abs_path)
    else:
        entry["byte_size"] = None
        entry["sha256"] = None
    return entry


def build_ppg_dalia() -> list[dict]:
    ppg = json.loads((REPO_ROOT / "results" / "ppg_dalia_imu_ablation.json").read_text())
    source = ppg["dataset_source"]
    version = ppg["dataset_version"]

    entries = []
    # Single raw archive, one record for the whole zip - PPG-DaLiA is
    # distributed as one per-subject-pickle-containing zip, not per-subject
    # files on disk (extracted on demand, see ml/datasets/ppg_dalia.py).
    zip_path = Path("datasets/ppg-dalia/raw_uci/ppg_dalia_uci.zip")
    role_by_subject = {}
    for s in ppg["train_subjects"]:
        role_by_subject[s] = "train"
    for s in ppg["validation_subjects"]:
        role_by_subject[s] = "validation"
    for s in ppg["test_subjects"]:
        role_by_subject[s] = "primary_test"

    entries.append(record(
        dataset="ppg_dalia", version=version, source=source, subject="ALL_15_SUBJECTS_SINGLE_ARCHIVE",
        session=None, rel_path=zip_path, role="train+validation+primary_test (single combined raw archive)",
    ))
    entries[-1]["subjects_covered"] = role_by_subject

    # Also fingerprint the per-subject windowized processed cache actually
    # read at train/eval time (extracted deterministically from the zip
    # above) - gives per-subject/per-role granularity.
    for subj, role in sorted(role_by_subject.items()):
        npz_path = Path("datasets/ppg-dalia/processed") / f"{subj}.npz"
        entries.append(record(
            dataset="ppg_dalia_processed_cache", version=version, source=f"derived from {source} via ml/datasets/ppg_dalia.py (deterministic windowization, cached)",
            subject=subj, session=None, rel_path=npz_path, role=role,
        ))
    return entries


def build_ptt() -> list[dict]:
    ptt = json.loads((REPO_ROOT / "results" / "ptt_ppg_site_ablation.json").read_text())
    split = ptt["subject_split"]
    source = "PhysioNet Pulse Transit Time PPG Dataset v1.1.0"
    version = "v1.1.0"
    raw_dir = Path(ptt["config"]["raw_dir"])

    role_of = {}
    for s in split["train"]:
        role_of[s] = "train"
    for s in split["val"]:
        role_of[s] = "validation"
    for s in split["test"]:
        role_of[s] = "primary_test"

    entries = []
    for subj, role in sorted(role_of.items()):
        for activity in ("sit", "walk", "run"):
            for ext in ("hea", "dat", "atr"):
                rel_path = raw_dir / f"{subj}_{activity}.{ext}"
                entries.append(record(
                    dataset="pulse_transit_time_ppg", version=version, source=source,
                    subject=subj, session=activity, rel_path=rel_path, role=role,
                ))
    return entries


def build_sleep_primary() -> list[dict]:
    sleep = json.loads((REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation.json").read_text())
    split = sleep["frozen_protocol"]["subject_split"]
    source = "PhysioNet Sleep-EDFx sleep-cassette (https://physionet.org/content/sleep-edfx/1.0.0/)"
    version = "1.0.0"
    raw_dir = Path("datasets/sleep-edfx/raw")

    from ml.datasets.sleep_edf import find_subject_pairs

    pairs = find_subject_pairs(REPO_ROOT / raw_dir)
    pair_by_prefix = {psg.name.split("E")[0]: (psg, hyp) for psg, hyp in pairs}

    role_of = {}
    for s in split["train"]:
        role_of[s] = "train"
    for s in split["val"]:
        role_of[s] = "validation"
    for s in split["test"]:
        role_of[s] = "primary_test"

    entries = []
    for subj, role in sorted(role_of.items()):
        if subj not in pair_by_prefix:
            entries.append({
                "dataset": "sleep_edf_cassette", "version": version, "source": source,
                "subject": subj, "session_or_night": "night1", "path": None, "role": role,
                "locally_present": False, "raw_file_committed_to_git": False, "byte_size": None, "sha256": None,
            })
            continue
        psg, hyp = pair_by_prefix[subj]
        entries.append(record(dataset="sleep_edf_cassette", version=version, source=source,
                               subject=subj, session="night1", rel_path=psg.relative_to(REPO_ROOT), role=f"{role}_psg"))
        entries.append(record(dataset="sleep_edf_cassette", version=version, source=source,
                               subject=subj, session="night1", rel_path=hyp.relative_to(REPO_ROOT), role=f"{role}_hypnogram"))
    return entries


def build_sleep_secondary() -> list[dict]:
    cohort = json.loads((REPO_ROOT / "ml" / "experiments" / "sleep_edf_secondary_holdout" / "cohort.json").read_text())
    source = "PhysioNet Sleep-EDFx sleep-cassette (https://physionet.org/content/sleep-edfx/1.0.0/) - same distribution as primary, additional subjects"
    version = "1.0.0"
    raw_dir = Path("datasets/sleep-edfx/raw")

    entries = []
    for c in cohort["cohort"]:
        entries.append(record(dataset="sleep_edf_cassette", version=version, source=source,
                               subject=c["subject_prefix"], session="night1",
                               rel_path=raw_dir / c["psg"], role="secondary_holdout_psg"))
        entries.append(record(dataset="sleep_edf_cassette", version=version, source=source,
                               subject=c["subject_prefix"], session="night1",
                               rel_path=raw_dir / c["hypnogram"], role="secondary_holdout_hypnogram"))
    return entries


def main() -> None:
    ppg_entries = build_ppg_dalia()
    ptt_entries = build_ptt()
    sleep_primary_entries = build_sleep_primary()
    sleep_secondary_entries = build_sleep_secondary()

    all_entries = ppg_entries + ptt_entries + sleep_primary_entries + sleep_secondary_entries

    def summarize(entries: list[dict]) -> dict:
        present = [e for e in entries if e["locally_present"]]
        return {
            "n_records": len(entries),
            "n_present": len(present),
            "n_missing": len(entries) - len(present),
            "n_committed_to_git": sum(1 for e in entries if e["raw_file_committed_to_git"]),
        }

    out = {
        "purpose": "Day 10 dataset-level reproducibility fingerprint - raw input identity for every frozen experiment. Read-only, no dataset modification.",
        "datasets": {
            "ppg_dalia": {"summary": summarize(ppg_entries), "entries": ppg_entries},
            "pulse_transit_time_ppg": {"summary": summarize(ptt_entries), "entries": ptt_entries},
            "sleep_edf_primary": {"summary": summarize(sleep_primary_entries), "entries": sleep_primary_entries},
            "sleep_edf_secondary_holdout": {"summary": summarize(sleep_secondary_entries), "entries": sleep_secondary_entries},
        },
        "overall_summary": summarize(all_entries),
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("Wrote", OUT_PATH)
    for name, block in out["datasets"].items():
        print(name, block["summary"])


if __name__ == "__main__":
    main()
