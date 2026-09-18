import type { HeartRateInferenceState, HeartRateModelPrediction, ReplayFaultState } from "@/lib/types";

/**
 * Prediction availability is reported independently of accuracy (master
 * prompt §8.5 — "Error metrics are defined only for valid predictions.
 * Prediction availability is reported separately."). `not_applicable` covers
 * both "disconnected" and "synthetic demo" — this codebase has no AI-
 * estimated HR outside recorded replay, so treating those the same way here
 * is not a shortcut, it is the actual contract.
 */
export type PredictionAvailability = "available" | "unavailable_no_prediction" | "not_applicable";

export function derivePredictionAvailability(params: {
  connected: boolean;
  isReplay: boolean;
  prediction: HeartRateModelPrediction | null | undefined;
}): PredictionAvailability {
  if (!params.connected || !params.isReplay) return "not_applicable";
  return params.prediction ? "available" : "unavailable_no_prediction";
}

export function predictionAvailabilityLabel(availability: PredictionAvailability): string {
  switch (availability) {
    case "available":
      return "Valid prediction for the current window";
    case "unavailable_no_prediction":
      return "No valid prediction for the current window";
    case "not_applicable":
      return "Not applicable — recorded replay is not active";
  }
}

export function inferenceStatusLabel(inference: HeartRateInferenceState | null | undefined, isReplay: boolean): string {
  if (!inference) {
    return isReplay
      ? "No inference status reported yet for the current replay session"
      : "Not applicable in synthetic demo mode";
  }
  switch (inference.status) {
    case "warming_up":
      return "Model is warming up";
    case "available":
      return "Model available";
    case "input_unavailable":
      return "Required PPG + IMU input window is unavailable";
    case "model_unavailable":
      return "HR model is unavailable";
    case "error":
      return "Inference error";
  }
}

/**
 * A fault is only ever "simulated" in this codebase — there is no genuine
 * hardware-failure detector. The word "simulated" is included in every
 * non-empty label on purpose (master prompt §5.6/§8.6).
 */
export function deriveFaultSummaryLabel(fault: ReplayFaultState | null | undefined): string {
  if (!fault?.active) return "No simulated fault is active.";
  const parts = [
    fault.target ? fault.target.toUpperCase() : null,
    fault.fault_type ? fault.fault_type.replaceAll("_", " ") : null,
    fault.severity !== null && fault.severity !== undefined ? `severity ${fault.severity}` : null,
  ].filter((part): part is string => Boolean(part));
  return `Simulated fault active — ${parts.join(" · ")}`;
}

/**
 * The runtime contract has no reference/ground-truth HR channel — see
 * backend/app/schemas/telemetry.py VitalsSnapshot and
 * HeartRateModelPrediction, neither of which carries one. `reference` will
 * therefore always be `null` from every current caller; this function stays
 * generic so it fails closed (returns null) rather than silently treating a
 * missing reference as zero difference.
 */
export function computeCurrentWindowAbsoluteDifference(
  estimateBpm: number | null,
  referenceBpm: number | null,
): number | null {
  if (estimateBpm === null || referenceBpm === null) return null;
  return Math.abs(estimateBpm - referenceBpm);
}
