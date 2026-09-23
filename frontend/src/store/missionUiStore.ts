import { create } from "zustand";

import type { FinalModality } from "@/lib/architecture";

/**
 * Prompt-4 §22 — UI-only selection state for `/mission-overview`, lifted out
 * of MissionOverviewExperience's local `useState` so the demo reset (fired
 * from the DemoControlDrawer, a descendant that cannot reach that local state)
 * can return the selected modality to PPG. This holds NO telemetry and NO
 * scientific value — it is purely which modality the operator is currently
 * inspecting, so it is deliberately separate from the telemetry `missionStore`
 * and its confirmed-snapshot logic.
 */
interface MissionUiState {
  selectedModality: FinalModality;
  setSelectedModality: (modality: FinalModality) => void;
}

export const useMissionUiStore = create<MissionUiState>((set) => ({
  selectedModality: "PPG",
  setSelectedModality: (selectedModality) => set({ selectedModality }),
}));
