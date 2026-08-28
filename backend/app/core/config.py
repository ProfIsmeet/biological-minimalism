"""Application configuration.

All values can be overridden via environment variables (see `.env.example`
in the backend root). Defaults are tuned for a smooth local demo.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BIOMIN_", env_file=".env", extra="ignore")

    app_name: str = "Biological Minimalism Mission Control API"
    api_version: str = "0.1.0"

    # CORS
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Simulation engine
    tick_interval_seconds: float = 0.5
    """How often the mock data engine advances internal state."""

    telemetry_broadcast_hz: float = 2.0
    """How often WebSocket clients receive a telemetry frame."""

    rolling_history_length: int = 600
    """Number of ticks kept in-memory for trend charts (~5 minutes at 2Hz)."""

    ppg_waveform_points_per_frame: int = 64
    """Number of PPG waveform samples included in each telemetry frame, for charting."""

    ppg_sample_rate_hz: float = 128.0
    """Synthetic sampling rate used when generating the PPG/ECG-like waveforms."""

    # ML
    model_checkpoint_path: Path | None = None
    """Optional path to a trained BiologicalDigitalTwinNet checkpoint (.pt).

    When set and the file exists, AIInferenceEngine loads the real PyTorch
    model instead of the rule-based demo estimator. Unset by default because
    no checkpoint has been trained in this task's scope (mock-data only).
    """

    shap_background_samples: int = 80
    """Number of synthetic background samples used by the SHAP KernelExplainer."""

    random_seed: int = 42


settings = Settings()
