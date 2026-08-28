"""Stateful mock telemetry engine.

`MockDataEngine` is the single mutable source of "ground truth" simulated
astronaut state for the whole backend. It advances an internal set of
smooth (Ornstein-Uhlenbeck) random walks on every `tick()`, shaped by the
current `MissionMode` and per-sensor `SensorStatus`, and turns them into
the fully-typed snapshots served over REST and the WebSocket feed.

No real sensor or dataset is used — this is explicitly a synthetic
data generator (see docs/PDD §Dashboard Architecture). Its formulas call
into `app/engine/physiology.py`, which is the same module the
explainability layer introspects, so "why did confidence drop" answers are
computed from the same logic that produced the number, not decorative
text.
"""

from __future__ import annotations

import time
from collections import deque

import numpy as np

from app.core.config import settings
from app.engine import physiology as phys
from app.schemas.digital_twin import DigitalTwinState, DigitalTwinSystemScore
from app.schemas.mission import MissionMode, SensorName, SensorStatus
from app.schemas.telemetry import (
    AIConfidenceSnapshot,
    CognitiveSnapshot,
    LiveMetricsSnapshot,
    SensorHealthSnapshot,
    SensorReading,
    SpaceAdaptationSnapshot,
    VitalsSnapshot,
)

_EEG_MODE_BIAS = {
    MissionMode.EARTH_ORBIT: {"delta": 0.20, "theta": 0.20, "alpha": 0.34, "beta": 0.26},
    MissionMode.LUNAR_SURFACE: {"delta": 0.18, "theta": 0.22, "alpha": 0.28, "beta": 0.32},
    MissionMode.DEEP_SPACE: {"delta": 0.17, "theta": 0.25, "alpha": 0.24, "beta": 0.34},
    MissionMode.SOLAR_EVENT: {"delta": 0.15, "theta": 0.27, "alpha": 0.18, "beta": 0.40},
}

_DIGITAL_TWIN_SYSTEMS = {
    "Cardiovascular": {"baseline": 42.0, "k": 0.16, "asymptote": 88.0},
    "Cognitive": {"baseline": 55.0, "k": 0.20, "asymptote": 90.0},
    "Fluid Balance": {"baseline": 33.0, "k": 0.11, "asymptote": 82.0},
    "Thermal Regulation": {"baseline": 60.0, "k": 0.24, "asymptote": 93.0},
}


def _quality_for(status: SensorStatus) -> float:
    if status == SensorStatus.OFFLINE:
        return 0.0
    if status == SensorStatus.DEGRADED:
        return 0.45
    return 1.0


class MockDataEngine:
    def __init__(self, seed: int | None = None) -> None:
        self.rng = np.random.default_rng(seed if seed is not None else settings.random_seed)
        self.mission_mode: MissionMode = MissionMode.EARTH_ORBIT
        self.sensor_status: dict[SensorName, SensorStatus] = {s: SensorStatus.NOMINAL for s in SensorName}
        self._start_time = time.time()
        self.mission_day: float = 1.0

        self._hr = 68.0
        self._hrv = 68.0
        self._temp = 36.8
        self._temp_drift = 0.0
        self._bioz_trend = 0.0
        self._eeg = dict(_EEG_MODE_BIAS[MissionMode.EARTH_ORBIT])

        self.history: deque[LiveMetricsSnapshot] = deque(maxlen=settings.rolling_history_length)
        self.last_snapshot: LiveMetricsSnapshot | None = None

    # -- control -----------------------------------------------------
    def set_mode(self, mode: MissionMode) -> None:
        self.mission_mode = mode

    def set_sensor_status(self, sensor: SensorName, status: SensorStatus) -> None:
        self.sensor_status[sensor] = status

    def reset_sensor_status(self) -> None:
        self.sensor_status = {s: SensorStatus.NOMINAL for s in SensorName}

    # -- simulation ----------------------------------------------------
    def tick(self, dt: float) -> LiveMetricsSnapshot:
        profile = phys.MODE_PROFILES[self.mission_mode]
        self.mission_day = min(30.0, self.mission_day + dt / 300.0)  # ~1 mission day per 5 real minutes

        quality = {s.value: _quality_for(status) for s, status in self.sensor_status.items()}
        noise = profile.noise_multiplier

        if self.sensor_status[SensorName.PPG] != SensorStatus.OFFLINE:
            degrade = 1.0 + (1.0 - quality["ppg"]) * 2.5
            hr_mean = 68.0 + profile.risk_bias * 0.25
            self._hr = phys.clamp(
                phys.ou_step(self._hr, hr_mean, theta=0.12, sigma=1.1 * noise * degrade, dt=dt, rng=self.rng), 48.0, 150.0
            )
            hrv_mean = phys.clamp(76.0 - profile.risk_bias * 0.9, 18.0, 92.0)
            self._hrv = phys.clamp(
                phys.ou_step(self._hrv, hrv_mean, theta=0.10, sigma=1.4 * noise * degrade, dt=dt, rng=self.rng), 10.0, 135.0
            )

        if self.sensor_status[SensorName.TEMPERATURE] != SensorStatus.OFFLINE:
            degrade = 1.0 + (1.0 - quality["temperature"]) * 2.5
            self._temp = phys.clamp(
                phys.ou_step(self._temp, 36.8 + profile.risk_bias * 0.01, theta=0.06, sigma=0.03 * noise * degrade, dt=dt, rng=self.rng),
                35.5,
                38.5,
            )
            self._temp_drift = phys.ou_step(self._temp_drift, 0.0, theta=0.08, sigma=0.01 * noise, dt=dt, rng=self.rng)

        if self.sensor_status[SensorName.BIOIMPEDANCE] != SensorStatus.OFFLINE:
            degrade = 1.0 + (1.0 - quality["bioimpedance"]) * 2.5
            target = phys.clamp(-0.5 + self.mission_day / 30.0, -0.5, 0.6)
            self._bioz_trend = phys.clamp(
                phys.ou_step(self._bioz_trend, target, theta=0.05, sigma=0.05 * noise * degrade, dt=dt, rng=self.rng), -1.0, 1.5
            )

        if self.sensor_status[SensorName.EEG] != SensorStatus.OFFLINE:
            degrade = 1.0 + (1.0 - quality["eeg"]) * 2.5
            targets = _EEG_MODE_BIAS[self.mission_mode]
            for band in phys.EEG_BANDS:
                self._eeg[band] = max(
                    0.02,
                    phys.ou_step(self._eeg[band], targets[band], theta=0.09, sigma=0.02 * noise * degrade, dt=dt, rng=self.rng),
                )
            total = sum(self._eeg.values())
            self._eeg = {band: value / total for band, value in self._eeg.items()}

        mode_bias = profile.risk_bias

        cognitive_load = phys.cognitive_load_from_eeg(self._eeg["beta"], self._eeg["theta"], self._eeg["alpha"])
        attention = phys.attention_from_eeg(self._eeg["alpha"], self._eeg["beta"])
        fatigue = phys.fatigue_score(self._hrv, cognitive_load, self._eeg["theta"], self._eeg["alpha"])
        elapsed_hours = (time.time() - self._start_time) / 3600.0 * 24.0  # accelerated clock for the demo
        circadian = phys.circadian_stability(elapsed_hours, self.mission_day, mode_bias)

        systolic, diastolic = phys.estimate_blood_pressure(self._hr, self._hrv)
        resp_rate = phys.respiration_rate_from_hrv(self._hrv, self._hr)

        fluid_shift = phys.fluid_shift_risk(self._bioz_trend, self.mission_day, mode_bias)
        autonomic = phys.autonomic_balance(self._hrv, mode_bias)
        thermal = phys.thermal_stability(self._temp, self._temp_drift)

        overall_confidence, contribution = phys.fused_confidence(quality)

        n_points = settings.ppg_waveform_points_per_frame
        sr = settings.ppg_sample_rate_hz
        if self.sensor_status[SensorName.PPG] == SensorStatus.OFFLINE:
            ppg_wave = [0.0] * n_points
            ecg_wave = [0.0] * n_points
        else:
            wave_noise = 0.02 * noise * (1.0 + (1.0 - quality["ppg"]) * 3.0)
            ppg_wave = phys.generate_ppg_waveform(n_points, sr, self._hr, self._hrv, wave_noise, self.rng)
            ecg_wave = phys.generate_ecg_like_waveform(n_points, sr, self._hr, wave_noise, self.rng)

        snapshot = LiveMetricsSnapshot(
            timestamp=time.time(),
            mission_mode=self.mission_mode,
            mission_day=round(self.mission_day, 3),
            vitals=VitalsSnapshot(
                heart_rate_bpm=round(self._hr, 1),
                hrv_rmssd_ms=round(self._hrv, 1),
                respiration_rate_bpm=round(resp_rate, 1),
                blood_pressure_systolic_mmhg=round(systolic, 1),
                blood_pressure_diastolic_mmhg=round(diastolic, 1),
                ppg_waveform=ppg_wave,
                ecg_like_waveform=ecg_wave,
            ),
            cognitive=CognitiveSnapshot(
                cognitive_load=round(cognitive_load, 1),
                fatigue=round(fatigue, 1),
                circadian_stability=round(circadian, 1),
                eeg_attention=round(attention, 1),
                eeg_band_powers={k: round(v, 4) for k, v in self._eeg.items()},
            ),
            space_adaptation=SpaceAdaptationSnapshot(
                fluid_shift_risk=round(fluid_shift, 1),
                autonomic_balance=round(autonomic, 1),
                thermal_stability=round(thermal, 1),
            ),
            sensor_health=SensorHealthSnapshot(
                sensors=[
                    SensorReading(sensor=s, status=status, signal_quality=quality[s.value])
                    for s, status in self.sensor_status.items()
                ]
            ),
            ai_confidence=AIConfidenceSnapshot(
                overall_confidence=round(overall_confidence, 1),
                sensor_contribution={k: round(v, 1) for k, v in contribution.items()},
            ),
        )

        self.history.append(snapshot)
        self.last_snapshot = snapshot
        return snapshot

    def feature_vector(self) -> dict[str, float]:
        """The current raw feature vector, used by ml/explainability.py.

        Keeping this in the engine (rather than re-deriving it elsewhere)
        guarantees the explanation always matches what actually produced
        the live numbers.
        """

        return {
            "heart_rate_bpm": self._hr,
            "hrv_rmssd_ms": self._hrv,
            "eeg_alpha": self._eeg["alpha"],
            "eeg_beta": self._eeg["beta"],
            "eeg_theta": self._eeg["theta"],
            "temperature_c": self._temp,
            "bioimpedance_trend": self._bioz_trend,
            "mission_day": self.mission_day,
            "mode_risk_bias": phys.MODE_PROFILES[self.mission_mode].risk_bias,
        }

    def signal_quality(self) -> dict[str, float]:
        return {s.value: _quality_for(status) for s, status in self.sensor_status.items()}

    # -- digital twin ----------------------------------------------------
    def get_digital_twin_state(self, day: float) -> DigitalTwinState:
        day = phys.clamp(day, 0.0, 30.0)
        systems: list[DigitalTwinSystemScore] = []
        for name, cfg in _DIGITAL_TWIN_SYSTEMS.items():
            baseline = cfg["baseline"]
            asymptote = cfg["asymptote"]
            k = cfg["k"]
            current = baseline + (asymptote - baseline) * (1.0 - np.exp(-k * max(day - 1.0, 0.0)))
            systems.append(
                DigitalTwinSystemScore(
                    system=name,
                    baseline_score=round(baseline, 1),
                    current_score=round(float(current), 1),
                    delta=round(float(current) - baseline, 1),
                )
            )

        overall = sum(s.current_score for s in systems) / len(systems)

        if day < 3:
            milestone = f"Day {day:.0f} — Acute Adaptation Phase"
        elif day < 8:
            milestone = f"Day {day:.0f} — Early Adaptation"
        elif day < 20:
            milestone = f"Day {day:.0f} — Consolidating Adaptation"
        else:
            milestone = f"Day {day:.0f} — Stabilized Adaptation"

        weakest = min(systems, key=lambda s: s.current_score)
        narrative = (
            f"By mission day {day:.0f}, the Biological Digital Twin estimates {overall:.0f}% overall "
            f"physiological adaptation relative to its Day 1 baseline. {weakest.system} is the current "
            f"focus area at {weakest.current_score:.0f}% (+{weakest.delta:.0f} pts vs. Day 1)."
        )

        return DigitalTwinState(
            mission_day=round(day, 1),
            milestone_label=milestone,
            narrative=narrative,
            systems=systems,
            overall_adaptation=round(overall, 1),
        )


engine = MockDataEngine()
