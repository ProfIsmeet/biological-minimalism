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
  ReplayFaultConfig,
  ResearchExperimentEnvelope,
  ResearchExperimentSummaryEnvelope,
  ResearchProjectSummary,
  SensorHealthSnapshot,
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
};
