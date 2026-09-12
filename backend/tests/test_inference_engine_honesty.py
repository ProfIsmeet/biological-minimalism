"""Audit M10/M31 + §50: the Torch inference engine must NOT advertise real
inference, because `confidence_and_contribution` returns mock snapshot values
rather than a model forward pass. This guards against a future edit silently
re-introducing a false real-inference claim."""

from __future__ import annotations

from app.ml.inference import RuleBasedInferenceEngine, TorchInferenceEngine, create_inference_engine


def test_torch_engine_does_not_claim_real_inference() -> None:
    assert TorchInferenceEngine.runs_real_inference is False
    assert "mock" in TorchInferenceEngine.name.lower()
    doc = " ".join((TorchInferenceEngine.__doc__ or "").split())
    assert "does NOT yet run a forward pass" in doc


def test_default_engine_is_rule_based_without_checkpoint() -> None:
    # With no trained checkpoint present, the factory must not pretend to run a model.
    engine = create_inference_engine()
    assert isinstance(engine, RuleBasedInferenceEngine)
