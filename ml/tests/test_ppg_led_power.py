"""Tests for ml/engineering/ppg_led_power.py (Stage 4 coverage gap close).

compute_led_power() had no dedicated test despite being the formula behind
the Stage-4 wrist/second-PPG LED power figures. Covers the core arithmetic,
the never-zero-for-unknown discipline, and the duty-factor bounds check.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "ml"))

from engineering.ppg_led_power import LedPowerInputs, compute_led_power  # noqa: E402


def test_ready_result_matches_hand_computed_formula() -> None:
    inputs = LedPowerInputs(n_active_leds=2, i_led_peak_ma=20.0, v_led_forward_v=3.0, t_pulse_seconds=100e-6, f_pulse_hz=64.0)
    result = compute_led_power(inputs)
    assert result.status == "READY"
    assert result.missing_inputs == []
    expected_duty_factor = 100e-6 * 64.0
    assert result.duty_factor == pytest.approx(expected_duty_factor)
    expected_per_led = 20.0 * 3.0 * expected_duty_factor
    assert result.per_led_average_power_mw == pytest.approx(expected_per_led)
    assert result.total_average_power_mw == pytest.approx(expected_per_led * 2)


@pytest.mark.parametrize(
    "missing_field",
    ["n_active_leds", "i_led_peak_ma", "v_led_forward_v", "t_pulse_seconds", "f_pulse_hz"],
)
def test_any_missing_input_is_not_ready_never_zero(missing_field: str) -> None:
    kwargs = dict(n_active_leds=2, i_led_peak_ma=20.0, v_led_forward_v=3.0, t_pulse_seconds=100e-6, f_pulse_hz=64.0)
    kwargs[missing_field] = None
    result = compute_led_power(LedPowerInputs(**kwargs))
    assert result.status == "NOT_READY"
    assert result.missing_inputs == [missing_field]
    assert result.total_average_power_mw is None
    assert result.per_led_average_power_mw is None
    assert result.duty_factor is None


def test_all_inputs_missing_lists_all_five() -> None:
    result = compute_led_power(LedPowerInputs())
    assert result.status == "NOT_READY"
    assert set(result.missing_inputs) == {
        "n_active_leds", "i_led_peak_ma", "v_led_forward_v", "t_pulse_seconds", "f_pulse_hz",
    }


def test_duty_factor_over_one_raises_instead_of_silently_clamping() -> None:
    # t_pulse * f_pulse > 1 means "on" more than 100% of the time — a unit-mixup
    # (e.g. ms instead of s), not a valid duty factor. Must raise, not clamp.
    inputs = LedPowerInputs(n_active_leds=1, i_led_peak_ma=20.0, v_led_forward_v=3.0, t_pulse_seconds=0.5, f_pulse_hz=64.0)
    with pytest.raises(ValueError):
        compute_led_power(inputs)


def test_zero_duty_factor_is_a_valid_ready_zero_not_unknown() -> None:
    # A genuine 0 Hz pulse rate (LEDs never fire) is a real, computable 0 mW —
    # distinct from an *unknown* rate, which must stay NOT_READY (tested above).
    inputs = LedPowerInputs(n_active_leds=2, i_led_peak_ma=20.0, v_led_forward_v=3.0, t_pulse_seconds=100e-6, f_pulse_hz=0.0)
    result = compute_led_power(inputs)
    assert result.status == "READY"
    assert result.total_average_power_mw == 0.0
