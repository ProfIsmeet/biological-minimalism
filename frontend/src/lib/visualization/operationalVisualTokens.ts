/**
 * Mission Overview scientific visual recomposition — ONE centralized mapping
 * for every operational visualization colour, so identity/state colours can
 * never silently drift between the concentric orbit, the coverage radar, the
 * signal lanes, the pipeline and the fault timeline (the master prompt's §15
 * "do not spread raw hex values through many components" rule).
 *
 * Pure and JSX-free so scripts/verify-monitoring-state.ts can assert the
 * mapping directly, matching the existing lib/monitoring/*.ts convention.
 */

import type { IntegrityState } from "@/lib/monitoring/integrityRings";

/** Per-stage identity colours for the four concentric integrity rings (§9.3). */
export const STAGE_IDENTITY_COLOR = {
  source: "#8FA5AD",
  ppg: "#45D6E5",
  imu: "#86AEEB",
  output: "#C8D92B",
} as const;

export type StageKey = keyof typeof STAGE_IDENTITY_COLOR;

/**
 * Categorical state treatment. EVERY state carries BOTH a colour AND a
 * distinct dash pattern AND a word — colour is never the only carrier of
 * meaning (§15 / §9.3 / WCAG).
 */
export interface StateTreatment {
  /** null = use the ring's own stage identity colour (confirmed case only). */
  color: string | null;
  /** undefined = solid stroke. */
  dash?: string;
  opacity: number;
  /** Always rendered as text next to the mark — never colour-only. */
  word: string;
  /** Rounded caps only for confirmed/recovered (§9.2). */
  roundCap: boolean;
}

export const INTEGRITY_STATE_TREATMENT: Record<IntegrityState, StateTreatment> = {
  confirmed: { color: null, opacity: 1, word: "Confirmed", roundCap: true },
  recovered: { color: "#63BFB7", opacity: 1, word: "Recovered", roundCap: true },
  awaiting: { color: "#D5A45E", dash: "10 7", opacity: 0.95, word: "Awaiting confirmation", roundCap: false },
  warmup: { color: "#D5A45E", dash: "4 6", opacity: 0.95, word: "Rebuilding window", roundCap: false },
  fault: { color: "#D46F70", dash: "8 6", opacity: 1, word: "Simulated fault", roundCap: false },
  unavailable: { color: "#516269", dash: "2 7", opacity: 0.8, word: "No channel in current source", roundCap: false },
  disconnected: { color: "#516269", opacity: 0.4, word: "Disconnected", roundCap: false },
  source_error: { color: "#D46F70", dash: "2 6", opacity: 0.85, word: "Source error", roundCap: false },
};

/** Resolves the final stroke colour for a ring: identity colour when confirmed, state colour otherwise. */
export function resolveRingStroke(stage: StageKey, state: IntegrityState): string {
  const treatment = INTEGRITY_STATE_TREATMENT[state];
  return treatment.color ?? STAGE_IDENTITY_COLOR[stage];
}

/** Shared analytical-plot colours (§15). */
export const PLOT_COLOR = {
  hrLine: "#69B7AD",
  recoveryMarker: "#63BFB7",
  faultBand: "#D46F70",
  rebuildBand: "#D5A45E",
  grid: "rgba(242,246,247,0.08)",
  axisText: "#A8BAC0",
  /** Static architecture membership series on the coverage radar. */
  architectureSeries: "#C8D92B",
  /** Currently-observed-channel series on the coverage radar. */
  observationSeries: "#45D6E5",
} as const;

/** Per-modality signal-lane stroke colours and widths (§11.1). */
export const SIGNAL_LANE_STYLE = {
  PPG: { color: "#45D6E5", strokeWidth: 2.25 },
  IMU: { color: "#86AEEB", strokeWidth: 2 },
  ECG: { color: "#D46F70", strokeWidth: 2 },
} as const;

/**
 * Stable categorical connection language (§8.1 / §19). Replaces the removed
 * per-second "Last confirmed frame" ticker: the operator sees a state word
 * that only changes on a real transition, never a number that moves every
 * second purely to prove the page is alive.
 *
 * Critically, `connecting` maps to ESTABLISHING SOURCE (neutral/amber), NOT
 * to a red error — a red SOURCE ERROR is reserved for a genuine authoritative
 * request failure (`source_error`), never the ordinary startup window.
 */
export type OperationalPhase = "establishing" | "awaiting_confirmation" | "connected" | "disconnected" | "source_error";

export interface PhasePresentation {
  label: string;
  /** "neutral" and "warning" must never render as fault red (§8.1). */
  tone: "neutral" | "warning" | "nominal" | "fault";
}

export const PHASE_PRESENTATION: Record<OperationalPhase, PhasePresentation> = {
  establishing: { label: "ESTABLISHING SOURCE", tone: "warning" },
  awaiting_confirmation: { label: "AWAITING CONFIRMATION", tone: "warning" },
  connected: { label: "CONNECTED", tone: "nominal" },
  disconnected: { label: "DISCONNECTED", tone: "fault" },
  source_error: { label: "SOURCE ERROR", tone: "fault" },
};

/**
 * Derives the operational phase from the two authoritative inputs already
 * owned by the shared view model. No new state, no new source of truth.
 */
export function deriveOperationalPhase(params: {
  connectionLabel: "CONNECTING" | "CONNECTED" | "DISCONNECTED";
  telemetryAvailability: "active" | "awaiting_confirmation" | "disconnected" | "source_error";
}): OperationalPhase {
  const { connectionLabel, telemetryAvailability } = params;
  // A genuine authoritative REST failure outranks everything — this is the
  // ONLY path to the red SOURCE ERROR presentation.
  if (telemetryAvailability === "source_error") return "source_error";
  // The ordinary startup window: the socket has not opened yet. Neutral/amber,
  // never red (§8.1).
  if (connectionLabel === "CONNECTING") return "establishing";
  if (connectionLabel === "DISCONNECTED" || telemetryAvailability === "disconnected") return "disconnected";
  if (telemetryAvailability === "awaiting_confirmation") return "awaiting_confirmation";
  return "connected";
}
