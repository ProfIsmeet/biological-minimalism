"use client";

import { RefreshCw } from "lucide-react";

import { useMonitoringSession } from "@/components/monitoring/MonitoringSessionContext";
import { formatReplayPosition } from "@/lib/monitoring/formatMonitoringValue";
import { deriveIdentityContextDisplay } from "@/lib/monitoring/liveMonitoringPresentation";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";

// Master-prompt §8.1 — monitoring source strip. Every field is either a real
// derived value or an explicit unavailable string; nothing here is a fake
// default. Reuses the same canonical connection/source-label helpers as the
// jury SourceStatusStrip so the two surfaces can never disagree.
//
// Corrective package 01 F-01: all displayed state comes from the same
// availability-gated operational model as Mission Overview. The session
// context is used only for the retry action.
export function MonitoringSourceStrip() {
  const view = useOperationalViewModel();
  const { retrySourceState } = useMonitoringSession();
  const retainedContext = view.telemetryAvailability !== "active";
  const datasetDisplay = deriveIdentityContextDisplay({
    kind: "Dataset",
    telemetry: view.telemetryAvailability,
    currentValue: view.datasetName,
    retainedValue: view.retainedDatasetName,
  });
  const subjectDisplay = deriveIdentityContextDisplay({
    kind: "Subject",
    telemetry: view.telemetryAvailability,
    currentValue: view.subjectId,
    retainedValue: view.retainedSubjectId,
  });

  const fields: { label: string; value: string }[] = [
    {
      label: retainedContext ? "Source context" : "Source type",
      value: retainedContext
        ? `${view.isReplay ? "RECORDED REPLAY" : "SYNTHETIC DEMO"} — retained configuration context, not current telemetry`
        : view.sourceLabel,
    },
    { label: "Connection", value: view.connectionLabel },
    { label: "Replay state", value: view.replaySessionStateLabel },
    { label: datasetDisplay.label, value: view.isReplay ? datasetDisplay.value : "Not applicable — synthetic demo" },
    { label: subjectDisplay.label, value: view.isReplay ? subjectDisplay.value : "Not applicable — synthetic demo" },
    {
      label: "Replay position",
      value: view.telemetryAvailability === "active" && view.isReplay && (view.replaySessionState === "playing" || view.replaySessionState === "paused" || view.replaySessionState === "completed")
        ? formatReplayPosition(view.replayPositionSeconds, view.replayDurationSeconds)
        : "Replay not active",
    },
    { label: "Simulated fault", value: view.faultActive ? view.faultSummaryLabel : view.telemetryAvailability === "active" ? "None" : "Not currently confirmed" },
  ];

  return (
    <div className="flex flex-col gap-2">
      {view.sourceStateStatus === "error" ? (
        <div
          role="alert"
          className="flex flex-col gap-2 rounded-md border border-jury-fault/30 bg-jury-fault-soft px-3 py-2 text-xs text-ink-primary sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <p className="font-semibold">Source state could not be loaded.</p>
            {view.sourceStateError ? <p className="mt-0.5 text-ink-muted">{view.sourceStateError}</p> : null}
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
      {view.telemetryAvailability === "awaiting_confirmation" ? (
        <p role="status" className="rounded-md border border-information/25 bg-information-soft px-3 py-2 text-xs text-information">
          Waiting for a confirmed frame from the selected source.
        </p>
      ) : null}
      {/* A11y fix (Stage 2 A1): "Replay position" updates on every telemetry
          tick during active playback (multiple times per second). A
          `role="status"` on this whole grid would re-announce all seven
          fields at that rate. The sr-only summary below carries the live
          region instead, built only from the fields that represent real
          state transitions (everything except replay position) — its text
          can only change, and therefore only be announced, when one of
          those actually changes. The visible grid itself carries no live
          role, so it stays readable on request without auto-announcing. */}
      <span className="sr-only" role="status" aria-live="polite">
        {fields.filter((field) => field.label !== "Replay position").map((field) => `${field.label}: ${field.value}`).join(". ")}
      </span>
      <div
        className={
          view.faultActive
            ? "grid grid-cols-2 gap-x-4 gap-y-3 rounded-[6px] border border-jury-fault/40 bg-surface-1 px-4 py-3 sm:grid-cols-3 lg:grid-cols-7"
            : "grid grid-cols-2 gap-x-4 gap-y-3 rounded-[6px] border border-jury-border-subtle bg-surface-1 px-4 py-3 sm:grid-cols-3 lg:grid-cols-7"
        }
      >
        {fields.map((field, index) => (
          <div key={field.label} className="flex flex-col gap-0.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-ink-muted">{field.label}</span>
            <span
              className={
                index < 2
                  ? "text-sm font-semibold text-ink-primary"
                : field.label === "Simulated fault" && view.faultActive
                    ? "text-xs font-medium text-jury-fault"
                    : "text-xs font-medium text-ink-secondary"
              }
            >
              {field.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
