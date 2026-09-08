"""Cache provenance schema for Stage-2 dataset expansion loaders (Stage 1B, spec-only).

This module defines the reusable provenance record that every new Stage-2
dataset cache (GalaxyPPG, HMC, QDE V2, LBNP, ds003838) should attach to its
preprocessed/cached tensors, so a cached file can always be traced back to
the exact raw source file, preprocessing version, and protocol version that
produced it - avoiding the current project's PPG/PTT cache-provenance
ambiguity (flagged, not yet resolved elsewhere in the repo).

Not wired into any existing loader by this sprint - see
docs/STAGE1B_DATASET_EXPANSION_FEASIBILITY_REPORT.md Section 19 for why
(avoiding touching shared loader infrastructure while Claude's Stage 1A
integration is in flight, per this sprint's parallel-work boundary).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CacheProvenance:
    dataset_id: str
    dataset_version: str
    subject_id: str
    session_id: str
    raw_file_sha256: str
    protocol_version: str
    preprocessing_version: str
    split_version: str
    native_rate_metadata: dict
    created_by_commit: str

    def to_dict(self) -> dict:
        return {
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "subject_id": self.subject_id,
            "session_id": self.session_id,
            "raw_file_sha256": self.raw_file_sha256,
            "protocol_version": self.protocol_version,
            "preprocessing_version": self.preprocessing_version,
            "split_version": self.split_version,
            "native_rate_metadata": self.native_rate_metadata,
            "created_by_commit": self.created_by_commit,
        }
