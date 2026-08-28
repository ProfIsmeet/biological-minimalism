"""Explainability layer — genuine SHAP over the physiology engine.

`physiology.py`'s scoring functions are treated as "the model": each is a
transparent, fixed function of a small feature vector, so
`shap.KernelExplainer` (a model-agnostic, perturbation-based Shapley-value
estimator) can compute real feature attributions for it without needing a
trained neural network first. This gives honest, computed explanations of
the exact numbers the dashboard shows — the natural-language summary is
generated from the actual top SHAP contributors, never hand-written.

Two targets are wired up:
- "ai_confidence": explains the overall AI confidence score in terms of
  each sensor's signal quality. This is what powers Demo 1 (sensor
  failure) — "AI Confidence dropped because PPG signal quality fell to 0%."
- "fatigue_risk": explains the fatigue score in terms of HRV, EEG band
  powers, cognitive load and mission-mode stress — matching the style of
  example given in the brief ("Fatigue risk increased because HRV
  decreased while cognitive workload remained elevated.").
"""

from __future__ import annotations

import time

import numpy as np
import shap

from app.core.config import settings
from app.engine import physiology as phys
from app.schemas.explanation import AIExplanation, FeatureContribution

CONFIDENCE_FEATURES = ["ppg_quality", "eeg_quality", "temperature_quality", "bioimpedance_quality"]
FATIGUE_FEATURES = ["hrv_rmssd_ms", "eeg_theta", "eeg_alpha", "cognitive_load", "mode_risk_bias"]

_FEATURE_LABELS = {
    "ppg_quality": "PPG signal quality",
    "eeg_quality": "EEG signal quality",
    "temperature_quality": "Temperature signal quality",
    "bioimpedance_quality": "Bio-impedance signal quality",
    "hrv_rmssd_ms": "Heart rate variability (HRV)",
    "eeg_theta": "EEG theta power",
    "eeg_alpha": "EEG alpha power",
    "cognitive_load": "Cognitive workload",
    "mode_risk_bias": "Mission-mode stress level",
}

_SIGNIFICANCE_THRESHOLD = 0.5


def _confidence_fn(x: np.ndarray) -> np.ndarray:
    out = np.zeros(x.shape[0])
    for i, row in enumerate(x):
        quality = dict(zip(["ppg", "eeg", "temperature", "bioimpedance"], row))
        confidence, _ = phys.fused_confidence(quality)
        out[i] = confidence
    return out


def _fatigue_fn(x: np.ndarray) -> np.ndarray:
    out = np.zeros(x.shape[0])
    for i, row in enumerate(x):
        hrv, theta, alpha, cognitive_load, _mode_bias = row
        out[i] = phys.fatigue_score(hrv, cognitive_load, theta, alpha)
    return out


class AIExplainer:
    """Owns the two SHAP explainers and turns their output into
    `AIExplanation` objects. Construction fits both KernelExplainers once
    (on synthetic background data spanning plausible operating ranges),
    which is the only "training" step involved — cheap and deterministic
    given `settings.random_seed`.
    """

    def __init__(self, rng: np.random.Generator | None = None) -> None:
        rng = rng or np.random.default_rng(settings.random_seed)
        n = settings.shap_background_samples

        confidence_bg = rng.uniform(0.0, 1.0, size=(n, len(CONFIDENCE_FEATURES)))
        self._confidence_bg_mean = confidence_bg.mean(axis=0)
        self._confidence_explainer = shap.KernelExplainer(_confidence_fn, confidence_bg)

        fatigue_bg = np.column_stack(
            [
                rng.uniform(15, 100, size=n),  # hrv_rmssd_ms
                rng.uniform(0.05, 0.4, size=n),  # eeg_theta
                rng.uniform(0.1, 0.45, size=n),  # eeg_alpha
                rng.uniform(0, 100, size=n),  # cognitive_load
                rng.uniform(0, 30, size=n),  # mode_risk_bias
            ]
        )
        self._fatigue_bg_mean = fatigue_bg.mean(axis=0)
        self._fatigue_explainer = shap.KernelExplainer(_fatigue_fn, fatigue_bg)

    def explain_confidence(self, quality: dict[str, float]) -> AIExplanation:
        x = np.array([[quality.get(s, 1.0) for s in ("ppg", "eeg", "temperature", "bioimpedance")]])
        shap_values = np.asarray(self._confidence_explainer.shap_values(x, silent=True))[0]
        predicted = float(_confidence_fn(x)[0])
        base_value = float(self._confidence_explainer.expected_value)
        # Positive SHAP = raises confidence = GOOD, so it is a "risk-decreasing" contribution.
        bad_direction_values = -shap_values
        return self._build(
            target="ai_confidence",
            feature_names=CONFIDENCE_FEATURES,
            values=x[0],
            bg_mean=self._confidence_bg_mean,
            shap_values=shap_values,
            bad_direction_values=bad_direction_values,
            base_value=base_value,
            predicted=predicted,
            as_percent=True,
        )

    def explain_fatigue(self, hrv: float, theta: float, alpha: float, cognitive_load: float, mode_risk_bias: float) -> AIExplanation:
        x = np.array([[hrv, theta, alpha, cognitive_load, mode_risk_bias]])
        shap_values = np.asarray(self._fatigue_explainer.shap_values(x, silent=True))[0]
        predicted = float(_fatigue_fn(x)[0])
        base_value = float(self._fatigue_explainer.expected_value)
        return self._build(
            target="fatigue_risk",
            feature_names=FATIGUE_FEATURES,
            values=x[0],
            bg_mean=self._fatigue_bg_mean,
            shap_values=shap_values,
            bad_direction_values=shap_values,
            base_value=base_value,
            predicted=predicted,
            as_percent=False,
        )

    def _build(
        self,
        *,
        target: str,
        feature_names: list[str],
        values: np.ndarray,
        bg_mean: np.ndarray,
        shap_values: np.ndarray,
        bad_direction_values: np.ndarray,
        base_value: float,
        predicted: float,
        as_percent: bool,
    ) -> AIExplanation:
        contributions: list[FeatureContribution] = []
        trends: dict[str, str] = {}
        for name, value, bad_sv in zip(feature_names, values, bad_direction_values):
            direction = "increased_risk" if bad_sv > _SIGNIFICANCE_THRESHOLD else "decreased_risk" if bad_sv < -_SIGNIFICANCE_THRESHOLD else "neutral"
            contributions.append(
                FeatureContribution(feature=_FEATURE_LABELS.get(name, name), value=float(value), shap_value=float(bad_sv), direction=direction)
            )

        for name, value, mean in zip(feature_names, values, bg_mean):
            label = _FEATURE_LABELS.get(name, name)
            if as_percent:
                # Signal-quality features have a natural reference point (1.0
                # = fully nominal), not the synthetic background's mean, so
                # we describe them relative to that ceiling instead.
                if value >= 0.95:
                    trends[label] = f"remains nominal ({value * 100:.0f}%)"
                elif value <= 0.05:
                    trends[label] = "dropped to 0%"
                else:
                    trends[label] = f"degraded to {value * 100:.0f}%"
            else:
                if value < mean * 0.9:
                    trends[label] = "decreased"
                elif value > mean * 1.1:
                    trends[label] = "increased"
                else:
                    trends[label] = "stayed near its typical level"

        contributions.sort(key=lambda c: abs(c.shap_value), reverse=True)
        summary = _narrate(target, contributions, trends, predicted)

        return AIExplanation(
            target=target,
            summary_text=summary,
            base_value=round(base_value, 2),
            predicted_value=round(predicted, 2),
            contributions=contributions,
            generated_at=time.time(),
        )


def _narrate(target: str, contributions: list[FeatureContribution], trends: dict[str, str], predicted: float) -> str:
    significant = [c for c in contributions if c.direction != "neutral"][:2]

    if target == "ai_confidence":
        if not significant:
            return f"AI Confidence is {predicted:.0f}%, supported by nominal signal quality across all four sensors."
        clauses = [f"{c.feature} {trends[c.feature]}" for c in significant]
        return f"AI Confidence is {predicted:.0f}% because " + " while ".join(clauses) + "."

    if not significant:
        return f"Fatigue risk is {predicted:.0f}/100, with no single dominant driver at this moment."
    clauses = [f"{c.feature.lower()} {trends[c.feature]}" for c in significant]
    return f"Fatigue risk is {predicted:.0f}/100 because " + " while ".join(clauses) + "."


explainer = AIExplainer()
