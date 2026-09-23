import { create } from "zustand";

import type { OperationalEvent } from "@/lib/monitoring/operationalEvents";

const MAX_EVENTS = 40;

interface OperationalEventState {
  events: OperationalEvent[];
  appendEvents: (events: OperationalEvent[]) => void;
  /**
   * Prompt-4 §22 — clear the session-only event log as part of the one-click
   * demo reset. This is the only supported way to empty the log; it is never
   * called automatically by the watcher (which only ever appends).
   */
  clear: () => void;
}

/**
 * Session-scoped event log (master prompt 3 §16). Populated only by
 * `OperationalEventLogWatcher` (mounted once in the root layout so the log
 * survives navigation between `/mission-overview` and `/live-monitoring`
 * within the same browser session) — never backfilled, never persisted
 * across a page reload.
 */
/**
 * Two independent effects resolve the same authoritative source-state REST
 * call on mount (LiveFeedProvider and MonitoringSessionContext, by design —
 * see MonitoringSessionContext's own doc comment) and can each briefly land
 * a different intermediate value before settling, which can otherwise
 * produce two "source_changed" (or other) events back to back for what is
 * really one observable transition. Collapsing an incoming event into a
 * no-op when it exactly repeats the immediately-preceding stored event
 * (same kind and modality) is the duplicate-event prevention this session
 * log requires, independent of the exact upstream cause.
 */
export function dedupeAgainstLast(existing: OperationalEvent[], incoming: OperationalEvent[]): OperationalEvent[] {
  const deduped: OperationalEvent[] = [];
  let last = existing[existing.length - 1] ?? null;
  for (const event of incoming) {
    if (last && last.kind === event.kind && last.modality === event.modality) continue;
    deduped.push(event);
    last = event;
  }
  return deduped;
}

export const useOperationalEventStore = create<OperationalEventState>((set) => ({
  events: [],
  appendEvents: (newEvents) =>
    set((state) => {
      const deduped = dedupeAgainstLast(state.events, newEvents);
      return deduped.length === 0 ? state : { events: [...state.events, ...deduped].slice(-MAX_EVENTS) };
    }),
  clear: () => set({ events: [] }),
}));
