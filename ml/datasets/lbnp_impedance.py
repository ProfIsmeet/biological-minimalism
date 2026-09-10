"""Loader for the LBNP thoracic impedance dataset (Zenodo 10.5281/zenodo.10119427
/ version record 10119428), Stage 3.

Real archive: `Mayo_LBNP_raw_data.zip`, MD5-verified against Zenodo this
project's prior sprint. Real MATLAB v7.3-independent structure (loadable
directly with `scipy.io.loadmat`, NOT HDF5 like ds003838):

- `LBNP_level_times.mat` -> `LBNPinf[0, i]`: fields `lbnp` (pressure level
  sequence, mmHg) and `ts` (real stage-transition timestamps, MINUTES -
  confirmed this sprint by cross-checking against Labchart's `ts` units:
  dt = 1.6667e-5 (same unit) = 0.001s at 1000 Hz, so the unit is minutes).
- `raw_sciospec_dat.mat` -> `SSout[0, i]['sciodat']`: 3-element struct
  (Thoracic/Abdominal/Arm per `sciolocs`), each with `tvec` (minutes,
  same timebase as LBNPinf), `fs` (100-point real excitation-frequency
  axis, 100 Hz-1 MHz), `Zmat` (real complex impedance, shape
  n_spectra x 100), `erflg` (per-spectrum error flag).
- `raw_labchart_data.mat` -> `Labchart[0, i]`: fields `ts` (minutes,
  confirmed 1000 Hz native ECG/pleth/MAP rate this sprint), `ecgs`,
  `MAP`, `pleth`.

REAL DATA-QUALITY FINDING (this sprint): subjects at struct index 0-3
(0-based) have `pleth` entirely NaN - no valid plethysmography for those
4 subjects. Only struct indices 4-15 (12 of 16) have complete ECG+pleth.
This is a genuine eligibility exclusion (data-quality, predeclared before
any model outcome), not an outcome-based decision - it reduces the usable
LBNP cohort for the ECG+pleth-based experiment from n=16 to n=12.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import scipy.io

RAW_DIR_DEFAULT = "datasets/lbnp-impedance/raw/extracted/share_data"
ECG_PLETH_NATIVE_HZ = 1000.0
EIS_FREQ_POINTS = 100
THORACIC_SITE_INDEX = 0  # per sciolocs = ['Thoracic', 'Abdominal', 'Arm']


def load_all(raw_dir: str | Path = RAW_DIR_DEFAULT) -> dict:
    raw_dir = Path(raw_dir)
    lbnp_inf = scipy.io.loadmat(raw_dir / "LBNP_level_times.mat")["LBNPinf"]
    ss_out = scipy.io.loadmat(raw_dir / "raw_sciospec_dat.mat")["SSout"]
    labchart = scipy.io.loadmat(raw_dir / "raw_labchart_data.mat")["Labchart"]
    n_subjects = lbnp_inf.shape[1]
    assert ss_out.shape[1] == n_subjects == labchart.shape[1] == 16
    return {"lbnp_inf": lbnp_inf, "ss_out": ss_out, "labchart": labchart, "n_subjects": n_subjects}


def subject_has_valid_pleth(labchart, subject_idx: int) -> bool:
    pleth = labchart[0, subject_idx]["pleth"].ravel()
    return bool(np.any(~np.isnan(pleth)))


def get_stage_at_time(lbnp_levels: np.ndarray, lbnp_times: np.ndarray, t: float) -> float:
    """Step-function lookup: the stage in effect at time t is the level
    whose transition time is the largest one <= t."""
    idx = np.searchsorted(lbnp_times, t, side="right") - 1
    if idx < 0:
        return float(lbnp_levels[0])
    return float(lbnp_levels[idx])


def build_subject_windows(data: dict, subject_idx: int, window_seconds: float = 20.0) -> dict:
    """Real, per-EIS-spectrum windows: for each real thoracic EIS spectrum,
    extract the preceding `window_seconds` of real ECG+pleth (ending at the
    spectrum's own real timestamp) and the real LBNP stage in effect at
    that time (step-function lookup, real data, no synthesis)."""
    labchart = data["labchart"][0, subject_idx]
    ts_min = labchart["ts"].ravel()
    ecg = labchart["ecgs"].ravel()
    pleth = labchart["pleth"].ravel()

    lbnp = data["lbnp_inf"][0, subject_idx]
    lbnp_levels = lbnp["lbnp"].ravel()
    lbnp_times = lbnp["ts"].ravel()

    sciodat = data["ss_out"][0, subject_idx]["sciodat"][0]
    thoracic = sciodat[THORACIC_SITE_INDEX]
    tvec = thoracic["tvec"].ravel()  # minutes, real per-spectrum timestamps
    zmat = thoracic["Zmat"]  # (n_spectra, 100) complex
    erflg = thoracic["erflg"].ravel()

    n_win_samples = int(round(window_seconds * ECG_PLETH_NATIVE_HZ))
    ecg_windows, pleth_windows, eis_mag, eis_phase, stages = [], [], [], [], []

    for i, t_min in enumerate(tvec):
        if erflg[i] != 0:
            continue  # real error-flagged spectrum, excluded (data-integrity rule)
        end_idx = np.searchsorted(ts_min, t_min)
        start_idx = end_idx - n_win_samples
        if start_idx < 0 or end_idx > len(ecg):
            continue
        ecg_seg = ecg[start_idx:end_idx]
        pleth_seg = pleth[start_idx:end_idx]
        if np.any(np.isnan(pleth_seg)) or np.any(np.isnan(ecg_seg)):
            continue
        stage = get_stage_at_time(lbnp_levels, lbnp_times, t_min)
        ecg_windows.append(ecg_seg.astype(np.float32))
        pleth_windows.append(pleth_seg.astype(np.float32))
        eis_mag.append(np.abs(zmat[i]).astype(np.float64))
        eis_phase.append(np.angle(zmat[i]).astype(np.float64))
        stages.append(stage)

    if not ecg_windows:
        return {"ecg": np.empty((0, n_win_samples), dtype=np.float32), "pleth": np.empty((0, n_win_samples), dtype=np.float32),
                "eis_mag": np.empty((0, EIS_FREQ_POINTS)), "eis_phase": np.empty((0, EIS_FREQ_POINTS)), "stage": np.empty((0,))}

    return {
        "ecg": np.stack(ecg_windows), "pleth": np.stack(pleth_windows),
        "eis_mag": np.stack(eis_mag), "eis_phase": np.stack(eis_phase),
        "stage": np.array(stages, dtype=np.float64),
    }
