"""Display-projection DTOs for Stage-3 accepted governing science.

These are the ONLY shapes any frontend/paper/jury consumer should read for
Stage-3 evidence. Raw artifact JSON is never exposed directly (governing
prompt Part IV §25/§26) - every field here is either a verified value
extracted from the resolved governing artifact, or explicitly None
(UNKNOWN), never silently defaulted to zero/false.

This is distinct from `app.schemas.experiment_manifest`, which is the
placeholder ingestion contract for Ismet's *future* (not-yet-arrived)
Stage-4 science handoff package. This module instead projects the
*already-accepted* Stage-3 governing evidence (21 registry families,
resolved via `ml.stage3_science_resolver.resolve_current`).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Stage3ArtifactType(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"


class Stage3EvidenceEntry(BaseModel):
    family_id: str
    artifact_path: str
    artifact_type: Stage3ArtifactType

    experiment_id: str | None = None
    classification: str | None = None

    biological_subject_n: int | None = None
    held_out_or_reduced_n: int | None = None
    full_cohort_target_n: int | None = None
    optimization_seed_n: int | None = None

    primary_comparison_label: str | None = None
    primary_effect_value: float | None = None
    primary_effect_unit: str | None = None

    secondary_comparison_label: str | None = None
    secondary_effect_value: float | None = None
    secondary_effect_unit: str | None = None

    heterogeneity_note: str | None = None
    limitation: str | None = None
    summary: str | None = None
    provenance_doc: str | None = None


class Stage3EvidenceEnvelope(BaseModel):
    schema_version: str = "1.0.0"
    source_registry: str
    source_freeze_manifest: str
    final_architecture_status: str
    formal_pareto_status: str
    entries: list[Stage3EvidenceEntry]
