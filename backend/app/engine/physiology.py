"""Physiology scoring engine.

This module is the single source of truth for every derived physiological
metric shown on the dashboard. It is intentionally a transparent, documented
set of formulas rather than a black box — this is what lets
`ml/explainability.py` compute genuine SHAP attributions over it, and what
lets `ml/inference.py` expose it as the default ("demo mode") implementation
of the `AIInferenceEngine` interface.

IMPORTANT — scientific status of these formulas: they are simplified,
literature-*inspired* engineering approximations built for a live demo
running on synthetic data, NOT clinically validated models. Relationships
they encode (e.g. HRV as a marker of parasympathetic/autonomic activity,
pulse-arrival-time-style cuffless blood pressure estimation, EEG band-power
ratios as workload/attention proxies, respiratory sinus arrhythmia linking
HRV and respiration rate) are grounded in the physiology literature
summarized in `docs/PDD_Biological_Minimalism_IAC2026.md`, but the exact
coefficients below are engineering choices for this demonstrator, not
fitted or validated against real subject data. Anywhere this distinction
matters, the PDD calls it out explicitly as a design proposal rather than a
proven result.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from app.schemas.mission import MissionMode

EEG_BANDS = ("delta", "theta", "alpha", "beta")

# Baseline relative sensor contribution weights when all four sensors are
# nominal, reused from the project's own planning analysis (see
# Biological_Minimalism_Yol_Haritasi.md, Phase 5 example). These are a
# design proposal, re-normalized at runtime over whichever sensors are
# actually active.
BASE_SENSOR_WEIGHTS: dict[str, float] = {
    "ppg": 0.41,
    "eeg": 0.35,
    "temperature": 0.14,
    "bioimpedance": 0.10,
}


@dataclass(frozen=True)
class ModeProfile:
    """How strongly a mission mode perturbs noise and baseline risk."""

    noise_multiplier: float
    risk_bias: float
    label: str


MODE_PROFILES: dict[MissionMode, ModeProfile] = {
    MissionMode.EARTH_ORBIT: ModeProfile(noise_multiplier=1.0, risk_bias=0.0, label="Earth Orbit"),
    MissionMode.LUNAR_SURFACE: ModeProfile(noise_multiplier=1.35, risk_bias=8.0, label="Lunar Surface"),
    MissionMode.DEEP_SPACE: ModeProfile(noise_multiplier=1.7, risk_bias=16.0, label="Deep Space"),
    MissionMode.SOLAR_EVENT: ModeProfile(noise_multiplier=2.4, risk_bias=30.0, label="Solar Event"),
}


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def ou_step(prev: float, mean: float, theta: float, sigma: float, dt: float, rng: np.random.Generator) -> float:
    """One Euler-Maruyama step of an Ornstein-Uhlenbeck process.

    Produces a smooth, mean-reverting random walk — used everywhere in the
    mock engine so telemetry looks like continuous physiology rather than
    independent random noise from tick to tick.
    """

    drift = theta * (mean - prev) * dt
    diffusion = sigma * math.sqrt(dt) * rng.normal()
    return prev + drift + diffusion


# ---------------------------------------------------------------------------
# Cardiovascular
# ---------------------------------------------------------------------------


def estimate_blood_pressure(hr_bpm: float, hrv_rmssd_ms: float) -> tuple[float, float]:
    """Simplified cuffless BP estimate.

    Loosely inspired by pulse-arrival-time (PAT) based cuffless BP
    literature, where a shorter arrival time (here proxied from HR/HRV
    since no literal transit-time is available from mock signals) is
    associated with higher pressure. This is a demo-grade proxy, not a
    validated PAT extraction.
    """

    pat_proxy = clamp(1.0 / hr_bpm * (1.0 + hrv_rmssd_ms / 220.0), 0.006, 0.02)
    systolic = clamp(205.0 - 6200.0 * pat_proxy, 90.0, 165.0)
    diastolic = clamp(systolic * 0.64 - 0.05 * hrv_rmssd_ms, 55.0, 100.0)
    return systolic, diastolic


def respiration_rate_from_hrv(hrv_rmssd_ms: float, hr_bpm: float) -> float:
    """Respiratory-sinus-arrhythmia-inspired respiration estimate.

    Higher HRV is associated with stronger vagal/parasympathetic tone,
    which we model here as a mild pull toward a slower, more efficient
    respiration rate; higher heart rate pulls the other way.
    """

    baseline = 15.0
    vagal_pull = -0.02 * (hrv_rmssd_ms - 60.0)
    hr_pull = 0.03 * (hr_bpm - 70.0)
    return clamp(baseline + vagal_pull + hr_pull, 9.0, 28.0)


# ---------------------------------------------------------------------------
# Cognitive / EEG-derived
# ---------------------------------------------------------------------------


def cognitive_load_from_eeg(beta: float, theta: float, alpha: float) -> float:
    """Beta/(alpha+theta) engagement-style ratio, scaled to 0-100.

    Elevated beta relative to alpha+theta is commonly associated with
    higher mental workload in EEG workload literature (see PDD §Signal
    Processing / STEW dataset discussion).
    """

    ratio = beta / max(alpha + theta, 1e-6)
    return clamp(100.0 * (ratio / (ratio + 0.8)), 0.0, 100.0)


def attention_from_eeg(alpha: float, beta: float) -> float:
    ratio = beta / max(alpha, 1e-6)
    return clamp(100.0 * (ratio / (ratio + 1.1)), 0.0, 100.0)


def fatigue_score(hrv_rmssd_ms: float, cognitive_load: float, theta: float, alpha: float) -> float:
    """Composite fatigue estimate.

    Rises when HRV is depressed (autonomic strain) while cognitive
    workload stays elevated, and when EEG theta/alpha ratio rises (a
    commonly reported drowsiness marker). This exact composite formula is
    an engineering design choice for the demo, documented as such.
    """

    hrv_component = clamp(100.0 - (hrv_rmssd_ms - 20.0) * (100.0 / 100.0), 0.0, 100.0)
    drowsiness_component = clamp(100.0 * (theta / max(alpha, 1e-6) - 0.6), 0.0, 100.0)
    return clamp(0.45 * hrv_component + 0.35 * cognitive_load + 0.20 * drowsiness_component, 0.0, 100.0)


def circadian_stability(elapsed_hours: float, mission_day: float, mode_bias: float) -> float:
    """0-100 circadian alignment score.

    Modeled as a ~24h sinusoidal phase model whose amplitude decays with
    mission-mode stress (mode_bias) and very slowly re-stabilizes as the
    Digital Twin adapts across mission days — used by both the live feed
    and the Digital Twin timeline.
    """

    phase = 2 * math.pi * (elapsed_hours % 24.0) / 24.0
    ideal_amplitude = 35.0
    decay = clamp(1.0 - mode_bias / 60.0, 0.35, 1.0)
    adaptation_gain = clamp(mission_day / 30.0, 0.0, 1.0) * 10.0
    score = 65.0 + adaptation_gain + decay * ideal_amplitude * math.cos(phase) * 0.15
    return clamp(score, 0.0, 100.0)


# ---------------------------------------------------------------------------
# Space adaptation
# ---------------------------------------------------------------------------


def fluid_shift_risk(bioimpedance_trend: float, mission_day: float, mode_bias: float) -> float:
    """0-100 cephalad fluid-shift risk proxy from a bio-impedance trend signal.

    Acute risk is highest early in a mission/exposure and is modeled to
    ease as the Digital Twin's adaptation curve progresses toward Day 30,
    consistent with the general adaptation narrative described in the PDD
    (grounded in bed-rest/dry-immersion analog literature, not a fitted
    curve from that literature).
    """

    acute = clamp(60.0 - 1.3 * mission_day, 10.0, 60.0)
    trend_component = clamp(bioimpedance_trend * 40.0, -20.0, 40.0)
    return clamp(acute + trend_component + mode_bias * 0.5, 0.0, 100.0)


def autonomic_balance(hrv_rmssd_ms: float, mode_bias: float) -> float:
    """0-100 sympathetic/parasympathetic balance score (100 = well balanced)."""

    hrv_component = clamp(hrv_rmssd_ms / 1.1, 0.0, 100.0)
    return clamp(hrv_component - mode_bias * 0.6, 0.0, 100.0)


def thermal_stability(temp_c: float, temp_drift_c: float) -> float:
    deviation = abs(temp_c - 36.8) + abs(temp_drift_c) * 4.0
    return clamp(100.0 - deviation * 22.0, 0.0, 100.0)


# ---------------------------------------------------------------------------
# AI confidence / sensor fusion weighting
# ---------------------------------------------------------------------------


def fused_confidence(signal_quality: dict[str, float]) -> tuple[float, dict[str, float]]:
    """Combine per-sensor signal quality (0-1, 0 for offline) into an overall
    confidence score plus a normalized sensor-contribution breakdown.

    A sensor that is offline contributes 0 and its weight is redistributed
    across the remaining active sensors, which is why losing a
    high-weight sensor (e.g. PPG) both lowers overall confidence *and*
    visibly shifts the contribution chart — the effect Demo 1 relies on.
    """

    weighted = {name: BASE_SENSOR_WEIGHTS[name] * quality for name, quality in signal_quality.items()}
    total_weight = sum(weighted.values())
    if total_weight <= 1e-9:
        return 0.0, {name: 0.0 for name in signal_quality}

    contribution = {name: 100.0 * value / total_weight for name, value in weighted.items()}
    # Confidence reflects both how much signal is available (total_weight
    # relative to the fully-nominal case) and how balanced it is.
    max_possible_weight = sum(BASE_SENSOR_WEIGHTS.values())
    availability = clamp(total_weight / max_possible_weight, 0.0, 1.0)
    overall = clamp(100.0 * availability, 0.0, 100.0)
    return overall, contribution


# ---------------------------------------------------------------------------
# Waveform synthesis (for chart display only — not re-derived from these
# waveforms; the metrics above are the source of truth and these are drawn
# to be visually consistent with them.)
# ---------------------------------------------------------------------------


def generate_ppg_waveform(n_points: int, sample_rate_hz: float, hr_bpm: float, hrv_rmssd_ms: float, noise_level: float, rng: np.random.Generator) -> list[float]:
    t = np.arange(n_points) / sample_rate_hz
    period = 60.0 / max(hr_bpm, 1e-3)
    jitter = rng.normal(0.0, hrv_rmssd_ms / 4000.0, size=n_points)
    phase = (t + jitter) % period / period
    # Skewed pulse shape: fast systolic upstroke, slower diastolic decay.
    pulse = np.exp(-((phase - 0.12) ** 2) / (2 * 0.04 ** 2)) - 0.35 * np.exp(-((phase - 0.45) ** 2) / (2 * 0.12 ** 2))
    noise = rng.normal(0.0, noise_level, size=n_points)
    waveform = pulse + noise
    return waveform.astype(float).round(4).tolist()


def generate_ecg_like_waveform(n_points: int, sample_rate_hz: float, hr_bpm: float, noise_level: float, rng: np.random.Generator) -> list[float]:
    """A stylized, QRS-spike-like waveform derived from the same beat timing
    as the PPG signal, for the "ECG-like" trend chart. The sensor suite in
    this project has no literal ECG electrode — this is explicitly an
    illustrative, PPG-timing-derived visualization, not a claimed ECG
    measurement (the dashboard labels it "ECG-like")."""

    t = np.arange(n_points) / sample_rate_hz
    period = 60.0 / max(hr_bpm, 1e-3)
    phase = (t % period) / period
    spike = np.exp(-((phase - 0.5) ** 2) / (2 * 0.006 ** 2)) * 1.4
    p_wave = 0.15 * np.exp(-((phase - 0.30) ** 2) / (2 * 0.02 ** 2))
    t_wave = 0.25 * np.exp(-((phase - 0.68) ** 2) / (2 * 0.05 ** 2))
    noise = rng.normal(0.0, noise_level, size=n_points)
    waveform = spike + p_wave + t_wave + noise
    return waveform.astype(float).round(4).tolist()
