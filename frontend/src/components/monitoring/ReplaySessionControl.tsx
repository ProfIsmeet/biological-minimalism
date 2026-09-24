"use client";

import clsx from "clsx";
import { AlertTriangle, Database, Info, RefreshCw } from "lucide-react";

import { useMonitoringSession } from "@/components/monitoring/MonitoringSessionContext";
import { deriveReplayControlPresentation } from "@/lib/monitoring/controlPresentation";
import { formatReplayPosition } from "@/lib/monitoring/formatMonitoringValue";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";

const SPEEDS = [1, 5, 10] as const;

function subjectLabel(subjectId: string): { label: string; note: string | null } {
  if (subjectId === "S14") {
    return {
      label: "S14 — robustness demonstration subject",
      note: "Single-participant stress test; not population validation.",
    };
  }
  return { label: subjectId, note: null };
}

// Master-prompt §8.2 — recorded replay session. Subjects come only from
// `/data-source/subjects`; S14 is never hard-coded as guaranteed to exist,
// and nothing here auto-selects it. When the dataset path is unconfigured
// this renders the informational (not alarming) unavailable state instead
// of the interactive controls.
export function ReplaySessionControl() {
  const {
    datasetConfigured,
    subjects,
    subjectListState,
    subjectListError,
    retrySubjectList,
    selectedSubjectId,
    setSelectedSubjectId,
    pending,
    requestError,
    switchToSynthetic,
    loadSubject,
    play,
    pause,
    reset,
    setSpeed,
  } = useMonitoringSession();
  const view = useOperationalViewModel();
  const control = deriveReplayControlPresentation({
    telemetry: view.telemetryAvailability,
    isReplay: view.isReplay,
    replaySessionState: view.replaySessionState,
    playbackSpeed: view.playbackSpeed,
    replayPositionSeconds: view.replayPositionSeconds,
    replayDurationSeconds: view.replayDurationSeconds,
    subjectId: view.subjectId,
    pendingAction: pending,
  });

  if (datasetConfigured === false && control.authoritativeCurrent) {
    return (
      <section aria-labelledby="replay-unavailable-heading" className="rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
        <div className="flex items-start gap-2.5">
          <Info size={16} className="mt-0.5 shrink-0 text-ink-muted" aria-hidden="true" />
          <div>
            <h2 id="replay-unavailable-heading" className="text-sm font-semibold text-ink-primary">
              Recorded replay unavailable
            </h2>
            <p className="mt-1.5 max-w-xl text-xs leading-relaxed text-ink-secondary">
              The PPG-DaLiA replay source is not configured in this environment. Synthetic demo mode remains
              available, but it is not a substitute for recorded replay evidence.
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section aria-labelledby="replay-session-heading" className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <h2 id="replay-session-heading" className="text-sm font-semibold text-ink-primary">
        Recorded replay session
      </h2>

      {control.unavailableMessage ? (
        <p role="status" className="rounded-md border border-information/25 bg-information-soft px-3 py-2 text-xs text-information">
          Current replay state unavailable. {control.unavailableMessage}
        </p>
      ) : null}

      {subjectListState === "error" ? (
        <div className="flex flex-col gap-2 rounded-md border border-jury-fault/30 bg-jury-fault-soft px-4 py-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-2">
            <AlertTriangle size={15} className="mt-0.5 shrink-0 text-jury-fault" aria-hidden="true" />
            <div>
              <p className="text-xs font-semibold text-ink-primary">Replay subjects unavailable</p>
              <p className="mt-0.5 text-[11px] leading-relaxed text-ink-secondary">
                The subject list could not be loaded from the replay source.
              </p>
              <p className="mt-1 text-[11px] text-ink-muted">{subjectListError}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={retrySubjectList}
            className="flex w-fit shrink-0 items-center gap-1.5 rounded-[4px] border border-jury-border-strong px-2.5 py-1.5 text-[11px] font-medium text-ink-secondary hover:bg-surface-2"
          >
            <RefreshCw size={12} aria-hidden="true" /> Retry
          </button>
        </div>
      ) : (
        // Row 1 — subject selection and load.
        <div className="flex flex-col gap-1.5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-ink-muted">
            Replay subject configuration{control.authoritativeCurrent ? "" : " — retained selection, not current telemetry"}
          </p>
          <div className="flex flex-col gap-2 sm:flex-row">
            <label className="sr-only" htmlFor="replay-subject-select">Replay subject configuration</label>
            <select
              id="replay-subject-select"
              value={selectedSubjectId}
              onChange={(event) => setSelectedSubjectId(event.target.value)}
              disabled={subjectListState !== "available" || !control.canChangeSource}
              className="min-w-40 rounded-[6px] border border-jury-border-strong bg-surface-2 px-3 py-2 text-xs text-ink-primary disabled:opacity-50"
            >
              {subjectListState === "loading"
                ? <option>Loading subjects…</option>
                : subjectListState === "available"
                  ? subjects.map((subject) => <option key={subject} value={subject}>{subjectLabel(subject).label}</option>)
                  : <option>No subjects returned by backend</option>}
            </select>
            <button
              type="button"
              onClick={() => void loadSubject(selectedSubjectId)}
              disabled={!selectedSubjectId || !control.canChangeSource}
              title={!selectedSubjectId ? "Select a subject returned by the backend before loading." : undefined}
              className="rounded-[6px] bg-final-accent px-3 py-2 text-xs font-semibold text-[#07100F] disabled:opacity-40"
            >
              {pending === "load" ? "Loading real subject…" : "Load subject"}
            </button>
            <button
              type="button"
              onClick={() => void switchToSynthetic()}
              disabled={!control.canChangeSource || !view.isReplay}
              className="rounded-[6px] border border-jury-border-strong px-3 py-2 text-xs font-medium text-ink-secondary disabled:opacity-40"
            >
              Switch to synthetic demo
            </button>
          </div>
        </div>
      )}

      {selectedSubjectId && subjectLabel(selectedSubjectId).note ? (
        <p className="text-[11px] leading-relaxed text-jury-warning">{subjectLabel(selectedSubjectId).note}</p>
      ) : null}

      {/* Row 2 — playback controls. */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          disabled={!control.canPlay}
          title={!control.authoritativeCurrent ? "Current source state must be confirmed before playback controls are available." : !view.isReplay ? "Load a subject before playback controls are available." : undefined}
          onClick={() => void play()}
          className="rounded-[6px] border border-jury-border-strong px-3 py-1.5 text-xs text-ink-secondary disabled:opacity-40"
        >
          Play
        </button>
        <button
          type="button"
          disabled={!control.canControlPlayback}
          title={!control.authoritativeCurrent ? "Current source state must be confirmed before playback controls are available." : !view.isReplay ? "Load a subject before playback controls are available." : undefined}
          onClick={() => void pause()}
          className="rounded-[6px] border border-jury-border-strong px-3 py-1.5 text-xs text-ink-secondary disabled:opacity-40"
        >
          Pause
        </button>
        <button
          type="button"
          disabled={!control.canControlPlayback}
          title={!control.authoritativeCurrent ? "Current source state must be confirmed before playback controls are available." : !view.isReplay ? "Load a subject before playback controls are available." : undefined}
          onClick={() => void reset()}
          className="rounded-[6px] border border-jury-border-strong px-3 py-1.5 text-xs text-ink-secondary disabled:opacity-40"
        >
          Reset
        </button>
        <span className="rounded-[4px] border border-jury-border-subtle px-2 py-1 text-[11px] text-ink-muted">
          {control.playbackStateLabel}
        </span>
      </div>

      {/* Row 3 — playback speed and position. */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[10px] uppercase tracking-wider text-ink-muted">Speed</span>
        {SPEEDS.map((value) => (
          <button
            key={value}
            type="button"
            disabled={!control.canControlPlayback}
            onClick={() => void setSpeed(value)}
            className={clsx(
              "rounded-[6px] border px-2.5 py-1.5 text-xs disabled:opacity-40",
              control.playbackSpeed === value ? "border-final-accent/50 text-final-accent" : "border-jury-border-subtle text-ink-muted",
            )}
          >
            {value}x
          </button>
        ))}
        <div className="ml-auto flex items-center gap-2 rounded-[6px] border border-jury-border-subtle bg-surface-2 px-3 py-2 text-xs text-ink-secondary">
          <Database size={13} className="shrink-0 text-ink-muted" aria-hidden="true" />
          <span>
            {!control.authoritativeCurrent
              ? `Current replay details unavailable — ${control.unavailableMessage}`
              : view.isReplay
                ? `${view.datasetName ?? "Dataset unavailable"} · ${control.activeSubjectId ?? "subject not loaded"} · ${control.playbackStateLabel} · ${formatReplayPosition(control.replayPositionSeconds, control.replayDurationSeconds)}`
                : "Replay not active — synthetic demo is the current session."}
          </span>
        </div>
      </div>

      {requestError ? <p role="alert" className="text-xs text-jury-fault">{requestError}</p> : null}
    </section>
  );
}
