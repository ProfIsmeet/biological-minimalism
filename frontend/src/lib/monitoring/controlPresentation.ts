import { deriveFaultSummaryLabel } from "@/lib/monitoring/inferenceState";
import { replaySessionStateLabel, type ReplaySessionState } from "@/lib/monitoring/runtimeState";
import { telemetryAvailabilityLabel, type TelemetryAvailability } from "@/lib/monitoring/telemetryAvailability";
import type { ReplayFaultState } from "@/lib/types";

export interface ReplayControlPresentation {
  authoritativeCurrent: boolean;
  unavailableMessage: string | null;
  playbackStateLabel: string;
  playbackSpeed: number | null;
  replayPositionSeconds: number | null;
  replayDurationSeconds: number | null;
  activeSubjectId: string | null;
  canChangeSource: boolean;
  canControlPlayback: boolean;
  canPlay: boolean;
}

export function deriveReplayControlPresentation(params: {
  telemetry: TelemetryAvailability;
  isReplay: boolean;
  replaySessionState: ReplaySessionState;
  playbackSpeed: number | null;
  replayPositionSeconds: number | null;
  replayDurationSeconds: number | null;
  subjectId: string | null;
  pendingAction: string | null;
}): ReplayControlPresentation {
  const authoritativeCurrent = params.telemetry === "active";
  const unavailableMessage = authoritativeCurrent ? null : telemetryAvailabilityLabel(params.telemetry);
  const canChangeSource = authoritativeCurrent && params.pendingAction === null;
  const canControlPlayback = canChangeSource && params.isReplay;
  return {
    authoritativeCurrent,
    unavailableMessage,
    playbackStateLabel: authoritativeCurrent
      ? replaySessionStateLabel(params.replaySessionState)
      : `Not currently confirmed — ${unavailableMessage}`,
    playbackSpeed: authoritativeCurrent ? params.playbackSpeed : null,
    replayPositionSeconds: authoritativeCurrent ? params.replayPositionSeconds : null,
    replayDurationSeconds: authoritativeCurrent ? params.replayDurationSeconds : null,
    activeSubjectId: authoritativeCurrent ? params.subjectId : null,
    canChangeSource,
    canControlPlayback,
    canPlay: canControlPlayback && params.replaySessionState !== "completed",
  };
}

export interface FaultControlPresentation {
  authoritativeCurrent: boolean;
  unavailableMessage: string | null;
  faultActive: boolean;
  currentFaultLabel: string;
  canApply: boolean;
  canClear: boolean;
}

export function deriveFaultControlPresentation(params: {
  telemetry: TelemetryAvailability;
  isReplay: boolean;
  fault: ReplayFaultState | null;
  pendingAction: string | null;
}): FaultControlPresentation {
  const authoritativeCurrent = params.telemetry === "active";
  const unavailableMessage = authoritativeCurrent ? null : telemetryAvailabilityLabel(params.telemetry);
  const faultActive = authoritativeCurrent && params.isReplay && Boolean(params.fault?.active);
  const canApply = authoritativeCurrent && params.isReplay && params.pendingAction === null;
  return {
    authoritativeCurrent,
    unavailableMessage,
    faultActive,
    currentFaultLabel: !authoritativeCurrent
      ? `Fault state not currently confirmed — ${unavailableMessage}`
      : params.isReplay
        ? deriveFaultSummaryLabel(params.fault)
        : "Not applicable — recorded replay only",
    canApply,
    canClear: canApply && faultActive,
  };
}
