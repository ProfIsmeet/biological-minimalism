/**
 * Stage 6 Visualization C — pure, JSX-free fault/recovery timeline
 * derivation. Consumes ONLY the existing authoritative sources: the
 * session's own `OperationalEvent[]` log (lib/monitoring/operationalEvents.ts
 * — real `sourceTimestampSeconds` grounded in the confirmed snapshot's own
 * replay clock, or null when not calculable) and the existing `HrTrendSample`
 * shape already used by lib/monitoring/hrTrend.ts. It never invents a
 * timestamp, never evenly-spaces events when a real one is unavailable, and
 * never substitutes client wall-clock arrival order for replay time.
 *
 * Design rule (master prompt §12): if ANY event that must appear on the
 * time-scaled axis lacks `sourceTimestampSeconds`, the whole plotted set for
 * that render falls back to `axisAvailable: false` and the caller must show
 * the text chronology instead of a false/misleading axis — never a mix of
 * real and fabricated positions on the same axis.
 */

import type { OperationalEvent, OperationalEventKind } from "@/lib/monitoring/operationalEvents";

export type FaultTimelineEventClass = "fault_onset" | "fault_clear" | "recovery" | "other";

const EVENT_CLASS: Partial<Record<OperationalEventKind, FaultTimelineEventClass>> = {
  fault_applied: "fault_onset",
  fault_cleared: "fault_clear",
  prediction_recovered: "recovery",
  prediction_unavailable: "fault_onset",
  prediction_available: "recovery",
};

export interface FaultTimelineEvent {
  id: string;
  label: string;
  eventClass: FaultTimelineEventClass;
  /** Always true for fault_applied/fault_cleared in this runtime — the only fault-injection mechanism is the simulated-fault control. Never mislabels an organic/source fault as simulated. */
  simulated: boolean;
  modality: string | null;
  timeSeconds: number | null;
  clientMs: number;
}

export interface FaultInterval {
  id: string;
  modality: string | null;
  simulated: boolean;
  onsetSeconds: number;
  /** null while the fault is still active — the caller extends the interval to the current chart edge, never inventing a clear time. */
  clearSeconds: number | null;
  ongoing: boolean;
}

export interface HrPoint {
  timeSeconds: number;
  /** null marks an explicit withheld/missing interval — never rendered as 0 and never connected across. */
  heartRateBpm: number | null;
}

export interface FaultRecoveryTimelineResult {
  axisAvailable: boolean;
  events: FaultTimelineEvent[];
  intervals: FaultInterval[];
  hrPoints: HrPoint[];
  domainSeconds: [number, number] | null;
}

function classify(event: OperationalEvent): FaultTimelineEventClass {
  return EVENT_CLASS[event.kind] ?? "other";
}

/**
 * Builds the timeline model from the raw event log and HR history. `nowSeconds`
 * is the current replay position (used only to extend an ongoing fault
 * interval to the current edge — never to fabricate a clear time).
 */
export function deriveFaultRecoveryTimeline(
  rawEvents: OperationalEvent[],
  hrSamples: { timestampSeconds: number; heartRateBpm: number | null }[],
  nowSeconds: number | null,
): FaultRecoveryTimelineResult {
  const relevant = rawEvents.filter((e) => classify(e) !== "other" || e.kind === "warmup_started");
  const events: FaultTimelineEvent[] = relevant.map((e) => ({
    id: e.id,
    label: e.label,
    eventClass: classify(e),
    simulated: e.simulated,
    modality: e.modality,
    timeSeconds: e.sourceTimestampSeconds,
    clientMs: e.clientMs,
  }));

  const axisAvailable = events.length > 0 && events.every((e) => e.timeSeconds !== null);

  // Pair fault_applied -> fault_cleared per modality, in chronological event order.
  const intervals: FaultInterval[] = [];
  const openByModality = new Map<string, FaultTimelineEvent>();
  for (const event of events) {
    if (event.eventClass === "fault_onset" && event.modality) {
      openByModality.set(event.modality, event);
    } else if (event.eventClass === "fault_clear" && event.modality) {
      const open = openByModality.get(event.modality);
      if (open && axisAvailable && open.timeSeconds !== null && event.timeSeconds !== null) {
        intervals.push({
          id: `${open.id}->${event.id}`,
          modality: event.modality,
          simulated: open.simulated,
          onsetSeconds: open.timeSeconds,
          clearSeconds: event.timeSeconds,
          ongoing: false,
        });
      }
      openByModality.delete(event.modality);
    }
  }
  // Any still-open fault extends to the current replay edge, never a fabricated clear time.
  if (axisAvailable && nowSeconds !== null) {
    for (const open of openByModality.values()) {
      if (open.timeSeconds !== null) {
        intervals.push({
          id: `${open.id}->ongoing`,
          modality: open.modality,
          simulated: open.simulated,
          onsetSeconds: open.timeSeconds,
          clearSeconds: null,
          ongoing: true,
        });
      }
    }
  }

  const hrPoints: HrPoint[] = hrSamples
    .filter((s) => Number.isFinite(s.timestampSeconds))
    .sort((a, b) => a.timestampSeconds - b.timestampSeconds)
    .map((s) => ({ timeSeconds: s.timestampSeconds, heartRateBpm: s.heartRateBpm }));

  let domainSeconds: [number, number] | null = null;
  if (axisAvailable) {
    const times = [
      ...events.map((e) => e.timeSeconds!),
      ...hrPoints.map((p) => p.timeSeconds),
      ...(nowSeconds !== null ? [nowSeconds] : []),
    ];
    if (times.length > 0) domainSeconds = [Math.min(...times), Math.max(...times)];
  }

  return { axisAvailable, events, intervals, hrPoints, domainSeconds };
}
