"""Loader for NASA OSDR (Open Science Data Repository) spaceflight-analog
studies — head-down-tilt bed rest and dry immersion protocols relevant to
the fluid-shift / bio-impedance modality.

Source: NASA Open Science Data Repository. https://osdr.nasa.gov/bio/repo/
Search the repository for "head-down tilt bed rest" or "dry immersion" to
find specific accessioned studies; cite the specific OSD-### study used
once one is selected for training (see docs/PDD_Biological_Minimalism_IAC2026.md,
Dataset Research section, for the domain-gap discussion this dataset choice
is meant to address).

Not bundled with this repository. This module raises `NotImplementedError`
until pointed at a real local export of a chosen OSDR study.
"""

from __future__ import annotations

from pathlib import Path


def load_osdr_windows(dataset_dir: str | Path, window_seconds: float = 10.0):
    """Yield (bioimpedance_window, fluid_shift_label) pairs from a local OSDR export."""

    dataset_dir = Path(dataset_dir)
    if not dataset_dir.exists():
        raise NotImplementedError(
            f"NASA OSDR export not found at {dataset_dir}. Download a "
            "specific study per datasets/README.md, then re-run with "
            "--osdr-dir pointing at the extracted folder."
        )
    # TODO(research phase): OSDR study formats vary by accession; this
    # requires selecting one specific OSD-### study and writing a parser
    # for its particular file layout.
    raise NotImplementedError("NASA OSDR parsing is not implemented in this task's scope.")
