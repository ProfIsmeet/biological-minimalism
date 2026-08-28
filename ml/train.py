#!/usr/bin/env python
"""Training entrypoint for `BiologicalDigitalTwinNet`.

Imports the real model architecture from `backend/app/ml/models.py` (the
same class the dashboard's `TorchInferenceEngine` loads) rather than
duplicating it, so a checkpoint trained here is guaranteed to be loadable
by the backend as-is.

No training has been run for this deliverable's dashboard: the datasets/
loaders under `ml/datasets/` raise `NotImplementedError` until pointed at
real, locally-downloaded data (see `datasets/README.md`). Running this
script against real WESAD/STEW/PulseDB/OSDR data is future research work,
scoped in `docs/PDD_Biological_Minimalism_IAC2026.md`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT))

import torch  # noqa: E402
from torch import nn, optim  # noqa: E402
from torch.utils.data import DataLoader, Dataset  # noqa: E402

from app.ml.models import BiologicalDigitalTwinNet, OUTPUT_TARGETS  # noqa: E402

from ml.datasets.wesad import load_wesad_windows  # noqa: E402
from ml.datasets.stew import load_stew_windows  # noqa: E402
from ml.datasets.pulsedb import load_pulsedb_windows  # noqa: E402
from ml.datasets.osdr import load_osdr_windows  # noqa: E402


class WindowedPhysiologyDataset(Dataset):
    """Wraps whichever dataset loaders successfully produced windows.

    Each item is `(modality_windows: dict[str, Tensor], targets: dict[str, Tensor])`.
    Left as a thin container — the real windowing/label-alignment logic
    belongs in each `ml/datasets/*.py` loader once real data is available.
    """

    def __init__(self, samples: list[tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]]) -> None:
        self.samples = samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int):
        return self.samples[index]


def build_dataset(args: argparse.Namespace) -> WindowedPhysiologyDataset:
    samples: list[tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]] = []
    loaders = [
        (args.wesad_dir, load_wesad_windows),
        (args.stew_dir, load_stew_windows),
        (args.pulsedb_dir, load_pulsedb_windows),
        (args.osdr_dir, load_osdr_windows),
    ]
    for dataset_dir, loader in loaders:
        if dataset_dir is None:
            continue
        samples.extend(loader(dataset_dir))

    if not samples:
        raise SystemExit(
            "No dataset directories were provided (or none produced samples). "
            "Pass at least one of --wesad-dir/--stew-dir/--pulsedb-dir/--osdr-dir "
            "pointing at real, locally-downloaded data — see datasets/README.md."
        )
    return WindowedPhysiologyDataset(samples)


def train(args: argparse.Namespace) -> None:
    dataset = build_dataset(args)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

    model = BiologicalDigitalTwinNet()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr)
    loss_fn = nn.MSELoss()

    model.train()
    for epoch in range(args.epochs):
        total_loss = 0.0
        for modality_windows, targets in loader:
            optimizer.zero_grad()
            predictions = model(modality_windows)
            loss = sum(loss_fn(predictions[target], targets[target]) for target in OUTPUT_TARGETS if target in targets)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item())
        print(f"epoch {epoch + 1}/{args.epochs} — loss {total_loss / max(len(loader), 1):.4f}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_path)
    print(f"Saved checkpoint to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wesad-dir", type=str, default=None)
    parser.add_argument("--stew-dir", type=str, default=None)
    parser.add_argument("--pulsedb-dir", type=str, default=None)
    parser.add_argument("--osdr-dir", type=str, default=None)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--output", type=str, default="checkpoints/biotwin_v1.pt")
    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
