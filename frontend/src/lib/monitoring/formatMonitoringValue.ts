/**
 * Small, deterministic display-only transforms shared by the live-monitoring
 * signal stack. None of these touch model input — they exist purely so the
 * chart/label code in components doesn't re-derive the same formatting
 * differently in five places.
 */

import { downsampleExtremaPreserving } from "./waveformDisplay";

export function formatSecondsClock(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value.toFixed(1)}s`;
}

export function formatReplayPosition(position: number | null | undefined, duration: number | null | undefined): string {
  if (position === null || position === undefined) return "—";
  if (duration === null || duration === undefined) return formatSecondsClock(position);
  return `${position.toFixed(1)} / ${duration.toFixed(1)} s`;
}

export function formatFaultTypeLabel(faultType: string | null | undefined): string {
  return faultType ? faultType.replaceAll("_", " ") : "—";
}

/**
 * Client-side display transform only — computed from the same raw payload
 * the chart otherwise renders per-axis, never fed back into model input.
 * Documented formula (master prompt §8.3 IMU): sqrt(x² + y² + z²).
 */
export function computeAccelerationMagnitude(rows: number[][]): number[] {
  return rows.map((row) => {
    const x = row[0] ?? 0;
    const y = row[1] ?? 0;
    const z = row[2] ?? 0;
    return Math.sqrt(x * x + y * y + z * z);
  });
}

/**
 * Display-only decimation (master prompt 3 §8.6) — never applied to model
 * input, never mutates the source array. Labeled "Display downsampled" by
 * the caller whenever this actually reduces the sample count. Delegates to
 * the deterministic extrema-preserving bucket algorithm in
 * lib/monitoring/waveformDisplay.ts so a narrow peak/trough between flat
 * regions is never discarded the way plain stride decimation would discard
 * it; this wrapper keeps the flat `values` shape existing callers expect.
 */
export function downsampleForDisplay(data: number[], maxPoints = 400): { values: number[]; downsampled: boolean } {
  const { points, downsampled } = downsampleExtremaPreserving(data, maxPoints);
  return { values: points.map((point) => point.value), downsampled };
}
