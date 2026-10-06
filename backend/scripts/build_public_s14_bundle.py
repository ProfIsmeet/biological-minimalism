"""Build a memory-bounded, provenance-rich S14 presentation bundle.

The official synchronized pickle contains channels the public application never
reads.  This tool preserves the exact arrays used by the accepted replay and
Model B paths while omitting unrelated channels from the deployment artifact.
It must only be run against a trusted, hash-verified official PPG-DaLiA pickle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import zipfile
from pathlib import Path
from typing import Any

import numpy as np

SUBJECT = "S14"
SOURCE_SHA256 = "c192b9090ac3c0107000d8424c038ccd11292cded1f6c46c97e2cae85c725392"
SELECTED_CHANNELS = {
    "wrist_bvp": ("signal", "wrist", "BVP"),
    "wrist_acc": ("signal", "wrist", "ACC"),
    "chest_ecg": ("signal", "chest", "ECG"),
    "wrist_temp": ("signal", "wrist", "TEMP"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nested_value(payload: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = payload
    for key in path:
        if not isinstance(value, dict) or key not in value:
            raise ValueError(f"Official S14 payload is missing {'/'.join(path)}")
        value = value[key]
    return value


def array_sha256(array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array)
    return hashlib.sha256(memoryview(contiguous).cast("B")).hexdigest()


def build_bundle(source: Path, output: Path) -> dict[str, Any]:
    actual_source_hash = sha256_file(source)
    if actual_source_hash != SOURCE_SHA256:
        raise ValueError("Source S14 pickle SHA-256 does not match the accepted official artifact")

    with source.open("rb") as stream:
        raw = pickle.load(stream, encoding="latin1")  # noqa: S301 - trusted hash-pinned UCI artifact
    if not isinstance(raw, dict) or str(raw.get("subject", "")).upper() != SUBJECT:
        raise ValueError("Source pickle does not identify itself as S14")

    selected: dict[str, dict[str, np.ndarray]] = {"wrist": {}, "chest": {}}
    channels: dict[str, dict[str, Any]] = {}
    for name, path in SELECTED_CHANNELS.items():
        array = np.asarray(nested_value(raw, path))
        selected[path[1]][path[2]] = array
        channels[name] = {
            "source_path": "/".join(path),
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "sha256": array_sha256(array),
        }

    reduced = {"subject": SUBJECT, "signal": selected}
    manifest = {
        "schema_version": 1,
        "dataset": "PPG-DaLiA",
        "license": "CC BY 4.0",
        "source_url": "https://doi.org/10.24432/C53890",
        "subject": SUBJECT,
        "official_s14_pickle_sha256": actual_source_hash,
        "derivation": "Exact selected arrays only; no resampling, filtering, conversion, or value change.",
        "channels": channels,
    }
    attribution = (
        "PPG-DaLiA (CC BY 4.0)\n"
        "Reiss, A., Indlekofer, I., & Schmidt, P. (2019).\n"
        "UCI Machine Learning Repository. https://doi.org/10.24432/C53890\n"
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".partial")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            with archive.open(f"PPG_FieldStudy/{SUBJECT}/{SUBJECT}.pkl", "w") as stream:
                pickle.dump(reduced, stream, protocol=pickle.HIGHEST_PROTOCOL)
            archive.writestr("DERIVATION.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            archive.writestr("ATTRIBUTION.txt", attribution)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)

    manifest["bundle_sha256"] = sha256_file(output)
    manifest["bundle_bytes"] = output.stat().st_size
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Trusted official S14.pkl")
    parser.add_argument("output", type=Path, help="Output S14 presentation zip")
    args = parser.parse_args()
    print(json.dumps(build_bundle(args.source, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
