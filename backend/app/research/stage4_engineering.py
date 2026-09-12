"""Read-only adapter that projects results/stage4_engineering_readiness.json into
the API-facing Stage4EngineeringReadinessEnvelope (Stage 4 integration prep).

Same discipline as app.research.engineering_readiness: never sums or invents a
number the frozen artifact does not contain, never coerces a missing field to
0, and never relabels an ENGINEERING_ASSUMPTION value as a datasheet fact.
This module is purely a typed projection of the artifact that
scripts/build_stage4_engineering_readiness.py wrote; it recomputes nothing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.research.catalog import REPOSITORY_ROOT
from app.schemas.engineering_readiness import QuantityStatus
from app.schemas.research import ResearchAvailability
from app.schemas.stage4_engineering import (
    EvidenceClass,
    EvidenceQuantity,
    Stage4BomAdvancement,
    Stage4DutyScheduleEntry,
    Stage4EngineeringReadiness,
    Stage4EngineeringReadinessEnvelope,
    Stage4SystemDataRate,
    Stage4SystemMass,
    Stage4SystemPower,
)

STAGE4_ARTIFACT_PATH = "results/stage4_engineering_readiness.json"


def _evidence_quantity(source: dict, unit: str, provenance: str) -> EvidenceQuantity:
    """Project a {value, unit, evidence_class, note} object (this artifact's
    convention) into a typed EvidenceQuantity. Absent/non-numeric `value` ->
    UNKNOWN(value=None) — never coerced to 0, matching app.research.engineering_readiness._quantity."""
    if not isinstance(source, dict) or "value" not in source:
        return EvidenceQuantity(
            value=None, unit=unit, status=QuantityStatus.UNKNOWN, display="Unknown",
            reason_if_unavailable="value absent from frozen artifact", provenance=provenance,
            evidence_class=EvidenceClass.ENGINEERING_ASSUMPTION,
        )
    raw: Any = source["value"]
    evidence_raw = source.get("evidence_class", EvidenceClass.ENGINEERING_ASSUMPTION.value)
    try:
        evidence_class = EvidenceClass(evidence_raw)
    except ValueError:
        evidence_class = EvidenceClass.ENGINEERING_ASSUMPTION
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return EvidenceQuantity(
            value=None, unit=source.get("unit", unit), status=QuantityStatus.UNKNOWN, display="Unknown",
            reason_if_unavailable="value present but non-numeric", provenance=provenance,
            evidence_class=evidence_class,
        )
    value = float(raw)
    display = f"{value:,.4g} {source.get('unit', unit)}"
    return EvidenceQuantity(
        value=value, unit=source.get("unit", unit), status=QuantityStatus.AVAILABLE,
        display=display, provenance=source.get("note", provenance), evidence_class=evidence_class,
    )


class Stage4EngineeringReader:
    """Loads results/stage4_engineering_readiness.json on demand; never caches
    a stale result and never falls back to the Day-11 Part-2 artifact on
    failure (each artifact reports its own honest unavailability)."""

    def __init__(self, repository_root: str | Path = REPOSITORY_ROOT) -> None:
        self.repository_root = Path(repository_root).resolve()
        self.artifact_path = self.repository_root / STAGE4_ARTIFACT_PATH

    def artifact(self) -> Stage4EngineeringReadinessEnvelope:
        if not self.artifact_path.is_file():
            return Stage4EngineeringReadinessEnvelope(
                availability=ResearchAvailability.UNAVAILABLE,
                error=f"{STAGE4_ARTIFACT_PATH} does not exist.",
            )
        try:
            raw = json.loads(self.artifact_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            return Stage4EngineeringReadinessEnvelope(
                availability=ResearchAvailability.UNAVAILABLE,
                error=f"{STAGE4_ARTIFACT_PATH} is malformed: {exc}",
            )

        try:
            readiness = self._build(raw)
        except (KeyError, TypeError, ValueError) as exc:
            return Stage4EngineeringReadinessEnvelope(
                availability=ResearchAvailability.UNAVAILABLE,
                error=f"{STAGE4_ARTIFACT_PATH} failed schema projection: {exc}",
            )
        return Stage4EngineeringReadinessEnvelope(availability=ResearchAvailability.AVAILABLE, readiness=readiness)

    def _build(self, raw: dict) -> Stage4EngineeringReadiness:
        power = raw["power"]["system_average_power"]
        data_rate = raw["data_rate"]
        mass = raw["mass"]
        bom = raw["bom"]

        duty_schedule = [
            Stage4DutyScheduleEntry(
                module=module_id,
                state=entry["state"],
                duty_fraction=float(entry["duty_fraction"]),
                note=entry["note"],
            )
            for module_id, entry in raw["power"]["duty_schedule"].items()
        ]

        system_power = Stage4SystemPower(
            status=power["status"],
            reason=power["reason"],
            base_topology_load_side_mw=_evidence_quantity(power["base_topology_load_side_mw"], "mW", STAGE4_ARTIFACT_PATH),
            base_topology_battery_side_mw=_evidence_quantity(power["base_topology_battery_side_mw"], "mW", STAGE4_ARTIFACT_PATH),
            contributors_mw=dict(power["contributors_mw"]),
            excluded_from_base_total_mw={
                "leg_bioz_mw": float(power["excluded_from_base_total"]["leg_bioz_mw"]),
                "second_ppg_site_incl_led_mw": float(power["excluded_from_base_total"]["second_ppg_site_incl_led_mw"]),
            },
            duty_schedule=duty_schedule,
        )

        system_data_rate = Stage4SystemDataRate(
            system_raw_total_bps=_evidence_quantity(data_rate["system_raw_total_bps"], "bps", STAGE4_ARTIFACT_PATH),
            system_transmitted_bps=_evidence_quantity(data_rate["system_transmitted_bps"], "bps", STAGE4_ARTIFACT_PATH),
            processed_data_rate_status=data_rate["processed_data_rate_status"],
            excluded_from_base_total_bps=dict(data_rate["excluded_from_base_total_bps"]),
        )

        system_mass = Stage4SystemMass(
            status=mass["system_mass_status"],
            tier_achieved=mass["tier_achieved"],
            system_mass_base_topology_excl_leg_g=_evidence_quantity(mass["system_mass_base_topology_excl_leg_g"], "g", STAGE4_ARTIFACT_PATH),
            eog_incremental_mass_g=_evidence_quantity(mass["eog_incremental_mass_g"], "g", STAGE4_ARTIFACT_PATH),
        )

        bom_advancement = Stage4BomAdvancement(
            not_a_final_bom=bool(bom["not_a_final_bom"]),
            final=bool(bom["final"]),
            items_advanced=[dict(item) for item in bom["items_advanced"]],
            still_missing=list(bom["still_missing"]),
        )

        return Stage4EngineeringReadiness(
            artifact_id=raw["artifact_id"],
            sprint=raw["sprint"],
            statement=raw["statement"],
            prohibited=list(raw["prohibited"]),
            system_average_power=system_power,
            system_data_rate=system_data_rate,
            system_mass=system_mass,
            bom=bom_advancement,
            final_architecture_status=raw["final_architecture_status"],
            formal_pareto_status=raw["formal_pareto_status"],
            source_artifacts=list(raw["source_artifacts"]),
        )


stage4_engineering_readiness = Stage4EngineeringReader()
