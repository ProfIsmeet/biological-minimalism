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
    set((state) => {
      const previousIdentity = state.latest
        ? `${state.latest.source.source_type}:${state.latest.source.subject_id ?? ""}`
        : null;
      const nextIdentity = `${snapshot.source.source_type}:${snapshot.source.subject_id ?? ""}`;
      return {
        latest: snapshot,
        history: previousIdentity === nextIdentity ? [...state.history, snapshot].slice(-MAX_HISTORY) : [snapshot],
      };
    }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
}));
