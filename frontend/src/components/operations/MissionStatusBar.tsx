"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";

import { DemoControlDrawer } from "@/components/operations/DemoControlDrawer";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";

/**
 * Starts `null` (matching server render) and is set to a real timestamp only
 * after mount, so the server-rendered markup and the client's first render
 * are identical — `Date.now()` can never be used as initial state without
 * causing a hydration mismatch between the two clocks.
 */
function useNowMs(intervalMs: number): number | null {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    setNow(Date.now());
    const id = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
  return now;
}

function formatUtcClock(ms: number): string {
  return `${new Date(ms).toISOString().slice(11, 19)} UTC`;
}

function formatFrameAge(confirmedTimestampSeconds: number | null, nowMs: number): string | null {
  if (confirmedTimestampSeconds === null || !Number.isFinite(confirmedTimestampSeconds)) return null;
  const ageSeconds = nowMs / 1000 - confirmedTimestampSeconds;
  if (!Number.isFinite(ageSeconds) || ageSeconds < 0) return null;
  if (ageSeconds < 1) return "< 1s ago";
  if (ageSeconds < 60) return `${ageSeconds.toFixed(0)}s ago`;
  return `${(ageSeconds / 60).toFixed(1)} min ago`;
}

function fieldTone(kind: "primary" | "fault" | "muted" | "success"): string {
  if (kind === "fault") return "text-jury-fault";
  if (kind === "success") return "text-jury-success";
  if (kind === "muted") return "text-ink-secondary";
  return "text-ink-primary";
}

interface Field {
  label: string;
  value: string;
  tone: "primary" | "fault" | "muted" | "success";
}

/**
 * Row 1 of `/mission-overview` (master prompt 3 §11). A compact instrument
 * strip, not a tall explanatory card — every field is a real derived value
 * from the shared operational view model, and the scope label is a single
 * short sentence rather than the old long Results disclaimer paragraph.
 */
export function MissionStatusBar() {
  const view = useOperationalViewModel();
  const nowMs = useNowMs(1000);
  const frameAge = nowMs === null ? null : formatFrameAge(view.confirmedTimestampSeconds, nowMs);

  // Prompt 3A.1 §4.3/§4.4 — session identity must never leak through while
  // telemetry is flatly disconnected or the REST source-state channel is
  // erroring; it may legitimately show the *target* identity while a
  // switch-in-progress (`awaiting_confirmation`) is resolving, since that is
  // not stale data, it is the confirmed destination of an in-flight action.
  const sessionIdentity =
    view.telemetryAvailability === "disconnected"
      ? "No session"
      : view.telemetryAvailability === "source_error"
        ? "Session unavailable"
        : view.isReplay
          ? `${view.datasetName ?? "PPG-DaLiA"} · ${view.subjectId ?? "subject not loaded"}`
          : "Synthetic demo session";

  // Prompt 3A.1 §5 — "Do not display None for simulated fault when the
  // system cannot currently confirm fault state. Use Unavailable." — `None`
  // is only ever shown while telemetry is active and genuinely confirms no
  // fault is running.
  const faultValue =
    view.telemetryAvailability !== "active"
      ? "Unavailable"
      : view.faultActive
        ? view.faultSummaryLabel.replace("Simulated fault active — ", "")
        : "None";

  // Master prompt 3A §12 — required order: session, source, connection,
  // replay state, simulated fault, last confirmed frame, session clock. A
  // field that is genuinely not applicable (replay state while synthetic,
  // frame age before any frame is confirmed) is omitted entirely rather
  // than shown as a long placeholder sentence.
  const fields: Field[] = [
    { label: "Session", value: sessionIdentity, tone: "primary" },
    { label: "Source", value: view.sourceLabel, tone: view.sourceLabel === "UNAVAILABLE" ? "fault" : "primary" },
    { label: "Connection", value: view.connectionLabel, tone: view.connected ? "success" : "fault" },
  ];
  if (view.isReplay) fields.push({ label: "Replay state", value: view.replaySessionStateLabel, tone: view.telemetryAvailability === "active" ? "muted" : "fault" });
  fields.push({ label: "Simulated fault", value: faultValue, tone: view.faultActive && view.telemetryAvailability === "active" ? "fault" : "muted" });
  if (frameAge) fields.push({ label: "Last confirmed frame", value: frameAge, tone: "muted" });
  fields.push({ label: "Session time", value: nowMs === null ? "—" : formatUtcClock(nowMs), tone: "muted" });

  return (
    <div role="status" className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 px-4 py-3">
      <div className="mission-status-fields">
        {fields.map((field) => (
          <div key={field.label} className="flex min-w-0 flex-col gap-0.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-ink-muted">{field.label}</span>
            <span className={clsx("truncate text-xs font-semibold sm:text-sm", fieldTone(field.tone))}>{field.value}</span>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-jury-border-subtle pt-2.5">
        <span className="text-[11px] leading-snug text-ink-muted sm:max-w-[420px]">
          {view.isReplay ? "Recorded human-data replay" : "Synthetic demonstrator"} · Not live astronaut monitoring
        </span>
        <DemoControlDrawer />
      </div>
    </div>
  );
}
