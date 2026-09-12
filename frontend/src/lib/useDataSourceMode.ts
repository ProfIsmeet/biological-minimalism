"use client";

import { useMissionStore } from "@/store/missionStore";

/**
 * Combines WebSocket provenance with the authoritative REST source state.
 * The REST check covers replay that was loaded but remains paused, before a
 * replay frame has replaced the last synthetic WebSocket snapshot.
 */
export function useDatasetReplayMode(): boolean {
  const liveSourceType = useMissionStore((state) => state.latest?.source.source_type);
  const restSourceType = useMissionStore((state) => state.dataSourceStatus?.source_type);

  // When either view still says replay, hide synthetic-only values. This is
  // intentionally conservative during source-transition races.
  return liveSourceType === "dataset_replay" || restSourceType === "dataset_replay";
}
