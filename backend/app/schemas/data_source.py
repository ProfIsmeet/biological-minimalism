"""Schemas for telemetry provenance and dataset-replay control."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class DataSourceType(StrEnum):
    SYNTHETIC = "synthetic"
    DATASET_REPLAY = "dataset_replay"


class ReplayPlaybackState(StrEnum):
    UNLOADED = "unloaded"
    PAUSED = "paused"
    PLAYING = "playing"
    ENDED = "ended"


class ChannelMetadata(BaseModel):
    name: str
    sample_rate_hz: float = Field(..., gt=0)
    device: str
    role: str
    axes: list[str]
    units: str


class TelemetrySourceMetadata(BaseModel):
    source_type: DataSourceType
    display_label: str
    dataset_name: str | None = None
    subject_id: str | None = None
    replay_position_seconds: float | None = Field(default=None, ge=0)
    duration_seconds: float | None = Field(default=None, ge=0)
    playback_state: ReplayPlaybackState | None = None
    playback_speed: float | None = Field(default=None, gt=0)
    end_behavior: str | None = None
    license: str | None = None
    source_url: str | None = None
    available_channels: list[str] = Field(default_factory=list)
    unavailable_channels: list[str] = Field(default_factory=list)


class RawChannelBatch(BaseModel):
    dataset_name: str
    subject_id: str
    channel_name: str
    device: str
    role: str
    axes: list[str]
    units: str
    sample_rate_hz: float = Field(..., gt=0)
    sample_start_index: int = Field(..., ge=0)
    start_timestamp_seconds: float = Field(..., ge=0)
    end_timestamp_seconds: float = Field(..., ge=0)
    samples: list[float] | list[list[float]]


class DataSourceStatus(BaseModel):
    source_type: DataSourceType
    dataset_configured: bool
    dataset_name: str | None = None
    subject_id: str | None = None
    replay_position_seconds: float | None = Field(default=None, ge=0)
    duration_seconds: float | None = Field(default=None, ge=0)
    playback_state: ReplayPlaybackState | None = None
    playback_speed: float | None = Field(default=None, gt=0)
    end_behavior: str | None = None
    channels: list[ChannelMetadata] = Field(default_factory=list)


class AvailableSubjectsResponse(BaseModel):
    dataset_name: str
    subjects: list[str]


class LoadReplayRequest(BaseModel):
    subject_id: str
    channels: list[str] | None = None


class SetPlaybackSpeedRequest(BaseModel):
    speed: float
