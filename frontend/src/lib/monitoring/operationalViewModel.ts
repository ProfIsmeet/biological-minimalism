"use client";

/**
 * Single shared operational view model (master prompt 3 §6) for every
 * component on the operational mission interface (`/mission-overview` and
 * the compact reuses on `/live-monitoring`). Every field here is derived
 * from the same canonical sources the pre-existing jury/monitoring
 * components already used independently (MonitoringSessionContext,
 * useConfirmedSnapshot, useDatasetReplayMode, deriveModalityObservation,
 * inferenceState helpers) — nothing is re-implemented, only composed once so
 * a source transition can never leave one operational component showing a
 * stale value while another has already moved on.
 *
 * No component under components/operations/** may read
 * `useMissionStore((s) => s.latest)` or `.history` directly, or call
 * `useMonitoringSession()` itself — they all read this hook instead. Guarded
 * structurally by scripts/verify-monitoring-consumers.mjs.
 */

import { useMonitoringSession } from "@/components/monitoring/MonitoringSessionContext";
import { FINAL_SENSOR_INVENTORY, type FinalModality, type FinalRegion } from "@/lib/architecture";
import { deriveFaultSummaryLabel, derivePredictionAvailability, inferenceStatusLabel, type PredictionAvailability } from "@/lib/monitoring/inferenceState";
import { deriveModalityObservation, type ModalityObservation } from "@/lib/monitoring/modalityObservation";
import { deriveModalityNodeState, nodeStateLabel, type ModalityNodeState, type OperationalStateWord } from "@/lib/monitoring/modalityNodeState";
import { resolvePlotSeries, type PlotSeries } from "@/lib/monitoring/plotSeries";
import { deriveReplaySessionState, type ReplaySessionState } from "@/lib/monitoring/runtimeState";
import { deriveConnectionLabel, deriveSourceLabel, deriveSourceType, type SourceType } from "@/lib/monitoring/sourceState";
import { applyFaultOverride, applyTelemetryGate, deriveTelemetryAvailability, resolveReplayStateLabel, type TelemetryAvailability } from "@/lib/monitoring/telemetryAvailability";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import type { ConnectionLabel, SourceLabel } from "@/lib/sourceLabel";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";
import type { HeartRateInferenceState, HeartRateModelPrediction, ReplayFaultState, ReplayFaultTarget } from "@/lib/types";

export type { OperationalStateWord, ModalityNodeState, TelemetryAvailability };

export interface OperationalModalityState {
  modality: FinalModality;
  region: FinalRegion;
  observation: ModalityObservation;
  nodeState: ModalityNodeState;
  stateLabel: OperationalStateWord;
  /** Real plottable samples for this modality/source, or null — never fabricated. */
  plot: PlotSeries | null;
}

export interface OperationalViewModel {
  // --- connection / source -------------------------------------------------
  connected: boolean;
  connectionLabel: ConnectionLabel;
  sourceType: SourceType;
  sourceLabel: SourceLabel;
  isReplay: boolean;
  sourceStateStatus: "loading" | "available" | "error";
  sourceStateError: string | null;
  /** Prompt 3A.1 §4.2 — the single authoritative "may current telemetry be trusted" gate. See telemetryAvailability.ts. */
  telemetryAvailability: TelemetryAvailability;
  // --- session identity ------------------------------------------------------
  datasetName: string | null;
  subjectId: string | null;
  isS14: boolean;
  subjects: string[];
  subjectListState: "loading" | "available" | "empty" | "error";
  subjectListError: string | null;
  // --- replay ----------------------------------------------------------------
  replaySessionState: ReplaySessionState;
  replaySessionStateLabel: string;
  replayPositionSeconds: number | null;
  replayDurationSeconds: number | null;
  playbackSpeed: number | null;
  // --- confirmed snapshot ------------------------------------------------------
  isWaitingForConfirmation: boolean;
  confirmedTimestampSeconds: number | null;
  // --- modalities --------------------------------------------------------------
  modalities: OperationalModalityState[];
  confirmedModalityCount: number;
  totalModalityCount: number;
  // --- fault ---------------------------------------------------------------
  fault: ReplayFaultState | null;
  faultActive: boolean;
  faultSummaryLabel: string;
  faultedModalities: FinalModality[];
  // --- inference / prediction ------------------------------------------------
  prediction: HeartRateModelPrediction | null;
  predictionAvailability: PredictionAvailability;
  inference: HeartRateInferenceState | null;
  inferenceStatusLabel: string;
  // --- overall summary label (MissionStatusBar / drawer header) --------------
  overallStateLabel: OperationalStateWord;
  // --- pending demo-control action --------------------------------------------
  pendingAction: string | null;
  requestError: string | null;
}

const FAULT_TARGET_MODALITIES: Record<ReplayFaultTarget, FinalModality[]> = {
  ppg: ["PPG"],
  imu: ["IMU"],
  both: ["PPG", "IMU"],
};

export function useOperationalViewModel(): OperationalViewModel {
  const connectionStatus = useMissionStore((state) => state.connectionStatus);
  // Prompt 3A.1 §4.3 — deliberately read independently of `latest`/`current`
  // below: this is the one field explicitly permitted to survive a
  // disconnect (missionStore only clears it on a genuine identity/fault
  // change, never on transport drop — see missionStore.ts).
  const lastConfirmedTimestampSeconds = useMissionStore((state) => state.lastConfirmedTimestampSeconds);
  const isReplay = useDatasetReplayMode();
  const { snapshot: latest, isWaitingForConfirmation } = useConfirmedSnapshot();
  const {
    status,
    datasetConfigured,
    sourceStateStatus,
    sourceStateError,
    subjects,
    subjectListState,
    subjectListError,
    selectedSubjectId,
    pending,
    requestError,
  } = useMonitoringSession();

  const connected = connectionStatus === "open";
  const sourceType = deriveSourceType({ connectionStatus, isReplay });
  const sourceLabel = deriveSourceLabel({ connectionStatus, isReplay });
  const connectionLabel = deriveConnectionLabel(connectionStatus);

  // Prompt 3A.1 §4.1/§4.2 — root-cause fix. `latest` is already
  // identity-confirmed (useConfirmedSnapshot) and, since the missionStore
  // fix, already null whenever transport is not open. `telemetryAvailability`
  // additionally folds in the REST-only `source_error` case (where the WS
  // could technically still be delivering frames but `/data-source/state`
  // itself is erroring) — see telemetryAvailability.ts for the full
  // priority order. `current` is the one gated alias every current-frame
  // field below reads instead of `latest` directly, so nothing can
  // accidentally bypass the gate the way the pre-3A.1 code did.
  const telemetryAvailability = deriveTelemetryAvailability({
    connected,
    sourceStateStatus,
    hasConfirmedSnapshot: latest !== null,
  });
  const telemetryActive = telemetryAvailability === "active";
  const current = telemetryActive ? latest : null;
  // Showing the *target* session identity while genuinely mid-transition
  // (awaiting_confirmation — e.g. right after switching subject, before the
  // first matching frame) is informative, not stale data, and explicitly
  // allowed. Disconnected and source_error must not fall back to anything
  // here (§4.3/§4.4 — "do not fall back to previous... session identity").
  const statusFallbackAllowed = telemetryAvailability === "awaiting_confirmation";

  const datasetName = current?.source.dataset_name ?? (statusFallbackAllowed ? status?.dataset_name : null) ?? null;
  // `selectedSubjectId` is the replay subject-selector's pending value — it
  // must never leak into `subjectId` while the active source is synthetic
  // (that field is genuinely null for synthetic per the backend contract),
  // or every consumer keyed on subjectId (event-log source-change
  // detection, MissionStatusBar) would see a spurious change the moment the
  // subject list finishes loading, even though no real session changed.
  const subjectId =
    current?.source.subject_id ?? (statusFallbackAllowed ? (status?.subject_id ?? (isReplay ? selectedSubjectId || null : null)) : null);
  const isS14 = subjectId === "S14";

  const rawReplaySessionState = deriveReplaySessionState({
    datasetConfigured,
    isReplaySource: isReplay,
    playbackState: current?.source.playback_state ?? (statusFallbackAllowed ? status?.playback_state : undefined),
    selectedSubjectId: subjectId,
    pendingAction: pending,
    requestError,
  });
  const replayPositionSeconds = current?.source.replay_position_seconds ?? (statusFallbackAllowed ? status?.replay_position_seconds : null) ?? null;
  const replayDurationSeconds = current?.source.duration_seconds ?? (statusFallbackAllowed ? status?.duration_seconds : null) ?? null;
  const playbackSpeed = (statusFallbackAllowed ? status?.playback_speed : null) ?? current?.source.playback_speed ?? null;

  // Prompt 3A.1 §4.3/§5 — "Simulated-fault status must not be presented as
  // currently confirmed" while telemetry is gated; dropping the `status`
  // fallback outside the awaiting-confirmation window means a stale
  // REST-reported fault can never outlive a disconnect/source-error.
  const fault = isReplay ? (current?.fault_injection ?? (statusFallbackAllowed ? status?.fault_injection : null) ?? null) : null;
  const faultActive = Boolean(fault?.active);
  const faultedModalities = faultActive && fault?.target ? FAULT_TARGET_MODALITIES[fault.target] : [];

  const channels = current?.channels;
  const availableChannels = current?.source.available_channels;
  const sensors = current?.sensor_health?.sensors;
  const syntheticPpgWaveform = current?.vitals?.ppg_waveform;

  const modalities: OperationalModalityState[] = FINAL_SENSOR_INVENTORY.map((entry) => {
    const rawObservation = deriveModalityObservation(entry.modality, { isReplay, channels, availableChannels, sensors });
    const isFaulted = faultedModalities.includes(entry.modality);
    const nodeState = deriveModalityNodeState({ telemetry: telemetryAvailability, isFaulted, observation: rawObservation });
    // The gate-copy override is applied only for *display* text; the plot is
    // resolved from `rawObservation` (channelBatch is already null whenever
    // telemetry is gated, since `channels` above was already forced to
    // `undefined`) — both paths agree on "no plot", only the shown reason
    // differs. A `fault` node state additionally forces both observation and
    // plot to the explicit fault copy (§4.6), regardless of what the
    // backend's channel payload still contained for this fault type.
    const observation =
      nodeState === "fault" ? applyFaultOverride(rawObservation, entry.modality) : applyTelemetryGate(rawObservation, telemetryAvailability);
    const plot = nodeState === "fault" ? null : resolvePlotSeries(entry.modality, isReplay, rawObservation, syntheticPpgWaveform);
    return {
      modality: entry.modality,
      region: entry.region,
      observation,
      nodeState,
      stateLabel: nodeStateLabel(nodeState),
      plot,
    };
  });
  const confirmedModalityCount = modalities.filter((entry) => entry.nodeState === "confirmed").length;

  const prediction = isReplay ? (current?.heart_rate_prediction ?? null) : null;
  const inference = isReplay ? (current?.heart_rate_inference ?? null) : null;
  const predictionAvailability = derivePredictionAvailability({ connected: telemetryActive, isReplay, prediction });

  let overallStateLabel: OperationalStateWord;
  if (telemetryAvailability === "source_error") overallStateLabel = "Source error";
  else if (telemetryAvailability === "disconnected") overallStateLabel = "Disconnected";
  else if (telemetryAvailability === "awaiting_confirmation") overallStateLabel = "Connected — awaiting confirmed frame";
  else if (faultActive) overallStateLabel = "Simulated fault";
  else overallStateLabel = "Confirmed";

  return {
    connected,
    connectionLabel,
    sourceType,
    sourceLabel,
    isReplay,
    sourceStateStatus,
    sourceStateError,
    telemetryAvailability,
    datasetName,
    subjectId,
    isS14,
    subjects,
    subjectListState,
    subjectListError,
    replaySessionState: rawReplaySessionState,
    replaySessionStateLabel: resolveReplayStateLabel({ telemetry: telemetryAvailability, replaySessionState: rawReplaySessionState }),
    replayPositionSeconds,
    replayDurationSeconds,
    playbackSpeed,
    isWaitingForConfirmation,
    confirmedTimestampSeconds: lastConfirmedTimestampSeconds,
    modalities,
    confirmedModalityCount,
    totalModalityCount: FINAL_SENSOR_INVENTORY.length,
    fault,
    faultActive,
    faultSummaryLabel: deriveFaultSummaryLabel(fault),
    faultedModalities,
    prediction,
    predictionAvailability,
    inference,
    inferenceStatusLabel: inferenceStatusLabel(inference, isReplay),
    overallStateLabel,
    pendingAction: pending,
    requestError,
  };
}
