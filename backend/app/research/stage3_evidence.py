"""Stage-3 accepted governing science, consumed ONLY through the
integrity-verified resolver `ml.stage3_science_resolver.resolve_current`.

This module is the single Stage-4 bridge onto Stage-3's frozen, accepted
scientific state (governing prompt Part III/IV). It never reads
`results/*.json` directly and never duplicates the resolver's governance
logic - every family's content comes from `resolve_current(family_id)`,
which independently re-verifies registry status, live semantic content,
and freeze-manifest hash integrity before returning anything. On any
governance or integrity failure this module fails closed
(`Stage3EvidenceUnavailable`), it never substitutes an unverified helper
and never falls back to a hard-coded path.

Distinct from `app.research.future_science_ingestion`, which remains the
placeholder for Ismet's *future* (not-yet-arrived) Stage-4 science
handoff package - that concern is untouched by this module.
"""

from __future__ import annotations

import json
import sys

from app.research.catalog import REPOSITORY_ROOT
from app.schemas.stage3_evidence import (
    Stage3ArtifactType,
    Stage3EvidenceEntry,
    Stage3EvidenceEnvelope,
)

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.stage3_science_resolver import (  # noqa: E402
    GovernanceResolutionError,
    IntegrityVerificationError,
    list_families,
    resolve_current,
)

REGISTRY_PATH = "results/stage3_governance_registry.json"
FREEZE_MANIFEST_PATH = "results/stage3_scientific_freeze_manifest.json"


class Stage3EvidenceUnavailable(RuntimeError):
    """Raised when governing Stage-3 evidence cannot be safely resolved.

    Fail closed: callers must surface this as an error, never substitute
    unverified or historical content in its place.
    """


def _g(d: dict | None, *path: str, default=None):
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _subject_count(protocol: dict | None, split_key: str = "subject_split") -> int | None:
    split = _g(protocol, split_key)
    if not isinstance(split, dict):
        return None
    total = 0
    found = False
    for cohort in ("train", "val", "test"):
        members = split.get(cohort)
        if isinstance(members, list):
            total += len(members)
            found = True
    return total if found else None


def _seed_count(protocol: dict | None) -> int | None:
    seeds = _g(protocol, "seeds")
    if isinstance(seeds, list):
        return len(seeds)
    return None


# --- per-family extractors -------------------------------------------------
# Each extractor returns a dict of Stage3EvidenceEntry fields, pulled only
# from keys verified present in the actual resolved artifact content. Any
# field not found stays None (UNKNOWN) rather than defaulting to zero.


def _x_galaxyppg_external_replication(c: dict) -> dict:
    agg = _g(c, "aggregate_across_all_18_eligible_subjects", default={})
    a_to_b, c_to_b = _g(agg, "A_to_B", default={}), _g(agg, "C_to_B", default={})
    return dict(
        experiment_id=c.get("experiment_id"),
        classification=c.get("final_classification"),
        biological_subject_n=_g(a_to_b, "n_subjects_total"),
        primary_comparison_label="A_cap -> B (participant-level mean MAE delta)",
        primary_effect_value=_g(a_to_b, "mean"),
        primary_effect_unit="bpm",
        secondary_comparison_label="C -> B (participant-level mean MAE delta)",
        secondary_effect_value=_g(c_to_b, "mean"),
        secondary_effect_unit="bpm",
        heterogeneity_note=(
            f"{_g(a_to_b, 'n_subjects_favor_B')}/{_g(a_to_b, 'n_subjects_total')} subjects favor B over A_cap; "
            f"{_g(c_to_b, 'n_subjects_favor_B')}/{_g(c_to_b, 'n_subjects_total')} favor B over C"
        ),
        limitation=c.get("final_classification_rationale"),
    )


def _x_galaxyppg_eligibility_qc(c: dict) -> dict:
    return dict(
        biological_subject_n=c.get("n_total"),
        held_out_or_reduced_n=c.get("n_eligible"),
        summary=c.get("gate"),
        limitation=c.get("p01_specific_adjudication"),
        provenance_doc=c.get("qc_source"),
    )


def _x_ppg_dalia_capacity_control(c: dict) -> dict:
    protocol = _g(c, "frozen_protocol", default={})
    seeds = _g(protocol, "training_seeds")
    pc = _g(c, "primary_comparisons", default={})
    a_to_b, c_to_b = _g(pc, "baseline_Acap_candidate_B", default={}), _g(pc, "baseline_C_candidate_B", default={})
    return dict(
        experiment_id=c.get("experiment_id"),
        biological_subject_n=_subject_count(protocol),
        optimization_seed_n=len(seeds) if isinstance(seeds, list) else None,
        primary_comparison_label="A_cap -> B (capacity-controlled MAE delta)",
        primary_effect_value=_g(a_to_b, "mean"),
        primary_effect_unit="bpm",
        secondary_comparison_label="C -> B (capacity-controlled MAE delta)",
        secondary_effect_value=_g(c_to_b, "mean"),
        secondary_effect_unit="bpm",
        heterogeneity_note=(
            f"{_g(a_to_b, 'n_seeds_candidate_better')}/{_g(a_to_b, 'n_seeds_total')} seeds favor B over A_cap"
        ),
        limitation="Capacity-controlled comparison (A_cap, not the raw-parameter-count A); "
        "do not conflate with the historical capacity-confounded ~20.6%/23% figure.",
        provenance_doc=c.get("predeclaration"),
    )


def _sleep_ab_fields(c: dict) -> dict:
    protocol = _g(c, "frozen_protocol", default={})
    agg = _g(c, "aggregate", default={})
    delta = _g(agg, "delta_candidate_minus_baseline", default={})
    return dict(
        experiment_id=c.get("experiment_id"),
        biological_subject_n=_subject_count(protocol),
        optimization_seed_n=_seed_count(protocol),
        primary_comparison_label="candidate (EEG+EOG) - baseline (EEG only), macro-F1",
        primary_effect_value=_g(delta, "mean"),
        primary_effect_unit="macro_f1",
        heterogeneity_note=f"{_g(delta, 'n_seeds_candidate_better')}/{_g(delta, 'n_seeds_total')} seeds favor candidate",
        limitation=c.get("purpose"),
        provenance_doc=c.get("seeding_protocol_doc"),
    )


def _x_sleep_edf_primary_ab(c: dict) -> dict:
    return _sleep_ab_fields(c)


def _x_sleep_edf_shuffled_control_c(c: dict) -> dict:
    protocol = _g(c, "frozen_protocol", default={})
    return dict(
        experiment_id=c.get("experiment_id"),
        biological_subject_n=_subject_count(protocol),
        optimization_seed_n=_seed_count(protocol),
        summary=c.get("purpose"),
        provenance_doc=c.get("seeding_protocol_doc"),
    )


def _x_sleep_edf_interaction(c: dict) -> dict:
    protocol = _g(c, "frozen_protocol", default={})
    agg = _g(c, "aggregate", default={})
    interaction = _g(agg, "interaction_term", default={})
    return dict(
        experiment_id=c.get("experiment_id"),
        biological_subject_n=_subject_count(protocol),
        optimization_seed_n=_seed_count(protocol),
        classification=agg.get("stability_classification"),
        primary_comparison_label="EEG x EOG x Resp interaction term (macro-F1)",
        primary_effect_value=_g(interaction, "mean"),
        primary_effect_unit="macro_f1 (interaction term)",
        heterogeneity_note=(
            f"{_g(interaction, 'n_seeds_positive')} positive / {_g(interaction, 'n_seeds_negative')} negative "
            f"of {_g(interaction, 'n_seeds_total')} seeds"
        ),
        limitation="Interaction is mixed/unresolved; do not present as strong modality synergy.",
        provenance_doc=c.get("seeding_protocol_doc"),
    )


def _x_ptt_second_ppg_site(c: dict) -> dict:
    cfg = _g(c, "config", default={})
    agg = _g(c, "aggregate", default={})
    delta = _g(agg, "paired_delta_mae_b_minus_a", default={})
    n_train, n_val, n_test = cfg.get("n_train_subjects"), cfg.get("n_val_subjects"), cfg.get("n_test_subjects")
    total_n = (
        (n_train or 0) + (n_val or 0) + (n_test or 0)
        if any(v is not None for v in (n_train, n_val, n_test))
        else None
    )
    return dict(
        biological_subject_n=total_n,
        optimization_seed_n=len(cfg["training_seeds"]) if isinstance(cfg.get("training_seeds"), list) else None,
        primary_comparison_label="Model B (second PPG site) - Model A, MAE delta",
        primary_effect_value=delta.get("mean"),
        primary_effect_unit="bpm",
        limitation="Second-site PPG evidence is fragile/mixed; sensitivity can flip direction. "
        "Treat as deprioritized/mixed, not a positive controlled result.",
    )


def _x_qde_v2_leg_bioz(c: dict) -> dict:
    agg = _g(c, "aggregate", default={})
    return dict(
        # NOTE: this artifact declares no self-contained classification/status
        # field (unlike GalaxyPPG's final_classification or LBNP's
        # classification) - leave classification=None (UNKNOWN) rather than
        # asserting one; the interpretive characterization lives only in
        # `limitation` below as prose, not as a fabricated extracted field.
        biological_subject_n=c.get("n_subjects"),
        primary_comparison_label="A (arm+trunk) - B (arm+trunk+legs), subject-macro MAE",
        primary_effect_value=agg.get("A_minus_B_mean"),
        primary_effect_unit="mae (arbitrary target units)",
        secondary_comparison_label="C (deranged legs) - B, subject-macro MAE",
        secondary_effect_value=agg.get("C_minus_B_mean"),
        secondary_effect_unit="mae (arbitrary target units)",
        heterogeneity_note=(
            f"{agg.get('n_subjects_favoring_B_over_A')}/{c.get('n_subjects')} favor B over A; "
            f"{agg.get('n_subjects_favoring_B_over_C')}/{c.get('n_subjects')} favor B over C"
        ),
        limitation="Aggregate negative/heterogeneous/sensitivity-fragile. "
        "Do not generalize to universal BioZ uselessness.",
        provenance_doc=c.get("frozen_protocol_reference"),
    )


def _x_lbnp_thoracic_eis(c: dict) -> dict:
    agg = _g(c, "aggregate", default={})
    loo = _g(c, "leave_one_subject_out_sensitivity", default={})
    return dict(
        experiment_id=c.get("experiment_id"),
        classification=c.get("classification"),
        biological_subject_n=c.get("n_subjects"),
        primary_comparison_label="A (ECG+pleth) - B (+thoracic EIS), subject-macro MAE",
        primary_effect_value=agg.get("A_minus_B_mean"),
        primary_effect_unit="mmHg-context MAE",
        secondary_comparison_label="C (deranged EIS) - B, subject-macro MAE",
        secondary_effect_value=agg.get("C_minus_B_mean"),
        secondary_effect_unit="mmHg-context MAE",
        heterogeneity_note=(
            f"{agg.get('n_subjects_favoring_B_over_A')}/{agg.get('n_subjects_total')} favor B over A; "
            f"{agg.get('n_subjects_favoring_B_over_C')}/{agg.get('n_subjects_total')} favor B over C; "
            f"A-B sign reverses under LOO: {_g(loo, 'A_minus_B', 'any_single_subject_reverses_sign')}"
        ),
        limitation=c.get("classification_rationale"),
        provenance_doc=c.get("frozen_protocol_reference"),
    )


def _x_hmc_bounded_diagnostic(c: dict) -> dict:
    agg = _g(c, "aggregate", default={})
    b_minus_a = _g(agg, "B_minus_A", default={})
    return dict(
        experiment_id=c.get("experiment_id"),
        classification=c.get("cohort_type"),
        biological_subject_n=c.get("reduced_cohort_size"),
        full_cohort_target_n=c.get("full_frozen_cohort_size"),
        optimization_seed_n=_g(b_minus_a, "n_seeds_total"),
        primary_comparison_label="B (EEG+EOG) - A (EEG only), macro-F1",
        primary_effect_value=b_minus_a.get("mean"),
        primary_effect_unit="macro_f1",
        heterogeneity_note=f"{b_minus_a.get('n_seeds_favor_B')}/{b_minus_a.get('n_seeds_total')} seeds favor B",
        limitation=c.get("scope_disclosure"),
        provenance_doc=c.get("reduced_cohort_deviation_doc"),
    )


def _x_ds003838_bounded_diagnostic(c: dict) -> dict:
    a, b = _g(c, "A_sparse4", default={}), _g(c, "B_full_montage", default={})
    delta = None
    if isinstance(a.get("macro_f1_mean"), (int, float)) and isinstance(b.get("macro_f1_mean"), (int, float)):
        delta = b["macro_f1_mean"] - a["macro_f1_mean"]
    return dict(
        classification=c.get("status"),
        biological_subject_n=c.get("n_subjects"),
        primary_comparison_label="B (full montage) - A (sparse-4), macro-F1",
        primary_effect_value=delta,
        primary_effect_unit="macro_f1",
        limitation=c.get("scope_disclosure"),
    )


_EXTRACTORS = {
    "galaxyppg_external_replication": _x_galaxyppg_external_replication,
    "galaxyppg_eligibility_qc": _x_galaxyppg_eligibility_qc,
    "ppg_dalia_capacity_control": _x_ppg_dalia_capacity_control,
    "sleep_edf_primary_ab": _x_sleep_edf_primary_ab,
    "sleep_edf_shuffled_control_c": _x_sleep_edf_shuffled_control_c,
    "sleep_edf_interaction": _x_sleep_edf_interaction,
    "ptt_second_ppg_site": _x_ptt_second_ppg_site,
    "qde_v2_leg_bioz": _x_qde_v2_leg_bioz,
    "lbnp_thoracic_eis": _x_lbnp_thoracic_eis,
    "hmc_bounded_diagnostic": _x_hmc_bounded_diagnostic,
    "ds003838_bounded_diagnostic": _x_ds003838_bounded_diagnostic,
}


def _extract_meta(content: dict | str, is_markdown: bool) -> dict:
    if is_markdown:
        text = content.get("text", "") if isinstance(content, dict) else str(content)
        return dict(summary=text.strip().splitlines()[0][:300] if text.strip() else None)
    if isinstance(content, dict):
        return dict(summary=content.get("purpose"))
    return {}


def _registry_families() -> dict[str, str | None]:
    registry = json.loads((REPOSITORY_ROOT / REGISTRY_PATH).read_text())
    return {fam: fd.get("artifact_type") for fam, fd in registry["families"].items()}


def _governing_path(family_id: str) -> str:
    freeze = json.loads((REPOSITORY_ROOT / FREEZE_MANIFEST_PATH).read_text())
    return freeze["governing_artifacts"][family_id]


def _resolve_entry(family_id: str) -> Stage3EvidenceEntry:
    registry_families = _registry_families()
    artifact_type = (
        Stage3ArtifactType.MARKDOWN
        if registry_families.get(family_id) == "markdown"
        else Stage3ArtifactType.JSON
    )
    content = resolve_current(family_id)
    extractor = _EXTRACTORS.get(family_id)
    is_md = artifact_type == Stage3ArtifactType.MARKDOWN
    fields = extractor(content) if extractor else _extract_meta(content, is_md)
    path = content.get("path") if is_md else _governing_path(family_id)
    return Stage3EvidenceEntry(family_id=family_id, artifact_path=path, artifact_type=artifact_type, **fields)


def get_stage3_evidence_entry(family_id: str) -> Stage3EvidenceEntry:
    try:
        return _resolve_entry(family_id)
    except (GovernanceResolutionError, IntegrityVerificationError, KeyError) as exc:
        raise Stage3EvidenceUnavailable(f"Stage-3 evidence for '{family_id}' failed closed: {exc}") from exc


def get_stage3_evidence_envelope() -> Stage3EvidenceEnvelope:
    architecture = resolve_current("architecture_evidence_handoff")
    entries = [get_stage3_evidence_entry(family_id) for family_id in list_families()]
    return Stage3EvidenceEnvelope(
        source_registry=REGISTRY_PATH,
        source_freeze_manifest=FREEZE_MANIFEST_PATH,
        final_architecture_status=architecture.get("final_architecture_status", "UNKNOWN"),
        formal_pareto_status="FORMAL_PARETO_NOT_READY",
        entries=entries,
    )
