/**
 * Stage 8 §14 — pure, JSX-free chronology presentation for
 * `/mission-timeline`.
 *
 * Two rules drive this module, and both are §14 requirements the route
 * previously could not satisfy because it showed no event chronology at all:
 *
 *  1. EVERY event declares its ORIGIN. A simulated-control action, a
 *     source-reported state change, an inference transition and a transport
 *     event are different kinds of fact and must never be styled or read as
 *     one undifferentiated stream.
 *
 *  2. EVERY timestamp declares its TIME BASIS. This runtime has two genuinely
 *     different clocks — the replay position (seconds into the recorded
 *     session) and the client's wall clock — and §14 forbids mixing them
 *     without labels. An event that has no replay position is reported on the
 *     session clock and SAYS so; a missing timestamp is never fabricated.
 *
 * Pure so scripts/verify-monitoring-state.ts can assert the mapping directly.
 */

import type { OperationalEvent, OperationalEventKind } from "@/lib/monitoring/operationalEvents";

/** Where the fact came from. Never inferred from styling alone. */
export type EventOrigin = "simulated_control" | "source_reported" | "inference" | "transport";

export const EVENT_ORIGIN_LABEL: Record<EventOrigin, string> = {
  simulated_control: "Simulated control",
  source_reported: "Source-reported",
  inference: "Inference transition",
  transport: "Transport",
};

const ORIGIN_BY_KIND: Record<OperationalEventKind, EventOrigin> = {
  // Operator-driven fault injection — an action a person took, not something
  // the recorded data did.
  fault_applied: "simulated_control",
  fault_cleared: "simulated_control",
  // Replay/session state reported by the authoritative source.
  source_connected: "source_reported",
  source_changed: "source_reported",
  replay_loaded: "source_reported",
  replay_started: "source_reported",
  replay_paused: "source_reported",
  // Model/inference lifecycle.
  warmup_started: "inference",
  prediction_available: "inference",
  prediction_unavailable: "inference",
  prediction_recovered: "inference",
  // Transport-level facts.
  disconnected: "transport",
  source_error: "transport",
};

export function eventOrigin(kind: OperationalEventKind): EventOrigin {
  return ORIGIN_BY_KIND[kind];
}

/** Which clock a rendered timestamp is expressed in. */
export type TimeBasis = "replay_seconds" | "session_clock";

export const TIME_BASIS_LABEL: Record<TimeBasis, string> = {
  replay_seconds: "replay time",
  session_clock: "session clock",
};

export interface TimelineRow {
  id: string;
  label: string;
  origin: EventOrigin;
  originLabel: string;
  modality: string | null;
  /** Exact rendered time text, already carrying its own basis suffix. */
  timeText: string;
  basis: TimeBasis;
}

/**
 * Formats one event for display. `sessionStartMs` anchors the wall-clock
 * fallback so it reads as an offset into this interface session rather than
 * an absolute time the recorded data never claimed.
 */
export function toTimelineRow(event: OperationalEvent, sessionStartMs: number): TimelineRow {
  const origin = eventOrigin(event.kind);
  const hasReplayTime = event.sourceTimestampSeconds !== null && Number.isFinite(event.sourceTimestampSeconds);
  const basis: TimeBasis = hasReplayTime ? "replay_seconds" : "session_clock";
  const timeText = hasReplayTime
    ? `t+${(event.sourceTimestampSeconds as number).toFixed(1)}s replay`
    : `+${Math.max(0, (event.clientMs - sessionStartMs) / 1000).toFixed(1)}s session`;

  return {
    id: event.id,
    label: event.label,
    origin,
    originLabel: EVENT_ORIGIN_LABEL[origin],
    modality: event.modality,
    timeText,
    basis,
  };
}

/**
 * True when the rendered rows mix both clocks, so the caller must show the
 * dual-basis explanation rather than a single axis caption.
 */
export function usesMixedTimeBases(rows: TimelineRow[]): boolean {
  return rows.some((r) => r.basis === "replay_seconds") && rows.some((r) => r.basis === "session_clock");
}
