import type { ConnectionStatus } from "@/store/missionStore";
import type { ReplayPlaybackState } from "@/lib/types";

/**
 * Transport state is the WebSocket connection lifecycle only. It must never
 * be used to infer data-source scope (see sourceState.ts) — a connection
 * being "connected" says nothing about whether the payload is synthetic,
 * recorded replay, or (never currently) live hardware.
 */
export type TransportState = "connecting" | "connected" | "disconnected" | "error";

export function deriveTransportState(connectionStatus: ConnectionStatus): TransportState {
  if (connectionStatus === "open") return "connected";
  if (connectionStatus === "connecting") return "connecting";
  return "disconnected";
}

/**
 * Canonical replay-session lifecycle (master prompt §5.3). Driven only by
 * fields the backend actually reports — `DataSourceStatus.dataset_configured`
 * for the BIOMIN_PPG_DALIA_PATH boundary, `playback_state` for the rest.
 * `playing` is never inferred merely because the WebSocket is open.
 */
export type ReplaySessionState =
  | "not_applicable"
  | "dataset_unavailable"
  | "subject_unselected"
  | "loading"
  | "ready"
  | "playing"
  | "paused"
  | "completed"
  | "error";

export function deriveReplaySessionState(params: {
  /** null = `/data-source/state` has not resolved yet. */
  datasetConfigured: boolean | null;
  isReplaySource: boolean;
  playbackState: ReplayPlaybackState | null | undefined;
  selectedSubjectId: string | null;
  pendingAction: string | null;
  requestError: string | null;
}): ReplaySessionState {
  const { datasetConfigured, isReplaySource, playbackState, selectedSubjectId, pendingAction, requestError } = params;
  if (datasetConfigured === null) return "loading";
  if (!datasetConfigured) return "dataset_unavailable";
  if (requestError) return "error";
  if (pendingAction === "load") return "loading";
  if (!isReplaySource) return selectedSubjectId ? "not_applicable" : "subject_unselected";
  if (playbackState === "playing") return "playing";
  if (playbackState === "paused") return "paused";
  if (playbackState === "ended") return "completed";
  return "ready";
}

export function replaySessionStateLabel(state: ReplaySessionState): string {
  switch (state) {
    case "not_applicable":
      return "Replay not active";
    case "dataset_unavailable":
      return "Dataset unavailable";
    case "subject_unselected":
      return "No subject selected";
    case "loading":
      return "Loading…";
    case "ready":
      return "Loaded — ready to play";
    case "playing":
      return "Playing";
    case "paused":
      return "Paused";
    case "completed":
      return "Completed";
    case "error":
      return "Replay request failed";
  }
}
