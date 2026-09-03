import { create } from "zustand";

import { api } from "@/lib/api";
import type {
  ResearchExperiment,
  ResearchExperimentSummaryEnvelope,
  ResearchProjectSummary,
} from "@/lib/types";

interface ResearchState {
  summaries: ResearchExperimentSummaryEnvelope[];
  projectSummary: ResearchProjectSummary | null;
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
  experiments: {},
  selectedExperimentId: null,
  loading: false,
  error: null,
  load: async () => {
    set({ loading: true, error: null });
    try {
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
      const unavailable = [
        ...summaries.filter((item) => item.availability === "unavailable"),
        ...envelopes.filter((item) => item.availability === "unavailable"),
      ];
      set((state) => ({
        summaries,
        projectSummary,
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
      });
    }
  },
  selectExperiment: (experimentId) => set({ selectedExperimentId: experimentId }),
}));
