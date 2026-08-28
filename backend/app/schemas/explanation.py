"""Explainability schemas — real SHAP-derived output, see `ml/explainability.py`."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FeatureContribution(BaseModel):
    feature: str
    value: float = Field(..., description="The feature's current value")
    shap_value: float = Field(..., description="Signed contribution to the model output (SHAP value)")
    direction: str = Field(..., description="'increased_risk' | 'decreased_risk' | 'neutral'")


class AIExplanation(BaseModel):
    target: str = Field(..., description="Which output this explanation is for, e.g. 'fatigue_risk'")
    summary_text: str = Field(..., description="Natural-language explanation generated from the SHAP values")
    base_value: float = Field(..., description="SHAP expected value (average model output over the background set)")
    predicted_value: float
    contributions: list[FeatureContribution]
    generated_at: float = Field(..., description="Unix epoch seconds")
