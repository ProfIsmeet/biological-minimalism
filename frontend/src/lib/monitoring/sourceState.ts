import { deriveConnectionLabel, deriveSourceLabel, type ConnectionLabel, type SourceLabel } from "../sourceLabel";
import type { ConnectionStatus } from "@/store/missionStore";

export { deriveConnectionLabel, deriveSourceLabel };
export type { ConnectionLabel, SourceLabel };

/**
 * Machine-readable counterpart to `SourceLabel` (lib/sourceLabel.ts), which
 * holds the display strings. Kept separate rather than folded into
 * sourceLabel.ts because callers that branch on source type (e.g. deciding
 * whether fault injection is enabled) want a stable enum, not display text
 * that could be restyled independently later.
 */
export type SourceType = "synthetic_demo" | "recorded_replay" | "live_hardware" | "unavailable";

export function deriveSourceType(params: {
  connectionStatus: ConnectionStatus;
  isReplay: boolean;
  /** Reserved for a future genuine live-hardware source; always false today. */
  isLiveHardware?: boolean;
}): SourceType {
  const { connectionStatus, isReplay, isLiveHardware = false } = params;
  if (connectionStatus !== "open") return "unavailable";
  if (isLiveHardware) return "live_hardware";
  return isReplay ? "recorded_replay" : "synthetic_demo";
}

/**
 * A short, honest sentence for "what is this session, exactly" — used by the
 * source strip and the scope/provenance footer. Never invents a dataset name
 * or subject id; falls back to explicit unavailable text.
 */
export function deriveSourceProvenanceText(params: {
  sourceType: SourceType;
  datasetName: string | null | undefined;
  subjectId: string | null | undefined;
}): string {
  const { sourceType, datasetName, subjectId } = params;
  if (sourceType === "unavailable") return "Not provided by current source";
  if (sourceType === "synthetic_demo") return "Synthetic demo session (mock data engine)";
  if (sourceType === "live_hardware") return "Live hardware session";
  return `${datasetName ?? "Dataset unavailable"} · ${subjectId ?? "No subject selected"}`;
}
