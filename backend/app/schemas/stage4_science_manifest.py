"""Display schemas for Ismet's (Science Owner) Stage-4 science handoff
package (`docs/STAGE4_SCIENCE_OWNER_HANDOFF_TO_INTEGRATION_OWNER.md`).

These artifacts are already Science-Owner-curated, typed, per-family/claim
summaries built by reading every number through
`ml.stage3_science_resolver.resolve_current` (governing prompt Part XI) -
they are the AUTHORITATIVE safe-wording/classification surface, distinct
from `app.schemas.stage3_evidence`'s raw resolver passthrough (which exists
for numeric cross-verification, not narrative). Integration Owner code must
never author its own classification or safe-claim wording here - every
field is read verbatim from the Science Owner's package.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Stage4AcceptedStage3Reference(BaseModel):
    branch: str
    sha: str
    accepted_state: str


class Stage4ScienceFamilyEntry(BaseModel):
    family_id: str
    governing_artifact: str
    experiment_protocol_version: str
    # Some families have no clean single integer for these (e.g. QDE's LOSO
    # design has no seed dimension, ds003838's bounded design points to
    # "see source") - the Science Owner deliberately used a descriptive
    # string rather than fabricating a number (governing prompt §26), so
    # these stay a union rather than forcing int and losing that honesty.
    biological_n: int | str | None = None
    held_out_test_biological_n: int | str | None = None
    note_on_n: str | None = None
    optimization_seed_n: int | str | None = None
    a_b_c_definitions: dict[str, str] = {}
    primary_metric: str | None = None
    governing_numeric_result: dict[str, Any] | str = {}
    heterogeneity: str | None = None
    sensitivity: str | None = None
    evidence_classification: str
    strongest_safe_claim: str
    prohibited_overclaim: str
    architecture_relevance: str | None = None
    consumption_status: str
    provenance_hash_reference: str | None = None
    unresolved_limitation: str | None = None


class Stage4ScienceConsumptionManifest(BaseModel):
    purpose: str
    accepted_stage3_reference: Stage4AcceptedStage3Reference
    consumption_rule: str
    families: list[Stage4ScienceFamilyEntry]
    final_architecture_status: str
    formal_pareto_status: str


class Stage4SensorModality(BaseModel):
    modality: str
    anatomical_site: str
    supported_target_use: str
    strongest_positive_evidence: str
    strongest_negative_evidence: str
    external_replication_status: str
    heterogeneity: str
    incremental_value_status: str
    burden_relevance: str
    confidence_tier: str
    unresolved_evidence: str
    architecture_implication: str


class Stage4SensorValueMatrix(BaseModel):
    purpose: str
    accepted_stage3_sha: str
    final_architecture_status: str
    modalities: list[Stage4SensorModality]


class Stage4ScienceClaim(BaseModel):
    claim_id: str
    exact_safe_wording: str
    strength: str
    governing_evidence: list[str]
    relevant_numeric_result: str
    scope_limitation: str
    prohibited_stronger_wording: str
    stage4_consumer_guidance: str


class Stage4ScienceClaimLedger(BaseModel):
    purpose: str
    accepted_stage3_sha: str
    strength_enum: list[str]
    claims: list[Stage4ScienceClaim]


class Stage4ArchitectureDecisionCandidate(BaseModel):
    modality: str
    scientific_value: str
    independent_replication_status: str
    consistency: str
    heterogeneity: str
    negative_evidence: str
    strongest_supported_endpoint: str
    weakest_supported_endpoint: str
    evidence_maturity: str
    additional_engineering_burden_to_compare: str
    pending_science_that_could_change_decision: str
    decision_sensitivity_to_pending_science: str


class Stage4ArchitectureDecisionInputsScience(BaseModel):
    purpose: str
    accepted_stage3_sha: str
    final_architecture_status: str
    formal_pareto_status: str
    candidates: list[Stage4ArchitectureDecisionCandidate]
