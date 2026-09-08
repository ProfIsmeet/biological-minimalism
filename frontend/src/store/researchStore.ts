import { create } from "zustand";

import { api } from "@/lib/api";
import type {
  OperationalCostCatalog,
  EngineeringReadiness,
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
  engineeringReadiness: EngineeringReadiness | null;
  engineeringReadinessError: string | null;
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
      const [operationalCosts, decisionInputEnvelope, topologyEnvelope, readinessEnvelope, engineeringEnvelope] =
        await Promise.all([
          optional(api.getOperationalCosts()),
          optional(api.getDecisionInputs()),
          optional(api.getHardwareTopology()),
          optional(api.getParetoReadiness()),
          optional(api.getEngineeringReadiness()),
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
      });
    }
  },
  selectExperiment: (experimentId) => set({ selectedExperimentId: experimentId }),
}));
