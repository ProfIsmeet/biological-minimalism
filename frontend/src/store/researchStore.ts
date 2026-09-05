import { create } from "zustand";

import { api } from "@/lib/api";
import type {
  OperationalCostCatalog,
  HardwareTopologyContract,
  ParetoDecisionInputs,
  ParetoReadinessDay6,
  ResearchExperiment,
  ResearchExperimentSummaryEnvelope,
  ResearchProjectSummary,
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
  experiments: {},
  selectedExperimentId: null,
  loading: false,
  error: null,
  load: async () => {
    set({ loading: true, error: null });
    try {
      const [summaries, projectSummary, operationalCosts, decisionInputEnvelope, topologyEnvelope, readinessEnvelope] = await Promise.all([
        api.getResearchExperiments(),
        api.getResearchSummary(),
        api.getOperationalCosts(),
        api.getDecisionInputs(),
        api.getHardwareTopology(),
        api.getParetoReadiness(),
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
      const unavailable = [
        ...summaries.filter((item) => item.availability === "unavailable"),
        ...envelopes.filter((item) => item.availability === "unavailable"),
      ];
      set((state) => ({
        summaries,
        projectSummary,
        operationalCostCatalog: operationalCosts.catalog,
        operationalCostError:
          operationalCosts.availability === "unavailable"
            ? operationalCosts.error ?? "Operational-cost catalog unavailable."
            : null,
        decisionInputs: decisionInputEnvelope.decision_inputs,
        decisionInputsError:
          decisionInputEnvelope.availability === "unavailable"
            ? decisionInputEnvelope.error ?? "Decision inputs unavailable."
            : null,
        hardwareTopology: topologyEnvelope.topology,
        hardwareTopologyError: topologyEnvelope.availability === "unavailable" ? topologyEnvelope.error ?? "Hardware topology unavailable." : null,
        paretoReadiness: readinessEnvelope.readiness,
        paretoReadinessError: readinessEnvelope.availability === "unavailable" ? readinessEnvelope.error ?? "Pareto readiness unavailable." : null,
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
      });
    }
  },
  selectExperiment: (experimentId) => set({ selectedExperimentId: experimentId }),
}));
