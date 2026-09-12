import { create } from "zustand";

import { api } from "@/lib/api";
import type {
  OperationalCostCatalog,
  EngineeringReadiness,
  FutureScienceManifestEnvelope,
  HardwareTopologyContract,
  ParetoDecisionInputs,
  ParetoReadinessDay6,
  ResearchExperiment,
  ResearchExperimentSummaryEnvelope,
  ResearchProjectSummary,
  Stage3EvidenceEnvelope,
  Stage4ArchitectureAcceptanceGates,
  Stage4ArchitectureCandidateClasses,
  Stage4ArchitectureDecisionInputsScience,
  Stage4ArchitectureDecisionProjection,
  Stage4ArchitectureScienceDecisionFramework,
  Stage4BatteryTopologyScenarios,
  Stage4CandidateBurdenMatrix,
  Stage4CandidateClassBurdenComparison,
  Stage4ContactElectrodeBurden,
  Stage4EngineeringReadiness,
  Stage4FinalArchitectureDecisionPacket,
  Stage4FinalClosureManifest,
  FinalWearableArchitecture,
  Stage4FormalParetoAnalysis,
  Stage4GateDBurdenCompleteness,
  Stage4GateECoordinatorDecisions,
  Stage4GateECoordinatorOptions,
  Stage4ScienceClaimLedger,
  Stage4ScienceConsumptionManifest,
  Stage4ScientificParetoInputs,
  Stage4SensorDecisionSensitivity,
  Stage4SensorValueMatrix,
} from "@/lib/types";

interface ResearchState {
  summaries: ResearchExperimentSummaryEnvelope[];
  projectSummary: ResearchProjectSummary | null;
  operationalCostCatalog: OperationalCostCatalog | null;
  operationalCostError: string | null;
  decisionInputs: ParetoDecisionInputs | null;
  decisionInputsError: string | null;
  hardwareTopology: HardwareTopologyContract | null;
  hardwareTopologyError: string | null;
  paretoReadiness: ParetoReadinessDay6 | null;
  paretoReadinessError: string | null;
  engineeringReadiness: EngineeringReadiness | null;
  engineeringReadinessError: string | null;
  stage4EngineeringReadiness: Stage4EngineeringReadiness | null;
  stage4EngineeringReadinessError: string | null;
  stage3Evidence: Stage3EvidenceEnvelope | null;
  stage3EvidenceError: string | null;
  stage4ScienceManifest: Stage4ScienceConsumptionManifest | null;
  stage4ScienceManifestError: string | null;
  stage4SensorValueMatrix: Stage4SensorValueMatrix | null;
  stage4ScienceClaims: Stage4ScienceClaimLedger | null;
  stage4ArchitectureDecisionInputsScience: Stage4ArchitectureDecisionInputsScience | null;
  stage4ArchitectureScienceDecisionFramework: Stage4ArchitectureScienceDecisionFramework | null;
  stage4SensorDecisionSensitivity: Stage4SensorDecisionSensitivity | null;
  stage4ScientificParetoInputs: Stage4ScientificParetoInputs | null;
  stage4ArchitectureAcceptanceGates: Stage4ArchitectureAcceptanceGates | null;
  stage4ArchitectureCandidateClasses: Stage4ArchitectureCandidateClasses | null;
  stage4GateDBurdenCompleteness: Stage4GateDBurdenCompleteness | null;
  stage4GateDBurdenCompletenessError: string | null;
  stage4CandidateClassBurdenComparison: Stage4CandidateClassBurdenComparison | null;
  stage4ArchitectureDecisionProjection: Stage4ArchitectureDecisionProjection | null;
  stage4GateECoordinatorOptions: Stage4GateECoordinatorOptions | null;
  stage4FinalArchitectureDecisionPacket: Stage4FinalArchitectureDecisionPacket | null;
  stage4ContactElectrodeBurden: Stage4ContactElectrodeBurden | null;
  stage4ContactElectrodeBurdenError: string | null;
  stage4BatteryTopologyScenarios: Stage4BatteryTopologyScenarios | null;
  stage4BatteryTopologyScenariosError: string | null;
  stage4CandidateBurdenMatrix: Stage4CandidateBurdenMatrix | null;
  stage4CandidateBurdenMatrixError: string | null;
  stage4GateECoordinatorDecisions: Stage4GateECoordinatorDecisions | null;
  stage4GateECoordinatorDecisionsError: string | null;
  stage4FormalParetoAnalysis: Stage4FormalParetoAnalysis | null;
  stage4FormalParetoAnalysisError: string | null;
  finalWearableArchitecture: FinalWearableArchitecture | null;
  finalWearableArchitectureError: string | null;
  stage4FinalClosureManifest: Stage4FinalClosureManifest | null;
  stage4FinalClosureManifestError: string | null;
  // Stored as the WHOLE envelope (not decomposed into data/error) because its
  // 3-way status (PENDING_SCIENCE_HANDOFF / INGESTION_FAILED / INGESTED) is
  // not a simple success/failure — PENDING is an honest, expected state, not
  // an error to alarm the user with.
  futureScienceManifest: FutureScienceManifestEnvelope | null;
  experiments: Record<string, ResearchExperiment>;
  selectedExperimentId: string | null;
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
  selectExperiment: (experimentId: string) => void;
}

export const useResearchStore = create<ResearchState>((set) => ({
  summaries: [],
  projectSummary: null,
  operationalCostCatalog: null,
  operationalCostError: null,
  decisionInputs: null,
  decisionInputsError: null,
  hardwareTopology: null,
  hardwareTopologyError: null,
  paretoReadiness: null,
  paretoReadinessError: null,
  engineeringReadiness: null,
  engineeringReadinessError: null,
  stage4EngineeringReadiness: null,
  stage4EngineeringReadinessError: null,
  stage3Evidence: null,
  stage3EvidenceError: null,
  stage4ScienceManifest: null,
  stage4ScienceManifestError: null,
  stage4SensorValueMatrix: null,
  stage4ScienceClaims: null,
  stage4ArchitectureDecisionInputsScience: null,
  stage4ArchitectureScienceDecisionFramework: null,
  stage4SensorDecisionSensitivity: null,
  stage4ScientificParetoInputs: null,
  stage4ArchitectureAcceptanceGates: null,
  stage4ArchitectureCandidateClasses: null,
  stage4GateDBurdenCompleteness: null,
  stage4GateDBurdenCompletenessError: null,
  stage4CandidateClassBurdenComparison: null,
  stage4ArchitectureDecisionProjection: null,
  stage4GateECoordinatorOptions: null,
  stage4FinalArchitectureDecisionPacket: null,
  stage4ContactElectrodeBurden: null,
  stage4ContactElectrodeBurdenError: null,
  stage4BatteryTopologyScenarios: null,
  stage4BatteryTopologyScenariosError: null,
  stage4CandidateBurdenMatrix: null,
  stage4CandidateBurdenMatrixError: null,
  stage4GateECoordinatorDecisions: null,
  stage4GateECoordinatorDecisionsError: null,
  stage4FormalParetoAnalysis: null,
  stage4FormalParetoAnalysisError: null,
  finalWearableArchitecture: null,
  finalWearableArchitectureError: null,
  stage4FinalClosureManifest: null,
  stage4FinalClosureManifestError: null,
  futureScienceManifest: null,
  experiments: {},
  selectedExperimentId: null,
  loading: false,
  error: null,
  load: async () => {
    set({ loading: true, error: null });
    // Audit M12: OPTIONAL panels (operational cost, decision inputs, hardware
    // topology, Pareto, engineering readiness) load in ISOLATION. Each rejection
    // is caught here and mapped to that panel's own error, so a 404/500/malformed
    // response on an optional endpoint can NEVER abort the core scientific panels.
    const optional = async <T>(
      promise: Promise<T>,
    ): Promise<{ ok: true; value: T } | { ok: false; error: string }> => {
      try {
        return { ok: true, value: await promise };
      } catch (error) {
        return { ok: false, error: error instanceof Error ? error.message : "unavailable" };
      }
    };
    try {
      // CORE (required) scientific data. A failure here is a genuine Research Mode error.
      const [summaries, projectSummary] = await Promise.all([
        api.getResearchExperiments(),
        api.getResearchSummary(),
      ]);
      const availableIds = summaries
        .filter((item) => item.availability === "available")
        .map((item) => item.experiment_id);
      const envelopes = await Promise.all(availableIds.map((id) => api.getResearchExperiment(id)));
      const experiments: Record<string, ResearchExperiment> = {};
      for (const envelope of envelopes) {
        if (envelope.availability === "available" && envelope.experiment) {
          experiments[envelope.experiment_id] = envelope.experiment;
        }
      }
      // OPTIONAL panels — settled independently; `optional()` never rejects, so
      // this Promise.all cannot throw into the core catch below.
      const [
        operationalCosts,
        decisionInputEnvelope,
        topologyEnvelope,
        readinessEnvelope,
        engineeringEnvelope,
        stage4EngineeringEnvelope,
        stage3EvidenceEnvelope,
        stage4ScienceManifestResult,
        stage4SensorValueMatrixResult,
        stage4ScienceClaimsResult,
        stage4ArchitectureDecisionInputsScienceResult,
        stage4ArchitectureScienceDecisionFrameworkResult,
        stage4SensorDecisionSensitivityResult,
        stage4ScientificParetoInputsResult,
        stage4ArchitectureAcceptanceGatesResult,
        stage4ArchitectureCandidateClassesResult,
        stage4GateDEnvelope,
        stage4CandidateBurdenEnvelope,
        stage4DecisionProjectionEnvelope,
        stage4GateEEnvelope,
        stage4FinalPacketEnvelope,
        stage4ContactElectrodeBurdenEnvelope,
        stage4BatteryTopologyScenariosEnvelope,
        stage4CandidateBurdenMatrixEnvelope,
        stage4GateECoordinatorDecisionsEnvelope,
        stage4FormalParetoAnalysisEnvelope,
        finalWearableArchitectureEnvelope,
        stage4FinalClosureManifestEnvelope,
        futureScienceEnvelope,
      ] = await Promise.all([
        optional(api.getOperationalCosts()),
        optional(api.getDecisionInputs()),
        optional(api.getHardwareTopology()),
        optional(api.getParetoReadiness()),
        optional(api.getEngineeringReadiness()),
        optional(api.getStage4EngineeringReadiness()),
        optional(api.getStage3Evidence()),
        optional(api.getStage4ScienceManifest()),
        optional(api.getStage4SensorValueMatrix()),
        optional(api.getStage4ScienceClaims()),
        optional(api.getStage4ArchitectureDecisionInputsScience()),
        optional(api.getStage4ArchitectureScienceDecisionFramework()),
        optional(api.getStage4SensorDecisionSensitivity()),
        optional(api.getStage4ScientificParetoInputs()),
        optional(api.getStage4ArchitectureAcceptanceGates()),
        optional(api.getStage4ArchitectureCandidateClasses()),
        optional(api.getStage4GateDBurdenCompleteness()),
        optional(api.getStage4CandidateClassBurdenComparison()),
        optional(api.getStage4ArchitectureDecisionProjection()),
        optional(api.getStage4GateECoordinatorOptions()),
        optional(api.getStage4FinalArchitectureDecisionPacket()),
        optional(api.getStage4ContactElectrodeBurden()),
        optional(api.getStage4BatteryTopologyScenarios()),
        optional(api.getStage4CandidateBurdenMatrix()),
        optional(api.getStage4GateECoordinatorDecisions()),
        optional(api.getStage4FormalParetoAnalysis()),
        optional(api.getFinalWearableArchitecture()),
        optional(api.getStage4FinalClosureManifest()),
        optional(api.getFutureScienceManifest()),
      ]);
      const unavailable = [
        ...summaries.filter((item) => item.availability === "unavailable"),
        ...envelopes.filter((item) => item.availability === "unavailable"),
      ];
      set((state) => ({
        summaries,
        projectSummary,
        operationalCostCatalog: operationalCosts.ok ? operationalCosts.value.catalog : null,
        operationalCostError: operationalCosts.ok
          ? (operationalCosts.value.availability === "unavailable"
              ? operationalCosts.value.error ?? "Operational-cost catalog unavailable."
              : null)
          : operationalCosts.error,
        decisionInputs: decisionInputEnvelope.ok ? decisionInputEnvelope.value.decision_inputs : null,
        decisionInputsError: decisionInputEnvelope.ok
          ? (decisionInputEnvelope.value.availability === "unavailable"
              ? decisionInputEnvelope.value.error ?? "Decision inputs unavailable."
              : null)
          : decisionInputEnvelope.error,
        hardwareTopology: topologyEnvelope.ok ? topologyEnvelope.value.topology : null,
        hardwareTopologyError: topologyEnvelope.ok
          ? (topologyEnvelope.value.availability === "unavailable"
              ? topologyEnvelope.value.error ?? "Hardware topology unavailable."
              : null)
          : topologyEnvelope.error,
        paretoReadiness: readinessEnvelope.ok ? readinessEnvelope.value.readiness : null,
        paretoReadinessError: readinessEnvelope.ok
          ? (readinessEnvelope.value.availability === "unavailable"
              ? readinessEnvelope.value.error ?? "Pareto readiness unavailable."
              : null)
          : readinessEnvelope.error,
        engineeringReadiness: engineeringEnvelope.ok ? engineeringEnvelope.value.readiness : null,
        engineeringReadinessError: engineeringEnvelope.ok
          ? (engineeringEnvelope.value.availability === "unavailable"
              ? engineeringEnvelope.value.error ?? "Engineering readiness unavailable."
              : null)
          : engineeringEnvelope.error,
        stage4EngineeringReadiness: stage4EngineeringEnvelope.ok ? stage4EngineeringEnvelope.value.readiness : null,
        stage4EngineeringReadinessError: stage4EngineeringEnvelope.ok
          ? (stage4EngineeringEnvelope.value.availability === "unavailable"
              ? stage4EngineeringEnvelope.value.error ?? "Stage 4 engineering readiness unavailable."
              : null)
          : stage4EngineeringEnvelope.error,
        stage3Evidence: stage3EvidenceEnvelope.ok ? stage3EvidenceEnvelope.value : null,
        stage3EvidenceError: stage3EvidenceEnvelope.ok ? null : stage3EvidenceEnvelope.error,
        stage4ScienceManifest: stage4ScienceManifestResult.ok ? stage4ScienceManifestResult.value : null,
        stage4ScienceManifestError: stage4ScienceManifestResult.ok ? null : stage4ScienceManifestResult.error,
        stage4SensorValueMatrix: stage4SensorValueMatrixResult.ok ? stage4SensorValueMatrixResult.value : null,
        stage4ScienceClaims: stage4ScienceClaimsResult.ok ? stage4ScienceClaimsResult.value : null,
        stage4ArchitectureDecisionInputsScience: stage4ArchitectureDecisionInputsScienceResult.ok
          ? stage4ArchitectureDecisionInputsScienceResult.value
          : null,
        stage4ArchitectureScienceDecisionFramework: stage4ArchitectureScienceDecisionFrameworkResult.ok
          ? stage4ArchitectureScienceDecisionFrameworkResult.value
          : null,
        stage4SensorDecisionSensitivity: stage4SensorDecisionSensitivityResult.ok
          ? stage4SensorDecisionSensitivityResult.value
          : null,
        stage4ScientificParetoInputs: stage4ScientificParetoInputsResult.ok
          ? stage4ScientificParetoInputsResult.value
          : null,
        stage4ArchitectureAcceptanceGates: stage4ArchitectureAcceptanceGatesResult.ok
          ? stage4ArchitectureAcceptanceGatesResult.value
          : null,
        stage4ArchitectureCandidateClasses: stage4ArchitectureCandidateClassesResult.ok
          ? stage4ArchitectureCandidateClassesResult.value
          : null,
        stage4GateDBurdenCompleteness: stage4GateDEnvelope.ok ? stage4GateDEnvelope.value.assessment : null,
        stage4GateDBurdenCompletenessError: stage4GateDEnvelope.ok
          ? (stage4GateDEnvelope.value.availability === "unavailable"
              ? stage4GateDEnvelope.value.error ?? "Gate D burden-completeness assessment unavailable."
              : null)
          : stage4GateDEnvelope.error,
        stage4CandidateClassBurdenComparison: stage4CandidateBurdenEnvelope.ok
          ? stage4CandidateBurdenEnvelope.value.comparison
          : null,
        stage4ArchitectureDecisionProjection: stage4DecisionProjectionEnvelope.ok
          ? stage4DecisionProjectionEnvelope.value.projection
          : null,
        stage4GateECoordinatorOptions: stage4GateEEnvelope.ok ? stage4GateEEnvelope.value.options : null,
        stage4FinalArchitectureDecisionPacket: stage4FinalPacketEnvelope.ok ? stage4FinalPacketEnvelope.value.packet : null,
        stage4ContactElectrodeBurden: stage4ContactElectrodeBurdenEnvelope.ok ? stage4ContactElectrodeBurdenEnvelope.value.burden : null,
        stage4ContactElectrodeBurdenError: stage4ContactElectrodeBurdenEnvelope.ok
          ? (stage4ContactElectrodeBurdenEnvelope.value.availability === "unavailable"
              ? stage4ContactElectrodeBurdenEnvelope.value.error ?? "Contact/electrode burden unavailable."
              : null)
          : stage4ContactElectrodeBurdenEnvelope.error,
        stage4BatteryTopologyScenarios: stage4BatteryTopologyScenariosEnvelope.ok ? stage4BatteryTopologyScenariosEnvelope.value.scenarios : null,
        stage4BatteryTopologyScenariosError: stage4BatteryTopologyScenariosEnvelope.ok
          ? (stage4BatteryTopologyScenariosEnvelope.value.availability === "unavailable"
              ? stage4BatteryTopologyScenariosEnvelope.value.error ?? "Battery topology scenarios unavailable."
              : null)
          : stage4BatteryTopologyScenariosEnvelope.error,
        stage4CandidateBurdenMatrix: stage4CandidateBurdenMatrixEnvelope.ok ? stage4CandidateBurdenMatrixEnvelope.value.matrix : null,
        stage4CandidateBurdenMatrixError: stage4CandidateBurdenMatrixEnvelope.ok
          ? (stage4CandidateBurdenMatrixEnvelope.value.availability === "unavailable"
              ? stage4CandidateBurdenMatrixEnvelope.value.error ?? "Candidate burden matrix unavailable."
              : null)
          : stage4CandidateBurdenMatrixEnvelope.error,
        stage4GateECoordinatorDecisions: stage4GateECoordinatorDecisionsEnvelope.ok ? stage4GateECoordinatorDecisionsEnvelope.value.decisions : null,
        stage4GateECoordinatorDecisionsError: stage4GateECoordinatorDecisionsEnvelope.ok
          ? (stage4GateECoordinatorDecisionsEnvelope.value.availability === "unavailable"
              ? stage4GateECoordinatorDecisionsEnvelope.value.error ?? "Gate E coordinator decisions unavailable."
              : null)
          : stage4GateECoordinatorDecisionsEnvelope.error,
        stage4FormalParetoAnalysis: stage4FormalParetoAnalysisEnvelope.ok ? stage4FormalParetoAnalysisEnvelope.value.analysis : null,
        stage4FormalParetoAnalysisError: stage4FormalParetoAnalysisEnvelope.ok
          ? (stage4FormalParetoAnalysisEnvelope.value.availability === "unavailable"
              ? stage4FormalParetoAnalysisEnvelope.value.error ?? "Formal Pareto analysis unavailable."
              : null)
          : stage4FormalParetoAnalysisEnvelope.error,
        finalWearableArchitecture: finalWearableArchitectureEnvelope.ok ? finalWearableArchitectureEnvelope.value.architecture : null,
        finalWearableArchitectureError: finalWearableArchitectureEnvelope.ok
          ? (finalWearableArchitectureEnvelope.value.availability === "unavailable"
              ? finalWearableArchitectureEnvelope.value.error ?? "Final wearable architecture unavailable."
              : null)
          : finalWearableArchitectureEnvelope.error,
        stage4FinalClosureManifest: stage4FinalClosureManifestEnvelope.ok ? stage4FinalClosureManifestEnvelope.value.manifest : null,
        stage4FinalClosureManifestError: stage4FinalClosureManifestEnvelope.ok
          ? (stage4FinalClosureManifestEnvelope.value.availability === "unavailable"
              ? stage4FinalClosureManifestEnvelope.value.error ?? "Final closure manifest unavailable."
              : null)
          : stage4FinalClosureManifestEnvelope.error,
        // A transport/network failure is folded into the same envelope shape
        // as a content-level INGESTION_FAILED, rather than a bare null — the
        // panel always has an honest status string to render, never silence.
        futureScienceManifest: futureScienceEnvelope.ok
          ? futureScienceEnvelope.value
          : {
              availability: "unavailable",
              status: "INGESTION_FAILED",
              manifest_path: "results/stage2_4_science_completion_manifest.json",
              error_code: null,
              error: futureScienceEnvelope.error,
              manifest: null,
              display_projections: [],
            },
        experiments,
        selectedExperimentId:
          state.selectedExperimentId && experiments[state.selectedExperimentId]
            ? state.selectedExperimentId
            : availableIds[0] ?? null,
        loading: false,
        error: unavailable.length
          ? unavailable.map((item) => `${item.experiment_id}: ${item.error ?? "artifact unavailable"}`).join("; ")
          : null,
      }));
    } catch (error) {
      set({
        loading: false,
        error: error instanceof Error ? error.message : "Research artifacts could not be loaded.",
        operationalCostCatalog: null,
        operationalCostError: error instanceof Error ? error.message : "Operational-cost catalog could not be loaded.",
        decisionInputs: null,
        decisionInputsError: error instanceof Error ? error.message : "Decision inputs could not be loaded.",
        hardwareTopology: null,
        hardwareTopologyError: error instanceof Error ? error.message : "Hardware topology could not be loaded.",
        paretoReadiness: null,
        paretoReadinessError: error instanceof Error ? error.message : "Pareto readiness could not be loaded.",
        engineeringReadiness: null,
        engineeringReadinessError: error instanceof Error ? error.message : "Engineering readiness could not be loaded.",
        stage3Evidence: null,
        stage3EvidenceError: error instanceof Error ? error.message : "Stage 3 evidence could not be loaded.",
        stage4ScienceManifest: null,
        stage4ScienceManifestError: error instanceof Error ? error.message : "Stage 4 science manifest could not be loaded.",
        stage4SensorValueMatrix: null,
        stage4ScienceClaims: null,
        stage4ArchitectureDecisionInputsScience: null,
        stage4ArchitectureScienceDecisionFramework: null,
        stage4SensorDecisionSensitivity: null,
        stage4ScientificParetoInputs: null,
        stage4ArchitectureAcceptanceGates: null,
        stage4ArchitectureCandidateClasses: null,
        stage4GateDBurdenCompleteness: null,
        stage4GateDBurdenCompletenessError: error instanceof Error ? error.message : "Gate D assessment could not be loaded.",
        stage4CandidateClassBurdenComparison: null,
        stage4ArchitectureDecisionProjection: null,
        stage4GateECoordinatorOptions: null,
        stage4FinalArchitectureDecisionPacket: null,
        stage4ContactElectrodeBurden: null,
        stage4ContactElectrodeBurdenError: error instanceof Error ? error.message : "Contact/electrode burden could not be loaded.",
        stage4BatteryTopologyScenarios: null,
        stage4BatteryTopologyScenariosError: error instanceof Error ? error.message : "Battery topology scenarios could not be loaded.",
        stage4CandidateBurdenMatrix: null,
        stage4CandidateBurdenMatrixError: error instanceof Error ? error.message : "Candidate burden matrix could not be loaded.",
        stage4GateECoordinatorDecisions: null,
        stage4GateECoordinatorDecisionsError: error instanceof Error ? error.message : "Gate E coordinator decisions could not be loaded.",
        stage4FormalParetoAnalysis: null,
        stage4FormalParetoAnalysisError: error instanceof Error ? error.message : "Formal Pareto analysis could not be loaded.",
        finalWearableArchitecture: null,
        finalWearableArchitectureError: error instanceof Error ? error.message : "Final wearable architecture could not be loaded.",
        stage4FinalClosureManifest: null,
        stage4FinalClosureManifestError: error instanceof Error ? error.message : "Final closure manifest could not be loaded.",
        futureScienceManifest: null,
      });
    }
  },
  selectExperiment: (experimentId) => set({ selectedExperimentId: experimentId }),
}));
