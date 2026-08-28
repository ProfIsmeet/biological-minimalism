import { create } from "zustand";

import type { LiveMetricsSnapshot } from "@/lib/types";

const MAX_HISTORY = 180;

export type ConnectionStatus = "connecting" | "open" | "closed";

interface MissionState {
  latest: LiveMetricsSnapshot | null;
  history: LiveMetricsSnapshot[];
  connectionStatus: ConnectionStatus;
  ingest: (snapshot: LiveMetricsSnapshot) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
}

export const useMissionStore = create<MissionState>((set) => ({
  latest: null,
  history: [],
  connectionStatus: "connecting",
  ingest: (snapshot) =>
    set((state) => ({
      latest: snapshot,
      history: [...state.history, snapshot].slice(-MAX_HISTORY),
    })),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
}));
