/**
 * Deterministic 2-decimal rounding for trig-derived SVG/CSS coordinates.
 * `Math.cos`/`Math.sin` results can differ in their last floating-point
 * digits between Next.js server rendering and client hydration (V8 build
 * differences between the Node and browser runtimes), which otherwise
 * produces a hydration-mismatch error the moment such a value is rendered
 * as a JSX attribute. Rounding to hundredths of a pixel is visually
 * meaningless but guarantees the server and client strings always match.
 */
export function round2(value: number): number {
  return Math.round(value * 100) / 100;
}

export function formatNumber(value: number, digits = 0): string {
  return value.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function formatMissionClock(timestampSeconds: number): string {
  const date = new Date(timestampSeconds * 1000);
  return date.toUTCString().split(" ")[4] + " UTC";
}

export function riskLevel(score: number, warningAt = 55, criticalAt = 78): "nominal" | "warning" | "critical" {
  if (score >= criticalAt) return "critical";
  if (score >= warningAt) return "warning";
  return "nominal";
}

export function confidenceLevel(score: number): "nominal" | "warning" | "critical" {
  if (score < 45) return "critical";
  if (score < 70) return "warning";
  return "nominal";
}

export function titleCase(value: string): string {
  return value
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
