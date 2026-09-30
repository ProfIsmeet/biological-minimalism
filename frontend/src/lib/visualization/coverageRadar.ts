/**
 * Mission Overview §11.2 — binary architecture-coverage radar derivation.
 *
 * DATA-TO-MARK CONTRACT (enforced by the types below):
 *
 * - Axis set: exactly the five FINAL_SENSOR_INVENTORY modalities.
 * - Series A "Selected final architecture": STATIC membership in
 *   CORE_PLUS_CONTEXT. Value is exactly 0 or 1. Never live, never derived
 *   from the current source.
 * - Series B "Observed in current confirmed source": LIVE. Value is exactly
 *   0 or 1, and is 1 ONLY when that channel is genuinely present AND
 *   confirmed right now.
 * - Scale: exactly [0, 1]. There is no percentage, quality, performance,
 *   reliability, accuracy, sensitivity or confidence anywhere in this
 *   module, and no third continuous series may be added to these axes.
 *
 * The critical fail-closed rule (§11.2): when the source is not yet
 * confirmed, or is erroring, the observation series is WITHHELD entirely
 * (`observed: null`) rather than drawn as an all-zero polygon — an all-zero
 * polygon would read as "we looked and found nothing", which is a different
 * and false claim from "we cannot yet say".
 *
 * Pure and JSX-free so the mapping is directly testable.
 */

import { FINAL_SENSOR_INVENTORY, type FinalModality } from "@/lib/architecture";
import type { ModalityNodeState } from "@/lib/monitoring/modalityNodeState";
import type { TelemetryAvailability } from "@/lib/monitoring/telemetryAvailability";

/** Exactly the modalities in the selected CORE_PLUS_CONTEXT architecture. Static fact. */
const CORE_PLUS_CONTEXT_MEMBERS: readonly FinalModality[] = ["PPG", "IMU", "ECG", "EEG", "EOG"];

export type BinaryCoverage = 0 | 1;

export interface CoverageAxis {
  modality: FinalModality;
  /** Static architecture membership — 0 or 1, never live. */
  selected: BinaryCoverage;
  /**
   * Live channel observation — 0 or 1, or null when the observation series
   * as a whole is withheld (unconfirmed/erroring source). Never a partial
   * or fractional value.
   */
  observed: BinaryCoverage | null;
  /** Exact operator-facing reason, for the semantic table beside the radar. */
  observationReason: string;
}

export interface CoverageRadarModel {
  axes: CoverageAxis[];
  /** False whenever the live polygon must not be drawn at all (§11.2 fail-closed). */
  observationSeriesAvailable: boolean;
  /** Exact reason shown in place of the withheld polygon. */
  withheldReason: string | null;
}

export function deriveCoverageRadar(params: {
  telemetry: TelemetryAvailability;
  modalityStates: { modality: FinalModality; nodeState: ModalityNodeState; unavailableReason: string | null }[];
  isReplay: boolean;
}): CoverageRadarModel {
  const { telemetry, modalityStates, isReplay } = params;

  // Fail closed: never draw an all-zero observation polygon for a source we
  // simply cannot speak for yet.
  let observationSeriesAvailable = true;
  let withheldReason: string | null = null;
  if (telemetry === "awaiting_confirmation") {
    observationSeriesAvailable = false;
    withheldReason = "AWAITING CONFIRMED SOURCE";
  } else if (telemetry === "source_error") {
    observationSeriesAvailable = false;
    withheldReason = "SOURCE ERROR — observation withheld";
  } else if (telemetry === "disconnected") {
    observationSeriesAvailable = false;
    withheldReason = "DISCONNECTED — observation withheld";
  }

  const axes: CoverageAxis[] = FINAL_SENSOR_INVENTORY.map((entry) => {
    const selected: BinaryCoverage = CORE_PLUS_CONTEXT_MEMBERS.includes(entry.modality) ? 1 : 0;
    const live = modalityStates.find((m) => m.modality === entry.modality);

    if (!observationSeriesAvailable) {
      return { modality: entry.modality, selected, observed: null, observationReason: withheldReason ?? "Withheld" };
    }

    // "Confirmed" is the only state that counts as genuinely observed. A
    // faulted, warming-up, or absent channel is 0 — and each carries its own
    // exact reason so the semantic table never collapses them together.
    const nodeState = live?.nodeState ?? "unavailable";
    if (nodeState === "confirmed") {
      return { modality: entry.modality, selected, observed: 1, observationReason: "Confirmed in current source" };
    }
    if (nodeState === "fault") {
      return { modality: entry.modality, selected, observed: 0, observationReason: "Simulated fault — channel withheld" };
    }
    if (nodeState === "warmup") {
      return { modality: entry.modality, selected, observed: 0, observationReason: "Awaiting current-window samples" };
    }
    return {
      modality: entry.modality,
      selected,
      observed: 0,
      observationReason: live?.unavailableReason ?? (isReplay ? "Not provided by this replay" : "Not reported by current telemetry"),
    };
  });

  return { axes, observationSeriesAvailable, withheldReason };
}

/**
 * Regular-polygon vertex geometry for an N-axis radar. Angle 0 points up;
 * vertices proceed clockwise. Returns SVG-space coordinates.
 */
export function radarPoint(params: { cx: number; cy: number; radius: number; index: number; count: number; value: number }): { x: number; y: number } {
  const { cx, cy, radius, index, count, value } = params;
  const angle = (index / count) * 2 * Math.PI - Math.PI / 2;
  const r = radius * value;
  return { x: round2(cx + Math.cos(angle) * r), y: round2(cy + Math.sin(angle) * r) };
}

/** Deterministic rounding so SSR and client markup match exactly (same convention as lib/format.ts round2). */
function round2(value: number): number {
  return Math.round(value * 100) / 100;
}

/** Builds the closed SVG polygon path for one binary series. */
export function radarPolygonPoints(params: { cx: number; cy: number; radius: number; values: number[] }): string {
  const { cx, cy, radius, values } = params;
  return values
    .map((value, index) => {
      const p = radarPoint({ cx, cy, radius, index, count: values.length, value });
      return `${p.x},${p.y}`;
    })
    .join(" ");
}
