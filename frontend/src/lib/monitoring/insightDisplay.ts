import { confidenceLevel } from "@/lib/format";
import type { StatusLevel } from "@/components/ui/StatusBadge";

export type ConfidenceDisplay =
  | { kind: "available"; value: number; level: "nominal" | "warning" | "critical" }
  | { kind: "unavailable"; label: "Unavailable"; level: "offline" };

/** Missing is a state, not the numeric value zero. A genuine zero remains zero. */
export function deriveConfidenceDisplay(value: number | null | undefined): ConfidenceDisplay {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return { kind: "unavailable", label: "Unavailable", level: "offline" };
  }
  return { kind: "available", value, level: confidenceLevel(value) };
}

export function metricLevelForAvailability(
  value: number | null | undefined,
  availableLevel: Exclude<StatusLevel, "offline"> = "nominal",
): StatusLevel {
  return isFiniteMetricValue(value) ? availableLevel : "offline";
}

export function isFiniteMetricValue(value: number | null | undefined): value is number {
  return value !== null && value !== undefined && Number.isFinite(value);
}

export function metricGroupLevelForAvailability(
  values: readonly (number | null | undefined)[],
  availableLevel: Exclude<StatusLevel, "offline"> = "nominal",
): StatusLevel {
  return values.length > 0 && values.every(isFiniteMetricValue) ? availableLevel : "offline";
}
