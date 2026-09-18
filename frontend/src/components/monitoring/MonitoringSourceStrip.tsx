"use client";

import { RefreshCw } from "lucide-react";

import { useMonitoringSession } from "@/components/monitoring/MonitoringSessionContext";
import { deriveFaultSummaryLabel } from "@/lib/monitoring/inferenceState";
import { formatReplayPosition } from "@/lib/monitoring/formatMonitoringValue";
import { deriveReplaySessionState, replaySessionStateLabel } from "@/lib/monitoring/runtimeState";
import { deriveConnectionLabel, deriveSourceLabel } from "@/lib/monitoring/sourceState";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

// Master-prompt §8.1 — monitoring source strip. Every field is either a real
// derived value or an explicit unavailable string; nothing here is a fake
// default. Reuses the same canonical connection/source-label helpers as the
// jury SourceStatusStrip so the two surfaces can never disagree.
//
// Prompt-2 corrective pass §2: reads `latest` only through
// `useConfirmedSnapshot()`, so a late-arriving frame from a source the user
// has since switched away from can never repopulate the dataset/subject/
// fault/position fields here.
export function MonitoringSourceStrip() {
  const connectionStatus = useMissionStore((state) => state.connectionStatus);
  const isReplay = useDatasetReplayMode();
  const { snapshot: latest, isWaitingForConfirmation } = useConfirmedSnapshot();
  const { status, datasetConfigured, sourceStateStatus, sourceStateError, retrySourceState, selectedSubjectId, pending, requestError } = useMonitoringSession();

  const sourceLabel = deriveSourceLabel({ connectionStatus, isReplay });
  const connectionLabel = deriveConnectionLabel(connectionStatus);
  const datasetName = latest?.source.dataset_name ?? status?.dataset_name;
  const subjectId = latest?.source.subject_id ?? status?.subject_id ?? (selectedSubjectId || null);
  const replayState = deriveReplaySessionState({
    datasetConfigured,
    isReplaySource: isReplay,
    playbackState: latest?.source.playback_state ?? status?.playback_state,
    selectedSubjectId: subjectId,
    pendingAction: pending,
    requestError,
  });
  const position = latest?.source.replay_position_seconds ?? status?.replay_position_seconds ?? null;
  const duration = latest?.source.duration_seconds ?? status?.duration_seconds ?? null;
  const fault = isReplay ? (latest?.fault_injection ?? status?.fault_injection ?? null) : null;

  const fields: { label: string; value: string }[] = [
    { label: "Source type", value: sourceLabel },
    { label: "Connection", value: connectionLabel },
    { label: "Replay state", value: replaySessionStateLabel(replayState) },
    { label: "Dataset", value: isReplay ? (datasetName ?? "Dataset unavailable") : "Not applicable — synthetic demo" },
    { label: "Subject", value: isReplay ? (subjectId ?? "No subject selected") : "Not applicable — synthetic demo" },
    {
      label: "Replay position",
      value: isReplay && (replayState === "playing" || replayState === "paused" || replayState === "completed")
        ? formatReplayPosition(position, duration)
        : "Replay not active",
    },
    { label: "Simulated fault", value: fault?.active ? deriveFaultSummaryLabel(fault) : "None" },
  ];

  return (
    <div className="flex flex-col gap-2">
      {sourceStateStatus === "error" ? (
        <div
          role="alert"
          className="flex flex-col gap-2 rounded-md border border-jury-fault/30 bg-jury-fault-soft px-3 py-2 text-xs text-ink-primary sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <p className="font-semibold">Source state could not be loaded.</p>
            {sourceStateError ? <p className="mt-0.5 text-ink-muted">{sourceStateError}</p> : null}
          </div>
          <button
            type="button"
            onClick={retrySourceState}
            className="flex w-fit shrink-0 items-center gap-1.5 rounded-[4px] border border-jury-border-strong px-2.5 py-1.5 text-[11px] font-medium text-ink-secondary hover:bg-surface-2"
          >
            <RefreshCw size={12} aria-hidden="true" /> Retry
          </button>
        </div>
      ) : null}
      {isWaitingForConfirmation ? (
        <p role="status" className="rounded-md border border-cyan-400/20 bg-cyan-400/5 px-3 py-2 text-xs text-cyan-200">
          Waiting for a confirmed frame from the selected source.
        </p>
      ) : null}
      <div
        role="status"
        className="grid grid-cols-2 gap-x-4 gap-y-3 rounded-lg border border-white/5 bg-white/[0.02] px-4 py-3 sm:grid-cols-3 lg:grid-cols-7"
      >
        {fields.map((field) => (
          <div key={field.label} className="flex flex-col gap-0.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{field.label}</span>
            <span className="text-xs font-medium text-slate-200">{field.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
