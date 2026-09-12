"""Parameterized PPG LED average-power model (Day 12 support artifact).

Implements exactly the formula already frozen in
results/reference_power_budget_day11_part2.json:

    P_LED_avg = N_active_LEDs * I_LED_peak * V_LED_forward * duty_factor
    duty_factor = t_pulse_seconds * f_pulse_hz

This module does NOT choose a final LED count, current, or wavelength
schedule - it is a calculator Claude can call once those values are
frozen. Any missing input returns a NOT_READY result, never a silent
zero. This is deliberate: an unknown LED current must never be treated
as "0 mW" (which would understate power), and a missing pulse rate must
never be treated as "0 Hz" (which would fabricate zero duty).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LedPowerInputs:
    n_active_leds: float | None = None
    i_led_peak_ma: float | None = None
    v_led_forward_v: float | None = None
    t_pulse_seconds: float | None = None
    f_pulse_hz: float | None = None


@dataclass
class LedPowerResult:
    status: str  # "READY" or "NOT_READY"
    missing_inputs: list[str]
    duty_factor: float | None
    per_led_average_power_mw: float | None
    total_average_power_mw: float | None
    formula: str = "P_LED_avg = N_active_LEDs * I_LED_peak * V_LED_forward * (t_pulse * f_pulse)"


def compute_led_power(inputs: LedPowerInputs) -> LedPowerResult:
    missing = [
        name
        for name, value in (
            ("n_active_leds", inputs.n_active_leds),
            ("i_led_peak_ma", inputs.i_led_peak_ma),
            ("v_led_forward_v", inputs.v_led_forward_v),
            ("t_pulse_seconds", inputs.t_pulse_seconds),
            ("f_pulse_hz", inputs.f_pulse_hz),
        )
        if value is None
    ]

    if missing:
        return LedPowerResult(
            status="NOT_READY",
            missing_inputs=missing,
            duty_factor=None,
            per_led_average_power_mw=None,
            total_average_power_mw=None,
        )

    duty_factor = inputs.t_pulse_seconds * inputs.f_pulse_hz
    if not (0.0 <= duty_factor <= 1.0):
        raise ValueError(
            f"duty_factor={duty_factor} is outside [0, 1] - t_pulse*f_pulse must be a "
            "fraction of time-on; check units (seconds and Hz, not ms/kHz)."
        )

    per_led_peak_power_mw = inputs.i_led_peak_ma * inputs.v_led_forward_v  # mA * V = mW
    per_led_average_power_mw = per_led_peak_power_mw * duty_factor
    total_average_power_mw = per_led_average_power_mw * inputs.n_active_leds

    return LedPowerResult(
        status="READY",
        missing_inputs=[],
        duty_factor=duty_factor,
        per_led_average_power_mw=per_led_average_power_mw,
        total_average_power_mw=total_average_power_mw,
    )
