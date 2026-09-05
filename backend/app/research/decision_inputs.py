"""Source-verified adapter for the committed Day 5 decision-input artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.research.catalog import REPOSITORY_ROOT, ResearchArtifactError
from app.research.operational_costs import _validate_catalog
from app.schemas.decision_inputs import (
    AccuracyMetrics,
    ClaimBoundaries,
    ComponentJoinMapping,
    ComponentReadiness,
    DecisionConfiguration,
    DecisionInputComponent,
    MetricEstimate,
    OperationalCostInput,
    ParetoDecisionInputs,
    ParetoDecisionInputsEnvelope,
    ParetoReadiness,
    ParetoStatus,
    ReadinessAvailability,
    RobustnessEvidence,
    ScientificMarginalValue,
    ScientificProvenance,
    SourceArtifactReference,
)
from app.schemas.operational_cost import CostAvailability, OperationalCostCatalog
from app.schemas.research import ResearchAvailability

DECISION_INPUTS_PATH = "results/pareto_decision_inputs.json"
SCIENTIFIC_CONTRACT_PATH = "results/sensor_marginal_value_contract.json"
OPERATIONAL_CATALOG_PATH = "results/operational_cost_catalog.json"
ROBUSTNESS_PATH = "results/ppg_dalia_fault_robustness.json"
ROBUSTNESS_AUDIT_PATH = "docs/PHASE5_ROBUSTNESS_AUDIT_ADDENDUM.md"
SCIENTIFIC_METHODOLOGY_PATH = "docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md"
FROZEN_ROBUSTNESS_SHA256 = "c40397fb0bb43b4f4a778aac4a4e0ba72b7b0387cab1aabec1e0708cc2912dcb"

JOIN_MAPPINGS = (
    {
        "component_id": "wrist_imu",
        "scientific_component_id": "wrist_imu_accelerometer",
        "scientific_experiment_id": "ppg_dalia_imu_hr",
        "operational_experiment_id": "ppg-dalia-imu-ablation",
    },
    {
        "component_id": "second_ppg_site",
        "scientific_component_id": "second_physical_ppg_site_proximal_phalanx",
        "scientific_experiment_id": "ptt_second_ppg_site_hr",
        "operational_experiment_id": "ptt-ppg-site-ablation",
    },
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    if not path.is_file():
        raise ResearchArtifactError(f"Decision-input source unavailable: {relative_path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResearchArtifactError(f"Decision-input source could not be read ({relative_path}): {exc}") from exc
    if not isinstance(value, dict):
        raise ResearchArtifactError(f"Decision-input source must be a JSON object: {relative_path}")
    return value


def _accuracy_metrics(raw: dict[str, Any]) -> AccuracyMetrics:
    suffix = "_mean" if "mae_bpm_mean" in raw else ""
    return AccuracyMetrics(
        mae=MetricEstimate(mean=raw[f"mae_bpm{suffix}"], sd=raw.get("mae_bpm_sd"), unit="bpm"),
        rmse=MetricEstimate(mean=raw[f"rmse_bpm{suffix}"], sd=raw.get("rmse_bpm_sd"), unit="bpm"),
        n_windows=raw.get("n_windows"),
    )


def _scientific_value(experiment: dict[str, Any]) -> ScientificMarginalValue:
    limitations = list(experiment.get("limitations", experiment.get("known_caveats", [])))
    return ScientificMarginalValue(
        scientific_component_id=experiment["candidate_component_id"],
        target_id=experiment["target_id"],
        experiment_id=experiment["experiment_id"],
        dataset_id=experiment["dataset_id"],
        baseline_configuration=DecisionConfiguration(
            description=experiment["baseline_configuration"]["description"],
            channels=experiment["baseline_configuration"]["channels"],
        ),
        candidate_configuration=DecisionConfiguration(
            description=experiment["candidate_configuration"]["description"],
            channels=experiment["candidate_configuration"]["channels"],
        ),
        primary_metric="mae",
        baseline_metrics=_accuracy_metrics(experiment["baseline_metrics"]),
        candidate_metrics=_accuracy_metrics(experiment["candidate_metrics"]),
        absolute_benefit=experiment["absolute_benefit"],
        relative_improvement=experiment["relative_improvement"],
        direction=experiment["marginal_status"]["overall_direction"],
        variability=experiment["variability"],
        heterogeneity=experiment["marginal_status"]["heterogeneity"],
        evidence_strength=experiment["marginal_status"]["evidence_strength"],
        evidence_scope=experiment["evidence_scope"],
        provenance=ScientificProvenance(
            source_artifact=experiment["source_artifact"],
            source_reproducibility_artifact=experiment.get("source_reproducibility_artifact"),
            methodology_path=SCIENTIFIC_METHODOLOGY_PATH,
            contract_path=SCIENTIFIC_CONTRACT_PATH,
        ),
        claim_boundaries=ClaimBoundaries(
            supported=[
                "Target-specific marginal direction and metrics within this experiment's frozen dataset and protocol."
            ],
            unsupported=[
                "Cross-dataset raw-error comparison or universal component ordering.",
                "Automatic final-architecture inclusion or global component removal.",
                "Astronaut, microgravity, clinical, or other-target generalization.",
            ],
            limitations=limitations,
        ),
    )


def _operational_value(catalog: OperationalCostCatalog, component_id: str) -> OperationalCostInput:
    component = next(item for item in catalog.components if item.component_id == component_id)
    evidence_ids = {
        provenance_id
        for quantity in [component.duty_cycle, *component.dimensions.values()]
        for provenance_id in quantity.provenance_ids
    }
    if component.hardware_characterization is not None:
        evidence_ids.update(component.hardware_characterization.identity.evidence_ids)
    return OperationalCostInput(
        source_component_id=component.component_id,
        candidate_hardware_identity=component.candidate_hardware_identity,
        duty_cycle=component.duty_cycle,
        dimensions=component.dimensions,
        shared_hardware=component.shared_hardware,
        known_dimensions=[
            name for name, quantity in component.dimensions.items() if quantity.availability == CostAvailability.KNOWN
        ],
        unknown_dimensions=[
            name for name, quantity in component.dimensions.items() if quantity.availability == CostAvailability.UNKNOWN
        ],
        unknowns=component.unknowns,
        evidence=[item for item in catalog.evidence if item.evidence_id in evidence_ids],
        hardware_characterization=component.hardware_characterization,
    )


def _robustness_value(robustness: dict[str, Any]) -> RobustnessEvidence:
    execution = robustness["execution"]
    clean = robustness["clean_baseline"]
    dataset = robustness["dataset"]
    boundary = robustness["interpretation_boundary"]
    return RobustnessEvidence(
        status="RESOLVED_FROM_INTEGRATION_SOURCE",
        experiment_id=robustness["experiment_id"],
        source_artifact=ROBUSTNESS_PATH,
        audit_addendum=ROBUSTNESS_AUDIT_PATH,
        subject_id=dataset["subject_id"],
        scope=robustness["scope"],
        condition_count=execution["condition_count"],
        eligible_windows_per_condition=execution["eligible_windows_per_condition"],
        total_condition_windows=execution["total_condition_windows"],
        clean_mae_bpm=clean["mae_bpm_valid_only"],
        clean_rmse_bpm=clean["rmse_bpm_valid_only"],
        clean_prediction_availability=clean["prediction_availability_rate"],
        imu_calibration_caveat=(
            "IMU noise and saturation scales came from the first affected S14 batch, whose motion variance was much "
            "lower than typical later windows; the tested grid is not proof of robustness to severe corruption."
        ),
        packet_loss_interpretation=(
            "Independent loss of a required native-rate sample primarily triggered fail-closed input rejection, so "
            "packet-loss results characterize prediction availability rather than continuous error degradation."
        ),
        supported_claim=boundary["supported"],
        unsupported_claims=boundary["not_supported"],
    )


def _readiness(component_id: str) -> ComponentReadiness:
    if component_id == "wrist_imu":
        return ComponentReadiness(
            component_id=component_id,
            scientific_benefit=ReadinessAvailability.AVAILABLE,
            power=ReadinessAvailability.PARTIAL,
            mass=ReadinessAvailability.MISSING,
            contact_burden=ReadinessAvailability.AVAILABLE,
            module_burden=ReadinessAvailability.AVAILABLE,
            compute_data_burden=ReadinessAvailability.AVAILABLE,
            robustness_evidence=ReadinessAvailability.AVAILABLE,
            evidence_provenance=ReadinessAvailability.AVAILABLE,
        )
    return ComponentReadiness(
        component_id=component_id,
        scientific_benefit=ReadinessAvailability.AVAILABLE,
        power=ReadinessAvailability.PARTIAL,
        mass=ReadinessAvailability.MISSING,
        contact_burden=ReadinessAvailability.PARTIAL,
        module_burden=ReadinessAvailability.MISSING,
        compute_data_burden=ReadinessAvailability.AVAILABLE,
        robustness_evidence=ReadinessAvailability.MISSING,
        evidence_provenance=ReadinessAvailability.AVAILABLE,
    )


def build_decision_inputs(repository_root: str | Path = REPOSITORY_ROOT) -> ParetoDecisionInputs:
    """Build the reviewed join deterministically from immutable source artifacts."""
    root = Path(repository_root).resolve()
    scientific = _read_json(root, SCIENTIFIC_CONTRACT_PATH)
    operational_raw = _read_json(root, OPERATIONAL_CATALOG_PATH)
    robustness = _read_json(root, ROBUSTNESS_PATH)
    audit_path = root / ROBUSTNESS_AUDIT_PATH
    if not audit_path.is_file():
        raise ResearchArtifactError(f"Robustness audit unavailable: {ROBUSTNESS_AUDIT_PATH}")

    if scientific["sign_convention"]["absolute_benefit"].split("(", 1)[0].strip() != "baseline_metric - candidate_metric":
        raise ResearchArtifactError("Scientific benefit sign convention changed.")
    if scientific["comparability_rules"]["cross_dataset_raw_metric_comparison"] != "PROHIBITED":
        raise ResearchArtifactError("Cross-dataset raw-metric prohibition is missing.")
    if scientific["universal_sensor_score"]["defined"] is not False:
        raise ResearchArtifactError("A universal sensor score must not be defined.")
    if _sha256(root / ROBUSTNESS_PATH) != FROZEN_ROBUSTNESS_SHA256:
        raise ResearchArtifactError("Frozen robustness artifact identity changed.")

    audit = audit_path.read_text(encoding="utf-8")
    for required in ("first affected S14 replay batch", "fail-closed pipeline availability", "not evidence that IMU is irrelevant"):
        if required not in audit:
            raise ResearchArtifactError(f"Robustness audit caveat missing: {required}")

    try:
        operational = _validate_catalog(OperationalCostCatalog.model_validate(operational_raw))
    except ValidationError as exc:
        raise ResearchArtifactError(f"Operational catalog validation failed: {exc}") from exc

    components: list[DecisionInputComponent] = []
    joins: list[ComponentJoinMapping] = []
    for mapping_raw in JOIN_MAPPINGS:
        mapping = ComponentJoinMapping.model_validate(mapping_raw)
        joins.append(mapping)
        experiment = scientific["experiments"][mapping.scientific_experiment_id]
        if experiment["candidate_component_id"] != mapping.scientific_component_id:
            raise ResearchArtifactError(f"Scientific component mapping changed for {mapping.component_id}.")
        operational_component = next(item for item in operational.components if item.component_id == mapping.component_id)
        if operational_component.scientific_experiment_ids != [mapping.operational_experiment_id]:
            raise ResearchArtifactError(f"Operational experiment mapping changed for {mapping.component_id}.")
        components.append(
            DecisionInputComponent(
                component_id=mapping.component_id,
                label=operational_component.label,
                target="heart_rate_bpm",
                experiment_id=mapping.scientific_experiment_id,
                scientific_marginal_value=_scientific_value(experiment),
                operational_cost=_operational_value(operational, mapping.component_id),
                robustness_evidence=_robustness_value(robustness) if mapping.component_id == "wrist_imu" else None,
            )
        )

    sources = [
        (SCIENTIFIC_CONTRACT_PATH, "scientific marginal-value contract"),
        (OPERATIONAL_CATALOG_PATH, "operational-cost contract"),
        (ROBUSTNESS_PATH, "frozen S14 robustness evidence"),
        (ROBUSTNESS_AUDIT_PATH, "post-hoc robustness interpretation boundary"),
    ]
    return ParetoDecisionInputs(
        schema_version="2.0.0",
        artifact_id="biological-minimalism-day6-decision-inputs-v2",
        source_artifacts=[
            SourceArtifactReference(path=path, sha256=_sha256(root / path), role=role) for path, role in sources
        ],
        join_mappings=joins,
        components=components,
        readiness=ParetoReadiness(
            pareto_status=ParetoStatus.NOT_READY,
            formal_pareto_calculated=False,
            missing_requirements=[
                "Deployable average power and daily energy remain unquantified for both candidate components.",
                "Incremental finished mass is unquantified for both candidate components.",
                "Embedded inference latency and protocol/storage/transport overhead are unquantified.",
                "Reference component identities and topology are frozen, but the final BOM, MCU, radio, battery, regulator, enclosure, and attachment are not selected.",
                "The second PPG site's module boundary and contact-region allocation are unresolved.",
                "Only heart rate has marginal-value evidence; other mission-relevant targets are unvalidated.",
                "Only two candidate additions have scientific evidence, from different datasets and model families.",
            ],
            cross_dataset_restriction=(
                "Raw MAE/RMSE and relative-improvement magnitudes from PPG-DaLiA and PTT are not comparable ranking coordinates."
            ),
            limited_structural_observation=(
                "Within the frozen PTT heart-rate experiment, the second PPG site worsened aggregate error while adding "
                "one physical and optical sensing site. This is a descriptive, target-specific observation—not a global architecture decision."
            ),
            component_matrix=[_readiness(mapping["component_id"]) for mapping in JOIN_MAPPINGS],
        ),
    )


class DecisionInputsReader:
    """Loads the committed artifact and proves that it matches current sources."""

    def __init__(self, repository_root: str | Path = REPOSITORY_ROOT) -> None:
        self.repository_root = Path(repository_root).resolve()

    def _read(self) -> ParetoDecisionInputs:
        path = self.repository_root / DECISION_INPUTS_PATH
        if not path.is_file():
            raise ResearchArtifactError(f"Decision-input artifact unavailable: {DECISION_INPUTS_PATH}")
        try:
            committed = ParetoDecisionInputs.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValidationError) as exc:
            raise ResearchArtifactError(f"Decision-input artifact could not be read: {exc}") from exc
        expected = build_decision_inputs(self.repository_root)
        if committed.model_dump(mode="json") != expected.model_dump(mode="json"):
            raise ResearchArtifactError("Committed decision-input artifact does not match its source contracts.")
        return committed

    def artifact(self) -> ParetoDecisionInputsEnvelope:
        try:
            artifact = self._read()
        except ResearchArtifactError as exc:
            return ParetoDecisionInputsEnvelope(availability=ResearchAvailability.UNAVAILABLE, error=str(exc))
        return ParetoDecisionInputsEnvelope(
            availability=ResearchAvailability.AVAILABLE,
            decision_inputs=artifact,
        )


decision_inputs = DecisionInputsReader()


def write_decision_inputs(repository_root: str | Path = REPOSITORY_ROOT) -> Path:
    """Regenerate the committed JSON with stable ordering and formatting."""
    root = Path(repository_root).resolve()
    output = root / DECISION_INPUTS_PATH
    artifact = build_decision_inputs(root)
    output.write_text(
        json.dumps(artifact.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


if __name__ == "__main__":
    print(write_decision_inputs())
