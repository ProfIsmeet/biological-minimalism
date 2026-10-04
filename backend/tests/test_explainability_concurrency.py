"""Concurrency regressions for the singleton SHAP explainers."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import numpy as np

from app.ml.explainability import AIExplainer


class _NonReentrantExplainer:
    """Stand-in for KernelExplainer's mutable calculation workspace."""

    expected_value = 50.0

    def __init__(self, feature_count: int) -> None:
        self._active = False
        self._guard = Lock()
        self._feature_count = feature_count

    def shap_values(self, _x: np.ndarray, *, silent: bool) -> np.ndarray:
        assert silent
        with self._guard:
            if self._active:
                raise RuntimeError("concurrent access to mutable explainer")
            self._active = True
        try:
            time.sleep(0.02)
            return np.zeros((1, self._feature_count))
        finally:
            with self._guard:
                self._active = False


def test_confidence_explanations_serialize_shared_kernel_explainer() -> None:
    subject = AIExplainer.__new__(AIExplainer)
    subject._confidence_explainer = _NonReentrantExplainer(4)
    subject._confidence_bg_mean = np.full(4, 0.5)
    subject._confidence_lock = Lock()

    quality = {"ppg": 1.0, "eeg": 1.0, "temperature": 1.0, "bioimpedance": 1.0}
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: subject.explain_confidence(quality), range(16)))

    assert len(results) == 16
    assert all(result.target == "ai_confidence" for result in results)


def test_fatigue_explanations_serialize_shared_kernel_explainer() -> None:
    subject = AIExplainer.__new__(AIExplainer)
    subject._fatigue_explainer = _NonReentrantExplainer(5)
    subject._fatigue_bg_mean = np.array([50.0, 0.2, 0.25, 50.0, 10.0])
    subject._fatigue_lock = Lock()

    def explain(_: int):
        return subject.explain_fatigue(50.0, 0.2, 0.25, 50.0, 10.0)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(explain, range(16)))

    assert len(results) == 16
    assert all(result.target == "fatigue_risk" for result in results)
