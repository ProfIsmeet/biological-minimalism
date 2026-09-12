"""Sleep-EDF V1/V2 protocol-version safety guard (Stage 1A, Day 12).

Background: H1 (see docs/SLEEP_SEEDING_PROTOCOL_V2.md and
docs/CLAUDE_H1_H2_SCIENTIFIC_REMEDIATION_HANDOFF.md) found that historical
Sleep-EDF trainers constructed the model before seeding torch's RNG, so the
recorded seed never controlled initial weights. A corrected protocol
(`ml/sleep_seed_utils.py`) was used to retrain Primary A/B under 5
seed-controlled runs each (`results/sleep_edf_primary_seedfix_v2.json`).
Shuffled-EOG control C and the interaction experiment (M_B/M_AB) were NOT
retrained under the corrected protocol this sprint and remain
PENDING_FOLLOWUP.

This module exists to make one failure mode structurally impossible: silently
combining a V2 (corrected-seed) result with a V1 (historical) result into a
single derived comparison (e.g. "corrected B minus historical C"), which
would mix two different training protocols and misrepresent what was
actually measured. Every cross-operand comparison in the Sleep-EDF research
surface must be routed through `resolve_version_safe_comparison` rather than
computed ad hoc.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

T = TypeVar("T")


class SleepProtocolVersion(str, Enum):
    """Which seeding protocol trained the checkpoints behind a given result."""

    V1_HISTORICAL = "V1_HISTORICAL"
    V2_SEEDFIX_CORRECTED = "V2_SEEDFIX_CORRECTED"
    UNKNOWN = "UNKNOWN"


class SleepResultStatus(str, Enum):
    """Machine-readable availability state for a Sleep-EDF experiment family."""

    V2_AVAILABLE = "V2_AVAILABLE"
    V2_PENDING_FOLLOWUP = "V2_PENDING_FOLLOWUP"
    V1_ONLY = "V1_ONLY"
    MALFORMED = "MALFORMED"


@dataclass(frozen=True)
class SleepComparisonResult(Generic[T]):
    """Outcome of attempting a version-gated comparison.

    `available=False` is the safe default for any ambiguity; callers must
    never fall back to computing the value anyway.
    """

    available: bool
    reason: str
    value: T | None = None


def resolve_version_safe_comparison(
    operand_a_version: SleepProtocolVersion,
    operand_b_version: SleepProtocolVersion,
    compute: Callable[[], T],
) -> SleepComparisonResult[T]:
    """Compute a comparison between two operands only if their protocol
    versions match exactly and are both known.

    This is the single choke point every cross-operand Sleep-EDF comparison
    (B-A, B-C, interaction legs) must pass through. It blocks:
      - either operand's version being UNKNOWN (malformed/missing metadata),
      - the two operands' versions differing (the mixed-protocol bug this
        module exists to prevent, e.g. V2 B minus V1 C).
    """
    if operand_a_version is SleepProtocolVersion.UNKNOWN or operand_b_version is SleepProtocolVersion.UNKNOWN:
        return SleepComparisonResult(
            available=False,
            reason="MALFORMED_UNKNOWN_PROTOCOL_VERSION",
        )
    if operand_a_version is not operand_b_version:
        return SleepComparisonResult(
            available=False,
            reason=(
                "BLOCKED_MIXED_PROTOCOL_VERSION:"
                f"{operand_a_version.value}_vs_{operand_b_version.value}"
            ),
        )
    return SleepComparisonResult(
        available=True,
        reason=f"VERSION_CONSISTENT:{operand_a_version.value}",
        value=compute(),
    )
