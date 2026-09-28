import type { PredictionAvailability } from "@/lib/monitoring/inferenceState";
import type { TelemetryAvailability } from "@/lib/monitoring/telemetryAvailability";

export interface HrCorePresentationInput {
  telemetryAvailability: TelemetryAvailability;
  isReplay: boolean;
  predictionValue: number | null;
  inferenceStatusLabel: string;
  faultActive: boolean;
  requiredWindowSeconds: number | null;
}

export interface HrCorePresentation {
  centerValue: string | null;
  centerReason: string;
  nextStateText: string;
}

/**
 * Pure, fail-closed presentation boundary for the current HR readout. Keeping
 * numeric visibility here makes the rebuilding/no-stale-value invariant
 * behaviorally testable without a browser or source-string inspection.
 */
export function deriveHrCorePresentation(input: HrCorePresentationInput): HrCorePresentation {
  const requiredWindowSeconds = input.requiredWindowSeconds ?? 8;
  let centerValue: string | null = null;
  let centerReason: string;

  if (input.telemetryAvailability === "source_error") centerReason = "Source error";
  else if (input.telemetryAvailability === "disconnected") centerReason = "Source disconnected";
  else if (input.telemetryAvailability === "awaiting_confirmation") centerReason = "Awaiting confirmed frame";
  else if (!input.isReplay) centerReason = "Not applicable — synthetic demo";
  else if (input.predictionValue !== null && Number.isFinite(input.predictionValue)) {
    centerValue = input.predictionValue.toFixed(1);
    centerReason = input.inferenceStatusLabel;
  } else centerReason = input.inferenceStatusLabel;

  let nextStateText: string;
  if (input.telemetryAvailability === "source_error") {
    nextStateText = "Next safe state: restore source-state service, then wait for a confirmed frame.";
  } else if (input.telemetryAvailability === "disconnected") {
    nextStateText = "Next safe state: reconnect the source, then wait for a confirmed frame.";
  } else if (input.telemetryAvailability === "awaiting_confirmation") {
    nextStateText = "Next safe state: wait for a confirmed frame from the selected source.";
  } else if (!input.isReplay) {
    nextStateText = "Replay HR is not expected while the synthetic demonstrator is active.";
  } else if (input.faultActive) {
    nextStateText = `Next safe state: clear the simulated fault, then assemble a fresh ${requiredWindowSeconds} s PPG + IMU window.`;
  } else if (centerValue === null) {
    nextStateText = `Next safe state: wait for a fresh ${requiredWindowSeconds} s synchronized PPG + IMU window.`;
  } else {
    nextStateText = "Current safe state: fresh model output available.";
  }

  return { centerValue, centerReason, nextStateText };
}

/** A historical trend value is never promoted to a current-HR summary. */
export function visibleTrendCurrentValue(
  predictionAvailability: PredictionAvailability,
  historicalCurrentValue: number | null,
): number | null {
  return predictionAvailability === "available" ? historicalCurrentValue : null;
}
