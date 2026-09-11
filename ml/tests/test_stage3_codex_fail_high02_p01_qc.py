"""HIGH-02 regression tests (Section 36): the GalaxyPPG reference-ECG QC
artifact must cover all 24 real participants, use only raw-signal-derived
fields (never model performance), and the eligibility decision must derive
mechanically from those fields with correct threshold math."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

PERFORMANCE_FIELD_NAMES = {"mae", "rmse", "mape", "accuracy", "f1", "loss", "hr_mae", "prediction"}


def _load(name):
    return json.loads((REPO_ROOT / "results" / name).read_text())


def test_all_24_qc_records_present():
    d = _load("galaxyppg_reference_ecg_qc.json")
    ids = {e["participant_id"] for e in d["table"]}
    assert len(d["table"]) == 24
    assert len(ids) == 24
    assert ids == {f"P{i:02d}" for i in range(1, 25)}


def test_raw_metrics_retained_for_every_present_subject():
    d = _load("galaxyppg_reference_ecg_qc.json")
    required = {
        "primary_r_peaks_per_min", "secondary_r_peaks_per_min",
        "detector_agreement_ratio_primary_over_secondary",
        "rr_implausible_fraction_primary", "clipping_fraction", "signal_snr_proxy",
    }
    for e in d["table"]:
        if e.get("ecg_present", True):
            assert required.issubset(e.keys())


def test_no_performance_field_in_qc_artifact():
    d = _load("galaxyppg_reference_ecg_qc.json")
    assert d["no_performance_data_used"] is True
    raw = json.dumps(d).lower()
    for bad in PERFORMANCE_FIELD_NAMES:
        assert f'"{bad}"' not in raw, f"performance-looking field '{bad}' found in QC artifact"


def test_eligibility_decision_derives_mechanically_from_qc_fields_only():
    """Recompute eligibility directly from the QC table's own fields and
    confirm it reproduces the published eligible/excluded sets exactly -
    proves the decision is a mechanical function of QC fields, not a
    separately-asserted list."""
    qc = _load("galaxyppg_reference_ecg_qc.json")
    elig = _load("galaxyppg_corrected_eligibility.json")

    recomputed_eligible = {
        e["participant_id"] for e in qc["table"]
        if e.get("ecg_present", True)
        and e["primary_r_peaks_per_min"] >= 40.0
        and e["detector_agreement_ratio_primary_over_secondary"] >= 0.50
    }
    assert recomputed_eligible == set(elig["eligible"])
    assert len(recomputed_eligible) == 18


def test_p01_fails_both_independent_dimensions():
    qc = _load("galaxyppg_reference_ecg_qc.json")
    p01 = next(e for e in qc["table"] if e["participant_id"] == "P01")
    assert p01["primary_r_peaks_per_min"] < 40.0
    assert p01["detector_agreement_ratio_primary_over_secondary"] < 0.50


def test_composite_rule_reproduces_prior_single_metric_cohort_exactly():
    """The HIGH-02 composite rule must match the prior single-metric 18/24
    cohort with zero symmetric difference - confirms P01's exclusion is not
    an artifact of switching rules."""
    elig = _load("galaxyppg_corrected_eligibility.json")
    prior_eligible = {
        "P02", "P04", "P05", "P06", "P08", "P09", "P10", "P11", "P12",
        "P13", "P14", "P16", "P17", "P18", "P20", "P21", "P23", "P24",
    }
    assert set(elig["eligible"]) == prior_eligible
