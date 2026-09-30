"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { CalendarClock, Clock } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { api } from "@/lib/api";
import { toTimelineRow, usesMixedTimeBases, type EventOrigin } from "@/lib/monitoring/timelinePresentation";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useOperationalEventStore } from "@/store/operationalEventStore";

const MILESTONE_DAYS = [1, 5, 12, 30];
const CONCEPTUAL_MARKERS = [
  "Conceptual initialization checkpoint",
  "Conceptual data-interface checkpoint",
  "Conceptual architecture-review checkpoint",
  "Conceptual evidence-planning checkpoint",
];

type TimelinePayloadState = "loading" | "available" | "unavailable" | "not_applicable";

/**
 * Stage 8 §14 — origin styling. Every origin is distinguished by its WORD
 * (rendered in the badge) as well as its colour, so colour is never the only
 * state indicator (§18).
 */
const ORIGIN_STYLE: Record<EventOrigin, string> = {
  simulated_control: "border-jury-fault/40 bg-jury-fault-soft text-jury-fault",
  source_reported: "border-information/40 bg-information-soft text-information",
  inference: "border-final-accent/40 bg-final-accent-soft text-final-accent",
  transport: "border-jury-border-strong bg-surface-2 text-ink-secondary",
};

export function MissionTimelineClient() {
  const [payloadState, setPayloadState] = useState<TimelinePayloadState>("loading");
  const isReplay = useDatasetReplayMode();

  // Stage 8 §14 — the session event chronology is READ-ONLY here. This route
  // stays on its existing runtime tier: it mounts no provider, opens no
  // socket, and starts no watcher. The store is a module-level session log
  // populated by the operational routes, so events recorded there remain
  // readable after navigating here without creating a second monitoring
  // owner (§20).
  const events = useOperationalEventStore((state) => state.events);

  // Anchors the wall-clock fallback to this interface session so a
  // replay-less event reads as a session offset, never as an absolute time
  // the recorded data never claimed.
  const sessionStartRef = useRef<number | null>(null);
  if (sessionStartRef.current === null) {
    sessionStartRef.current = events.length > 0 ? Math.min(...events.map((e) => e.clientMs)) : Date.now();
  }
  const rows = useMemo(
    () => events.map((event) => toTimelineRow(event, sessionStartRef.current as number)),
    [events],
  );
  const mixedBases = usesMixedTimeBases(rows);

  useEffect(() => {
    if (isReplay) {
      setPayloadState("not_applicable");
      return;
    }
    setPayloadState("loading");
    let cancelled = false;
    Promise.all(MILESTONE_DAYS.map((day) => api.getDigitalTwin(day)))
      .then(() => {
        if (!cancelled) setPayloadState("available");
      })
      .catch(() => {
        if (!cancelled) setPayloadState("unavailable");
      });
    return () => {
      cancelled = true;
    };
  }, [isReplay]);

  return (
    <div className="flex flex-col gap-7">
      <header className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary sm:text-[28px]">Mission Timeline</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-ink-secondary">
          Chronological record of this interface session&rsquo;s operational events, followed by the conceptual architecture
          checkpoints. Every event states its origin and the clock its timestamp is measured on.
        </p>
      </header>

      {/* ---------------- Section 1: real session chronology ---------------- */}
      <section aria-labelledby="timeline-session" className="flex flex-col gap-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="timeline-session" className="text-xl font-semibold leading-tight text-ink-primary">
            Session event chronology
          </h2>
          <span className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Observed this session · not persisted</span>
        </div>

        {rows.length === 0 ? (
          <div className="rounded-[10px] border border-jury-border-subtle bg-surface-1 px-4 py-5">
            <p className="text-sm font-semibold text-ink-primary">No operational events recorded in this interface session yet.</p>
            <p className="mt-1.5 max-w-3xl text-sm leading-relaxed text-ink-secondary">
              Events are observed while an operational route is open. Visit Mission Overview or Live Signals, start a replay, and
              apply or clear a simulated fault — the resulting onset, clearing, rebuilding and recovery events will be listed here.
              Nothing is backfilled and nothing survives a page reload.
            </p>
          </div>
        ) : (
          <>
            <p className="max-w-3xl text-xs leading-relaxed text-ink-muted">
              {mixedBases
                ? "Two clocks appear below and each row says which it uses: “replay” is seconds into the recorded session; “session” is seconds since the first event observed in this interface session. They are not interchangeable."
                : rows[0]?.basis === "replay_seconds"
                  ? "Times are measured in replay time — seconds into the recorded session."
                  : "Times are measured on the session clock — seconds since the first event observed in this interface session."}
            </p>
            <div className="overflow-x-auto rounded-[10px] border border-jury-border-subtle bg-surface-1">
              <table className="w-full min-w-[520px] text-left text-sm">
                <caption className="sr-only">Operational events observed in this interface session, with origin and time basis</caption>
                <thead className="border-b border-jury-border-subtle text-xs uppercase tracking-wide text-ink-muted">
                  <tr>
                    <th scope="col" className="px-4 py-2.5 font-semibold">Event</th>
                    <th scope="col" className="px-4 py-2.5 font-semibold">Origin</th>
                    <th scope="col" className="px-4 py-2.5 font-semibold">Modality</th>
                    <th scope="col" className="px-4 py-2.5 font-semibold">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-jury-border-subtle">
                  {rows.map((row) => (
                    <tr key={row.id}>
                      <td className="px-4 py-2.5 align-top font-medium text-ink-primary">{row.label}</td>
                      <td className="px-4 py-2.5 align-top">
                        <span className={`inline-flex rounded-[4px] border px-2 py-0.5 text-xs font-semibold ${ORIGIN_STYLE[row.origin]}`}>
                          {row.originLabel}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 align-top text-ink-secondary">{row.modality ?? "—"}</td>
                      <td className="px-4 py-2.5 align-top font-mono text-xs tabular-nums text-ink-secondary">{row.timeText}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>

      {/* -------- Section 2: conceptual milestones, strongly separated -------- */}
      <section aria-labelledby="timeline-conceptual" className="flex flex-col gap-3 border-t border-jury-border-strong pt-7">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="timeline-conceptual" className="text-xl font-semibold leading-tight text-ink-primary">
            Conceptual architecture checkpoints
          </h2>
          <span className="rounded-[4px] border border-jury-warning/30 bg-jury-warning-soft px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-jury-warning">
            Not session data
          </span>
        </div>

        <div role="note" className="rounded-[8px] border border-jury-border-subtle bg-surface-1 px-4 py-3">
          <p className="text-sm font-semibold text-ink-primary">Digital Twin boundary</p>
          <p className="mt-1 max-w-3xl text-sm leading-relaxed text-ink-secondary">
            Architecture only · untrained · unvalidated · not personalized. These checkpoints are conceptual and do not report
            physiological change, adaptation, prediction, clinical readiness, or flight qualification.
          </p>
        </div>

        <Panel title="Scenario markers" subtitle="Conceptual · Day 1 · 5 · 12 · 30" icon={<CalendarClock size={16} />}>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {MILESTONE_DAYS.map((day, index) => (
              <div key={day} className="flex flex-col gap-2 rounded-[8px] border border-jury-border-subtle bg-surface-2 p-4">
                <div className="flex items-center gap-2">
                  <Clock size={14} aria-hidden="true" className="text-ink-muted" />
                  <span className="text-sm font-semibold text-ink-primary">Day {day}</span>
                </div>
                <p className="text-xs font-medium text-ink-secondary">Conceptual marker — not a measured outcome</p>
                <p className="text-xs leading-relaxed text-ink-muted">{CONCEPTUAL_MARKERS[index]}</p>
              </div>
            ))}
          </div>
          <p role="status" className="mt-4 text-xs leading-relaxed text-ink-muted">
            {payloadState === "loading"
              ? "Checking conceptual scenario availability…"
              : payloadState === "available"
                ? "Legacy scenario payload received; quantitative fields are intentionally suppressed because they have no defensible user-facing interpretation."
                : payloadState === "unavailable"
                  ? "Conceptual scenario data unavailable; no model state is inferred."
                  : "Recorded replay does not populate Digital Twin state; no model state is inferred."}
          </p>
        </Panel>
      </section>
    </div>
  );
}
