"""Unit tests for the real PyTorch architecture in `app/ml/models.py`.

Run with `pytest` from `backend/`. Separate from `test_api.py` (which only
exercises the rule-based demo path) because these import torch directly -
`ensure_torch_dll_path()` (see `app/ml/_torch_bootstrap.py`) keeps that safe
on this project's Windows dev environment.
"""

from __future__ import annotations

import torch

from app.ml.models import MODALITIES, BiologicalDigitalTwinNet, ModalityFusionTransformer


def test_masked_modality_pooling_is_inert() -> None:
    """A modality flagged absent in `modality_mask` must not influence the
    fused output, no matter what garbage is in its embedding slot.

    Regression test for docs/TECHNICAL_HANDOFF_V2.md §16.7: the fusion
    Transformer's `src_key_padding_mask` stops other tokens from attending
    to a masked position, but the masked position itself still produces a
    real (non-zero) output as a query - a plain `fused.mean(dim=1)` would
    silently mix that leftover value back in. Pooling must exclude it.
    """

    torch.manual_seed(0)
    fusion = ModalityFusionTransformer(embedding_dim=16, n_heads=2, n_layers=1)
    fusion.eval()

    batch, n_modalities, dim = 1, len(MODALITIES), 16
    tokens = torch.randn(batch, n_modalities, dim)
    mask = torch.ones(batch, n_modalities, dtype=torch.bool)
    mask[0, 0] = False  # first modality marked absent

    with torch.no_grad():
        out_a = fusion(tokens, modality_mask=mask)

        tokens_perturbed = tokens.clone()
        tokens_perturbed[0, 0] = torch.randn(dim) * 1000.0  # wildly different "garbage" in the masked slot
        out_b = fusion(tokens_perturbed, modality_mask=mask)

    assert torch.allclose(out_a, out_b, atol=1e-5), (
        "Changing a masked-out modality's embedding changed the pooled fusion "
        "output - the masked position is still leaking into the result."
    )


def test_biological_digital_twin_net_forward_runs_with_missing_modality() -> None:
    """End-to-end sanity check: the full model still produces every output
    head when one modality is entirely omitted from `modality_windows`."""

    torch.manual_seed(0)
    model = BiologicalDigitalTwinNet(embedding_dim=16)
    model.eval()

    batch, seq_len = 2, 256
    windows = {m: torch.randn(batch, 1, seq_len) for m in MODALITIES if m != "eeg"}

    with torch.no_grad():
        outputs = model(windows)

    for target, tensor in outputs.items():
        assert tensor.shape == (batch,), f"unexpected shape for {target}: {tensor.shape}"
        assert torch.isfinite(tensor).all(), f"non-finite output for {target}"
