"""Raw, subject-preserving access to the original PPG-DaLiA distribution.

This module owns the single interpretation of the original synchronized
per-subject pickle.  The offline ML loader imports it through
``backend.app.data``; the running backend imports it through ``app.data``.
Only one subject pickle is materialized at a time.

Python pickle files can execute code while loading.  ``data_path`` must point
to the official UCI PPG-DaLiA distribution or a trusted extraction of it.
"""

from __future__ import annotations

import pickle
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

DATASET_NAME = "PPG-DaLiA"
DATASET_LICENSE = "CC BY 4.0"
DATASET_SOURCE_URL = "https://doi.org/10.24432/C53890"
ALL_SUBJECTS = tuple(f"S{i}" for i in range(1, 16))


class PpgDaliaError(RuntimeError):
    """Base class for controlled PPG-DaLiA loading failures."""


class PpgDaliaPathError(PpgDaliaError):
    """The configured archive/extraction path cannot be used."""


class PpgDaliaSubjectError(PpgDaliaError):
    """A requested subject is absent or internally mislabeled."""


class PpgDaliaChannelError(PpgDaliaError):
    """A requested channel is unsupported or malformed."""


@dataclass(frozen=True)
class ChannelDefinition:
    name: str
    pickle_path: tuple[str, ...]
    sample_rate_hz: float
    device: str
    role: str
    axes: tuple[str, ...]
    units: str


CHANNEL_DEFINITIONS: dict[str, ChannelDefinition] = {
    "wrist_bvp": ChannelDefinition(
        name="wrist_bvp",
        pickle_path=("signal", "wrist", "BVP"),
        sample_rate_hz=64.0,
        device="Empatica E4 (wrist)",
        role="physiological",
        axes=("bvp",),
        units="device units",
    ),
    "wrist_acc": ChannelDefinition(
        name="wrist_acc",
        pickle_path=("signal", "wrist", "ACC"),
        sample_rate_hz=32.0,
        device="Empatica E4 (wrist)",
        role="context_artifact_reference",
        axes=("x", "y", "z"),
        units="device units",
    ),
    "wrist_eda": ChannelDefinition(
        name="wrist_eda",
        pickle_path=("signal", "wrist", "EDA"),
        sample_rate_hz=4.0,
        device="Empatica E4 (wrist)",
        role="physiological",
        axes=("eda",),
        units="device units",
    ),
    "wrist_temp": ChannelDefinition(
        name="wrist_temp",
        pickle_path=("signal", "wrist", "TEMP"),
        sample_rate_hz=4.0,
        device="Empatica E4 (wrist)",
        role="physiological",
        axes=("temperature",),
        units="degrees Celsius",
    ),
    "chest_ecg": ChannelDefinition(
        name="chest_ecg",
        pickle_path=("signal", "chest", "ECG"),
        sample_rate_hz=700.0,
        device="RespiBAN (chest)",
        role="physiological_ground_truth_reference",
        axes=("ecg",),
        units="device units",
    ),
    "chest_acc": ChannelDefinition(
        name="chest_acc",
        pickle_path=("signal", "chest", "ACC"),
        sample_rate_hz=700.0,
        device="RespiBAN (chest)",
        role="context_artifact_reference",
        axes=("x", "y", "z"),
        units="device units",
    ),
    "chest_resp": ChannelDefinition(
        name="chest_resp",
        pickle_path=("signal", "chest", "Resp"),
        sample_rate_hz=700.0,
        device="RespiBAN (chest)",
        role="physiological",
        axes=("respiration",),
        units="device units",
    ),
    "chest_temp": ChannelDefinition(
        name="chest_temp",
        pickle_path=("signal", "chest", "Temp"),
        sample_rate_hz=700.0,
        device="RespiBAN (chest)",
        role="physiological",
        axes=("temperature",),
        units="device units",
    ),
    "chest_eda": ChannelDefinition(
        name="chest_eda",
        pickle_path=("signal", "chest", "EDA"),
        sample_rate_hz=700.0,
        device="RespiBAN (chest)",
        role="physiological",
        axes=("eda",),
        units="device units",
    ),
    "chest_emg": ChannelDefinition(
        name="chest_emg",
        pickle_path=("signal", "chest", "EMG"),
        sample_rate_hz=700.0,
        device="RespiBAN (chest)",
        role="physiological",
        axes=("emg",),
        units="device units",
    ),
}

# The replay UI starts with the channels needed for the PPG+IMU research
# question plus its same-session ECG reference and recorded wrist temperature.
DEFAULT_REPLAY_CHANNELS = ("wrist_bvp", "wrist_acc", "chest_ecg", "wrist_temp")


@dataclass(frozen=True)
class RawChannel:
    definition: ChannelDefinition
    samples: np.ndarray

    @property
    def duration_seconds(self) -> float:
        return len(self.samples) / self.definition.sample_rate_hz


@dataclass(frozen=True)
class RawSubjectRecording:
    dataset_name: str
    subject_id: str
    channels: dict[str, RawChannel]
    duration_seconds: float
    license: str
    source_url: str


def normalize_subject_id(subject_id: str) -> str:
    normalized = subject_id.strip().upper()
    if normalized.isdigit():
        normalized = f"S{int(normalized)}"
    match = re.fullmatch(r"S(\d+)", normalized)
    if match is None or normalized not in ALL_SUBJECTS:
        raise PpgDaliaSubjectError(
            f"Invalid PPG-DaLiA subject {subject_id!r}; expected one of "
            f"{', '.join(ALL_SUBJECTS)}."
        )
    return normalized


def _pickle_entry(subject_id: str) -> str:
    return f"PPG_FieldStudy/{subject_id}/{subject_id}.pkl"


def _load_from_archive(archive_path: Path, subject_id: str) -> dict[str, Any]:
    entry = _pickle_entry(subject_id)
    try:
        with zipfile.ZipFile(archive_path) as outer:
            if "data.zip" in outer.namelist():
                with outer.open("data.zip") as nested_stream:
                    with zipfile.ZipFile(nested_stream) as nested:
                        with nested.open(entry) as subject_stream:
                            return pickle.load(subject_stream, encoding="latin1")
            with outer.open(entry) as subject_stream:
                return pickle.load(subject_stream, encoding="latin1")
    except KeyError as exc:
        raise PpgDaliaSubjectError(
            f"Subject {subject_id} was not found in PPG-DaLiA archive {archive_path}."
        ) from exc
    except (OSError, pickle.UnpicklingError, zipfile.BadZipFile, EOFError, ValueError) as exc:
        raise PpgDaliaPathError(
            f"Could not read PPG-DaLiA archive {archive_path}: {exc}"
        ) from exc


def _field_study_root(data_path: Path) -> Path:
    direct = data_path / "PPG_FieldStudy"
    if direct.is_dir():
        return direct
    if data_path.name == "PPG_FieldStudy" and data_path.is_dir():
        return data_path
    return data_path


def _load_from_directory(data_path: Path, subject_id: str) -> dict[str, Any]:
    subject_path = _field_study_root(data_path) / subject_id / f"{subject_id}.pkl"
    if not subject_path.is_file():
        raise PpgDaliaSubjectError(
            f"Subject {subject_id} was not found at expected path {subject_path}."
        )
    try:
        with subject_path.open("rb") as subject_stream:
            return pickle.load(subject_stream, encoding="latin1")
    except (OSError, pickle.UnpicklingError, EOFError, ValueError) as exc:
        raise PpgDaliaPathError(
            f"Could not read PPG-DaLiA subject file {subject_path}: {exc}"
        ) from exc


def load_subject_payload(data_path: str | Path, subject_id: str) -> dict[str, Any]:
    path = Path(data_path).expanduser()
    subject = normalize_subject_id(subject_id)
    if not path.exists():
        raise PpgDaliaPathError(f"Configured PPG-DaLiA path does not exist: {path}")
    raw = _load_from_archive(path, subject) if path.is_file() else _load_from_directory(path, subject)
    if not isinstance(raw, dict):
        raise PpgDaliaPathError(
            f"PPG-DaLiA subject {subject} did not contain the expected dictionary payload."
        )
    embedded_subject = str(raw.get("subject", "")).upper()
    if embedded_subject != subject:
        raise PpgDaliaSubjectError(
            f"Requested {subject}, but the recording identifies itself as "
            f"{raw.get('subject')!r}; refusing to mix or relabel subjects."
        )
    return raw


def _nested_value(raw: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = raw
    for key in path:
        if not isinstance(value, dict) or key not in value:
            raise KeyError("/".join(path))
        value = value[key]
    return value


def _validated_channel(raw: dict[str, Any], definition: ChannelDefinition) -> np.ndarray:
    try:
        samples = np.asarray(_nested_value(raw, definition.pickle_path))
    except KeyError as exc:
        raise PpgDaliaChannelError(
            f"Recording is missing supported channel {definition.name} "
            f"at {'/'.join(definition.pickle_path)}."
        ) from exc

    if samples.ndim == 1:
        samples = samples.reshape(-1, 1)
    if samples.ndim != 2 or samples.shape[1] != len(definition.axes):
        raise PpgDaliaChannelError(
            f"Channel {definition.name} has shape {samples.shape}; expected "
            f"(samples, {len(definition.axes)})."
        )
    if len(samples) == 0:
        raise PpgDaliaChannelError(f"Channel {definition.name} contains no samples.")
    # Read-only views make accidental in-place alteration of a real recording
    # fail loudly while avoiding a full high-rate signal copy.
    samples.setflags(write=False)
    return samples


def load_raw_subject(
    data_path: str | Path,
    subject_id: str,
    channel_names: tuple[str, ...] | list[str] = DEFAULT_REPLAY_CHANNELS,
) -> RawSubjectRecording:
    subject = normalize_subject_id(subject_id)
    requested = tuple(dict.fromkeys(channel_names))
    if not requested:
        raise PpgDaliaChannelError("At least one PPG-DaLiA channel must be selected.")
    unsupported = [name for name in requested if name not in CHANNEL_DEFINITIONS]
    if unsupported:
        raise PpgDaliaChannelError(
            f"Unsupported PPG-DaLiA channel(s): {', '.join(unsupported)}. "
            f"Supported channels: {', '.join(CHANNEL_DEFINITIONS)}."
        )

    raw = load_subject_payload(data_path, subject)
    channels = {
        name: RawChannel(
            definition=CHANNEL_DEFINITIONS[name],
            samples=_validated_channel(raw, CHANNEL_DEFINITIONS[name]),
        )
        for name in requested
    }
    # The synchronized pickle uses a common t=0.  Stopping at the shortest
    # selected stream keeps every emitted batch inside that common interval.
    duration = min(channel.duration_seconds for channel in channels.values())
    return RawSubjectRecording(
        dataset_name=DATASET_NAME,
        subject_id=subject,
        channels=channels,
        duration_seconds=duration,
        license=DATASET_LICENSE,
        source_url=DATASET_SOURCE_URL,
    )


def list_available_subjects(data_path: str | Path) -> list[str]:
    path = Path(data_path).expanduser()
    if not path.exists():
        raise PpgDaliaPathError(f"Configured PPG-DaLiA path does not exist: {path}")

    if path.is_dir():
        root = _field_study_root(path)
        subjects = [
            subject
            for subject in ALL_SUBJECTS
            if (root / subject / f"{subject}.pkl").is_file()
        ]
        return subjects

    try:
        with zipfile.ZipFile(path) as outer:
            if "data.zip" in outer.namelist():
                with outer.open("data.zip") as nested_stream:
                    with zipfile.ZipFile(nested_stream) as nested:
                        names = nested.namelist()
            else:
                names = outer.namelist()
    except (OSError, zipfile.BadZipFile) as exc:
        raise PpgDaliaPathError(f"Could not inspect PPG-DaLiA archive {path}: {exc}") from exc

    found = {
        match.group(1)
        for name in names
        if (match := re.fullmatch(r"PPG_FieldStudy/(S\d+)/\1\.pkl", name))
    }
    return [subject for subject in ALL_SUBJECTS if subject in found]
