"use client";

import clsx from "clsx";
import { AlertTriangle, Database, Info, RefreshCw } from "lucide-react";

import { useMonitoringSession } from "@/components/monitoring/MonitoringSessionContext";
import { formatReplayPosition } from "@/lib/monitoring/formatMonitoringValue";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";

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
    status,
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
  const isReplay = useDatasetReplayMode();
  const { snapshot: confirmedLatest } = useConfirmedSnapshot();
  const latestSource = confirmedLatest?.source;

  if (datasetConfigured === false) {
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

  const playbackState = latestSource?.playback_state ?? status?.playback_state;
  const speed = status?.playback_speed ?? latestSource?.playback_speed ?? 1;
  const position = latestSource?.replay_position_seconds ?? status?.replay_position_seconds ?? 0;
  const duration = status?.duration_seconds ?? latestSource?.duration_seconds ?? 0;
  const activeSubject = status?.subject_id ?? latestSource?.subject_id;

  return (
    <section aria-labelledby="replay-session-heading" className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <h2 id="replay-session-heading" className="text-sm font-semibold text-ink-primary">
        Recorded replay session
      </h2>

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
        <div className="flex flex-col gap-2 sm:flex-row">
          <label className="sr-only" htmlFor="replay-subject-select">Replay subject</label>
          <select
            id="replay-subject-select"
            value={selectedSubjectId}
            onChange={(event) => setSelectedSubjectId(event.target.value)}
            disabled={subjectListState !== "available" || pending !== null}
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
            disabled={!selectedSubjectId || pending !== null}
            title={!selectedSubjectId ? "Select a subject returned by the backend before loading." : undefined}
            className="rounded-[6px] bg-final-accent px-3 py-2 text-xs font-semibold text-[#07100F] disabled:opacity-40"
          >
            {pending === "load" ? "Loading real subject…" : "Load subject"}
          </button>
          <button
            type="button"
            onClick={() => void switchToSynthetic()}
            disabled={pending !== null || !isReplay}
            className="rounded-[6px] border border-jury-border-strong px-3 py-2 text-xs font-medium text-ink-secondary disabled:opacity-40"
          >
            Switch to synthetic demo
          </button>
        </div>
      )}

      {selectedSubjectId && subjectLabel(selectedSubjectId).note ? (
        <p className="text-[11px] leading-relaxed text-jury-warning">{subjectLabel(selectedSubjectId).note}</p>
      ) : null}

      {/* Row 2 — playback controls. */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          disabled={!isReplay || pending !== null || playbackState === "ended"}
          title={!isReplay ? "Load a subject before playback controls are available." : undefined}
          onClick={() => void play()}
          className="rounded-[6px] border border-jury-border-strong px-3 py-1.5 text-xs text-ink-secondary disabled:opacity-40"
        >
          Play
        </button>
        <button
          type="button"
          disabled={!isReplay || pending !== null}
          title={!isReplay ? "Load a subject before playback controls are available." : undefined}
          onClick={() => void pause()}
          className="rounded-[6px] border border-jury-border-strong px-3 py-1.5 text-xs text-ink-secondary disabled:opacity-40"
        >
          Pause
        </button>
        <button
          type="button"
          disabled={!isReplay || pending !== null}
          title={!isReplay ? "Load a subject before playback controls are available." : undefined}
          onClick={() => void reset()}
          className="rounded-[6px] border border-jury-border-strong px-3 py-1.5 text-xs text-ink-secondary disabled:opacity-40"
        >
          Reset
        </button>
        <span className="rounded-[4px] border border-jury-border-subtle px-2 py-1 text-[11px] text-ink-muted">
          {playbackState ? playbackState : "unloaded"}
        </span>
      </div>

      {/* Row 3 — playback speed and position. */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[10px] uppercase tracking-wider text-ink-muted">Speed</span>
        {SPEEDS.map((value) => (
          <button
            key={value}
            type="button"
            disabled={!isReplay || pending !== null}
            onClick={() => void setSpeed(value)}
            className={clsx(
              "rounded-[6px] border px-2.5 py-1.5 text-xs disabled:opacity-40",
              speed === value ? "border-final-accent/50 text-final-accent" : "border-jury-border-subtle text-ink-muted",
            )}
          >
            {value}x
          </button>
        ))}
        <div className="ml-auto flex items-center gap-2 rounded-[6px] border border-jury-border-subtle bg-surface-2 px-3 py-2 text-xs text-ink-secondary">
          <Database size={13} className="shrink-0 text-ink-muted" aria-hidden="true" />
          <span>
            {isReplay
              ? `PPG-DaLiA · ${activeSubject ?? "subject not loaded"} · ${playbackState ?? "unloaded"} · ${formatReplayPosition(position, duration)}`
              : "Replay not active — synthetic demo is the current session."}
          </span>
        </div>
      </div>

      {requestError ? <p role="alert" className="text-xs text-jury-fault">{requestError}</p> : null}
    </section>
  );
}
