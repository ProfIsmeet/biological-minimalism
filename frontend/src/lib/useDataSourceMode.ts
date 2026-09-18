"use client";

import { useMissionStore } from "@/store/missionStore";

/**
 * Prompt-2 corrective pass §2: REST `/data-source/state` is authoritative
 * once it has resolved at least once. The previous "conservative OR" (WS
 * says replay OR REST says replay) could keep the interface labeled as
 * replay after a confirmed replay → synthetic switch, if a late-arriving
 * WS frame from the old replay source landed after the REST confirmation.
 * The WebSocket-derived source type is now used only during the brief
 * startup window before the first REST response lands.
 */
export function useDatasetReplayMode(): boolean {
  const restSourceType = useMissionStore((state) => state.dataSourceStatus?.source_type);
  const liveSourceType = useMissionStore((state) => state.latest?.source.source_type);

  if (restSourceType !== undefined) return restSourceType === "dataset_replay";
  return liveSourceType === "dataset_replay";
}
