"""Application configuration.

All values can be overridden via environment variables (see `.env.example`
in the backend root). Defaults are tuned for a smooth local demo.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BIOMIN_", env_file=".env", extra="ignore")

    app_name: str = "Biological Minimalism Mission Control API"
    api_version: str = "0.1.0"

    # CORS
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    """Exact browser origins permitted to call the API (used by CORSMiddleware).

    Override without editing this source via the ``BIOMIN_ALLOWED_ORIGINS``
    environment variable, encoded as a JSON array of exact origins, e.g.
    ``BIOMIN_ALLOWED_ORIGINS='["https://demo.example.org"]'``. Because
    ``allow_credentials=True`` (see ``app/main.py``), each entry must be an
    exact scheme://host[:port] origin — a wildcard would be both insecure and
    rejected by the browser for credentialed requests. A malformed value
    (not a JSON list) fails fast at startup rather than silently widening
    access. This is the allowed *browser* origin list; it is distinct from the
    frontend's own URL and from the backend's bind address.
    """

    @field_validator("allowed_origins")
    @classmethod
    def _reject_unsafe_cors_origins(cls, value: list[str]) -> list[str]:
        """Fail closed on empty, blank, or wildcard CORS origins.

        Deterministic and side-effect free: trims surrounding whitespace and
        refuses to widen access to ``*`` (or any blank entry). Callers must
        list explicit browser origins.
        """
        cleaned = [origin.strip() for origin in value]
        if not cleaned:
            raise ValueError("allowed_origins must list at least one exact browser origin")
        for origin in cleaned:
            if not origin:
                raise ValueError("allowed_origins must not contain blank entries")
            if origin == "*":
                raise ValueError(
                    "wildcard '*' is not permitted for allowed_origins; list exact "
                    "browser origins (credentials are enabled, so origins must be explicit)"
                )
        return cleaned

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

    ppg_dalia_path: Path | None = None
    """Official PPG-DaLiA zip or extracted PPG_FieldStudy path for replay."""

    ppg_dalia_hr_checkpoint_path: Path = (
        REPOSITORY_ROOT / "ml" / "checkpoints" / "model_b_ppg_plus_imu_ppg_dalia.pt"
    )
    """Validated Model B checkpoint used only for PPG-DaLiA replay HR inference."""

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
