"""Adversarial tests for checkpoint identity resolution and artifact
supersession (Codex parent-science-audit delta hardening, finding H-01 and
the stale-architecture-handoff / hash-semantics MEDIUM findings).

Failure mode under test throughout: checkpoint identity must never resolve
by filename alone. Every disagreement (hash, protocol, arm, seed, ambiguity,
noncanonical-only match) must fail closed with a typed error code — no
candidate is ever silently selected.
"""

from __future__ import annotations

from app.research.stage4_science_guards import (
    compute_canonical_text_sha256,
    compute_raw_byte_sha256,
    resolve_authoritative_artifact,
    resolve_checkpoint,
)
from app.schemas.stage4_science_guards import (
    ArtifactSupersessionHeader,
    CheckpointCandidate,
    CheckpointIdentity,
    CheckpointProvenanceClass,
    CheckpointResolutionErrorCode,
    CheckpointResolutionRequest,
    SupersessionResolutionErrorCode,
)

# All candidates below deliberately share the SAME filename — the exact
# collision Codex found — to prove resolution never depends on it.
_SHARED_FILENAME = "sleep_edf_v2_A_B_seed3.pt"
_ACCEPTED_SHA = "a" * 64
_NONCANONICAL_SHA = "b" * 64


def _candidate(
    *, version: str, arm: str, seed: int, sha: str | None, provenance_class: CheckpointProvenanceClass, path: str
) -> CheckpointCandidate:
    return CheckpointCandidate(
        filename=_SHARED_FILENAME,
        path=path,
        identity=CheckpointIdentity(
            experiment_version=version, arm=arm, optimization_seed=seed, sha256=sha, provenance_class=provenance_class
        ),
    )


def test_identical_filename_different_hash_resolves_to_requested_hash_only() -> None:
    accepted = _candidate(version="V2", arm="B", seed=3, sha=_ACCEPTED_SHA, provenance_class=CheckpointProvenanceClass.ACCEPTED, path="/ckpt/accepted.pt")
    mac_repro = _candidate(version="V2", arm="B", seed=3, sha=_NONCANONICAL_SHA, provenance_class=CheckpointProvenanceClass.NONCANONICAL_SUPPORTIVE_REPRODUCTION, path="/ckpt/mac_repro.pt")
    assert accepted.filename == mac_repro.filename  # the exact collision

    request = CheckpointResolutionRequest(experiment_version="V2", arm="B", optimization_seed=3, sha256=_ACCEPTED_SHA)
    result = resolve_checkpoint([accepted, mac_repro], request)
    assert result.status == "RESOLVED"
    assert result.resolved.path == "/ckpt/accepted.pt"


def test_identical_filename_wrong_hash_fails_hash_mismatch_not_silent_fallback() -> None:
    accepted = _candidate(version="V2", arm="B", seed=3, sha=_ACCEPTED_SHA, provenance_class=CheckpointProvenanceClass.ACCEPTED, path="/ckpt/accepted.pt")
    request = CheckpointResolutionRequest(experiment_version="V2", arm="B", optimization_seed=3, sha256="c" * 64)
    result = resolve_checkpoint([accepted], request)
    assert result.status == "FAILED"
    assert result.error_code == CheckpointResolutionErrorCode.HASH_MISMATCH
    assert result.resolved is None


def test_identical_filename_different_protocol_fails_protocol_mismatch() -> None:
    v1 = _candidate(version="V1", arm="B", seed=3, sha=_ACCEPTED_SHA, provenance_class=CheckpointProvenanceClass.ACCEPTED, path="/ckpt/v1.pt")
    request = CheckpointResolutionRequest(experiment_version="V2", arm="B", optimization_seed=3)
    result = resolve_checkpoint([v1], request)
    assert result.status == "FAILED"
    assert result.error_code == CheckpointResolutionErrorCode.PROTOCOL_MISMATCH


def test_identical_filename_different_arm_fails_arm_mismatch() -> None:
    arm_a = _candidate(version="V2", arm="A", seed=3, sha=_ACCEPTED_SHA, provenance_class=CheckpointProvenanceClass.ACCEPTED, path="/ckpt/armA.pt")
    request = CheckpointResolutionRequest(experiment_version="V2", arm="B", optimization_seed=3)
    result = resolve_checkpoint([arm_a], request)
    assert result.status == "FAILED"
    assert result.error_code == CheckpointResolutionErrorCode.ARM_MISMATCH


def test_different_seed_fails_seed_mismatch() -> None:
    seed5 = _candidate(version="V2", arm="B", seed=5, sha=_ACCEPTED_SHA, provenance_class=CheckpointProvenanceClass.ACCEPTED, path="/ckpt/seed5.pt")
    request = CheckpointResolutionRequest(experiment_version="V2", arm="B", optimization_seed=3)
    result = resolve_checkpoint([seed5], request)
    assert result.status == "FAILED"
    assert result.error_code == CheckpointResolutionErrorCode.SEED_MISMATCH


def test_missing_hash_fails_closed_never_treated_as_match() -> None:
    no_hash = _candidate(version="V2", arm="B", seed=3, sha=None, provenance_class=CheckpointProvenanceClass.ACCEPTED, path="/ckpt/unknown_hash.pt")
    request_with_hash = CheckpointResolutionRequest(experiment_version="V2", arm="B", optimization_seed=3, sha256=_ACCEPTED_SHA)
    result = resolve_checkpoint([no_hash], request_with_hash)
    assert result.status == "FAILED"
    assert result.error_code == CheckpointResolutionErrorCode.MISSING_HASH

    # Even without a requested hash, a resolved candidate with no recorded
    # hash must not be returned as a verified resolution.
    request_no_hash = CheckpointResolutionRequest(experiment_version="V2", arm="B", optimization_seed=3)
    result2 = resolve_checkpoint([no_hash], request_no_hash)
    assert result2.status == "FAILED"
    assert result2.error_code == CheckpointResolutionErrorCode.MISSING_HASH


def test_ambiguous_candidates_fail_closed() -> None:
    dup_a = _candidate(version="V2", arm="B", seed=3, sha=_ACCEPTED_SHA, provenance_class=CheckpointProvenanceClass.ACCEPTED, path="/ckpt/dup_a.pt")
    dup_b = _candidate(version="V2", arm="B", seed=3, sha=_ACCEPTED_SHA, provenance_class=CheckpointProvenanceClass.ACCEPTED, path="/ckpt/dup_b.pt")
    request = CheckpointResolutionRequest(experiment_version="V2", arm="B", optimization_seed=3, sha256=_ACCEPTED_SHA)
    result = resolve_checkpoint([dup_a, dup_b], request)
    assert result.status == "FAILED"
    assert result.error_code == CheckpointResolutionErrorCode.AMBIGUOUS


def test_noncanonical_only_match_never_silently_substituted() -> None:
    """The exact H-01 scenario: only a NONCANONICAL_SUPPORTIVE_REPRODUCTION
    candidate matches the requested identity. require_accepted=True (the
    default) must refuse to return it as the accepted checkpoint."""
    mac_repro = _candidate(version="V2", arm="B", seed=3, sha=_NONCANONICAL_SHA, provenance_class=CheckpointProvenanceClass.NONCANONICAL_SUPPORTIVE_REPRODUCTION, path="/ckpt/mac_repro.pt")
    request = CheckpointResolutionRequest(experiment_version="V2", arm="B", optimization_seed=3)
    result = resolve_checkpoint([mac_repro], request)
    assert result.status == "FAILED"
    assert result.error_code == CheckpointResolutionErrorCode.NONCANONICAL_ONLY_MATCH
    assert result.resolved is None


def test_empty_candidate_list_is_unavailable() -> None:
    request = CheckpointResolutionRequest(experiment_version="V2", arm="B", optimization_seed=3)
    result = resolve_checkpoint([], request)
    assert result.status == "FAILED"
    assert result.error_code == CheckpointResolutionErrorCode.UNAVAILABLE


def test_filename_is_never_read_by_the_resolver() -> None:
    """Two candidates with DIFFERENT filenames but the correct identity/hash
    must still resolve — proving filename plays no role either way."""
    accepted = CheckpointCandidate(
        filename="totally_different_name.bin",
        path="/ckpt/accepted.pt",
        identity=CheckpointIdentity(experiment_version="V2", arm="B", optimization_seed=3, sha256=_ACCEPTED_SHA, provenance_class=CheckpointProvenanceClass.ACCEPTED),
    )
    request = CheckpointResolutionRequest(experiment_version="V2", arm="B", optimization_seed=3, sha256=_ACCEPTED_SHA)
    result = resolve_checkpoint([accepted], request)
    assert result.status == "RESOLVED"


# --- Hash semantics: raw-byte vs canonical-text -----------------------------


def test_raw_byte_vs_canonical_text_hash_are_genuinely_distinct() -> None:
    """Codex MEDIUM finding (freeze-manifest CRLF/LF sensitivity): the same
    logical text with different line endings must produce DIFFERENT
    raw-byte hashes but the SAME canonical-text hash — proving the two hash
    kinds are not interchangeable and must carry explicit kind metadata."""
    crlf_text = "line1\r\nline2\r\n"
    lf_text = "line1\nline2\n"

    raw_crlf = compute_raw_byte_sha256(crlf_text.encode("utf-8"))
    raw_lf = compute_raw_byte_sha256(lf_text.encode("utf-8"))
    assert raw_crlf != raw_lf, "raw-byte hashes of CRLF vs LF text must differ"

    canonical_crlf = compute_canonical_text_sha256(crlf_text)
    canonical_lf = compute_canonical_text_sha256(lf_text)
    assert canonical_crlf == canonical_lf, "canonical-text hashes must agree after LF normalization"

    # The two hash KINDS must never be blindly compared against each other.
    assert raw_crlf != canonical_crlf


# --- Stale architecture-handoff supersession --------------------------------


def test_stale_architecture_artifact_can_be_superseded() -> None:
    stale = ArtifactSupersessionHeader(artifact_id="hmc_handoff_v1", source_version="v1", superseded_by="hmc_handoff_v2")
    current = ArtifactSupersessionHeader(artifact_id="hmc_handoff_v2", source_version="v2")
    # Deliberately list the STALE one first — resolution must not depend on
    # list order / "oldest handoff found first."
    result = resolve_authoritative_artifact([stale, current])
    assert result.status == "RESOLVED"
    assert result.authoritative.artifact_id == "hmc_handoff_v2"


def test_all_superseded_fails_closed() -> None:
    a = ArtifactSupersessionHeader(artifact_id="a", source_version="v1", superseded_by="b")
    b = ArtifactSupersessionHeader(artifact_id="b", source_version="v2", superseded_by="c")
    result = resolve_authoritative_artifact([a, b])
    assert result.status == "FAILED"
    assert result.error_code == SupersessionResolutionErrorCode.ALL_SUPERSEDED


def test_ambiguous_non_superseded_fails_closed() -> None:
    a = ArtifactSupersessionHeader(artifact_id="a", source_version="v1")
    b = ArtifactSupersessionHeader(artifact_id="b", source_version="v1-alt")
    result = resolve_authoritative_artifact([a, b])
    assert result.status == "FAILED"
    assert result.error_code == SupersessionResolutionErrorCode.AMBIGUOUS_NON_SUPERSEDED


def test_no_candidates_fails_closed() -> None:
    result = resolve_authoritative_artifact([])
    assert result.status == "FAILED"
    assert result.error_code == SupersessionResolutionErrorCode.NO_CANDIDATES
