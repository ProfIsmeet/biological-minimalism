"""`/ai/explanation` — genuine SHAP-derived natural-language explanation."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query

from app.engine.mock_data_engine import engine
from app.ml.explainability import explainer
from app.schemas.explanation import AIExplanation

router = APIRouter()


@router.get("/explanation", response_model=AIExplanation, summary="Explain the current AI confidence or fatigue estimate")
def get_ai_explanation(
    target: Literal["ai_confidence", "fatigue_risk"] = Query("ai_confidence"),
) -> AIExplanation:
    snapshot = engine.last_snapshot or engine.tick(0.5)

    if target == "ai_confidence":
        return explainer.explain_confidence(engine.signal_quality())

    features = engine.feature_vector()
    return explainer.explain_fatigue(
        hrv=features["hrv_rmssd_ms"],
        theta=features["eeg_theta"],
        alpha=features["eeg_alpha"],
        cognitive_load=snapshot.cognitive.cognitive_load,
        mode_risk_bias=features["mode_risk_bias"],
    )
