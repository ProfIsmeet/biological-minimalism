"""Core enums shared across the API."""

from __future__ import annotations

from enum import StrEnum


class MissionMode(StrEnum):
    """Operational context for the mock data engine.

    Each mode changes the noise profile and baseline risk of the simulated
    telemetry (see `engine/mock_data_engine.py`). This is a design proposal
    for demonstration purposes, not a validated model of real mission risk.
    """

    EARTH_ORBIT = "earth_orbit"
    LUNAR_SURFACE = "lunar_surface"
    DEEP_SPACE = "deep_space"
    SOLAR_EVENT = "solar_event"


class SensorName(StrEnum):
    EEG = "eeg"
    PPG = "ppg"
    TEMPERATURE = "temperature"
    BIOIMPEDANCE = "bioimpedance"


class SensorStatus(StrEnum):
    NOMINAL = "nominal"
    DEGRADED = "degraded"
    OFFLINE = "offline"
