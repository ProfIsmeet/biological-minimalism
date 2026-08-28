"""PyTorch model architecture for the Biological Digital Twin fusion network.

This defines the real architecture described in the PDD (CNN Architecture /
Transformer Fusion Architecture sections): a 1D-CNN encoder per sensor
modality feeding a Transformer fusion encoder and a set of regression
heads. It is structurally complete and trainable, but **no training run is
in scope for this task** — no checkpoint ships with this repo, and the
dashboard runs on `app.ml.inference.RuleBasedInferenceEngine` by default
(see inference.py).

To train this model, `ml/train.py` at the repo root loads real datasets
(WESAD, STEW, PulseDB, NASA OSDR — see `datasets/README.md`) and imports
this exact class, so the demo-time model can later be swapped in without
any API or frontend changes: point `BIOMIN_MODEL_CHECKPOINT_PATH` at a
trained `.pt` file and `create_inference_engine()` loads
`TorchInferenceEngine` instead.
"""

from __future__ import annotations

from app.ml._torch_bootstrap import ensure_torch_dll_path

ensure_torch_dll_path()

import torch  # noqa: E402
from torch import nn  # noqa: E402

MODALITIES = ("eeg", "ppg", "temperature", "bioimpedance")

OUTPUT_TARGETS = (
    "cognitive_load",
    "fatigue",
    "autonomic_balance",
    "fluid_shift_risk",
    "heart_rate_bpm",
    "hrv_rmssd_ms",
    "blood_pressure_systolic_mmhg",
    "blood_pressure_diastolic_mmhg",
    "respiration_rate_bpm",
)


class Conv1DEncoder(nn.Module):
    """Per-modality 1D-CNN feature extractor.

    Three conv blocks with increasing channel depth and stride-2
    downsampling, followed by global average pooling to a fixed-size
    embedding — a standard, lightweight design for wearable biosignal
    windows (see PDD, CNN Architecture section, for the supporting
    literature this design choice draws on).
    """

    def __init__(self, in_channels: int = 1, embedding_dim: int = 64) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(in_channels, 16, kernel_size=7, stride=2, padding=3),
            nn.BatchNorm1d(16),
            nn.GELU(),
            nn.Conv1d(16, 32, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm1d(32),
            nn.GELU(),
            nn.Conv1d(32, embedding_dim, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm1d(embedding_dim),
            nn.GELU(),
        )
        self.pool = nn.AdaptiveAvgPool1d(1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (batch, in_channels, sequence_length) -> (batch, embedding_dim)."""

        features = self.net(x)
        return self.pool(features).squeeze(-1)


class ModalityFusionTransformer(nn.Module):
    """Cross-sensor attention over the four per-modality embeddings.

    Each modality embedding is treated as one token in a length-4
    sequence; a small Transformer encoder lets the model learn, e.g.,
    that EEG and temperature jointly explain a state better than either
    alone (PDD, Transformer Fusion Architecture section) — and, crucially,
    that it can still produce reasonable estimates from the remaining
    tokens when one modality is masked at inference time, which is the
    modality-dropout mechanism behind graceful degradation on sensor
    failure (Demo 1).
    """

    def __init__(self, embedding_dim: int = 64, n_heads: int = 4, n_layers: int = 2, dropout: float = 0.1) -> None:
        super().__init__()
        self.embedding_dim = embedding_dim
        self.modality_embedding = nn.Parameter(torch.randn(len(MODALITIES), embedding_dim) * 0.02)
        layer = nn.TransformerEncoderLayer(
            d_model=embedding_dim,
            nhead=n_heads,
            dim_feedforward=embedding_dim * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=n_layers)

    def forward(self, modality_tokens: torch.Tensor, modality_mask: torch.Tensor | None = None) -> torch.Tensor:
        """modality_tokens: (batch, n_modalities, embedding_dim).

        modality_mask: (batch, n_modalities) bool, True = present. When
        None, all modalities are treated as present.
        """

        tokens = modality_tokens + self.modality_embedding.unsqueeze(0)
        key_padding_mask = ~modality_mask if modality_mask is not None else None
        fused = self.encoder(tokens, src_key_padding_mask=key_padding_mask)
        return fused.mean(dim=1)


class BiologicalDigitalTwinNet(nn.Module):
    """Full fusion model: 4 modality encoders -> Transformer fusion -> heads."""

    def __init__(self, embedding_dim: int = 64) -> None:
        super().__init__()
        self.embedding_dim = embedding_dim
        self.encoders = nn.ModuleDict({m: Conv1DEncoder(embedding_dim=embedding_dim) for m in MODALITIES})
        self.fusion = ModalityFusionTransformer(embedding_dim=embedding_dim)
        self.heads = nn.ModuleDict({target: nn.Linear(embedding_dim, 1) for target in OUTPUT_TARGETS})

    def forward(
        self,
        modality_windows: dict[str, torch.Tensor],
        modality_mask: dict[str, bool] | None = None,
    ) -> dict[str, torch.Tensor]:
        """`modality_windows[m]`: (batch, 1, sequence_length) raw window per modality.

        A missing modality may simply be omitted from `modality_windows`
        (or explicitly flagged False in `modality_mask`); the fusion
        Transformer's key-padding mask lets the remaining modalities
        carry the estimate.
        """

        batch_size = next(iter(modality_windows.values())).shape[0]
        device = next(iter(modality_windows.values())).device
        embeddings = []
        mask_tensor = torch.ones(batch_size, len(MODALITIES), dtype=torch.bool, device=device)

        for i, m in enumerate(MODALITIES):
            present = m in modality_windows and (modality_mask is None or modality_mask.get(m, True))
            if m in modality_windows:
                embeddings.append(self.encoders[m](modality_windows[m]))
            else:
                embeddings.append(torch.zeros(batch_size, self.embedding_dim, device=device))
            if not present:
                mask_tensor[:, i] = False

        stacked = torch.stack(embeddings, dim=1)
        fused = self.fusion(stacked, modality_mask=mask_tensor)
        return {target: head(fused).squeeze(-1) for target, head in self.heads.items()}
