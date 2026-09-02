import { create } from "zustand";

import type { DataSourceStatus, LiveMetricsSnapshot } from "@/lib/types";

const MAX_HISTORY = 180;

function faultIdentity(fault: LiveMetricsSnapshot["fault_injection"] | DataSourceStatus["fault_injection"]): string {
  return fault?.active
    ? `${fault.fault_type}:${fault.target}:${fault.severity}:${fault.seed}`
    : "clean";
}

export type ConnectionStatus = "connecting" | "open" | "closed";

interface MissionState {
  latest: LiveMetricsSnapshot | null;
  history: LiveMetricsSnapshot[];
  dataSourceStatus: DataSourceStatus | null;
  connectionStatus: ConnectionStatus;
  ingest: (snapshot: LiveMetricsSnapshot) => void;
  setDataSourceStatus: (status: DataSourceStatus) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
}

export const useMissionStore = create<MissionState>((set) => ({
  latest: null,
  history: [],
  dataSourceStatus: null,
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
  setDataSourceStatus: (status) =>
    set((state) => {
      const latestIdentity = state.latest
        ? `${state.latest.source.source_type}:${state.latest.source.subject_id ?? ""}`
        : null;
      const statusIdentity = `${status.source_type}:${status.subject_id ?? ""}`;
      const identityChanged = latestIdentity !== null && latestIdentity !== statusIdentity;
      const faultChanged = state.latest !== null
        && faultIdentity(state.latest.fault_injection) !== faultIdentity(status.fault_injection);
      return {
        dataSourceStatus: status,
        latest: identityChanged || faultChanged ? null : state.latest,
        history: identityChanged || faultChanged ? [] : state.history,
      };
    }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
}));
