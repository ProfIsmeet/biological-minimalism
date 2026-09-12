"""Architecture-level compute footprint of BiologicalDigitalTwinNet (§11 / cheap Day-8).

Reports parameter count, float32 weight memory, and (explicitly theoretical) int8
weight memory, plus a module/structure summary — all measurable from the deterministic
architecture WITHOUT any training or validation claim.

It does NOT report embedded latency, energy, or MCU runtime feasibility (those are not
measured), and it does NOT claim the model is trained or validated. Input-buffer size
is reported as non-deterministic because the architecture uses AdaptiveAvgPool1d and
therefore accepts variable-length inputs (no fixed input length is declared).

Run with PYTHONPATH=backend:  PYTHONPATH=backend python ml/build_digital_twin_footprint.py
"""

from __future__ import annotations

import json
from pathlib import Path

from app.ml.models import MODALITIES, OUTPUT_TARGETS, BiologicalDigitalTwinNet

REPO = Path(__file__).resolve().parents[1]
OUT_PATH = REPO / "results" / "digital_twin_architecture_footprint.json"


def _count(params) -> int:
    return int(sum(p.numel() for p in params))


def build() -> dict:
    model = BiologicalDigitalTwinNet()
    model.eval()

    total = _count(model.parameters())
    trainable = _count(p for p in model.parameters() if p.requires_grad)

    per_module = {
        "encoders_total": _count(model.encoders.parameters()),
        "fusion_transformer": _count(model.fusion.parameters()),
        "heads_total": _count(model.heads.parameters()),
    }
    per_module["per_single_encoder"] = per_module["encoders_total"] // max(len(MODALITIES), 1)
    per_module["per_single_head"] = per_module["heads_total"] // max(len(OUTPUT_TARGETS), 1)

    float32_bytes = total * 4
    int8_bytes = total * 1  # theoretical only — no quantized checkpoint exists

    return {
        "artifact_id": "biological-minimalism-digital-twin-architecture-footprint-v1",
        "model": "BiologicalDigitalTwinNet",
        "validation_status": "ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED",
        "note": (
            "Architecture-level footprint of untrained reference code. No trained checkpoint, "
            "no validated multi-target performance, and no runtime/energy/latency measurement is "
            "claimed. Architecture footprint is not deployment feasibility."
        ),
        "structure": {
            "modalities": list(MODALITIES),
            "output_targets": list(OUTPUT_TARGETS),
            "embedding_dim": model.embedding_dim,
            "summary": (
                f"{len(MODALITIES)} per-modality Conv1D encoders -> modality-fusion Transformer "
                f"-> {len(OUTPUT_TARGETS)} linear regression heads."
            ),
        },
        "parameters": {
            "total": total,
            "trainable": trainable,
            "by_module": per_module,
        },
        "weight_memory": {
            "float32_bytes": float32_bytes,
            "float32_kib": round(float32_bytes / 1024, 2),
            "int8_theoretical_bytes": int8_bytes,
            "int8_theoretical_kib": round(int8_bytes / 1024, 2),
            "int8_note": "Theoretical lower bound only; no quantized checkpoint exists and accuracy under int8 is unmeasured.",
        },
        "input_buffer": {
            "deterministic": False,
            "value": None,
            "reason": (
                "The encoders use AdaptiveAvgPool1d, so the architecture accepts variable-length "
                "per-modality windows; no fixed input length is declared, so an input-buffer size "
                "is not derivable from the architecture alone."
            ),
        },
        "explicitly_not_reported": [
            "embedded inference latency",
            "energy consumption",
            "runtime feasibility on any specific MCU",
            "trained accuracy or multi-target validation",
        ],
    }


if __name__ == "__main__":
    payload = build()
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("Wrote", OUT_PATH.relative_to(REPO))
    print("total_params:", payload["parameters"]["total"],
          "| float32_KiB:", payload["weight_memory"]["float32_kib"])
