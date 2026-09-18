import type { ConnectionStatus } from "@/store/missionStore";

/**
 * Single canonical source-label derivation, used by every surface that
 * displays data-source scope (TopBar, SourceStatusStrip, JuryHero,
 * FaultAwareInference, FinalSensorLedger).
 *
 * Connection state and data-source scope are separate concepts: a WebSocket
 * being open does not make synthetic mock data "live hardware". The current
 * backend contract (`DataSourceType = "synthetic" | "dataset_replay"`, see
 * lib/types.ts) has no live-hardware member, so `LIVE SOURCE` is accepted by
 * this type for forward-compatibility but this function can never currently
 * return it — it is derived only from `isLiveHardware`, which nothing in
 * this codebase sets true today.
 */
export type SourceLabel = "SYNTHETIC DEMO" | "RECORDED REPLAY" | "LIVE SOURCE" | "UNAVAILABLE";
export type ConnectionLabel = "CONNECTING" | "CONNECTED" | "DISCONNECTED";

export function deriveConnectionLabel(connectionStatus: ConnectionStatus): ConnectionLabel {
  if (connectionStatus === "open") return "CONNECTED";
  if (connectionStatus === "connecting") return "CONNECTING";
  return "DISCONNECTED";
}

export function deriveSourceLabel(params: {
  connectionStatus: ConnectionStatus;
  isReplay: boolean;
  /** Reserved for a future genuine live-hardware source; always false today. */
  isLiveHardware?: boolean;
}): SourceLabel {
  const { connectionStatus, isReplay, isLiveHardware = false } = params;
  if (connectionStatus !== "open") return "UNAVAILABLE";
  if (isLiveHardware) return "LIVE SOURCE";
  return isReplay ? "RECORDED REPLAY" : "SYNTHETIC DEMO";
}
