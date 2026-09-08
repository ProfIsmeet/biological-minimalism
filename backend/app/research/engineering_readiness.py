"""Read-only adapter that projects the Day-11 Part-2 engineering artifacts into a
concise, jury-facing engineering-readiness envelope (Part-3 integration).

It does NOT sum component powers, does NOT invent a system power/mass number, and
carries every unresolved quantity as an explicit NOT_READY / MISSING status. The
source of truth is the frozen Part-2 handoff artifact
`results/day11_part3_engineering_inputs.json` plus the raw data-rate budget.
"""

from __future__ import annotations

import json
from pathlib import Path

from typing import Any

from app.research.catalog import REPOSITORY_ROOT, ResearchArtifactError
from app.schemas.engineering_readiness import (
    EngineeringCandidate,
    EngineeringPanelRow,
    EngineeringReadiness,
    EngineeringReadinessEnvelope,
    Quantity,
    QuantityStatus,
    RawDataRate,
    ReadinessLevel,
)
from app.schemas.research import ResearchAvailability


def _quantity(source: dict, key: str, unit: str, provenance: str) -> Quantity:
    """Project one numeric field into a typed Quantity (audit H4/§9).

    Absent field -> UNKNOWN(value=None); present-but-non-numeric -> UNKNOWN
    (malformed); present-and-numeric -> AVAILABLE. A genuine 0 in the artifact
    (e.g. a colocated candidate with 0 new contacts) is preserved as an
    AVAILABLE 0, but a MISSING field is NEVER coerced to 0."""
    if key not in source:
        return Quantity(
            value=None, unit=unit, status=QuantityStatus.UNKNOWN, display="Unknown",
            reason_if_unavailable=f"'{key}' absent from frozen artifact", provenance=provenance,
        )
    raw: Any = source[key]
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return Quantity(
            value=None, unit=unit, status=QuantityStatus.UNKNOWN, display="Unknown",
            reason_if_unavailable=f"'{key}' present but non-numeric", provenance=provenance,
        )
    is_int = float(raw).is_integer()
    value = float(raw)
    display = f"{int(value):,} {unit}" if is_int else f"{value:g} {unit}"
    return Quantity(
        value=value, unit=unit, status=QuantityStatus.AVAILABLE,
        display=display, provenance=provenance,
    )

PART3_INPUTS_PATH = "results/day11_part3_engineering_inputs.json"
DATA_RATE_PATH = "results/reference_data_rate_budget_day11.json"

# Per-candidate presentation copy. Numeric burdens come from the frozen artifact;
# these strings only translate committed evidence into decision-relevant phrasing.
_CANDIDATE_COPY = {
    "wrist_imu": {
        "label": "Wrist IMU (BMI270)",
        "scientific_direction": "Modest positive (capacity-controlled)",
        "incremental_body_region": "0",
        "incremental_module": "0",
        "reference_component_power_display": "~0.018 mW (band 0.018–0.378), accel-only, gyro OFF",
        "reference_component_power_status": ReadinessLevel.PARTIAL,
        "engineering_summary": (
            "0 new body region, 0 new module, 0 new sensing contact in the colocated wrist "
            "reference; added PCB/data/compute only. Best-characterised power of all candidates."
        ),
        "caveat": (
            "Low incremental burden is CONDITIONAL on wrist co-location; component power is not "
            "system power, and system mass is NOT_READY."
        ),
    },
    "frontal_eog_horizontal": {
        "label": "Horizontal EOG (shared head module)",
        "scientific_direction": "Positive with matched control + prospective secondary support",
        "incremental_body_region": "0 or 1 (peri-ocular; framing-dependent)",
        "incremental_module": "0 (REFERENCE_SHARED_HEAD_MODULE)",
        "reference_component_power_display": "Not ready (shared head AFE operating point unquantified)",
        "reference_component_power_status": ReadinessLevel.NOT_READY,
        "engineering_summary": (
            "+2 lateral-ocular sensing contacts, 0 new module, shared reference/bias on the existing "
            "ADS1299-class head AFE (one spare channel). Materially higher contact burden than IMU."
        ),
        "caveat": (
            "Shared-head reference case is NOT the final wearable architecture; a standalone "
            "alternative would add 3–4 contacts and possibly +1 module. AFE power and system mass NOT_READY."
        ),
    },
    "second_ppg_site": {
        "label": "Second PPG optical site (MAX86141-class)",
        "scientific_direction": "Aggregate negative / heterogeneous (s2-driven)",
        "incremental_body_region": "1",
        "incremental_module": "OPEN (shared / tethered / standalone)",
        "reference_component_power_display": "Not ready (LED power + 500 Hz sequencing dominate, boundary open)",
        "reference_component_power_status": ReadinessLevel.NOT_READY,
        "engineering_summary": (
            "+1 physical optical site, +1 contact region, and the highest raw data-rate increment of "
            "all candidates. The negative HR result does NOT zero this engineering burden."
        ),
        "caveat": (
            "DEPRIORITIZE is a target-specific decision, not a global removal; optical power is NOT_READY "
            "and the module boundary is unresolved."
        ),
    },
}

_BOUNDARIES = (
    "Component and AFE reference powers are NOT system average power (SYSTEM_AVERAGE_POWER_NOT_READY).",
    "No system mass exists — package dimensions are not wearable mass (SYSTEM_MASS_NOT_READY).",
    "The ~48.068 kbps figure is a PARTIAL raw lower bound, not radio bandwidth.",
    "BOM is PARTIAL: reference component classes are selected (final=false); no final BOM.",
    "Final architecture is UNRESOLVED and no formal Pareto frontier is computed (FORMAL_PARETO_NOT_READY).",
    "A low component power does not imply a low system power; an unquantified quantity is shown as Not ready, never 0.",
)


class EngineeringReadinessReader:
    """Loads the frozen Part-2 artifacts on demand; never mutates or caches them."""

    def __init__(self, repository_root: str | Path = REPOSITORY_ROOT) -> None:
        self.repository_root = Path(repository_root).resolve()

    def _read_json(self, rel_path: str) -> dict:
        path = self.repository_root / rel_path
        if not path.is_file():
            raise ResearchArtifactError(f"Engineering artifact unavailable: {rel_path}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ResearchArtifactError(f"Engineering artifact could not be read: {rel_path}: {exc}") from exc

    def _build(self) -> EngineeringReadiness:
        inputs = self._read_json(PART3_INPUTS_PATH)
        data_rate = self._read_json(DATA_RATE_PATH)
        system_total = data_rate.get("system_raw_total")
        if not isinstance(system_total, dict):
            system_total = {}
        # Typed system raw-total: UNKNOWN if the frozen budget lacks it, NEVER 48068.
        total_rate = _quantity(system_total, "value_bps", "bps", DATA_RATE_PATH)
        if total_rate.status == QuantityStatus.AVAILABLE and total_rate.value is not None:
            bps = int(total_rate.value)
            kbps = round(bps / 1000.0, 3)
            total_rate.display = f"{bps:,} bps (~{kbps:g} kbps)"
            data_rate_row_display = f"~{kbps:g} kbps (partial lower bound)"
            data_rate_status = "PARTIAL_LOWER_BOUND"
            data_rate_panel_status = ReadinessLevel.PARTIAL
        else:
            bps = None
            kbps = None
            data_rate_row_display = "Unknown (raw total not in frozen budget)"
            data_rate_status = "UNKNOWN"
            data_rate_panel_status = ReadinessLevel.NOT_READY

        candidates: list[EngineeringCandidate] = []
        for entry in inputs.get("candidates", []):
            cid = entry.get("candidate", "")
            copy = _CANDIDATE_COPY.get(cid)
            if copy is None:
                # Unknown candidate: skip rather than silently mislabel it.
                continue
            candidates.append(
                EngineeringCandidate(
                    candidate=cid,
                    label=copy["label"],
                    scientific_target=str(entry.get("scientific_target", "")),
                    scientific_direction=copy["scientific_direction"],
                    gate_status=str(entry.get("gate_status", "")),
                    incremental_body_region=copy["incremental_body_region"],
                    incremental_module=copy["incremental_module"],
                    incremental_sensing_contacts=_quantity(
                        entry, "incremental_sensing_contacts", "contacts", PART3_INPUTS_PATH
                    ),
                    reference_component_power_display=copy["reference_component_power_display"],
                    reference_component_power_status=copy["reference_component_power_status"],
                    raw_data_rate_increment=_quantity(
                        entry, "raw_data_rate_increment_bps", "bps", PART3_INPUTS_PATH
                    ),
                    mass_tier=str(entry.get("mass_tier", "Tier0")),
                    bom_readiness=str(entry.get("bom_readiness", "")),
                    engineering_summary=copy["engineering_summary"],
                    caveat=copy["caveat"],
                )
            )

        panel = [
            EngineeringPanelRow(
                dimension="System average power",
                value_display="Not ready",
                status=ReadinessLevel.NOT_READY,
                note=(
                    "Partial component/reference values exist (e.g. IMU ~0.018 mW, ECG AFE 0.67 mW, "
                    "wrist sensing-electronics LED-excluded lower bound). No defensible system total."
                ),
            ),
            EngineeringPanelRow(
                dimension="System mass",
                value_display="Not ready",
                status=ReadinessLevel.NOT_READY,
                note="All modules Tier 0. PCB/battery/enclosure/electrodes/attachments unquantified.",
            ),
            EngineeringPanelRow(
                dimension="Module BOM",
                value_display="Partial",
                status=ReadinessLevel.PARTIAL,
                note="Reference component classes selected (final=false); electrodes/PCB/enclosure MISSING.",
            ),
            EngineeringPanelRow(
                dimension="Raw data rate",
                value_display=data_rate_row_display,
                status=data_rate_panel_status,
                note="Scientific-use-case head; excludes light + thoracic/leg BioZ, overhead, compression. Not radio bandwidth.",
            ),
            EngineeringPanelRow(
                dimension="Final architecture",
                value_display="Unresolved",
                status=ReadinessLevel.NOT_READY,
                note="No RETAIN outcome; cross-target incomparability + incomplete system power/mass/BOM.",
            ),
            EngineeringPanelRow(
                dimension="Formal Pareto",
                value_display="Not ready",
                status=ReadinessLevel.NOT_READY,
                note="Benefit axes not comparable across targets; burden dimensions incomplete. No frontier computed.",
            ),
        ]

        return EngineeringReadiness(
            artifact_id="biological-minimalism-day11-engineering-readiness-v1",
            part="DAY11_PART3_CANONICAL_INTEGRATION",
            source_head_commit=str(inputs.get("part1_head_commit", "")),
            statement=(
                "Concise engineering-readiness projection of the frozen Day-11 Part-2 evidence. It shows "
                "WHY the project refuses to select a final architecture: several component/AFE boundaries "
                "are quantified, but system power, mass, full BOM, and a comparable benefit frame are not."
            ),
            system_average_power_status="SYSTEM_AVERAGE_POWER_NOT_READY",
            system_mass_status="SYSTEM_MASS_NOT_READY",
            bom_status="PARTIAL",
            formal_pareto_status="FORMAL_PARETO_NOT_READY",
            final_architecture_status="UNRESOLVED",
            raw_data_rate=RawDataRate(
                value=total_rate,
                status=data_rate_status,
                radio_data_rate_status="NOT_READY",
                note=str(system_total.get("framing", "PARTIAL LOWER BOUND")),
            ),
            panel=panel,
            candidates=candidates,
            boundaries=list(_BOUNDARIES),
            source_artifacts=[
                PART3_INPUTS_PATH,
                DATA_RATE_PATH,
                "results/reference_power_budget_day11_part2.json",
                "results/reference_mass_readiness_day11_part2.json",
                "results/reference_bom_readiness_day11_part2.json",
            ],
        )

    def artifact(self) -> EngineeringReadinessEnvelope:
        try:
            readiness = self._build()
        except ResearchArtifactError as exc:
            return EngineeringReadinessEnvelope(
                availability=ResearchAvailability.UNAVAILABLE,
                error=str(exc),
            )
        return EngineeringReadinessEnvelope(
            availability=ResearchAvailability.AVAILABLE,
            readiness=readiness,
        )


engineering_readiness = EngineeringReadinessReader()
