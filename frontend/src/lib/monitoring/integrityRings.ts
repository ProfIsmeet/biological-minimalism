import type { ModalityNodeState } from "@/lib/monitoring/modalityNodeState";
import type { TelemetryAvailability } from "@/lib/monitoring/telemetryAvailability";

/**
 * Prompt 3B §8 — categorical signal-path integrity for the concentric
 * Inference Integrity Orbit. Every ring is CATEGORICAL: there is no
 * percentage, confidence, probability, health, or readiness value anywhere.
 * Pure and JSX-free so scripts/verify-monitoring-state.ts can assert the
 * mapping directly.
 */
export type IntegrityState = "confirmed" | "awaiting" | "warmup" | "unavailable" | "fault" | "disconnected" | "source_error" | "recovered";

export interface IntegrityRing {
  key: "source" | "ppg" | "imu" | "output";
  label: string;
  state: IntegrityState;
}

function fromTelemetry(t: TelemetryAvailability): IntegrityState {
  switch (t) {
    case "disconnected":
      return "disconnected";
    case "source_error":
      return "source_error";
    case "awaiting_confirmation":
      return "awaiting";
    case "active":
      return "confirmed";
  }
}

function fromNodeState(s: ModalityNodeState): IntegrityState {
  switch (s) {
    case "confirmed":
      return "confirmed";
    case "fault":
      return "fault";
    case "warmup":
      return "warmup";
    case "unavailable":
      return "unavailable";
    case "disconnected":
      return "disconnected";
    case "awaiting_confirmation":
      return "awaiting";
    case "source_error":
      return "source_error";
  }
}

export function deriveIntegrityRings(params: {
  telemetry: TelemetryAvailability;
  ppgState: ModalityNodeState;
  imuState: ModalityNodeState;
  isReplay: boolean;
  predictionAvailable: boolean;
  inferenceWarmingUp: boolean;
  recovered: boolean;
}): IntegrityRing[] {
  const { telemetry, ppgState, imuState, isReplay, predictionAvailable, inferenceWarmingUp, recovered } = params;
  const gated = telemetry !== "active";
  const telState = fromTelemetry(telemetry);

  const source: IntegrityState = gated ? telState : recovered ? "recovered" : "confirmed";
  const ppg: IntegrityState = gated ? telState : fromNodeState(ppgState);
  const imu: IntegrityState = gated ? telState : fromNodeState(imuState);

  let output: IntegrityState;
  if (gated) output = telState;
  else if (!isReplay) output = "unavailable"; // HR inference is replay-only; synthetic never claims output
  else if (recovered) output = "recovered";
  else if (inferenceWarmingUp) output = "warmup";
  else if (predictionAvailable) output = "confirmed";
  else output = "unavailable";

  return [
    { key: "source", label: "Source", state: source },
    { key: "ppg", label: "PPG", state: ppg },
    { key: "imu", label: "IMU", state: imu },
    { key: "output", label: "Output", state: output },
  ];
}
