import type { ModalityObservation } from "@/lib/monitoring/modalityObservation";
import type { ReplaySessionState } from "@/lib/monitoring/runtimeState";
import { replaySessionStateLabel } from "@/lib/monitoring/runtimeState";
import type { SourceStateStatus } from "@/components/monitoring/MonitoringSessionContext";

/**
 * Prompt 3A.1 §4.2 — the single authoritative "may current telemetry be
 * trusted right now" gate. Every operational component must derive its
 * current-frame display (observations, plots, prediction, fault, replay
 * position) from this, not from independent connected/isWaitingForConfirmation
 * checks scattered per-component — that scattering is exactly what let the
 * Prompt 3A `/mission-overview` UI show a disconnected modality with its
 * last-confirmed waveform still on screen (the transport-drop path never
 * cleared `missionStore.latest`, and no consumer separately re-checked
 * connection state before rendering it).
 *
 * `active` requires: WebSocket open, `/data-source/state` not in an error
 * state, and a confirmed snapshot already in hand (identity-matched to the
 * authoritative REST status — see sourceIdentity.ts). Anything else is one
 * of three fail-closed reasons, in priority order: a REST-level source error
 * takes precedence over a mere transport drop (both usually mean "nothing
 * can be trusted", but the operator-facing copy differs), then a plain
 * transport disconnect, then "connected, but no confirmed frame for the
 * current source yet" (first load, post-reconnect before a fresh frame,
 * or mid-transition to a new source/subject).
 */
export type TelemetryAvailability = "active" | "awaiting_confirmation" | "disconnected" | "source_error";

export function deriveTelemetryAvailability(params: {
  connected: boolean;
  sourceStateStatus: SourceStateStatus;
  /** Whether a snapshot already exists that is identity-confirmed against the authoritative source AND was received while transport was open. */
  hasConfirmedSnapshot: boolean;
}): TelemetryAvailability {
  const { connected, sourceStateStatus, hasConfirmedSnapshot } = params;
  if (sourceStateStatus === "error") return "source_error";
  if (!connected) return "disconnected";
  if (sourceStateStatus !== "available") return "awaiting_confirmation";
  if (!hasConfirmedSnapshot) return "awaiting_confirmation";
  return "active";
}

const GATE_COPY: Record<Exclude<TelemetryAvailability, "active">, { statusLabel: string; unavailableReason: string }> = {
  disconnected: {
    statusLabel: "Source disconnected",
    unavailableReason: "Source disconnected — no current samples",
  },
  awaiting_confirmation: {
    statusLabel: "Awaiting confirmed frame",
    unavailableReason: "Awaiting a confirmed frame from the selected source",
  },
  source_error: {
    statusLabel: "Source error",
    unavailableReason: "Source error — current samples unavailable",
  },
};

export function telemetryAvailabilityLabel(telemetry: TelemetryAvailability): string {
  return telemetry === "active" ? "Current telemetry confirmed" : GATE_COPY[telemetry].unavailableReason;
}

/**
 * Prompt 3A.1 §4.3/§4.4/§4.5 — rewrites a per-modality observation to the
 * exact required gate copy whenever telemetry is not `active`, regardless of
 * what `deriveModalityObservation` computed from the (already-gated-to-
 * undefined) source payload. `deriveModalityObservation` on its own only
 * knows "no channel/sensor data was passed in" and produces a generic
 * dataset-absence message ("Not reported by current telemetry") — that
 * message is correct for a modality genuinely absent from a dataset, but
 * wrong for a modality that IS in the dataset and simply cannot currently be
 * observed because the whole source is disconnected/unconfirmed/erroring.
 * This function is the single place that distinction is made explicit.
 */
export function applyTelemetryGate(observation: ModalityObservation, telemetry: TelemetryAvailability): ModalityObservation {
  if (telemetry === "active") return observation;
  const copy = GATE_COPY[telemetry];
  return {
    ...observation,
    state: "unavailable",
    unit: null,
    statusLabel: copy.statusLabel,
    unavailableReason: copy.unavailableReason,
    channelBatch: null,
    syntheticHealth: null,
  };
}

/**
 * Prompt 3A.1 §4.6 — "Do not show a normal clean waveform as though the
 * modality remains nominal" for a currently-faulted modality. The backend's
 * "modality dropout" fault type already stops reporting the channel
 * entirely (observed live: `wrist_bvp` genuinely absent from
 * `available_channels` while a PPG dropout fault is active), which
 * naturally produces an honest "unavailable" observation — but nothing
 * guarantees every fault type (packet loss, frozen sensor, additive noise,
 * saturation/clipping) removes the channel the same way; a fault type that
 * corrupts-in-place rather than removing the channel could otherwise still
 * deliver a channel batch that renders as a normal-looking ribbon. This is
 * the uniform frontend safety net: whenever a modality's node state is
 * `fault`, its observation and plot are always overridden here, regardless
 * of what the backend payload contained.
 */
export function applyFaultOverride(observation: ModalityObservation, modality: string): ModalityObservation {
  return {
    ...observation,
    state: "unavailable",
    unit: null,
    statusLabel: "Simulated fault",
    unavailableReason: `Simulated ${modality} fault active — current input unavailable`,
    channelBatch: null,
    syntheticHealth: null,
  };
}

/**
 * Prompt 3A.1 §5 — the mission-status-strip "Replay state" field must never
 * say `Playing`/`Paused`/`Ready` etc. while telemetry cannot be trusted, even
 * though the pure `deriveReplaySessionState` (runtimeState.ts) has no
 * awareness of transport/confirmation state and, fed a stale
 * `playbackState`, would happily keep reporting it. This wraps the raw label
 * with the gate, overriding it whenever telemetry is not active.
 */
export function resolveReplayStateLabel(params: { telemetry: TelemetryAvailability; replaySessionState: ReplaySessionState }): string {
  const { telemetry, replaySessionState } = params;
  if (telemetry === "disconnected") return "Unavailable — disconnected";
  if (telemetry === "source_error") return "Unavailable — source error";
  if (telemetry === "awaiting_confirmation") return "Awaiting source confirmation";
  return replaySessionStateLabel(replaySessionState);
}
