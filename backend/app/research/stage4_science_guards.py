"""Fail-closed checkpoint identity resolution and artifact-supersession
resolution (Codex parent-science-audit delta hardening, findings H-01 and
the stale-architecture-handoff MEDIUM finding).

`resolve_checkpoint` NEVER matches on filename. It matches on the identity
tuple (experiment_version, arm, optimization_seed[, sha256]) and every
disagreement — hash mismatch, protocol mismatch, arm mismatch, seed
mismatch, ambiguity, or a match that is only a noncanonical reproduction —
returns a typed failure. No candidate is ever silently selected.
"""

from __future__ import annotations

import hashlib

from app.schemas.stage4_science_guards import (
    ArtifactSupersessionHeader,
    CheckpointCandidate,
    CheckpointProvenanceClass,
    CheckpointResolution,
    CheckpointResolutionErrorCode,
    CheckpointResolutionRequest,
    SupersessionResolution,
    SupersessionResolutionErrorCode,
)


def compute_raw_byte_sha256(data: bytes) -> str:
    """SHA256 of the exact bytes given — the only hash kind that makes sense
    for a binary checkpoint file. Never text-normalized."""
    return hashlib.sha256(data).hexdigest()


def compute_canonical_text_sha256(text: str) -> str:
    """SHA256 of `text` after CRLF -> LF normalization. Codex MEDIUM finding
    (freeze-manifest CRLF/LF sensitivity): this is a DIFFERENT hash from
    `compute_raw_byte_sha256` applied to the same text's raw bytes whenever
    the text contains CRLF line endings — the two must never be compared to
    each other without explicit transformation metadata stating which kind
    is which (see `HashKind` on `CheckpointIdentity`)."""
    normalized = text.replace("\r\n", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _fail(code: CheckpointResolutionErrorCode, message: str) -> CheckpointResolution:
    return CheckpointResolution(status="FAILED", error_code=code, error=message)


def resolve_checkpoint(
    candidates: list[CheckpointCandidate], request: CheckpointResolutionRequest
) -> CheckpointResolution:
    """Resolve exactly one checkpoint candidate against `request`, or fail
    closed with a typed error code. Filename (`CheckpointCandidate.filename`)
    is never read by this function — matching is on `candidate.identity`
    fields only (Codex finding H-01)."""
    if not candidates:
        return _fail(CheckpointResolutionErrorCode.UNAVAILABLE, "no candidates provided.")

    protocol_matches = [c for c in candidates if c.identity.experiment_version == request.experiment_version]
    if not protocol_matches:
        return _fail(
            CheckpointResolutionErrorCode.PROTOCOL_MISMATCH,
            f"no candidate has experiment_version={request.experiment_version!r} "
            f"(candidates declare: {sorted({c.identity.experiment_version for c in candidates})}).",
        )

    arm_matches = [c for c in protocol_matches if c.identity.arm == request.arm]
    if not arm_matches:
        return _fail(
            CheckpointResolutionErrorCode.ARM_MISMATCH,
            f"no protocol-matching candidate has arm={request.arm!r} "
            f"(protocol-matching candidates declare: {sorted({c.identity.arm for c in protocol_matches})}).",
        )

    seed_matches = [c for c in arm_matches if c.identity.optimization_seed == request.optimization_seed]
    if not seed_matches:
        return _fail(
            CheckpointResolutionErrorCode.SEED_MISMATCH,
            f"no protocol+arm-matching candidate has optimization_seed={request.optimization_seed!r} "
            f"(matching candidates declare: {sorted({c.identity.optimization_seed for c in arm_matches})}).",
        )

    if request.require_accepted:
        accepted_matches = [
            c for c in seed_matches if c.identity.provenance_class == CheckpointProvenanceClass.ACCEPTED
        ]
        if not accepted_matches:
            # Every identity-tuple match is a noncanonical supportive
            # reproduction. Never silently substitute it for the accepted
            # checkpoint the caller asked for.
            return _fail(
                CheckpointResolutionErrorCode.NONCANONICAL_ONLY_MATCH,
                f"identity tuple (version={request.experiment_version!r}, arm={request.arm!r}, "
                f"seed={request.optimization_seed!r}) only matches "
                f"NONCANONICAL_SUPPORTIVE_REPRODUCTION candidate(s); require_accepted=True refuses "
                f"to substitute one for the accepted checkpoint.",
            )
        seed_matches = accepted_matches

    if request.sha256 is not None:
        missing_hash = [c for c in seed_matches if c.identity.sha256 is None]
        if missing_hash and len(seed_matches) == len(missing_hash):
            return _fail(
                CheckpointResolutionErrorCode.MISSING_HASH,
                f"{len(missing_hash)} identity-matching candidate(s) have no recorded sha256 — "
                f"cannot verify against requested sha256={request.sha256!r}.",
            )
        hash_matches = [c for c in seed_matches if c.identity.sha256 == request.sha256]
        if not hash_matches:
            return _fail(
                CheckpointResolutionErrorCode.HASH_MISMATCH,
                f"identity tuple matched, but no candidate's sha256 equals requested "
                f"{request.sha256!r} (matching candidates' hashes: "
                f"{sorted(c.identity.sha256 for c in seed_matches if c.identity.sha256)}).",
            )
        seed_matches = hash_matches

    if len(seed_matches) > 1:
        return _fail(
            CheckpointResolutionErrorCode.AMBIGUOUS,
            f"{len(seed_matches)} candidates share the full requested identity — cannot "
            f"disambiguate without an additional distinguishing field.",
        )

    resolved = seed_matches[0]
    if resolved.identity.sha256 is None:
        return _fail(
            CheckpointResolutionErrorCode.MISSING_HASH,
            f"resolved candidate at {resolved.path!r} has no recorded sha256 — cannot be "
            f"returned as a verified resolution.",
        )

    return CheckpointResolution(status="RESOLVED", resolved=resolved)


def resolve_authoritative_artifact(candidates: list[ArtifactSupersessionHeader]) -> SupersessionResolution:
    """Return the single non-superseded candidate, or fail closed. Never
    assumes the first/oldest candidate in `candidates` is authoritative
    merely by list/file-system order — only the explicit `superseded_by`
    field determines supersession (Codex MEDIUM finding: stale architecture
    handoffs)."""
    if not candidates:
        return SupersessionResolution(status="FAILED", error_code=SupersessionResolutionErrorCode.NO_CANDIDATES, error="no candidates provided.")

    non_superseded = [c for c in candidates if c.superseded_by is None]
    if not non_superseded:
        return SupersessionResolution(
            status="FAILED",
            error_code=SupersessionResolutionErrorCode.ALL_SUPERSEDED,
            error=f"all {len(candidates)} candidate(s) declare superseded_by; none is authoritative.",
        )
    if len(non_superseded) > 1:
        return SupersessionResolution(
            status="FAILED",
            error_code=SupersessionResolutionErrorCode.AMBIGUOUS_NON_SUPERSEDED,
            error=f"{len(non_superseded)} candidates are non-superseded for the same subject: "
            f"{[c.artifact_id for c in non_superseded]} — supersession must be made explicit.",
        )

    return SupersessionResolution(status="RESOLVED", authoritative=non_superseded[0])
