/**
 * Pure, JSX-free session event-log derivation for OperationalEventRail
 * (master prompt 3 §16). This codebase deliberately does not retain a
 * discrete event-history buffer anywhere else (see the old
 * InferenceResponseTimeline's honest disclosure) — this module is the first
 * place one is built, and it is built only from state the frontend itself
 * observed during the current interface session. It never reconstructs
 * events from before the page loaded and never invents a timestamp it did
 * not compute from either the payload's own clock or `Date.now()`.
 *
 * Kept separate from any React state so scripts/verify-monitoring-state.ts
 * can exercise the transition logic directly, the same convention as
 * lib/monitoring/plotSeries.ts and lib/monitoring/waveformDisplay.ts.
 */

import type { FinalModality } from "@/lib/architecture";
import type { PredictionAvailability } from "@/lib/monitoring/inferenceState";
import type { ReplaySessionState } from "@/lib/monitoring/runtimeState";
import type { SourceType } from "@/lib/monitoring/sourceState";
import type { ModelInferenceStatus } from "@/lib/types";

export type OperationalEventKind =
  | "source_connected"
  | "source_changed"
  | "replay_loaded"
  | "replay_started"
  | "replay_paused"
  | "warmup_started"
  | "prediction_available"
  | "fault_applied"
  | "prediction_unavailable"
  | "fault_cleared"
  | "prediction_recovered"
  | "disconnected"
  | "source_error";

export interface OperationalEvent {
  id: string;
  kind: OperationalEventKind;
  label: string;
  modality: FinalModality | null;
  simulated: boolean;
  sourceLabel: string;
  /** Grounded in the confirmed snapshot's own clock — null when not calculable. */
  sourceTimestampSeconds: number | null;
  /** Always available — the client's own clock at observation time. */
  clientMs: number;
}

export interface OperationalEventSignature {
  connected: boolean;
  sourceType: SourceType;
  subjectId: string | null;
  replaySessionState: ReplaySessionState;
  inferenceStatus: ModelInferenceStatus | null;
  predictionAvailability: PredictionAvailability;
  faultActive: boolean;
  faultedModalities: FinalModality[];
  sourceStateStatus: "loading" | "available" | "error";
}

const EVENT_LABEL: Record<OperationalEventKind, string> = {
  source_connected: "Source connected",
  source_changed: "Source changed",
  replay_loaded: "Replay loaded",
  replay_started: "Replay started",
  replay_paused: "Replay paused",
  warmup_started: "Warm-up started",
  prediction_available: "Prediction became available",
  fault_applied: "Simulated fault applied",
  prediction_unavailable: "Prediction became unavailable",
  fault_cleared: "Simulated fault cleared",
  prediction_recovered: "Prediction recovered",
  disconnected: "Source disconnected",
  source_error: "Source error",
};

let eventCounter = 0;

function makeEvent(params: {
  kind: OperationalEventKind;
  modality?: FinalModality | null;
  simulated?: boolean;
  sourceLabel: string;
  sourceTimestampSeconds: number | null;
  clientMs: number;
}): OperationalEvent {
  eventCounter += 1;
  return {
    id: `evt-${eventCounter}-${params.kind}`,
    kind: params.kind,
    label: EVENT_LABEL[params.kind],
    modality: params.modality ?? null,
    simulated: params.simulated ?? false,
    sourceLabel: params.sourceLabel,
    sourceTimestampSeconds: params.sourceTimestampSeconds,
    clientMs: params.clientMs,
  };
}

/**
 * Diffs two signatures and returns zero or more newly-observed events, in
 * chronological/priority order. `previous === null` means "first observation
 * this session" — only a genuinely-connected first state emits
 * `source_connected`; nothing is backfilled for the period before the page
 * mounted.
 */
export function deriveEventsFromTransition(
  previous: OperationalEventSignature | null,
  next: OperationalEventSignature,
  context: { sourceLabel: string; sourceTimestampSeconds: number | null; clientMs: number },
): OperationalEvent[] {
  const events: OperationalEvent[] = [];
  const base = { sourceLabel: context.sourceLabel, sourceTimestampSeconds: context.sourceTimestampSeconds, clientMs: context.clientMs };

  if (previous === null) {
    if (next.connected) events.push(makeEvent({ kind: "source_connected", ...base }));
    return events;
  }

  if (!previous.connected && next.connected) {
    events.push(makeEvent({ kind: "source_connected", ...base }));
    return events; // A fresh connection is never also reported as a "change" from the prior (disconnected) source.
  }
  if (previous.connected && !next.connected) {
    events.push(makeEvent({ kind: "disconnected", ...base }));
    return events; // Nothing else is meaningfully observable while disconnected.
  }

  if (previous.sourceType !== next.sourceType || previous.subjectId !== next.subjectId) {
    events.push(makeEvent({ kind: "source_changed", ...base }));
  }

  if (previous.replaySessionState === "loading" && next.replaySessionState === "ready") {
    events.push(makeEvent({ kind: "replay_loaded", ...base }));
  }
  if (previous.replaySessionState !== "playing" && next.replaySessionState === "playing") {
    events.push(makeEvent({ kind: "replay_started", ...base }));
  }
  if (previous.replaySessionState !== "paused" && next.replaySessionState === "paused") {
    events.push(makeEvent({ kind: "replay_paused", ...base }));
  }

  if (previous.inferenceStatus !== "warming_up" && next.inferenceStatus === "warming_up") {
    events.push(makeEvent({ kind: "warmup_started", ...base }));
  }

  if (!previous.faultActive && next.faultActive) {
    for (const modality of next.faultedModalities) {
      events.push(makeEvent({ kind: "fault_applied", modality, simulated: true, ...base }));
    }
  }
  if (previous.faultActive && !next.faultActive) {
    for (const modality of previous.faultedModalities) {
      events.push(makeEvent({ kind: "fault_cleared", modality, simulated: true, ...base }));
    }
  }

  if (previous.predictionAvailability !== "available" && next.predictionAvailability === "available") {
    events.push(makeEvent({ kind: previous.faultActive ? "prediction_recovered" : "prediction_available", ...base }));
  } else if (previous.predictionAvailability === "available" && next.predictionAvailability !== "available") {
    events.push(makeEvent({ kind: "prediction_unavailable", ...base }));
  }

  if (previous.sourceStateStatus !== "error" && next.sourceStateStatus === "error") {
    events.push(makeEvent({ kind: "source_error", ...base }));
  }

  return events;
}

/** Small helper so tests/consumers construct a signature with named fields only. */
export function buildOperationalEventSignature(fields: OperationalEventSignature): OperationalEventSignature {
  return fields;
}
