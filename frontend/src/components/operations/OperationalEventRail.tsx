"use client";

import clsx from "clsx";

import type { OperationalEvent, OperationalEventKind } from "@/lib/monitoring/operationalEvents";
import { useOperationalEventStore } from "@/store/operationalEventStore";

function eventTone(kind: OperationalEventKind): string {
  if (kind === "fault_applied" || kind === "disconnected" || kind === "source_error") return "border-jury-fault/40 bg-jury-fault-soft text-jury-fault";
  if (kind === "fault_cleared" || kind === "prediction_recovered") return "border-jury-success/40 bg-jury-success-soft text-jury-success";
  if (kind === "warmup_started" || kind === "replay_loaded") return "border-jury-warning/40 bg-jury-warning-soft text-jury-warning";
  return "border-jury-border-subtle bg-surface-2 text-ink-secondary";
}

/**
 * `sourceTimestampSeconds` is the confirmed snapshot's own clock — an
 * absolute Unix epoch value from the backend, not a small session-relative
 * number — so it is never rendered as "t=Xs" (which would misleadingly read
 * as elapsed seconds). Every event instead shows the client's own wall
 * clock, keeping all event timestamps in one consistent, readable format.
 */
function formatEventTime(event: OperationalEvent): string {
  return new Date(event.clientMs).toISOString().slice(11, 19);
}

/**
 * Session-only "what changed" rail for `/mission-overview` (master prompt 3
 * §16). Reads only `useOperationalEventStore`, populated exclusively by
 * `OperationalEventLogWatcher` — never fabricates history from before the
 * current interface session.
 */
export function OperationalEventRail() {
  const events = useOperationalEventStore((state) => state.events);
  const recent = events.slice(-12).reverse();

  return (
    <section aria-labelledby="event-rail-heading" className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <h2 id="event-rail-heading" className="text-sm font-semibold text-ink-primary">
        Session events
      </h2>

      {recent.length === 0 ? (
        <p className="text-xs text-ink-muted">No session events recorded in this interface session.</p>
      ) : (
        <ul className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:gap-2">
          {recent.map((event) => (
            <li
              key={event.id}
              className={clsx("flex items-center gap-2 rounded-[6px] border px-2.5 py-1.5 text-[11px]", eventTone(event.kind))}
            >
              <span className="font-mono text-[10px] opacity-80">{formatEventTime(event)}</span>
              <span className="font-medium">
                {event.label}
                {event.modality ? ` — ${event.modality}` : ""}
                {event.simulated ? " (Simulated)" : ""}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
