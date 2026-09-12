import { API_BASE_URL } from "@/lib/config";
import type {
  AIExplanation,
  AvailableSubjectsResponse,
  DataSourceStatus,
  DigitalTwinState,
  LiveMetricsSnapshot,
  MissionMode,
  OperationalCostCatalogEnvelope,
  OperationalCostComponentEnvelope,
  ParetoDecisionInputsEnvelope,
  EngineeringReadinessEnvelope,
  FutureScienceManifestEnvelope,
  HardwareTopologyEnvelope,
  ParetoReadinessDay6Envelope,
  ReplayFaultConfig,
  ResearchExperimentEnvelope,
  ResearchExperimentSummaryEnvelope,
  ResearchProjectSummary,
  SensorHealthSnapshot,
  Stage3EvidenceEnvelope,
  Stage3EvidenceEntry,
  Stage4ArchitectureAcceptanceGates,
  Stage4ArchitectureCandidateClasses,
  Stage4ArchitectureDecisionInputsScience,
  Stage4ArchitectureDecisionProjectionEnvelope,
  Stage4ArchitectureScienceDecisionFramework,
  Stage4BatteryTopologyScenariosEnvelope,
  Stage4CandidateBurdenMatrixEnvelope,
  Stage4CandidateClassBurdenComparisonEnvelope,
  Stage4ContactElectrodeBurdenEnvelope,
  Stage4EngineeringReadinessEnvelope,
  Stage4FinalArchitectureDecisionPacketEnvelope,
  Stage4FinalClosureManifestEnvelope,
  FinalWearableArchitectureEnvelope,
  Stage4FormalParetoAnalysisEnvelope,
  Stage4GateDBurdenCompletenessEnvelope,
  Stage4GateECoordinatorDecisionsEnvelope,
  Stage4GateECoordinatorOptionsEnvelope,
  Stage4ScienceClaimLedger,
  Stage4ScienceConsumptionManifest,
  Stage4ScientificParetoInputs,
  Stage4SensorDecisionSensitivity,
  Stage4SensorValueMatrix,
  SensorName,
  SensorStatus,
  SimulationStateResponse,
} from "@/lib/types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`Request to ${path} failed (${response.status}): ${body}`);
  }
  return (await response.json()) as T;
}

export const api = {
  getLiveMetrics: () => request<LiveMetricsSnapshot>("/metrics/live"),

  getMetricsHistory: (limit = 100) => request<LiveMetricsSnapshot[]>(`/metrics/history?limit=${limit}`),

  getDigitalTwin: (day: number) => request<DigitalTwinState>(`/digital-twin?day=${day}`),

  getSensorHealth: () => request<SensorHealthSnapshot>("/sensor-health"),

  getSimulationState: () => request<SimulationStateResponse>("/simulation/state"),

  setMissionMode: (mode: MissionMode) =>
    request<SimulationStateResponse>("/simulation/mode", {
      method: "POST",
      body: JSON.stringify({ mode }),
    }),

  setSensorFailure: (sensor: SensorName, status: SensorStatus) =>
    request<SimulationStateResponse>("/simulation/failure", {
      method: "POST",
      body: JSON.stringify({ sensor, status }),
    }),

  getExplanation: (target: "ai_confidence" | "fatigue_risk") =>
    request<AIExplanation>(`/ai/explanation?target=${target}`),

  getDataSourceState: () => request<DataSourceStatus>("/data-source/state"),

  getReplaySubjects: () => request<AvailableSubjectsResponse>("/data-source/subjects"),

  useSyntheticSource: () => request<DataSourceStatus>("/data-source/synthetic", { method: "POST" }),

  loadReplaySubject: (subjectId: string) =>
    request<DataSourceStatus>("/data-source/replay/load", {
      method: "POST",
      body: JSON.stringify({ subject_id: subjectId }),
    }),

  playReplay: () => request<DataSourceStatus>("/data-source/replay/play", { method: "POST" }),

  pauseReplay: () => request<DataSourceStatus>("/data-source/replay/pause", { method: "POST" }),

  resetReplay: () => request<DataSourceStatus>("/data-source/replay/reset", { method: "POST" }),

  setReplaySpeed: (speed: 1 | 5 | 10) =>
    request<DataSourceStatus>("/data-source/replay/speed", {
      method: "POST",
      body: JSON.stringify({ speed }),
    }),

  configureReplayFault: (config: ReplayFaultConfig) =>
    request<DataSourceStatus>("/data-source/replay/fault", {
      method: "POST",
      body: JSON.stringify(config),
    }),

  clearReplayFault: () =>
    request<DataSourceStatus>("/data-source/replay/fault", { method: "DELETE" }),

  getResearchExperiments: () =>
    request<ResearchExperimentSummaryEnvelope[]>("/research/experiments"),

  getResearchExperiment: (experimentId: string) =>
    request<ResearchExperimentEnvelope>(`/research/experiments/${encodeURIComponent(experimentId)}`),

  getResearchSummary: () => request<ResearchProjectSummary>("/research/summary"),

  getOperationalCosts: () =>
    request<OperationalCostCatalogEnvelope>("/research/operational-costs"),

  getOperationalCostComponent: (componentId: string) =>
    request<OperationalCostComponentEnvelope>(`/research/operational-costs/${encodeURIComponent(componentId)}`),

  getDecisionInputs: () => request<ParetoDecisionInputsEnvelope>("/research/decision-inputs"),

  getHardwareTopology: () => request<HardwareTopologyEnvelope>("/research/hardware-topology"),

  getParetoReadiness: () => request<ParetoReadinessDay6Envelope>("/research/pareto-readiness"),

  getEngineeringReadiness: () =>
    request<EngineeringReadinessEnvelope>("/research/engineering-readiness"),

  getFutureScienceManifest: () =>
    request<FutureScienceManifestEnvelope>("/research/future-science-manifest"),

  getStage4EngineeringReadiness: () =>
    request<Stage4EngineeringReadinessEnvelope>("/research/stage4-engineering-readiness"),

  getStage3Evidence: () => request<Stage3EvidenceEnvelope>("/research/stage3-evidence"),

  getStage3EvidenceFamily: (familyId: string) =>
    request<Stage3EvidenceEntry>(`/research/stage3-evidence/${familyId}`),

  getStage4ScienceManifest: () =>
    request<Stage4ScienceConsumptionManifest>("/research/stage4-science-manifest"),

  getStage4SensorValueMatrix: () =>
    request<Stage4SensorValueMatrix>("/research/stage4-sensor-value-matrix"),

  getStage4ScienceClaims: () => request<Stage4ScienceClaimLedger>("/research/stage4-science-claims"),

  getStage4ArchitectureDecisionInputsScience: () =>
    request<Stage4ArchitectureDecisionInputsScience>("/research/stage4-architecture-decision-inputs-science"),

  getStage4ArchitectureScienceDecisionFramework: () =>
    request<Stage4ArchitectureScienceDecisionFramework>("/research/stage4-architecture-science-decision-framework"),

  getStage4SensorDecisionSensitivity: () =>
    request<Stage4SensorDecisionSensitivity>("/research/stage4-sensor-decision-sensitivity"),

  getStage4ScientificParetoInputs: () =>
    request<Stage4ScientificParetoInputs>("/research/stage4-scientific-pareto-inputs"),

  getStage4ArchitectureAcceptanceGates: () =>
    request<Stage4ArchitectureAcceptanceGates>("/research/stage4-architecture-acceptance-gates"),

  getStage4ArchitectureCandidateClasses: () =>
    request<Stage4ArchitectureCandidateClasses>("/research/stage4-architecture-candidate-classes"),

  getStage4GateDBurdenCompleteness: () =>
    request<Stage4GateDBurdenCompletenessEnvelope>("/research/stage4-gate-d-burden-completeness"),

  getStage4CandidateClassBurdenComparison: () =>
    request<Stage4CandidateClassBurdenComparisonEnvelope>("/research/stage4-candidate-class-burden-comparison"),

  getStage4ArchitectureDecisionProjection: () =>
    request<Stage4ArchitectureDecisionProjectionEnvelope>("/research/stage4-architecture-decision-projection"),

  getStage4GateECoordinatorOptions: () =>
    request<Stage4GateECoordinatorOptionsEnvelope>("/research/stage4-gate-e-coordinator-options"),

  getStage4FinalArchitectureDecisionPacket: () =>
    request<Stage4FinalArchitectureDecisionPacketEnvelope>("/research/stage4-final-architecture-decision-packet"),

  getStage4ContactElectrodeBurden: () =>
    request<Stage4ContactElectrodeBurdenEnvelope>("/research/stage4-contact-electrode-burden"),

  getStage4BatteryTopologyScenarios: () =>
    request<Stage4BatteryTopologyScenariosEnvelope>("/research/stage4-battery-topology-scenarios"),

  getStage4CandidateBurdenMatrix: () =>
    request<Stage4CandidateBurdenMatrixEnvelope>("/research/stage4-candidate-burden-matrix"),

  getStage4GateECoordinatorDecisions: () =>
    request<Stage4GateECoordinatorDecisionsEnvelope>("/research/stage4-gate-e-coordinator-decisions"),

  getStage4FormalParetoAnalysis: () =>
    request<Stage4FormalParetoAnalysisEnvelope>("/research/stage4-formal-pareto-analysis"),

  getFinalWearableArchitecture: () =>
    request<FinalWearableArchitectureEnvelope>("/research/final-wearable-architecture"),

  getStage4FinalClosureManifest: () =>
    request<Stage4FinalClosureManifestEnvelope>("/research/stage4-final-closure-manifest"),
};
