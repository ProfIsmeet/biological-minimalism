import { deriveFaultSummaryLabel } from "./inferenceState";
import type { HeartRateInferenceState, HeartRateModelPrediction, ReplayFaultState } from "@/lib/types";

/**
 * Prompt-2C §4 — the exact wording every current-frame-dependent field in
 * FaultAwareInference must show while `isWaitingForConfirmation` is true.
 * This takes precedence over every other branch (replay, synthetic,
 * prediction-missing, inference-missing, fault-missing) because a mismatched
 * snapshot must never leak stale prediction/inference/fault content — see
 * useConfirmedSnapshot() and sourceIdentity.ts for why the mismatch happens.
 */
export const WAITING_FOR_CONFIRMED_FRAME_MESSAGE = "Waiting for a confirmed frame from the selected source.";

/**
 * Prompt-2D §3 — transport disconnect must suppress every current-frame
 * field, not just the ones that already happened to check `connected`.
 * `useLiveFeed`/`missionStore` flip `connectionStatus` on disconnect but
 * deliberately do not erase the last-received `latest` snapshot (so a
 * reconnect can resume without a blank flash) — which means a stale
 * prediction/inference/fault object can still be passed into this helper
 * after transport drops. Every current-frame field returns this exact
 * message in that case, ignoring whatever stale objects were passed in.
 */
export const SOURCE_DISCONNECTED_MESSAGE = "Unavailable — source disconnected";

/**
 * Prompt-2D §4 — connected replay before the backend has reported any
 * inference status yet. Distinct from "synthetic demo mode": replay IS the
 * active, applicable mode here, there is simply no inference payload yet.
 * Must never be conflated with the synthetic branch merely because
 * `inference` happens to be null.
 */
export const NO_INFERENCE_STATUS_YET_MESSAGE = "No inference status reported yet for the current replay session.";

const SYNTHETIC_NOT_APPLICABLE_MESSAGE = "Not applicable in synthetic demo mode";

export type FaultAwareInferenceStatus = "Nominal" | "Degraded" | "Unavailable" | "Waiting";

export interface FaultAwareInferenceView {
  status: FaultAwareInferenceStatus;
  currentInferenceSource: string;
  /** Architecture-level, not current-frame telemetry — never gated on waiting. */
  primaryVsFallback: string;
  activeFaultCondition: string;
  predictionAvailability: string;
  currentValidPrediction: string;
  inferenceModelStatus: string;
}

export function deriveFaultAwareInferenceView(params: {
  connected: boolean;
  isReplay: boolean;
  isWaitingForConfirmation: boolean;
  prediction: HeartRateModelPrediction | null | undefined;
  inference: HeartRateInferenceState | null | undefined;
  fault: ReplayFaultState | null | undefined;
}): FaultAwareInferenceView {
  const { connected, isReplay, isWaitingForConfirmation, prediction, inference, fault } = params;

  const primaryVsFallback = isReplay
    ? "Primary: PPG + IMU model. No fallback source is implemented."
    : "Not applicable in synthetic demo mode.";

  if (isWaitingForConfirmation) {
    return {
      status: "Waiting",
      currentInferenceSource: WAITING_FOR_CONFIRMED_FRAME_MESSAGE,
      primaryVsFallback,
      activeFaultCondition: WAITING_FOR_CONFIRMED_FRAME_MESSAGE,
      predictionAvailability: WAITING_FOR_CONFIRMED_FRAME_MESSAGE,
      currentValidPrediction: WAITING_FOR_CONFIRMED_FRAME_MESSAGE,
      inferenceModelStatus: WAITING_FOR_CONFIRMED_FRAME_MESSAGE,
    };
  }

  // Prompt-2D §3 — transport disconnect takes precedence over every
  // remaining branch. `prediction`/`inference`/`fault` are deliberately
  // never read below this point when disconnected: a stale snapshot from
  // before the drop must never be presented as current.
  if (!connected) {
    return {
      status: "Unavailable",
      currentInferenceSource: SOURCE_DISCONNECTED_MESSAGE,
      primaryVsFallback,
      activeFaultCondition: SOURCE_DISCONNECTED_MESSAGE,
      predictionAvailability: SOURCE_DISCONNECTED_MESSAGE,
      currentValidPrediction: SOURCE_DISCONNECTED_MESSAGE,
      inferenceModelStatus: SOURCE_DISCONNECTED_MESSAGE,
    };
  }

  if (!isReplay) {
    return {
      status: "Unavailable",
      currentInferenceSource: "Synthetic demo (not AI-estimated)",
      primaryVsFallback,
      activeFaultCondition: "None",
      predictionAvailability: SYNTHETIC_NOT_APPLICABLE_MESSAGE,
      currentValidPrediction: SYNTHETIC_NOT_APPLICABLE_MESSAGE,
      inferenceModelStatus: SYNTHETIC_NOT_APPLICABLE_MESSAGE,
    };
  }

  // Connected, replay selected, confirmed (or not-yet-received) snapshot.
  const status: FaultAwareInferenceStatus = !prediction
    ? "Unavailable"
    : fault?.active || inference?.status !== "available"
      ? "Degraded"
      : "Nominal";

  const currentInferenceSource = prediction ? "AI-estimated · PPG + IMU model" : "Unavailable";

  const activeFaultCondition = deriveFaultSummaryLabel(fault).replace("No simulated fault is active.", "None");

  const predictionAvailability = prediction
    ? "Valid prediction for the current window"
    : inference
      ? "No valid prediction — see status below"
      : "Unavailable";

  const currentValidPrediction = prediction
    ? `${prediction.value.toFixed(1)} bpm (window ${prediction.provenance.window_start_seconds.toFixed(1)}s)`
    : "None this window";

  const inferenceModelStatus = inference ? inference.status.replaceAll("_", " ") : NO_INFERENCE_STATUS_YET_MESSAGE;

  return {
    status,
    currentInferenceSource,
    primaryVsFallback,
    activeFaultCondition,
    predictionAvailability,
    currentValidPrediction,
    inferenceModelStatus,
  };
}
