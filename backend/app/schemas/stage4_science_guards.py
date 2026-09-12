"""Typed contracts for Stage-4 consumer-side guards added in response to the
independent Codex parent-science audit of `stage2-4-science-owner-completion`
(CONDITIONAL_PASS, 2 HIGH + several MEDIUM findings). See
`docs/STAGE4_CODEX_PARENT_AUDIT_DELTA_HARDENING.md` for the full finding map.

These guards do NOT remediate the underlying Science Owner artifacts — that
remains Science Owner scope. They exist so that Stage-4 consumers (backend
readers, frontend panels, paper/jury copy) cannot accidentally misresolve,
promote, or overstate a problematic artifact once it is eventually
integrated.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- H-01: checkpoint identity (never filename-only) -----------------------


class CheckpointProvenanceClass(StrEnum):
    """Codex finding H-01: the accepted corrected checkpoint and the
    Claude/Mac noncanonical reproduction can share a filename while having
    different hashes. `provenance_class` is the explicit dimension that
    distinguishes them — filename never is."""

    ACCEPTED = "ACCEPTED"
    NONCANONICAL_SUPPORTIVE_REPRODUCTION = "NONCANONICAL_SUPPORTIVE_REPRODUCTION"


class HashKind(StrEnum):
    """Codex MEDIUM finding (freeze-manifest CRLF/LF sensitivity): a hash is
    only meaningful together with an explicit statement of what was hashed.
    Checkpoints are binary — always RAW_BYTES. A future text-based freeze
    artifact (e.g. a JSON/CSV manifest) may need CANONICAL_TEXT_LF_NORMALIZED
    instead; the two must never be compared against each other."""

    RAW_BYTES = "RAW_BYTES"
    CANONICAL_TEXT_LF_NORMALIZED = "CANONICAL_TEXT_LF_NORMALIZED"


class CheckpointIdentity(StrictModel):
    """The authoritative identity tuple for a checkpoint. Filename is
    deliberately NOT a field here — it is carried only on `CheckpointCandidate.filename`
    as non-authoritative metadata (Codex finding H-01)."""

    experiment_version: str
    arm: str
    optimization_seed: int
    # Raw-byte SHA256 of the checkpoint file. None means "genuinely unknown",
    # never coerced to an empty/placeholder string.
    sha256: str | None = None
    hash_kind: HashKind = HashKind.RAW_BYTES
    provenance_class: CheckpointProvenanceClass
    dataset: str | None = None
    fold: str | None = None
    source_result_artifact: str | None = None


class CheckpointCandidate(StrictModel):
    filename: str  # metadata ONLY — never used to resolve identity
    path: str
    identity: CheckpointIdentity


class CheckpointResolutionErrorCode(StrEnum):
    UNAVAILABLE = "UNAVAILABLE"
    AMBIGUOUS = "AMBIGUOUS"
    HASH_MISMATCH = "HASH_MISMATCH"
    PROTOCOL_MISMATCH = "PROTOCOL_MISMATCH"
    ARM_MISMATCH = "ARM_MISMATCH"
    SEED_MISMATCH = "SEED_MISMATCH"
    MISSING_HASH = "MISSING_HASH"
    NONCANONICAL_ONLY_MATCH = "NONCANONICAL_ONLY_MATCH"


class CheckpointResolutionRequest(StrictModel):
    experiment_version: str
    arm: str
    optimization_seed: int
    sha256: str | None = None
    # If True (default), a candidate whose provenance_class is
    # NONCANONICAL_SUPPORTIVE_REPRODUCTION is never eligible, even if it is
    # the only identity-tuple match (Codex finding H-01: the noncanonical
    # Mac reproduction must never become the default checkpoint).
    require_accepted: bool = True


class CheckpointResolution(StrictModel):
    status: Literal["RESOLVED", "FAILED"]
    error_code: CheckpointResolutionErrorCode | None = None
    error: str | None = None
    resolved: CheckpointCandidate | None = None


# --- MEDIUM: stale architecture-handoff supersession ------------------------


class ArtifactSupersessionHeader(StrictModel):
    """Codex MEDIUM finding: some architecture/master artifacts describe
    stale states (e.g. HMC on another line, GalaxyPPG still access-blocked).
    Explicit versioning lets later verified evidence supersede a stale
    handoff without deleting/losing history."""

    artifact_id: str
    source_version: str
    source_sha: str | None = None
    generated_at: str | None = None
    # artifact_id of whichever artifact supersedes THIS one, if any. None
    # means this artifact is (as far as declared) not superseded.
    superseded_by: str | None = None


class SupersessionResolutionErrorCode(StrEnum):
    NO_CANDIDATES = "NO_CANDIDATES"
    ALL_SUPERSEDED = "ALL_SUPERSEDED"
    AMBIGUOUS_NON_SUPERSEDED = "AMBIGUOUS_NON_SUPERSEDED"


class SupersessionResolution(StrictModel):
    status: Literal["RESOLVED", "FAILED"]
    error_code: SupersessionResolutionErrorCode | None = None
    error: str | None = None
    authoritative: ArtifactSupersessionHeader | None = None
