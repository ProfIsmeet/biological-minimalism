/**
 * Pure, JSX-free modality-node-state derivation, split out of
 * operationalViewModel.ts (which transitively imports
 * components/monitoring/MonitoringSessionContext.tsx — real JSX that plain
 * `node --experimental-strip-types` cannot load) so
 * scripts/verify-monitoring-state.ts can exercise this logic directly, the
 * same convention as lib/monitoring/modalityObservation.ts and
 * lib/monitoring/plotSeries.ts.
 */

import type { ModalityObservation } from "@/lib/monitoring/modalityObservation";
import type { TelemetryAvailability } from "@/lib/monitoring/telemetryAvailability";

/** The exact nine-term operational state vocabulary (master prompt §7). */
export type OperationalStateWord =
  | "Confirmed"
  | "Connected — awaiting confirmed frame"
  | "Replay warm-up"
  | "No channel in current source"
  | "Unavailable"
  | "Disconnected"
  | "Simulated fault"
  | "Recovered"
  | "Source error";

/**
 * Per-modality node-ring state (master prompt §12, extended Prompt 3A.1
 * §4.2/§9). `awaiting_confirmation` and `source_error` were added in Prompt
 * 3A.1 so every modality ring can distinguish "connected, but no confirmed
 * frame for the current source yet" and "the REST source-state channel is
 * erroring" from a plain transport `disconnected` — both are still
 * fail-closed (no current data may be trusted), but the operator-facing
 * reason differs and telling them apart was a hard requirement.
 */
export type ModalityNodeState = "confirmed" | "warmup" | "unavailable" | "fault" | "disconnected" | "awaiting_confirmation" | "source_error";

export function deriveModalityNodeState(params: {
  telemetry: TelemetryAvailability;
  isFaulted: boolean;
  observation: ModalityObservation;
}): ModalityNodeState {
  const { telemetry, isFaulted, observation } = params;
  // Prompt 3A.1 §4.6 — telemetry-gate reasons take precedence over a
  // simulated fault: a fault can only be *currently confirmed* while
  // telemetry is active, never presented as confirmed during a disconnect/
  // awaiting-confirmation/source-error window.
  if (telemetry === "source_error") return "source_error";
  if (telemetry === "disconnected") return "disconnected";
  if (telemetry === "awaiting_confirmation") return "awaiting_confirmation";
  if (isFaulted) return "fault";
  if (observation.state === "unavailable") return "unavailable";
  if (observation.state === "recorded_replay_waiting_for_samples") return "warmup";
  if (observation.state === "synthetic_observed" && observation.syntheticHealth?.status === "offline") return "unavailable";
  return "confirmed";
}

export function nodeStateLabel(state: ModalityNodeState): OperationalStateWord {
  switch (state) {
    case "confirmed":
      return "Confirmed";
    case "warmup":
      return "Replay warm-up";
    case "unavailable":
      return "No channel in current source";
    case "fault":
      return "Simulated fault";
    case "disconnected":
      return "Disconnected";
    case "awaiting_confirmation":
      return "Connected — awaiting confirmed frame";
    case "source_error":
      return "Source error";
  }
}
