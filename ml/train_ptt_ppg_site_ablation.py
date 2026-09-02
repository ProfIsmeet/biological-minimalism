#!/usr/bin/env python
"""Day 3 experiment scaffold (docs/MODEL_CONTRACT_PTT_HR.md,
datasets/PTT_DATASET_AUDIT_DAY3.md):

    "Does a second PPG sensor site provide measurable value for heart-rate
    estimation over a single PPG site, particularly during running?"

**Day 3 scope: model interface + smoke test ONLY. This file intentionally
does not implement a `main()` training loop for the full ablation.** The
full Model A vs. Model B run requires explicit authorization after the
Day 3 gate is reviewed (see docs/PTT_DATASET_AUDIT_DAY3.md and the Day 3
master prompt, section 19/21).

Model A: single-site PPG (3 wavelength channels, distal phalanx).
Model B: two-site PPG (6 wavelength channels, distal + proximal phalanx).
Both use the exact same architecture family (one Conv1DEncoder + a Linear
head) and the same hyperparameters - the only difference is `in_channels`,
which is the variable under test (a second physical PPG site). No
Transformer/fusion module is used: the two sites are the same physiological
modality (PPG), not separate modalities requiring cross-modal fusion, so a
single encoder over the stacked channels is the smallest architecture that
can answer the sensor-site question (see contract doc "Fairness/Capacity
Policy" for the full rationale and the acknowledged channel-count confound).

Ground truth (HR) comes only from `ml/datasets/pulse_transit_time_ppg.py`'s
real ECG-R-peak-derived per-window label. ECG itself is never a model
input here.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT))

from app.ml._torch_bootstrap import ensure_torch_dll_path  # noqa: E402

ensure_torch_dll_path()

import torch  # noqa: E402
from torch import nn, optim  # noqa: E402

from app.ml.models import Conv1DEncoder  # noqa: E402

from ml.datasets.pulse_transit_time_ppg import (  # noqa: E402
    MODEL_A_CHANNELS,
    MODEL_B_CHANNELS,
    WINDOW_SAMPLES,
    RecordWindows,
)

EXPERIMENT_DIR = Path(__file__).parent / "experiments" / "ptt_ppg_site_ablation"


class PPGSiteHRModel(nn.Module):
    """One Conv1DEncoder over the stacked PPG-site channels + a linear HR
    head. Used for BOTH Model A (in_channels=3) and Model B (in_channels=6)
    - identical depth/width/hyperparameters in both cases, so the only
    thing that differs between the two trained models is the number of
    input channels (the second PPG site itself), not extra model capacity
    added on top of it."""

    def __init__(self, in_channels: int, embedding_dim: int = 32) -> None:
        super().__init__()
        self.encoder = Conv1DEncoder(in_channels=in_channels, embedding_dim=embedding_dim)
        self.head = nn.Linear(embedding_dim, 1)

    def forward(self, ppg: torch.Tensor) -> torch.Tensor:
        return self.head(self.encoder(ppg)).squeeze(-1)


def build_tensors(records: list[RecordWindows], model: str) -> dict[str, np.ndarray]:
    """`model`: "a" or "b". Concatenates windows across records (which may
    span multiple activities/subjects) into flat arrays, preserving
    provenance arrays alongside the tensors."""

    if model not in ("a", "b"):
        raise ValueError("model must be 'a' or 'b'")
    key = "ppg_a" if model == "a" else "ppg_b"

    ppg = np.concatenate([getattr(r, key) for r in records]) if records else np.zeros((0, 0, WINDOW_SAMPLES), dtype=np.float32)
    hr = np.concatenate([r.hr for r in records]) if records else np.zeros((0,), dtype=np.float32)
    subject_id = np.concatenate([np.full(len(r.hr), r.subject_id) for r in records]) if records else np.zeros((0,), dtype="<U8")
    activity = np.concatenate([np.full(len(r.hr), r.activity) for r in records]) if records else np.zeros((0,), dtype="<U8")

    return {"ppg": ppg, "hr": hr, "subject_id": subject_id, "activity": activity}


def smoke_test(cache_dir: str | Path) -> None:
    """Day 3 smoke test ONLY (see module docstring) - proves the pipeline
    end-to-end, including a couple of gradient steps to confirm the code
    path executes. **Not a scientific result**: uses whichever locally
    cached records are available (not the full frozen split), tiny data,
    no held-out evaluation reported."""

    from ml.datasets.pulse_transit_time_ppg import ALL_SUBJECTS, ACTIVITIES, load_cached_record

    cache_dir = Path(cache_dir)
    available = []
    for s in ALL_SUBJECTS:
        for a in ACTIVITIES:
            p = cache_dir / f"{s}_{a}.npz"
            if p.exists():
                available.append((s, a))

    if not available:
        raise FileNotFoundError(f"No cached PTT records found in {cache_dir} - run preprocess_record() first.")

    print(f"Smoke test using {len(available)} cached record(s): {available}")
    records = [load_cached_record(cache_dir, s, a) for s, a in available]

    for model_name, channels in (("a", MODEL_A_CHANNELS), ("b", MODEL_B_CHANNELS)):
        data = build_tensors(records, model_name)
        n = len(data["hr"])
        print(f"Model {model_name.upper()}: {n} windows, ppg shape {data['ppg'].shape}, channels={channels}")
        assert data["ppg"].shape[1] == len(channels), "channel count mismatch"
        assert data["ppg"].shape[2] == WINDOW_SAMPLES

        model = PPGSiteHRModel(in_channels=len(channels))
        opt = optim.Adam(model.parameters(), lr=1e-3)
        loss_fn = nn.L1Loss()

        ppg_t = torch.from_numpy(data["ppg"][: min(16, n)])
        hr_t = torch.from_numpy(data["hr"][: min(16, n)])
        hr_mean, hr_std = float(hr_t.mean()), float(hr_t.std() + 1e-6)
        hr_norm = (hr_t - hr_mean) / hr_std

        model.train()
        for step in range(2):
            opt.zero_grad()
            pred = model(ppg_t)
            assert pred.shape == hr_norm.shape, f"prediction shape {pred.shape} != target shape {hr_norm.shape}"
            loss = loss_fn(pred, hr_norm)
            loss.backward()
            opt.step()
            print(f"  Model {model_name.upper()} smoke-train step {step}: loss={loss.item():.4f} (NOT a scientific result)")

    print("SMOKE TEST PASSED - pipeline executes end-to-end. No held-out metric was computed or reported.")


if __name__ == "__main__":
    smoke_test(EXPERIMENT_DIR.parent.parent.parent / "datasets" / "pulse-transit-time-ppg" / "processed")
