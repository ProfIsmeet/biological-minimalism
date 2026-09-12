"""Adversarial tests for the Sleep-EDF V1/V2 protocol-version guard
(Stage 1A §36, Cases A-F) and for the integrated catalog adapter's
version-safety behavior. The failure mode under test: silently combining a
V2 (corrected-seed) result with a V1 (historical) result into one derived
comparison, e.g. a "corrected B minus historical C"."""

from __future__ import annotations

from app.research.catalog import ResearchCatalog
from app.research.sleep_version_guard import (
    SleepProtocolVersion,
    SleepResultStatus,
    resolve_version_safe_comparison,
)


# --- Section 36 Case A: only V1 exists -> historical display only ---------

def test_case_a_v1_only_is_available_and_labeled_historical() -> None:
    result = resolve_version_safe_comparison(
        SleepProtocolVersion.V1_HISTORICAL, SleepProtocolVersion.V1_HISTORICAL,
        compute=lambda: 0.0220,
    )
    assert result.available is True
    assert result.value == 0.0220
    assert "V1_HISTORICAL" in result.reason


# --- Section 36 Case B: V2 A/B exists, V2 C missing -> B-A available, B-C unavailable ---

def test_case_b_v2_b_minus_a_available() -> None:
    result = resolve_version_safe_comparison(
        SleepProtocolVersion.V2_SEEDFIX_CORRECTED, SleepProtocolVersion.V2_SEEDFIX_CORRECTED,
        compute=lambda: 0.0282,
    )
    assert result.available is True
    assert result.value == 0.0282


def test_case_b_v2_b_minus_c_unavailable_when_c_has_no_v2() -> None:
    # C's protocol version is UNKNOWN because no V2 retraining exists for it yet.
    result = resolve_version_safe_comparison(
        SleepProtocolVersion.V2_SEEDFIX_CORRECTED, SleepProtocolVersion.UNKNOWN,
        compute=lambda: (_ for _ in ()).throw(AssertionError("must not compute when unavailable")),
    )
    assert result.available is False
    assert result.reason == "MALFORMED_UNKNOWN_PROTOCOL_VERSION"


# --- Section 36 Case C: V2 B + V1 C -> must NOT derive corrected B-C ------

def test_case_c_mixed_v2_b_v1_c_is_blocked() -> None:
    result = resolve_version_safe_comparison(
        SleepProtocolVersion.V2_SEEDFIX_CORRECTED, SleepProtocolVersion.V1_HISTORICAL,
        compute=lambda: (_ for _ in ()).throw(AssertionError("must not compute a mixed-version comparison")),
    )
    assert result.available is False
    assert result.reason == "BLOCKED_MIXED_PROTOCOL_VERSION:V2_SEEDFIX_CORRECTED_vs_V1_HISTORICAL"
    assert result.value is None


def test_case_c_is_symmetric() -> None:
    """Order of operands must not matter -- V1 vs V2 is blocked either way."""
    result = resolve_version_safe_comparison(
        SleepProtocolVersion.V1_HISTORICAL, SleepProtocolVersion.V2_SEEDFIX_CORRECTED,
        compute=lambda: (_ for _ in ()).throw(AssertionError("must not compute")),
    )
    assert result.available is False


# --- Section 36 Case D: V2 interaction incomplete -> corrected interaction unavailable ---

def test_case_d_incomplete_v2_interaction_unavailable() -> None:
    # M_B has no V2 retraining (UNKNOWN); M_AB likewise. Any attempt to derive
    # a "corrected interaction" from a partially-V2 state must fail closed.
    result = resolve_version_safe_comparison(
        SleepProtocolVersion.UNKNOWN, SleepProtocolVersion.UNKNOWN,
        compute=lambda: (_ for _ in ()).throw(AssertionError("must not compute")),
    )
    assert result.available is False
    assert result.reason == "MALFORMED_UNKNOWN_PROTOCOL_VERSION"


# --- Section 36 Case E: historical interaction requested -> available only version-qualified ---

def test_case_e_historical_interaction_available_when_both_legs_v1() -> None:
    result = resolve_version_safe_comparison(
        SleepProtocolVersion.V1_HISTORICAL, SleepProtocolVersion.V1_HISTORICAL,
        compute=lambda: "approximately_additive_or_unresolved",
    )
    assert result.available is True
    assert result.reason == "VERSION_CONSISTENT:V1_HISTORICAL"


# --- Section 36 Case F: unknown protocol version -> MALFORMED, never silent PASS ---

def test_case_f_unknown_version_never_silently_passes() -> None:
    for a, b in (
        (SleepProtocolVersion.UNKNOWN, SleepProtocolVersion.V1_HISTORICAL),
        (SleepProtocolVersion.V2_SEEDFIX_CORRECTED, SleepProtocolVersion.UNKNOWN),
        (SleepProtocolVersion.UNKNOWN, SleepProtocolVersion.UNKNOWN),
    ):
        result = resolve_version_safe_comparison(a, b, compute=lambda: (_ for _ in ()).throw(AssertionError("must not compute")))
        assert result.available is False
        assert result.reason == "MALFORMED_UNKNOWN_PROTOCOL_VERSION"


def test_result_status_enum_has_no_implicit_pass_state() -> None:
    """H3's lesson (never default to PASS) applies to Sleep versioning too:
    there must be no status value that reads as an unconditional success."""
    values = {member.value for member in SleepResultStatus}
    assert values == {"V2_AVAILABLE", "V2_PENDING_FOLLOWUP", "V1_ONLY", "MALFORMED"}
    assert "PASS" not in values


# --- Integration: the actual catalog adapter must honor the guard ---------

def test_sleep_adapter_headline_is_v2_and_historical_is_preserved() -> None:
    experiment = ResearchCatalog().get("sleep-edf-eeg-eog-ablation").experiment
    mr = experiment.marginal_result
    assert mr is not None
    assert mr.headline_comparison_id == "seed_corrected_v2_primary_ab"

    by_id = {c.comparison_id: c for c in mr.controlled_comparisons}
    assert by_id["historical_v1_primary_ab"].role == "HISTORICAL_PRE_SEEDFIX_V1_RESULT"
    assert by_id["historical_v1_primary_ab"].delta.mean is not None
    assert by_id["seed_corrected_v2_primary_ab"].role == "SEED_CORRECTED_PREFERRED_V2"
    assert by_id["seed_corrected_v2_primary_ab"].delta.mean is not None
    # Headline delta must equal the V2 comparison's own delta, not a blend.
    assert mr.delta.mean == by_id["seed_corrected_v2_primary_ab"].delta.mean


def test_sleep_adapter_pending_families_have_no_fabricated_value() -> None:
    """C and the interaction legs must never carry a computed delta -- that
    would mean someone silently derived a mixed-version (or reused V1)
    number under a V2-sounding label."""
    experiment = ResearchCatalog().get("sleep-edf-eeg-eog-ablation").experiment
    by_id = {c.comparison_id: c for c in experiment.marginal_result.controlled_comparisons}
    for cid in (
        "seed_correction_pending_shuffled_eog_c",
        "seed_correction_pending_interaction_m_b",
        "seed_correction_pending_interaction_m_ab",
    ):
        comparison = by_id[cid]
        assert comparison.role == "SEED_CORRECTION_PENDING_FOLLOWUP"
        assert comparison.delta.mean is None
        assert comparison.n_seeds is None
        assert comparison.n_seeds_favor_candidate is None


def test_sleep_adapter_version_state_breakdown_never_marks_pending_as_preferred() -> None:
    experiment = ResearchCatalog().get("sleep-edf-eeg-eog-ablation").experiment
    version_state = next(b for b in experiment.breakdowns if b.breakdown_id == "sleep_v1_v2_version_state")
    by_id = {e.entry_id: e for e in version_state.entries}

    assert by_id["primary_ab"].dimensions["result_status"] == "V2_AVAILABLE"
    assert by_id["primary_ab"].dimensions["preferred_for_current_claim"] is True

    for family in ("shuffled_eog_c", "interaction_m_b", "interaction_m_ab"):
        entry = by_id[family]
        assert entry.dimensions["result_status"] == "V2_PENDING_FOLLOWUP"
        assert entry.dimensions["preferred_for_current_claim"] is False


def test_sleep_adapter_checkpoint_inventory_never_overstates_external_archival() -> None:
    """Stage 1A §30: the 10 new seedfix_v2 checkpoints exist locally but were
    not externally archived this sprint -- the version-state breakdown must
    say so explicitly rather than imply full durability."""
    experiment = ResearchCatalog().get("sleep-edf-eeg-eog-ablation").experiment
    version_state = next(b for b in experiment.breakdowns if b.breakdown_id == "sleep_v1_v2_version_state")
    primary_entry = next(e for e in version_state.entries if e.entry_id == "primary_ab")
    assert "external_archive=False" in str(primary_entry.dimensions["checkpoint_set"])
