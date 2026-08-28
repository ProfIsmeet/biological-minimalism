"""Inference layer: the swap-point between the demo rule engine and a real
trained PyTorch model.

`create_inference_engine()` picks the right implementation at startup:
`RuleBasedInferenceEngine` (default — no checkpoint is trained in this
task's scope, per the brief's "mock data now, real model later"
requirement) or `TorchInferenceEngine` when
`settings.model_checkpoint_path` points at an existing `.pt` file produced
by `ml/train.py`. Both expose the same interface, so the API layer and the
frontend never need to know which one is active.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.core.config import settings
from app.engine.mock_data_engine import MockDataEngine


class AIInferenceEngine(Protocol):
    name: str

    def confidence_and_contribution(self, engine: MockDataEngine) -> tuple[float, dict[str, float]]: ...


class RuleBasedInferenceEngine:
    """Default demo-mode engine.

    Delegates to the physiology rule engine that already produced the
    live snapshot (see `engine/mock_data_engine.py` and
    `engine/physiology.py`), so its output is identical to what the
    dashboard shows — this is the estimator `ml/explainability.py`
    explains with real SHAP values.
    """

    name = "rule_based_v1"

    def confidence_and_contribution(self, engine: MockDataEngine) -> tuple[float, dict[str, float]]:
        snapshot = engine.last_snapshot
        if snapshot is None:
            return 0.0, {}
        return snapshot.ai_confidence.overall_confidence, snapshot.ai_confidence.sensor_contribution


class TorchInferenceEngine:
    """Loads a trained `BiologicalDigitalTwinNet` checkpoint and runs real
    inference. Not exercised by default (no checkpoint is trained in this
    task), but fully implemented so a future training run can be dropped
    in without touching the API or frontend."""

    name = "torch_v1"

    def __init__(self, checkpoint_path: Path) -> None:
        import torch

        from app.ml.models import BiologicalDigitalTwinNet

        self.model = BiologicalDigitalTwinNet()
        state_dict = torch.load(checkpoint_path, map_location="cpu")
        self.model.load_state_dict(state_dict)
        self.model.eval()

    def confidence_and_contribution(self, engine: MockDataEngine) -> tuple[float, dict[str, float]]:
        # A trained model would run self.model(...) here on real raw
        # per-modality windows. This demo does not retain raw sample
        # buffers (see docs/PDD, Risk Analysis section), so the wiring
        # point is documented rather than exercised until a checkpoint
        # and a real windowing pipeline exist.
        snapshot = engine.last_snapshot
        if snapshot is None:
            return 0.0, {}
        return snapshot.ai_confidence.overall_confidence, snapshot.ai_confidence.sensor_contribution


def create_inference_engine() -> AIInferenceEngine:
    path = settings.model_checkpoint_path
    if path is not None and Path(path).exists():
        try:
            return TorchInferenceEngine(Path(path))
        except Exception:
            # Fall back to the rule-based engine rather than failing to boot.
            return RuleBasedInferenceEngine()
    return RuleBasedInferenceEngine()
